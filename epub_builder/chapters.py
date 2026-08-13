from html import escape
from ebooklib import epub


def _format_chapter_title(number: int, title: str) -> str:
    return title if title.lower().startswith("chapter") else f"Chapter {number} - {title}"


def create_chapter(chapter, style):
    number = chapter.get("chapter_number", 0)
    title = chapter.get("title", f"Chapter {number}")
    text = chapter.get("text", "")

    chapter_title = _format_chapter_title(number, title)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    paragraphs = []
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        paragraph = escape(paragraph).replace("\n", "<br/>")
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
