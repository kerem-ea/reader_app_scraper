import re
from html import escape
from ebooklib import epub


# Normalize a raw chapter title into "Chapter N - Title" or "Chapter N".
def _format_chapter_title(number: int, title: str | None) -> str:
    """Formats a chapter number and raw title cleanly and consistently."""
    if not title or not str(title).strip():
        return f"Chapter {number}"

    cleaned = str(title).strip()

    # If title already starts with 'Chapter <number>' or 'Chapter <digits>'
    if re.match(r"^chapter\s+\d+", cleaned, re.IGNORECASE):
        return cleaned

    # If title starts with digits followed by punctuation (e.g. '2 : Being Targeted...' or '2. Title')
    m = re.match(r"^\d+\s*[:\-–—\.]\s*(.+)$", cleaned)
    if m and m.group(1).strip():
        return f"Chapter {number} - {m.group(1).strip()}"

    # If title is just a number
    if cleaned.isdigit():
        return f"Chapter {number}"

    return f"Chapter {number} - {cleaned}"


# Build an XHTML chapter item from a scraped chapter dict.
def create_chapter(chapter, style):
    number = chapter.get("chapter_number", 0)
    title = chapter.get("title", f"Chapter {number}")
    text = chapter.get("text", "")

    chapter_title = _format_chapter_title(number, title)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(raw_paragraphs) <= 1 and "\n" in text:
        raw_paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    paragraphs = []
    for paragraph in raw_paragraphs:
        escaped_p = escape(paragraph).replace("\n", "<br/>")
        paragraphs.append(f"<p>{escaped_p}</p>")

    if not paragraphs:
        paragraphs.append("<p><em>No content available.</em></p>")

    content = f"""<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{escape(chapter_title)}</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <h1>{escape(chapter_title)}</h1>
    {''.join(paragraphs)}
</body>
</html>"""

    item = epub.EpubHtml(
        title=chapter_title,
        file_name=f"chapter-{number}.xhtml",
        lang="en"
    )
    item.content = content.encode("utf-8")
    item.add_item(style)
    return item


# Build a volume landing page listing its chapters.
def create_volume_page(volume_number, volume_title, volume_chapters, style):
    volume_name = f"Volume {volume_number} - {volume_title}"
    links = []
    for chapter in volume_chapters:
        number = chapter.get("chapter_number", 0)
        title = chapter.get("title", f"Chapter {number}")
        ch_title = _format_chapter_title(number, title)
        links.append(
            f"""
            <p class="toc-chapter">
                <a href="chapter-{number}.xhtml">
                    {escape(ch_title)}
                </a>
            </p>
            """
        )

    content = f"""<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{escape(volume_name)}</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <h1>{escape(volume_name)}</h1>
    {''.join(links)}
</body>
</html>"""

    item = epub.EpubHtml(
        title=volume_name,
        file_name=f"volume-{volume_number}.xhtml",
        lang="en"
    )
    item.content = content.encode("utf-8")
    item.add_item(style)
    return item