import asyncio
import re
import sys
import time

from catalog import get_chapter_titles
from constants import MODE_SETTINGS, Settings
from fetch import failed_chapters, run_fast_mode
from browser import run_browser_mode
import paths
from progress import ProgressWriter, compile_json, load_done
from site_config import SiteRegistry, SiteConfig


def collect_inputs() -> tuple[SiteConfig, str, int, int, str]:
    if len(sys.argv) >= 5:
        novel_input = sys.argv[1].strip()
        start_chapter = int(sys.argv[2].strip())
        end_chapter = int(sys.argv[3].strip())
        mode_choice = sys.argv[4].strip()
        site_config, novel_name = SiteRegistry.get(novel_input)
        return site_config, novel_name, start_chapter, end_chapter, mode_choice

    novel_input = input("Novel slug or supported novel URL: ").strip()
    if not novel_input:
        raise ValueError("Novel input cannot be empty.")

    site_config, novel_name = SiteRegistry.get(novel_input)

    start_text = input("Enter start chapter: ").strip() or "1"
    end_text = input("Enter end chapter: ").strip() or start_text

    start_chapter = int(start_text)
    end_chapter = int(end_text)

    if start_chapter < 1:
        raise ValueError("Start chapter must be at least 1.")
    if end_chapter < start_chapter:
        raise ValueError("End chapter must be >= start chapter.")

    mode_choice = None
    while mode_choice not in ("1", "2", "3"):
        mode_choice = input(
            "Choose mode:\n"
            "  1) MODE 1 (Fast HTTP) then MODE 2 for failures\n"
            "  2) MODE 2 (Browser-only)\n"
            "  3) MODE 3 (Slow HTTP) then MODE 2 for failures\n"
            "Enter 1, 2, or 3: "
        ).strip()

    return site_config, novel_name, start_chapter, end_chapter, mode_choice


async def main() -> None:
    site_config, novel_name, start_chapter, end_chapter, selected_mode = collect_inputs()
    paths.initialize_paths(site_config, novel_name, start_chapter, end_chapter)

    print()
    print(f"Site: {site_config.name}")
    print(f"Novel: {novel_name}")
    print(f"Chapters: {start_chapter}-{end_chapter}")
    print(f"Folder: {paths.OUT_JSON.parent}")
    print()

    chapter_titles = await get_chapter_titles(site_config=site_config)
    done = load_done(paths.TEMP_JSONL)

    queue = [
        (chapter_number, paths.CHAPTER_URL_TMPL.format(chapter_number))
        for chapter_number in range(start_chapter, end_chapter + 1)
        if f"chapter-{chapter_number}" not in done
    ]

    if not queue:
        print("Nothing left to download.")
        compile_json(paths.TEMP_JSONL, paths.OUT_JSON)
        return

    print(f"Remaining: {len(queue)}")

    writer = ProgressWriter(paths.TEMP_JSONL)
    stats = {"done": 0, "failed": 0, "t0": time.time()}

    try:
        if selected_mode in ("1", "3"):
            mode_key = "fast" if selected_mode == "1" else "slow"
            mode_label = "MODE 1: FAST" if selected_mode == "1" else "MODE 3: SLOW"
            print()
            print(mode_label)
            await run_fast_mode(
                queue,
                writer,
                stats,
                len(queue),
                Settings(mode=mode_key, **MODE_SETTINGS[mode_key]),
                chapter_titles,
                site_config=site_config,
            )
            writer.flush()

            if failed_chapters:
                retry_queue = [
                    (chapter_number, paths.CHAPTER_URL_TMPL.format(chapter_number))
                    for chapter_number in sorted(failed_chapters)
                ]
                print()
                print(f"MODE 2: RETRYING {len(retry_queue)} FAILED")
                await run_browser_mode(
                    retry_queue,
                    writer,
                    stats,
                    len(retry_queue),
                    Settings(mode="browser-only", **MODE_SETTINGS["browser_only"]),
                    chapter_titles,
                    site_config=site_config,
                )
                writer.flush()
                recovered = len(retry_queue) - len(failed_chapters)
                print(f"Mode 2 recovered: {recovered}")
                print(f"Still failed: {len(failed_chapters)}")
            else:
                print(f"{mode_label} completed with no failures.")
        else:
            print()
            print("MODE 2: BROWSER-ONLY")
            await run_browser_mode(
                queue,
                writer,
                stats,
                len(queue),
                Settings(mode="browser-only", **MODE_SETTINGS["browser_only"]),
                chapter_titles,
                site_config=site_config,
            )
            writer.flush()
            print(f"Mode 2 completed. Failed: {len(failed_chapters)}")
    finally:
        writer.close()
        compile_json(paths.TEMP_JSONL, paths.OUT_JSON)

    elapsed = time.time() - stats["t0"]

    print()
    print("DONE")
    print(f"Successful: {len(load_done(paths.TEMP_JSONL))}")
    print(f"Still failed: {len(failed_chapters)}")
    print(f"Elapsed: {elapsed:.1f}s")
    print(f"Output: {paths.OUT_JSON}")
    print(f"Progress: {paths.TEMP_JSONL}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Scraping interrupted by user.")
        sys.exit(0)
    except Exception as exc:
        print(f"\n[!] Scraping failed: {exc}")
        print("[!] Note: If Camoufox browser binaries are missing, run 'camoufox fetch'.")
        sys.exit(1)

