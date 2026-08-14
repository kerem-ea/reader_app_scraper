import json
import sys
from pathlib import Path

from .constants import get_novel_metadata
from .cover import prepare_cover
from .builder import create_full_book, create_volume_book
from .finder import find_scraped_novels
from .volumes import resolve_volumes


# Convert one novel's scraped JSON into full + per-volume EPUBs.
def build_novel(selected: dict, *, volume_count: int | None = None, force: str | None = None) -> None:
    novel_slug = selected["slug"]
    json_path = selected["json_file"]
    output_dir = selected["dir"]

    metadata = get_novel_metadata(output_dir, novel_slug)
    novel_title = metadata.get("title", novel_slug.replace("-", " ").title())
    author = metadata.get("author", "WebNovel Author")

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

    numbers = [ch.get("chapter_number", 0) for ch in chapters]
    if len(numbers) != len(set(numbers)):
        print("[!] Warning: duplicate chapter numbers detected; some EPUB item names may collide.")

    volumes = resolve_volumes(output_dir, novel_slug, len(chapters), volume_count=volume_count, force=force)
    metadata = {**metadata, "volumes": volumes}

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
        print("No volume groupings configured. Built full single-volume EPUB.")

    print("\n========================================")
    print("EPUB CONVERSION COMPLETE")
    print("========================================")
    print(f"Novel: {novel_title}")
    print(f"Output directory: {output_dir}")
    print(f"Generated EPUB: {full_book.name}")
    if volume_files:
        print(f"Generated Volume EPUBs: {len(volume_files)} volumes")
    print("========================================\n")


def _parse_args(argv) -> tuple[list[str], int | None, str | None]:
    positional: list[str] = []
    volume_count: int | None = None
    force: str | None = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--volumes", "-v") and i + 1 < len(argv):
            try:
                volume_count = int(argv[i + 1])
            except ValueError:
                print(f"Invalid --volumes value: {argv[i + 1]!r}")
                sys.exit(1)
            if volume_count < 1:
                print(f"--volumes must be a positive integer, got {volume_count!r}")
                sys.exit(1)
            i += 2
        elif arg == "--flat":
            force = "flat"
            i += 1
        elif arg == "--auto":
            force = "auto"
            i += 1
        else:
            positional.append(arg)
            i += 1
    return positional, volume_count, force


# CLI entry: build by slug / "all" / interactive menu.
def main():
    novels = find_scraped_novels()
    if not novels:
        print("No scraped novel data found in data/ directory.")
        print("Please run the scraper first (weaver-scraper).")
        return

    args, volume_count, force = _parse_args(sys.argv[1:])

    # Check CLI arguments
    if args:
        arg = args[0].strip().lower()
        if arg in ("-h", "--help"):
            print("Usage: weaver-epub [novel-slug | all] [--volumes N] [--flat] [--auto]")
            print()
            print("  --volumes N   Auto-split the novel into N volumes")
            print("  --flat        Build a single flat EPUB (ignore stored volumes)")
            print("  --auto        Regenerate stored volumes from the chapter count")
            return
        if arg in ("all", "--all", "-a"):
            print(f"Building EPUBs for all {len(novels)} novels...\n")
            for nov in novels:
                build_novel(nov, volume_count=volume_count, force=force)
            return

        for nov in novels:
            if nov["slug"].lower() == arg:
                build_novel(nov, volume_count=volume_count, force=force)
                return

        print(f"No novel found with slug '{arg}'.")
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

    build_all_keys = {"all", "a"}
    if len(novels) > 1:
        build_all_keys.add(str(len(novels) + 1))
    choice = input(f"\nSelect an option (1-{len(novels) + 1 if len(novels) > 1 else 1}) [default 1]: ").strip().lower()

    if choice in build_all_keys:
        for nov in novels:
            build_novel(nov, volume_count=volume_count, force=force)
        return

    try:
        idx = int(choice) - 1 if choice else 0
    except ValueError:
        print(f"Invalid selection: {choice!r}")
        return

    if not (0 <= idx < len(novels)):
        print(f"Invalid selection: {choice!r}")
        return

    vol_choice = input("\nVolumes [N=split into N, F=flat, Enter=default]: ").strip().lower()
    if vol_choice.isdigit():
        volume_count = int(vol_choice)
    elif vol_choice in ("f", "flat"):
        force = "flat"
    elif vol_choice in ("a", "auto"):
        force = "auto"

    try:
        build_novel(novels[idx], volume_count=volume_count, force=force)
    except Exception as exc:
        print(f"[!] Build failed: {exc}")


if __name__ == "__main__":
    main()