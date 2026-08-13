import asyncio

from curl_cffi.requests import AsyncSession
from camoufox.async_api import AsyncCamoufox

from constants import BOOTSTRAP_HEADLESS, IMPERSONATE_CANDIDATES
from parsing import looks_like_challenge
import paths


def camoufox_ctx(headless: bool) -> AsyncCamoufox:
    return AsyncCamoufox(
        headless=headless,
        persistent_context=False,
        humanize=True,
        geoip=True,
        i_know_what_im_doing=True,
    )


async def wait_for_challenge_clear(
    page,
    timeout: int = 60,
    extra_wait_on_timeout: int = 0,
    log_prefix: str | None = None,
    reload: bool = True,
) -> str:
    elapsed = 0.0
    backoff = 1.0

    while elapsed < timeout:
        title = await page.title()
        html = await page.content()

        if not looks_like_challenge(200, html) and "just a moment" not in title.lower():
            return html

        if log_prefix:
            print(f"{log_prefix}Cloudflare challenge detected, waiting {backoff:.1f}s...")

        await page.wait_for_timeout(int(backoff * 1000))
        elapsed += backoff
        backoff = min(backoff + 0.5, 2.0)

        if reload:
            try:
                await page.reload(wait_until="domcontentloaded", timeout=60000)
            except Exception:
                pass

    if extra_wait_on_timeout:
        await page.wait_for_timeout(extra_wait_on_timeout)

    return await page.content()


async def bootstrap_session(target_url: str | None = None) -> dict[str, object] | None:
    url = target_url or paths.CHAPTER_URL_TMPL.format(paths.START_CHAPTER)

    print(f"[bootstrap] {url}")

    async with camoufox_ctx(BOOTSTRAP_HEADLESS) as browser:
        page = await browser.new_page()

        await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await wait_for_challenge_clear(
            page,
            log_prefix="[bootstrap] ",
        )

        user_agent = await page.evaluate("() => navigator.userAgent")
        cookies = {c["name"]: c["value"] for c in await page.context.cookies()}

    session_data = {
        "cookies": cookies,
        "user_agent": user_agent,
    }

    print(f"[bootstrap] {len(cookies)} cookies captured")
    return session_data


async def bootstrap_with_retry(
    max_attempts: int = 3,
    target_url: str | None = None,
) -> dict[str, object] | None:
    for attempt in range(1, max_attempts + 1):
        try:
            return await bootstrap_session(target_url=target_url)
        except Exception as e:
            print(f"[bootstrap] Error {attempt}/{max_attempts}: {type(e).__name__}: {e}")
            if attempt < max_attempts:
                await asyncio.sleep(5 * attempt)
    return None


def make_impersonate_session() -> tuple[AsyncSession, str]:
    last_err = None

    for profile in IMPERSONATE_CANDIDATES:
        try:
            return AsyncSession(impersonate=profile), profile
        except Exception as e:
            last_err = e

    raise RuntimeError(f"No working impersonate profile found: {last_err}")