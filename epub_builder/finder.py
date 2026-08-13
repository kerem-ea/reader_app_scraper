from epub_builder.constants import BASE_DIR


def find_scraped_novels():
    if not BASE_DIR.exists():
        return []

    novels = []
    for item in BASE_DIR.iterdir():
        if item.is_dir():
            json_files = (
                list(item.glob("*_chapters_raw.json"))
                or list(item.glob("*_chapters.json"))
                or list(item.glob("chapters.json"))
            )
            if json_files:
                novels.append({
                    "slug": item.name,
                    "dir": item,
                    "json_file": json_files[0]
                })
    return novels
