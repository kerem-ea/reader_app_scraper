from epub_builder.constants import BASE_DIR


def find_scraped_novels():
    if not BASE_DIR.exists():
        return []

    novels = []
    for item in sorted(BASE_DIR.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            raw_files = list(item.glob("*_chapters_raw.json"))
            clean_files = list(item.glob("*_chapters.json"))
            chapters_file = list(item.glob("chapters.json"))
            all_json = [
                f for f in item.glob("*.json")
                if not f.name.endswith("metadata.json") and "progress" not in f.name.lower()
            ]
            json_files = raw_files or clean_files or chapters_file or all_json
            if json_files:
                novels.append({
                    "slug": item.name,
                    "dir": item,
                    "json_file": json_files[0]
                })
    return novels
