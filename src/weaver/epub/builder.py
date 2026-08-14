import re
import uuid
from pathlib import Path
from ebooklib import epub

from .constants import sanitize_filename
from .cover import add_cover, create_style
from .chapters import create_chapter, create_volume_page, _format_chapter_title


def _epub_identifier(slug: str) -> str:
    """Stable, spec-compliant URN identifier derived from the novel slug."""
    return f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, f'https://weaver.local/{slug}')}"


# Write TOC, spine and render the EPUB to disk.
def _finalize_epub(book, toc, spine, output_file: Path):
    book.toc = tuple(toc)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + spine
    print(f"Writing EPUB: {output_file.name}...")
    epub.write_epub(str(output_file), book)
    print(f"EPUB created successfully: {output_file}")


# Build one EPUB containing every chapter (volume-grouped when volumes exist).
def create_full_book(novel_title: str, chapters: list, cover_path: Path | None, output_dir: Path, metadata: dict | None = None) -> Path:
    print()
    print(f"Creating full {novel_title} EPUB...")
    print("----------------------------------------")

    metadata = metadata or {}
    author = metadata.get("author", "WebNovel Author")
    volumes = metadata.get("volumes", [])

    book = epub.EpubBook()
    slug = re.sub(r"[^a-zA-Z0-9_\-]+", "-", novel_title.lower()).strip("-") or "novel"

    book.set_identifier(_epub_identifier(slug))
    book.set_title(novel_title)
    book.set_language("en")
    book.add_author(author)

    if cover_path:
        add_cover(book, cover_path)

    style = create_style()
    book.add_item(style)

    chapter_items = {}
    for chapter in chapters:
        number = chapter.get("chapter_number", 0)
        item = create_chapter(chapter, style)
        book.add_item(item)
        chapter_items[number] = item

    safe_title = sanitize_filename(novel_title)
    output_file = output_dir / f"{safe_title}.epub"

    # Volume grouping
    volume_sections = []
    assigned_numbers = set()
    volume_items = {}

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

            vol_item = create_volume_page(volume_number, volume_title, volume_chapters, style)
            book.add_item(vol_item)
            volume_items[volume_number] = vol_item

            ch_links = []
            for ch in volume_chapters:
                num = ch.get("chapter_number", 0)
                assigned_numbers.add(num)
                ch_title = _format_chapter_title(num, ch.get("title"))
                ch_links.append(
                    epub.Link(f"chapter-{num}.xhtml", ch_title, f"chapter-{num}")
                )

            volume_name = f"Volume {volume_number} - {volume_title}"
            section = epub.Section(volume_name, f"volume-{volume_number}.xhtml")
            volume_sections.append((section, ch_links, volume_number, volume_chapters))

    if volume_sections:
        toc_entries = []
        spine = []

        # Check for unassigned chapters before the first volume (e.g. Chapter 0 / Prologue)
        pre_chapters = [ch for ch in chapters if ch.get("chapter_number", 0) not in assigned_numbers and ch.get("chapter_number", 0) < volume_sections[0][3][0].get("chapter_number", 0)]
        for ch in pre_chapters:
            num = ch.get("chapter_number", 0)
            assigned_numbers.add(num)
            ch_title = _format_chapter_title(num, ch.get("title"))
            toc_entries.append(epub.Link(f"chapter-{num}.xhtml", ch_title, f"chapter-{num}"))
            spine.append(chapter_items[num])

        for section, ch_links, vol_num, vol_chaps in volume_sections:
            toc_entries.append((section, ch_links))
            spine.append(volume_items[vol_num])
            for ch in vol_chaps:
                num = ch.get("chapter_number", 0)
                spine.append(chapter_items[num])

        # Check for remaining unassigned chapters after the volumes
        post_chapters = [ch for ch in chapters if ch.get("chapter_number", 0) not in assigned_numbers]
        if post_chapters:
            extra_links = []
            for ch in post_chapters:
                num = ch.get("chapter_number", 0)
                ch_title = _format_chapter_title(num, ch.get("title"))
                extra_links.append(epub.Link(f"chapter-{num}.xhtml", ch_title, f"chapter-{num}"))
                spine.append(chapter_items[num])
            toc_entries.append((epub.Section("Additional Chapters", "extra-chapters.xhtml"), extra_links))

        _finalize_epub(book, toc_entries, spine, output_file)
    else:
        # Flat book structure (no volumes or standalone novel)
        toc_entries = []
        spine = []
        for chapter in chapters:
            number = chapter.get("chapter_number", 0)
            title = chapter.get("title", f"Chapter {number}")
            ch_title = _format_chapter_title(number, title)
            toc_entries.append(
                epub.Link(
                    f"chapter-{number}.xhtml",
                    ch_title,
                    f"chapter-{number}"
                )
            )
            spine.append(chapter_items[number])

        _finalize_epub(book, toc_entries, spine, output_file)

    return output_file


# Build a standalone EPUB for a single volume's chapter range.
def create_volume_book(
    novel_title: str,
    volume_number: int,
    volume_title: str,
    volume_chapters: list,
    cover_path: Path | None,
    output_dir: Path,
    author: str = "WebNovel Author"
) -> Path:
    volume_name = f"Volume {volume_number} - {volume_title}"
    book = epub.EpubBook()

    slug = re.sub(r"[^a-zA-Z0-9_\-]+", "-", novel_title.lower()).strip("-") or "novel"
    identifier = _epub_identifier(f"{slug}-volume-{volume_number}")
    book.set_identifier(identifier)
    book.set_title(f"{novel_title} - {volume_name}")
    book.set_language("en")
    book.add_author(author)

    if cover_path:
        add_cover(book, cover_path)

    style = create_style()
    book.add_item(style)

    chapter_items = []
    toc_entries = []

    for chapter in volume_chapters:
        number = chapter.get("chapter_number", 0)
        title = chapter.get("title", f"Chapter {number}")
        ch_title = _format_chapter_title(number, title)
        item = create_chapter(chapter, style)
        book.add_item(item)
        chapter_items.append(item)
        toc_entries.append(
            epub.Link(
                f"chapter-{number}.xhtml",
                ch_title,
                f"chapter-{number}"
            )
        )

    safe_novel = sanitize_filename(novel_title)
    safe_vol = sanitize_filename(volume_title, fallback=f"Volume {volume_number}")
    output_file = output_dir / f"{safe_novel} - Volume {volume_number} - {safe_vol}.epub"
    _finalize_epub(book, toc_entries, chapter_items, output_file)
    return output_file