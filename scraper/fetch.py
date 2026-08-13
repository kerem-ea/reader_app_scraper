import asyncio
import time

from constants import (
    DEFAULT_HEADERS,
    FAIL_STREAK_LIMIT,
    MIN_WORD_COUNT,
    RATE_LIMIT_STREAK_LIMIT,
    REQUEST_TIMEOUT,
    REBOOTSTRAP_EVERY_N,
)
from parsing import (
    extract_content,
    extract_title_from_chapter_page,
    is_rate_limited,
    looks_like_challenge,
    parse_retry_after,
)
from progress import print_progress_line
from paths import NOVEL_URL
from session import bootstrap_with_retry, make_impersonate_session

failed_chapters: set[int] = set()


async def record_success(
    chapter_number: int,
    url: str,
    text: str,
    wc: int,
    writer,
    stats: dict,
    total: int,
    chapter_titles: dict[int, str],
    source_html: str | None = None,
) -> None:
    chapter_id = f"chapter-{chapter_number}"
    chapter_title = chapter_titles.get(chapter_number)
    if not chapter_title and source_html:
        chapter_title = extract_title_from_chapter_page(source_html)

    await writer.add(
        {
            "id": chapter_id,
            "chapter_number": chapter_number,
            "title": chapter_title,
            "url": url,
            "word_count": wc,
            "text": text,
            "status": "success",
        }
    )

    stats["done"] += 1

    if chapter_number in failed_chapters:
        failed_chapters.discard(chapter_number)
        if stats["failed"] > 0:
            stats["failed"] -= 1

    print_progress_line(
        chapter_id,
        chapter_title,
        stats["done"],
        total,
        stats["t0"],
    )


def record_failure(chapter_number: int) -> None:
    if chapter_number not in failed_chapters:
        failed_chapters.add(chapter_number)


class Gate:
    def __init__(self, settings):
        self.settings = settings
        self.lock = asyncio.Lock()
        self.next_slot = 0.0
        self.cooldown_until = 0.0
        self.fail_streak = 0
        self.rate_limit_streak = 0
        self.clean_streak = 0
        self.current_delay = settings.delay_between

    async def acquire_slot(self):
        async with self.lock:
            now = time.time()

            if now < self.cooldown_until:
                await asyncio.sleep(self.cooldown_until - now)
                now = time.time()

            if now < self.next_slot:
                await asyncio.sleep(self.next_slot - now)
                now = time.time()

            self.next_slot = now + self.current_delay

    async def success(self):
        async with self.lock:
            self.fail_streak = 0
            self.rate_limit_streak = 0
            self.clean_streak += 1

            if (
                self.clean_streak >= self.settings.ramp_down_every
                and self.current_delay > self.settings.min_delay
            ):
                self.clean_streak = 0
                self.current_delay = max(
                    self.settings.min_delay,
                    self.current_delay * self.settings.ramp_down_factor,
                )

    async def rate_limit_failure(self, retry_after: float | None = None):
        async with self.lock:
            self.rate_limit_streak += 1
            self.clean_streak = 0
            self.current_delay = min(self.current_delay * 1.8, 15.0)

            if retry_after:
                self.cooldown_until = time.time() + retry_after
            elif self.rate_limit_streak >= RATE_LIMIT_STREAK_LIMIT:
                pause = self.settings.global_cooldown * 2
                self.cooldown_until = time.time() + pause
                self.rate_limit_streak = 0

    async def generic_failure(self, retry_after: float | None = None):
        async with self.lock:
            self.fail_streak += 1
            self.clean_streak = 0
            self.current_delay = min(self.current_delay * 1.5, 10.0)

            if retry_after:
                self.cooldown_until = time.time() + retry_after
            elif self.fail_streak >= FAIL_STREAK_LIMIT:
                self.cooldown_until = time.time() + self.settings.global_cooldown
                self.fail_streak = 0


async def fetch_one(
    session_holder,
    chapter_number: int,
    url: str,
    sem: asyncio.Semaphore,
    gate: Gate,
    writer,
    stats: dict,
    total: int,
    settings,
    chapter_titles: dict[int, str],
    site_config=None,
):
    chap_id = f"chapter-{chapter_number}"
    async with sem:
        for attempt in range(settings.max_retries):
            await gate.acquire_slot()
            session = session_holder["session"]

            try:
                headers = dict(DEFAULT_HEADERS)
                headers["Referer"] = NOVEL_URL
                headers["User-Agent"] = session_holder["user_agent"]

                response = await session.get(
                    url,
                    timeout=REQUEST_TIMEOUT,
                    cookies=session_holder["cookies"],
                    headers=headers,
                )
            except Exception as e:
                print(
                    f"[!] {chap_id} request error {attempt}/{settings.max_retries}: {type(e).__name__}: {e}"
                )
                await gate.generic_failure()
                continue

            retry_after = parse_retry_after(response.headers)
            challenge = looks_like_challenge(response.status_code, response.text)

            if response.status_code == 200 and not challenge:
                text, wc = extract_content(response.text, site_config=site_config)
                if wc >= MIN_WORD_COUNT:
                    await record_success(
                        chapter_number,
                        url,
                        text,
                        wc,
                        writer,
                        stats,
                        total,
                        chapter_titles,
                        source_html=response.text,
                    )
                    await gate.success()
                    return

            if challenge:
                print(f"[cf] {chap_id} challenge 1/1")
                break

            if is_rate_limited(response.status_code):
                await gate.rate_limit_failure(retry_after)
                continue

            await gate.generic_failure(retry_after)

        print(f"[-] FAILED: {chap_id}")
        record_failure(chapter_number)
        stats["failed"] += 1


async def run_fast_mode(
    queue,
    writer,
    stats: dict,
    total: int,
    settings,
    chapter_titles: dict[int, str],
    site_config=None,
):
    session_data = await bootstrap_with_retry()
    if session_data is None:
        print("[bootstrap] Failed to establish session.")
        return

    session, profile_used = make_impersonate_session()
    print(f"[http] {profile_used}")

    session_holder = {
        "session": session,
        "cookies": session_data["cookies"],
        "user_agent": session_data["user_agent"],
    }

    refresh_lock = asyncio.Lock()
    gate = Gate(settings)
    sem = asyncio.Semaphore(settings.max_concurrent)

    async def periodic_refresh_watcher():
        last_refresh_at = 0
        while True:
            await asyncio.sleep(15)
            if stats["done"] - last_refresh_at >= REBOOTSTRAP_EVERY_N:
                last_refresh_at = stats["done"]
                async with refresh_lock:
                    new_data = await bootstrap_with_retry()
                    if new_data:
                        session_holder.update(
                            cookies=new_data["cookies"],
                            user_agent=new_data["user_agent"],
                        )

    watcher_task = asyncio.create_task(periodic_refresh_watcher())

    try:
        await asyncio.gather(
            *(
                fetch_one(
                    session_holder,
                    chapter_number,
                    url,
                    sem,
                    gate,
                    writer,
                    stats,
                    total,
                    settings,
                    chapter_titles,
                    site_config=site_config,
                )
                for chapter_number, url in queue
            )
        )

    finally:
        watcher_task.cancel()
        try:
            await watcher_task
        except asyncio.CancelledError:
            pass
        await session.close()
