from ebooklib import epub
from epub_builder.cover import add_cover, create_style
from epub_builder.chapters import create_chapter, create_volume_page


def create_full_book(novel_title, chapters, cover_path, output_dir, metadata=None):
    print()
    print(f"Creating full {novel_title} EPUB...")
    print("----------------------------------------")

    metadata = metadata or {}
    author = metadata.get("author", "WebNovel Author")
    volumes = metadata.get("volumes", [])

    book = epub.EpubBook()
    slug = novel_title.lower().replace(" ", "-")

    book.set_identifier(slug)
    book.set_title(novel_title)
    book.set_language("en")
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

    if volumes:
        for volume_number, volume_title, start, end in volumes:
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
        for volume_number, volume_title, start, end in volumes:
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
        for volume_number, volume_title, start, end in volumes:
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


def create_volume_book(novel_title, volume_number, volume_title, volume_chapters, cover_path, output_dir, author="WebNovel Author"):
    volume_name = f"Volume {volume_number} - {volume_title}"
    book = epub.EpubBook()

    slug = novel_title.lower().replace(" ", "-")
    identifier = f"{slug}-volume-{volume_number}"
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
    output_file = output_dir / f"{novel_title} - Volume {volume_number} - {safe_title}.epub"
    epub.write_epub(str(output_file), book)
    return output_file

