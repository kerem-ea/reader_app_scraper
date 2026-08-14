import json
import sys
from pathlib import Path

from .constants import get_novel_metadata
from .cover import prepare_cover
from .builder import create_full_book, create_volume_book
from .finder import find_scraped_novels


# Convert one novel's scraped JSON into full + per-volume EPUBs.
def build_novel(selected: dict) -> None:
    novel_slug = selected["slug"]
    json_path = selected["json_file"]
    output_dir = selected["dir"]

    metadata = get_novel_metadata(output_dir, novel_slug)
    novel_title = metadata.get("title", novel_slug.replace("-", " ").title())
    author = metadata.get("author", "WebNovel Author")
    volumes = metadata.get("volumes", [])

    print(f"\nReading {json_path.name}...")
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        chapters = list(data.values())
    elif isinstance(data, list):
        chapters = data
    else:
        chapters = []

    # Sort chapters by chapter number
    chapters.sort(key=lambda ch: ch.get("chapter_number", 0))
    print(f"Found {len(chapters)} chapters for '{novel_title}' by {author}")

    cover_path = prepare_cover(output_dir)
    if cover_path:
        print(f"Using cover image: {cover_path.name}")
    else:
        print("No cover image found, proceeding without cover.")

    # 1. Build the full novel EPUB
    full_book = create_full_book(novel_title, chapters, cover_path, output_dir, metadata=metadata)

    # 2. If volumes are configured, build standalone volume EPUBs as well
    volume_files = []
    if volumes:
        for vol in volumes:
            if len(vol) >= 4:
                volume_number, volume_title, start, end = vol[0], vol[1], vol[2], vol[3]
            else:
                continue

            volume_chapters = [
                ch for ch in chapters
                if start <= ch.get("chapter_number", 0) <= end
            ]
            if not volume_chapters:
                continue

            vol_file = create_volume_book(
                novel_title, volume_number, volume_title, volume_chapters, cover_path, output_dir, author=author
            )
            volume_files.append((volume_number, volume_title, len(volume_chapters), vol_file))

        if volume_files:
            print("\nVolume EPUBs created:")
            for vnum, vtitle, vcount, vfile in volume_files:
                print(f"  Volume {vnum} ({vtitle}): {vcount} chapters -> {vfile.name}")
    else:
        print(f"No volume groupings configured. Built full single-volume EPUB.")

    print("\n========================================")
    print("EPUB CONVERSION COMPLETE")
    print("========================================")
    print(f"Novel: {novel_title}")
    print(f"Output directory: {output_dir}")
    print(f"Generated EPUB: {full_book.name}")
    if volume_files:
        print(f"Generated Volume EPUBs: {len(volume_files)} volumes")
    print("========================================\n")


# CLI entry: build by slug / "all" / interactive menu.
def main():
    novels = find_scraped_novels()
    if not novels:
        print("No scraped novel data found in data/ directory.")
        print("Please run the scraper first (weaver-scraper).")
        return

    # Check CLI arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip().lower()
        if arg in ("-h", "--help"):
            print("Usage: weaver-epub [novel-slug | all]")
            return
        if arg in ("all", "--all", "-a"):
            print(f"Building EPUBs for all {len(novels)} novels...\n")
            for nov in novels:
                build_novel(nov)
            return

        for nov in novels:
            if nov["slug"].lower() == arg:
                build_novel(nov)
                return

    # Interactive menu
    print("========================================")
    print("Available Scraped Novels:")
    print("========================================")
    for idx, nov in enumerate(novels, 1):
        meta = get_novel_metadata(nov["dir"], nov["slug"])
        title = meta.get("title", nov["slug"].replace("-", " ").title())
        vol_info = f"{len(meta.get('volumes', []))} volumes" if meta.get("volumes") else "single book"
        print(f"[{idx}] {title} ({nov['slug']}) - [{vol_info}]")

    if len(novels) > 1:
        print(f"[{len(novels) + 1}] Build All Novels")

    choice = input(f"\nSelect an option (1-{len(novels) + 1 if len(novels) > 1 else 1}) [default 1]: ").strip().lower()

    if choice in ("all", "a", str(len(novels) + 1)) and len(novels) > 1:
        for nov in novels:
            build_novel(nov)
        return

    try:
        idx = int(choice) - 1 if choice else 0
        if 0 <= idx < len(novels):
            build_novel(novels[idx])
        else:
            build_novel(novels[0])
    except Exception:
        build_novel(novels[0])


if __name__ == "__main__":
    main()