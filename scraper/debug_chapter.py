import argparse
import asyncio
import random
from pathlib import Path

from constants import DEFAULT_HEADERS, REQUEST_TIMEOUT
from parsing import extract_content, extract_title_from_chapter_page, looks_like_challenge
from paths import initialize_paths, NOVEL_URL, CHAPTER_URL_TMPL
from session import bootstrap_with_retry, make_impersonate_session, camoufox_ctx, wait_for_challenge_clear
from site_config import SiteRegistry

HTML_OUT_DIR = Path(__file__).resolve().parent / "data"
HTML_OUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Debug a single chapter fetch using the new site config flow."
    )
    parser.add_argument(
        "novel",
        help="Novel slug or supported novel URL, e.g. shadow-slave or https://freewebnovel.com/novel/shadow-slave",
    )
    parser.add_argument(
        "chapter",
        type=int,
        help="Chapter number to debug",
    )
    parser.add_argument(
        "--mode",
        choices=["browser", "http"],
        default="browser",
        help="Fetch mode to use for debugging",
    )
    parser.add_argument(
        "--attempts",
        type=int,
        default=4,
        help="Number of attempts to try before giving up",
    )
    parser.add_argument(
        "--save-html",
        action="store_true",
        help="Save the response HTML to a local file for inspection",
    )
    parser.add_argument(
        "--save-screenshot",
        action="store_true",
        help="Save a browser screenshot when using browser mode",
    )
    return parser.parse_args()


async def debug_http(site_config, novel, chapter, attempts, save_html):
    initialize_paths(site_config, novel, chapter, chapter)

    session_data = await bootstrap_with_retry()
    if session_data is None:
        raise RuntimeError("Failed to bootstrap a session for debug_http")

    url = CHAPTER_URL_TMPL.format(chapter)
    session, profile_used = make_impersonate_session()

    print(f"[debug] Using impersonate profile: {profile_used}")
    print(f"[debug] Chapter URL: {url}")

    try:
        for attempt in range(1, attempts + 1):
            print(f"[debug][http] Attempt {attempt}/{attempts}")
            try:
                headers = dict(DEFAULT_HEADERS)
                headers["Referer"] = NOVEL_URL
                headers["User-Agent"] = session_data["user_agent"]

                response = await session.get(
                    url,
                    timeout=REQUEST_TIMEOUT,
                    cookies=session_data["cookies"],
                    headers=headers,
                )
            except Exception as exc:
                print(f"[debug][http] Request error: {type(exc).__name__}: {exc}")
                continue

            print(f"[debug][http] status_code={response.status_code}")
            print(f"[debug][http] challenge={looks_like_challenge(response.status_code, response.text)}")
            print("[debug][http] headers={0}".format({k: response.headers.get(k) for k in ["Retry-After", "Server"]}))

            if save_html:
                html_path = HTML_OUT_DIR / f"debug_chapter_{novel}_{chapter}_http.html"
                html_path.write_text(response.text, encoding="utf-8")
                print(f"[debug][http] Saved HTML to {html_path}")

            text, wc = extract_content(response.text)
            title = extract_title_from_chapter_page(response.text)

            print(f"[debug][http] extracted word_count={wc}")
            print(f"[debug][http] extracted title={title!r}")

            if wc > 100:
                return

            if attempt < attempts:
                await asyncio.sleep(random.uniform(1.5, 3.5))

        raise RuntimeError("HTTP debug fetch did not return readable chapter content")

    finally:
        await session.close()


async def debug_browser(site_config, novel, chapter, attempts, save_html, save_screenshot):
    initialize_paths(site_config, novel, chapter, chapter)
    url = CHAPTER_URL_TMPL.format(chapter)

    print(f"[debug] Chapter URL: {url}")
    print("[debug] Launching Camoufox...")

    async with camoufox_ctx(False) as ctx:
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        for attempt in range(1, attempts + 1):
            print(f"[debug][browser] Attempt {attempt}/{attempts}")
            try:
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=120000,
                )

                await page.wait_for_timeout(random.uniform(0.5, 1.2) * 1000)
                html = await wait_for_challenge_clear(
                    page,
                    timeout=45,
                    extra_wait_on_timeout=3500,
                    log_prefix="[debug] ",
                )

                title = await page.title()
                is_challenge = looks_like_challenge(0, html)
                print(f"[debug][browser] page title={title!r}")
                print(f"[debug][browser] challenge_detected={is_challenge}")

                if save_html:
                    html_path = HTML_OUT_DIR / f"debug_chapter_{novel}_{chapter}_browser.html"
                    html_path.write_text(html, encoding="utf-8")
                    print(f"[debug][browser] Saved HTML to {html_path}")

                if save_screenshot:
                    screenshot_path = HTML_OUT_DIR / f"debug_chapter_{novel}_{chapter}_browser.png"
                    await page.screenshot(path=str(screenshot_path), full_page=True)
                    print(f"[debug][browser] Saved screenshot to {screenshot_path}")

                content, wc = extract_content(html)
                extracted_title = extract_title_from_chapter_page(html)
                print(f"[debug][browser] extracted word_count={wc}")
                print(f"[debug][browser] extracted title={extracted_title!r}")

                if not is_challenge and wc >= 50:
                    return

                if attempt < attempts:
                    print("[debug][browser] Content not sufficient, retrying after delay...")
                    await asyncio.sleep(random.uniform(2.0, 4.0))
                    await page.reload(wait_until="domcontentloaded", timeout=120000)
                    continue

                raise RuntimeError("Browser debug fetch was unable to load chapter content")

            except Exception as exc:
                print(f"[debug][browser] Error: {type(exc).__name__}: {exc}")
                if attempt < attempts:
                    await asyncio.sleep(random.uniform(3.0, 6.0))
                    try:
                        await page.goto(
                            NOVEL_URL,
                            wait_until="domcontentloaded",
                            timeout=120000,
                        )
                    except Exception:
                        pass
                else:
                    raise


def main():
    args = parse_args()
    site_config, novel = SiteRegistry.get(args.novel)

    if args.mode == "http":
        runner = debug_http(
            site_config,
            novel,
            args.chapter,
            args.attempts,
            args.save_html,
        )
    else:
        runner = debug_browser(
            site_config,
            novel,
            args.chapter,
            args.attempts,
            args.save_html,
            args.save_screenshot,
        )

    try:
        asyncio.run(runner)
        print("[debug] Completed successfully.")
    except Exception as exc:
        print(f"[debug] Failed: {type(exc).__name__}: {exc}")
        raise


if __name__ == "__main__":
    main()
