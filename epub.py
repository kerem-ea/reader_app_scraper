import json
from html import escape
from pathlib import Path

from ebooklib import epub
from PIL import Image


JSON_FILE = r"C:\Users\lost from light\repos\reader_app_scraper\scraper\data\shadow-slave\shadow-slave_chapters_raw.json"
COVER_FILE = r"C:\Users\lost from light\repos\reader_app_scraper\reading_app\weaver.ico"
OUTPUT_DIR = r"C:\Users\lost from light\repos\reader_app_scraper"


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


def get_volume(chapter_number):
    for number, title, start, end in VOLUMES:
        if start <= chapter_number <= end:
            return number, title

    return None, None


def prepare_cover():
    cover_path = Path(OUTPUT_DIR) / "cover.png"

    image = Image.open(COVER_FILE)
    image = image.convert("RGB")
    image.save(cover_path, "PNG")

    return cover_path


def add_cover(book, cover_path):
    with open(cover_path, "rb") as file:
        book.set_cover(
            "cover.png",
            file.read()
        )


def create_style():
    return epub.EpubItem(
        uid="style",
        file_name="style.css",
        media_type="text/css",
        content=CSS.encode("utf-8")
    )


def create_chapter(chapter, style):
    number = chapter["chapter_number"]
    title = chapter["title"]
    text = chapter["text"]

    chapter_title = f"Chapter {number} - {title}"

    text = (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    paragraphs = []

    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        paragraph = escape(paragraph)
        paragraph = paragraph.replace("\n", "<br/>")

        paragraphs.append(
            f"<p>{paragraph}</p>"
        )

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
        number = chapter["chapter_number"]
        title = chapter["title"]

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


def create_full_book(chapters, cover_path):
    print()
    print("Creating full Shadow Slave EPUB...")
    print("----------------------------------------")

    book = epub.EpubBook()

    book.set_identifier("shadow-slave")
    book.set_title("Shadow Slave")
    book.set_language("en")
    book.add_author("Guiltythree")

    add_cover(book, cover_path)

    style = create_style()
    book.add_item(style)

    chapter_items = {}
    volume_items = {}

    for chapter in chapters:
        number = chapter["chapter_number"]

        print(
            f"Full EPUB - Chapter {number}: "
            f"{chapter['title']}"
        )

        item = create_chapter(
            chapter,
            style
        )

        book.add_item(item)
        chapter_items[number] = item

    for volume_number, volume_title, start, end in VOLUMES:
        volume_chapters = [
            chapter
            for chapter in chapters
            if start <= chapter["chapter_number"] <= end
        ]

        if not volume_chapters:
            continue

        print(
            f"Adding Volume {volume_number}: "
            f"{volume_title}"
        )

        volume_item = create_volume_page(
            volume_number,
            volume_title,
            volume_chapters,
            style
        )

        book.add_item(volume_item)
        volume_items[volume_number] = volume_item

    toc_entries = []

    for volume_number, volume_title, start, end in VOLUMES:
        if volume_number not in volume_items:
            continue

        chapter_entries = []

        for chapter in chapters:
            number = chapter["chapter_number"]

            if start <= number <= end:
                title = chapter["title"]

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

        spine.append(
            volume_items[volume_number]
        )

        for chapter in chapters:
            number = chapter["chapter_number"]

            if start <= number <= end:
                spine.append(
                    chapter_items[number]
                )

    book.spine = spine

    output_file = Path(OUTPUT_DIR) / "Shadow Slave.epub"

    print()
    print("Writing full EPUB...")

    epub.write_epub(
        str(output_file),
        book
    )

    print(
        f"Full EPUB created: {output_file}"
    )

    return output_file


def create_volume_book(
    volume_number,
    volume_title,
    volume_chapters,
    cover_path
):
    volume_name = f"Volume {volume_number} - {volume_title}"

    print()
    print(f"Creating {volume_name} EPUB...")
    print("----------------------------------------")

    book = epub.EpubBook()

    identifier = (
        f"shadow-slave-volume-{volume_number}"
    )

    book.set_identifier(identifier)
    book.set_title(volume_name)
    book.set_language("en")
    book.add_author("Guiltythree")

    add_cover(book, cover_path)

    style = create_style()
    book.add_item(style)

    chapter_items = []

    for chapter in volume_chapters:
        number = chapter["chapter_number"]

        print(
            f"Volume {volume_number} - "
            f"Chapter {number}: "
            f"{chapter['title']}"
        )

        item = create_chapter(
            chapter,
            style
        )

        book.add_item(item)
        chapter_items.append(item)

    toc_entries = []

    for chapter in volume_chapters:
        number = chapter["chapter_number"]
        title = chapter["title"]

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

    book.spine = [
        "nav"
    ] + chapter_items

    safe_title = (
        volume_title
        .replace("/", "-")
        .replace("\\", "-")
        .replace(":", "-")
        .replace("*", "-")
        .replace("?", "-")
        .replace('"', "'")
        .replace("<", "-")
        .replace(">", "-")
        .replace("|", "-")
    )

    output_file = (
        Path(OUTPUT_DIR)
        / f"Shadow Slave - Volume {volume_number} - {safe_title}.epub"
    )

    print()
    print(f"Writing Volume {volume_number} EPUB...")

    epub.write_epub(
        str(output_file),
        book
    )

    print(
        f"Volume {volume_number} created: "
        f"{output_file}"
    )

    return output_file


print("Reading JSON...")

with open(
    JSON_FILE,
    "r",
    encoding="utf-8"
) as file:
    data = json.load(file)

chapters = list(data.values())

chapters.sort(
    key=lambda chapter: chapter["chapter_number"]
)

print(
    f"Found {len(chapters)} chapters"
)

cover_path = prepare_cover()

full_book = create_full_book(
    chapters,
    cover_path
)

volume_files = []

for volume_number, volume_title, start, end in VOLUMES:
    volume_chapters = [
        chapter
        for chapter in chapters
        if start <= chapter["chapter_number"] <= end
    ]

    if not volume_chapters:
        continue

    volume_file = create_volume_book(
        volume_number,
        volume_title,
        volume_chapters,
        cover_path
    )

    volume_files.append(
        (
            volume_number,
            volume_title,
            len(volume_chapters),
            volume_file
        )
    )


print()
print("========================================")
print("DONE")
print("========================================")
print()
print(
    f"Total chapters found: {len(chapters)}"
)
print()
print(
    f"Full book: {full_book.name}"
)
print()
print("Volume EPUBs:")

for volume_number, volume_title, count, file in volume_files:
    print(
        f"Volume {volume_number}: "
        f"{count} chapters - {file.name}"
    )

print()
print(
    f"Created {len(volume_files)} volume EPUBs"
)
print(
    f"Created {len(volume_files) + 1} EPUBs total"
)
print("========================================")