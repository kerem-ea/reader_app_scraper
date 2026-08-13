import json
import sys
from epub_builder.constants import get_novel_metadata
from epub_builder.cover import prepare_cover
from epub_builder.builder import create_full_book, create_volume_book
from epub_builder.finder import find_scraped_novels


def main():
    novels = find_scraped_novels()
    if not novels:
        print("No scraped novel data found in data/ directory.")
        print("Please run the scraper first (python scraper/scrape.py).")
        return

    print("========================================")
    print("Available Scraped Novels:")
    print("========================================")
    for idx, nov in enumerate(novels, 1):
        print(f"[{idx}] {nov['slug'].replace('-', ' ').title()} ({nov['slug']})")

    selected = None
    if len(sys.argv) > 1:
        arg_slug = sys.argv[1].strip().lower()
        for nov in novels:
            if nov["slug"].lower() == arg_slug:
                selected = nov
                break

    if not selected:
        if len(novels) == 1:
            selected = novels[0]
            print(f"\nAutomatically selected: {selected['slug']}")
        else:
            try:
                choice = input(f"\nSelect a novel (1-{len(novels)}) [default 1]: ").strip()
                idx = int(choice) - 1 if choice else 0
                if 0 <= idx < len(novels):
                    selected = novels[idx]
            except Exception:
                selected = novels[0]

    if not selected:
        selected = novels[0]

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

    chapters.sort(key=lambda ch: ch.get("chapter_number", 0))
    print(f"Found {len(chapters)} chapters for {novel_title} by {author}")

    cover_path = prepare_cover(output_dir)

    full_book = create_full_book(novel_title, chapters, cover_path, output_dir, metadata=metadata)

    if volumes:
        volume_files = []
        for volume_number, volume_title, start, end in volumes:
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

        print("\nVolume EPUBs created:")
        for vnum, vtitle, vcount, vfile in volume_files:
            print(f"  Volume {vnum} ({vtitle}): {vcount} chapters -> {vfile.name}")

    print("\n========================================")
    print("EPUB CONVERSION COMPLETE")
    print("========================================")
    print(f"Novel: {novel_title}")
    print(f"Output directory: {output_dir}")
    print(f"Generated EPUB: {full_book.name}")
    print("========================================\n")
