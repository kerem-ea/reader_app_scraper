import asyncio
import random

from .constants import MIN_WORD_COUNT, REQUEST_TIMEOUT
from .fetch import record_failure, record_success
from .parsing import extract_content, looks_like_challenge
from . import paths
from .session import camoufox_ctx, wait_for_challenge_clear


# Extract content from browser HTML; record it if it passes the min word count.
async def _handle_content_success(html, chapter_number, url, writer, stats, total, chapter_titles, settings, site_config):
    text, wc = extract_content(html, site_config=site_config)
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
            source_html=html,
        )
        await asyncio.sleep(random.uniform(settings.min_delay, settings.delay_between))
        return True
    return False


# Fetch one chapter with a real browser, clicking through challenges if needed.
async def fetch_one_browser(
    page,
    prepare_page,
    chapter_number,
    url,
    writer,
    stats,
    total,
    settings,
    chapter_titles,
    site_config=None,
):
    chap_id = f"chapter-{chapter_number}"
    page_ok = True

    async def try_click_challenge_button(target_page):
        click_keywords = [
            "next",
            "continue",
            "proceed",
            "verify",
            "accept",
            "submit",
            "challenge",
        ]
        candidates = await target_page.query_selector_all("button, a, input[type=submit]")
        if not candidates:
            return False

        try:
            texts = await target_page.evaluate(
                "els => els.map(el => (el.innerText || el.value || '').toLowerCase().trim())",
                candidates,
            )
        except Exception:
            texts = []
            for element in candidates:
                try:
                    text = await target_page.evaluate(
                        "el => (el.innerText || el.value || '').toLowerCase().trim()",
                        element,
                    )
                except Exception:
                    text = ""
                texts.append(text)

        for element, text in zip(candidates, texts):
            if any(keyword in text for keyword in click_keywords):
                print(f"[browser] {chap_id} trying click on challenge element: {text}")
                try:
                    await element.click()
                    await target_page.wait_for_timeout(1000)
                    return True
                except Exception as exc:
                    print(f"[browser] {chap_id} challenge click error: {exc}")
        return False

    for attempt in range(1, settings.max_retries + 1):
        try:
            print(f"[browser] {chap_id} {attempt}/{settings.max_retries}")
            await page.goto(url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT * 1000)
            await page.wait_for_timeout(random.randint(250, 700))

            html = await wait_for_challenge_clear(page, timeout=5, extra_wait_on_timeout=0, reload=False)

            if looks_like_challenge(0, html):
                print(f"[cf] {chap_id} browser blocked, attempt {attempt}/{settings.max_retries}")
                clicked = await try_click_challenge_button(page)
                if clicked:
                    html = await wait_for_challenge_clear(page, timeout=10, extra_wait_on_timeout=1000, reload=False)

                if looks_like_challenge(0, html):
                    html = await wait_for_challenge_clear(page, timeout=20, extra_wait_on_timeout=1500)

                if not looks_like_challenge(0, html):
                    if await _handle_content_success(html, chapter_number, url, writer, stats, total, chapter_titles, settings, site_config):
                        return page_ok

                await asyncio.sleep(random.uniform(*settings.challenge_wait))
                try:
                    await page.close()
                except Exception:
                    pass
                if attempt < settings.max_retries:
                    page = await prepare_page()
                    continue
                page_ok = False
                break

            if await _handle_content_success(html, chapter_number, url, writer, stats, total, chapter_titles, settings, site_config):
                return page_ok

            if attempt < settings.max_retries:
                await asyncio.sleep(random.uniform(*settings.challenge_wait))

        except Exception as exc:
            print(f"[!] {chap_id} browser error {attempt}/{settings.max_retries}: {type(exc).__name__}: {exc}")
            if attempt < settings.max_retries:
                await asyncio.sleep(random.uniform(3.0, 6.0))
                try:
                    await page.close()
                except Exception:
                    pass
                page = await prepare_page()
                continue

    print(f"[-] FAILED: {chap_id}")
    record_failure(chapter_number)
    stats["failed"] += 1
    return page_ok


# Drive a pool of Camoufox pages to scrape all queued chapters.
async def run_browser_mode(
    queue,
    writer,
    stats,
    total,
    settings,
    chapter_titles,
    site_config=None,
):
    print("[browser] Launching Camoufox...")

    async with camoufox_ctx(False) as browser:
        page_count = min(settings.max_concurrent, 10)
        pages = []

        async def prepare_page(existing_page=None):
            if existing_page is not None and not getattr(existing_page, "is_closed", lambda: False)():
                return existing_page

            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(paths.NOVEL_URL, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT * 1000)
            await page.wait_for_timeout(random.randint(180, 320))
            await wait_for_challenge_clear(page, timeout=30, extra_wait_on_timeout=1500)
            return page

        for _ in range(page_count):
            page = await prepare_page()
            pages.append(page)

        page_pool = asyncio.Queue()
        for page in pages:
            await page_pool.put(page)

        async def worker(chapter_number, url):
            page = await page_pool.get()
            page_ok = True
            try:
                if getattr(page, "is_closed", lambda: False)():
                    page = await prepare_page()
                page_ok = await fetch_one_browser(
                    page,
                    prepare_page,
                    chapter_number,
                    url,
                    writer,
                    stats,
                    total,
                    settings,
                    chapter_titles,
                    site_config=site_config,
                )
            finally:
                if getattr(page, "is_closed", lambda: False)() or not page_ok:
                    if not getattr(page, "is_closed", lambda: False)():
                        try:
                            await page.close()
                        except Exception:
                            pass
                    page = await prepare_page()
                await page_pool.put(page)

        await asyncio.gather(*(worker(chapter_number, url) for chapter_number, url in queue))

    print("[browser] Closed")