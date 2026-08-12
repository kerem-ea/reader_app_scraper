import json
import sys
from html import escape
from pathlib import Path

from ebooklib import epub
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent / "data"
COVER_FILE = Path(__file__).resolve().parent / "reading_app" / "weaver.ico"

VOLUMES = [
    (1, "Child of Shadows", 1, 95),
    (2, "Demon of Change", 96, 350),
    (3, "Prince of Nothing", 351, 600),
    (4, "Chain Breaker", 601, 750),
    (5, "Dread Night", 751, 1060),
    (6, "All the Devils Are Here", 1061, 1230),
    (7, "The Tomb of Ariel", 1231, 1590),
    (8, "Lord of Shadows", 1591, 1840),
    (9, "Throne of War", 1841, 2260),
    (10, "Dark Lord's Dreadful Travelogue", 2261, 2720),
    (11, "The Song of Ariadne", 2721, 3000),
    (12, "Untitled", 3001, 999999),
]

CSS = """
body {
    font-family: serif;
    line-height: 1.6;
    margin: 5%;
}

h1 {
    text-align: center;
    margin-top: 2em;
    margin-bottom: 2em;
}

h2 {
    text-align: center;
    margin-top: 2em;
    margin-bottom: 1.5em;
}

p {
    margin-top: 0;
    margin-right: 0;
    margin-bottom: 1em;
    margin-left: 0;
    text-indent: 0;
}

.toc-chapter {
    text-indent: 0;
    margin-left: 1.5em;
    margin-bottom: 0.4em;
}
"""


def prepare_cover(output_dir):
    cover_path = output_dir / "cover.png"
    if COVER_FILE.exists():
        try:
            image = Image.open(COVER_FILE)
            image = image.convert("RGB")
            image.save(cover_path, "PNG")
            return cover_path
        except Exception:
            pass
    return None


def add_cover(book, cover_path):
    if cover_path and cover_path.exists():
        try:
            with open(cover_path, "rb") as file:
                book.set_cover("cover.png", file.read())
        except Exception:
            pass


def create_style():
    return epub.EpubItem(
        uid="style",
        file_name="style.css",
        media_type="text/css",
        content=CSS.encode("utf-8")
    )


def create_chapter(chapter, style):
    number = chapter.get("chapter_number", 0)
    title = chapter.get("title", f"Chapter {number}")
    text = chapter.get("text", "")

    chapter_title = f"Chapter {number} - {title}" if not title.lower().startswith("chapter") else title

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    paragraphs = []
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        paragraph = escape(paragraph)
        paragraph = paragraph.replace("\n", "<br/>")
        paragraphs.append(f"<p>{paragraph}</p>")

    content = f"""
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{escape(chapter_title)}</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <h1>{escape(chapter_title)}</h1>
    {''.join(paragraphs)}
</body>
</html>
"""

    item = epub.EpubHtml(
        title=chapter_title,
        file_name=f"chapter-{number}.xhtml",
        lang="en"
    )
    item.content = content.encode("utf-8")
    item.add_item(style)
    return item


def create_volume_page(volume_number, volume_title, volume_chapters, style):
    volume_name = f"Volume {volume_number} - {volume_title}"
    links = []
    for chapter in volume_chapters:
        number = chapter.get("chapter_number", 0)
        title = chapter.get("title", f"Chapter {number}")
        links.append(
            f"""
            <p class="toc-chapter">
                <a href="chapter-{number}.xhtml">
                    Chapter {number} - {escape(title)}
                </a>
            </p>
            """
        )

    content = f"""
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{escape(volume_name)}</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <h1>{escape(volume_name)}</h1>
    {''.join(links)}
</body>
</html>
"""

    item = epub.EpubHtml(
        title=volume_name,
        file_name=f"volume-{volume_number}.xhtml",
        lang="en"
    )
    item.content = content.encode("utf-8")
    item.add_item(style)
    return item


def create_full_book(novel_title, chapters, cover_path, output_dir, is_shadow_slave=False):
    print()
    print(f"Creating full {novel_title} EPUB...")
    print("----------------------------------------")

    book = epub.EpubBook()
    slug = novel_title.lower().replace(" ", "-")

    book.set_identifier(slug)
    book.set_title(novel_title)
    book.set_language("en")
    author = "Guiltythree" if is_shadow_slave else "WebNovel Author"
    book.add_author(author)

    if cover_path:
        add_cover(book, cover_path)

    style = create_style()
    book.add_item(style)

    chapter_items = {}
    volume_items = {}

    for chapter in chapters:
        number = chapter.get("chapter_number", 0)
        item = create_chapter(chapter, style)
        book.add_item(item)
        chapter_items[number] = item

    if is_shadow_slave:
        for volume_number, volume_title, start, end in VOLUMES:
            volume_chapters = [
                ch for ch in chapters
                if start <= ch.get("chapter_number", 0) <= end
            ]
            if not volume_chapters:
                continue

            volume_item = create_volume_page(volume_number, volume_title, volume_chapters, style)
            book.add_item(volume_item)
            volume_items[volume_number] = volume_item

        toc_entries = []
        for volume_number, volume_title, start, end in VOLUMES:
            if volume_number not in volume_items:
                continue

            chapter_entries = []
            for chapter in chapters:
                number = chapter.get("chapter_number", 0)
                if start <= number <= end:
                    title = chapter.get("title", f"Chapter {number}")
                    chapter_entries.append(
                        epub.Link(
                            f"chapter-{number}.xhtml",
                            f"Chapter {number} - {title}",
                            f"chapter-{number}"
                        )
                    )

            toc_entries.append(
                (
                    epub.Section(
                        f"Volume {volume_number} - {volume_title}",
                        f"volume-{volume_number}.xhtml"
                    ),
                    chapter_entries
                )
            )
        book.toc = tuple(toc_entries)

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        spine = ["nav"]
        for volume_number, volume_title, start, end in VOLUMES:
            if volume_number not in volume_items:
                continue
            spine.append(volume_items[volume_number])
            for chapter in chapters:
                number = chapter.get("chapter_number", 0)
                if start <= number <= end:
                    spine.append(chapter_items[number])
        book.spine = spine
    else:
        toc_entries = []
        for chapter in chapters:
            number = chapter.get("chapter_number", 0)
            title = chapter.get("title", f"Chapter {number}")
            toc_entries.append(
                epub.Link(
                    f"chapter-{number}.xhtml",
                    f"Chapter {number} - {title}" if not title.lower().startswith("chapter") else title,
                    f"chapter-{number}"
                )
            )
        book.toc = tuple(toc_entries)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ["nav"] + list(chapter_items.values())

    output_file = output_dir / f"{novel_title}.epub"
    print(f"Writing EPUB: {output_file.name}...")
    epub.write_epub(str(output_file), book)
    print(f"EPUB created successfully: {output_file}")
    return output_file


def create_volume_book(volume_number, volume_title, volume_chapters, cover_path, output_dir):
    volume_name = f"Volume {volume_number} - {volume_title}"
    book = epub.EpubBook()

    identifier = f"shadow-slave-volume-{volume_number}"
    book.set_identifier(identifier)
    book.set_title(volume_name)
    book.set_language("en")
    book.add_author("Guiltythree")

    if cover_path:
        add_cover(book, cover_path)

    style = create_style()
    book.add_item(style)

    chapter_items = []
    toc_entries = []

    for chapter in volume_chapters:
        number = chapter.get("chapter_number", 0)
        title = chapter.get("title", f"Chapter {number}")
        item = create_chapter(chapter, style)
        book.add_item(item)
        chapter_items.append(item)
        toc_entries.append(
            epub.Link(
                f"chapter-{number}.xhtml",
                f"Chapter {number} - {title}",
                f"chapter-{number}"
            )
        )

    book.toc = tuple(toc_entries)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + chapter_items

    safe_title = (
        volume_title.replace("/", "-").replace("\\", "-").replace(":", "-")
        .replace("*", "-").replace("?", "-").replace('"', "'")
        .replace("<", "-").replace(">", "-").replace("|", "-")
    )
    output_file = output_dir / f"Shadow Slave - Volume {volume_number} - {safe_title}.epub"
    epub.write_epub(str(output_file), book)
    return output_file


def find_scraped_novels():
    if not BASE_DIR.exists():
        return []

    novels = []
    for item in BASE_DIR.iterdir():
        if item.is_dir():
            json_files = list(item.glob("*_chapters_raw.json"))
            if json_files:
                novels.append({
                    "slug": item.name,
                    "dir": item,
                    "json_file": json_files[0]
                })
    return novels


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
                if not choice:
                    idx = 0
                else:
                    idx = int(choice) - 1
                if 0 <= idx < len(novels):
                    selected = novels[idx]
            except Exception:
                selected = novels[0]

    if not selected:
        selected = novels[0]

    novel_slug = selected["slug"]
    json_path = selected["json_file"]
    output_dir = selected["dir"]
    novel_title = novel_slug.replace("-", " ").title()

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
    print(f"Found {len(chapters)} chapters for {novel_title}")

    cover_path = prepare_cover(output_dir)
    is_shadow_slave = (novel_slug.lower() == "shadow-slave")

    full_book = create_full_book(novel_title, chapters, cover_path, output_dir, is_shadow_slave)

    if is_shadow_slave:
        volume_files = []
        for volume_number, volume_title, start, end in VOLUMES:
            volume_chapters = [
                ch for ch in chapters
                if start <= ch.get("chapter_number", 0) <= end
            ]
            if not volume_chapters:
                continue

            vol_file = create_volume_book(volume_number, volume_title, volume_chapters, cover_path, output_dir)
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


if __name__ == "__main__":
    main()