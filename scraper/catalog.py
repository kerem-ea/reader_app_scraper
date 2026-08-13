from parsing import extract_novel_metadata, parse_chapter_titles, save_scraped_metadata
from session import camoufox_ctx, wait_for_challenge_clear
from site_config import SiteConfig, FREEWEBNOVEL
import paths


async def get_chapter_titles(site_config: SiteConfig | None = None) -> dict[int, str]:
    config = site_config or FREEWEBNOVEL
    print("[catalog] Interactively fetching chapter titles via Camoufox...")

    titles: dict[int, str] = {}
    catalog_page_size = config.catalog_page_size
    needed_catalog_pages = (paths.END_CHAPTER + (catalog_page_size - 1)) // catalog_page_size

    async with camoufox_ctx(False) as browser:
        page = await browser.new_page()
        await page.goto(paths.NOVEL_URL, wait_until="domcontentloaded", timeout=60000)

        html = await wait_for_challenge_clear(
            page,
            timeout=50,
            extra_wait_on_timeout=1500,
            log_prefix="[catalog] ",
        )

        titles.update(parse_chapter_titles(html, site_config=config))
        print(f"[catalog] Page 1 loaded ({len(titles)} titles)")

        meta = extract_novel_metadata(html, paths.NOVEL_URL, site_config=config)
        save_scraped_metadata(
            output_dir=paths.OUT_JSON.parent,
            novel_slug=paths.NOVEL_NAME,
            metadata=meta,
            site_name=config.name,
            novel_url=paths.NOVEL_URL,
        )

        select_selector = config.catalog_select_selector
        options = await page.query_selector_all(f"{select_selector} option")
        total_available_pages = len(options) if options else 1
        pages_to_fetch = min(needed_catalog_pages, total_available_pages)

        if pages_to_fetch > 1:
            print(
                f"[catalog] Fetching {pages_to_fetch} catalog pages total for Chapter {paths.END_CHAPTER}..."
            )

            for p_idx in range(1, pages_to_fetch):
                page_number = p_idx + 1
                print(f"[catalog] Switching to catalog page {page_number}/{pages_to_fetch}...")
                try:
                    attempt = 0
                    while True:
                        attempt += 1
                        await page.select_option(select_selector, index=p_idx)
                        await page.wait_for_timeout(1000)

                        selected_index = await page.evaluate(
                            f"() => document.querySelector('{select_selector}')?.selectedIndex"
                        )
                        if selected_index == p_idx:
                            break

                        if attempt >= 6:
                            print(
                                f"[catalog] Warning: catalog page {page_number} did not register after {attempt} tries."
                            )
                            break

                        print(
                            f"[catalog] Catalog input still at page {selected_index + 1 if selected_index is not None else 'unknown'}, waiting 1s and retrying..."
                        )
                        await page.wait_for_timeout(1000)

                    new_html = await page.content()
                    new_titles = parse_chapter_titles(new_html, site_config=config)
                    titles.update(new_titles)
                    print(f"[catalog] Page {page_number} loaded ({len(new_titles)} titles)")
                except Exception as e:
                    print(f"[catalog] Error interacting with catalog page {page_number}: {e}")

    print(f"[catalog] Total chapter titles cached: {len(titles):,}")
    return titles
