import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / "data"
COVER_FILE = Path(__file__).resolve().parent.parent / "reading_app" / "weaver.ico"

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

DEFAULT_KNOWN_METADATA = {
    "shadow-slave": {
        "author": "Guiltythree",
        "volumes": VOLUMES,
    }
}


def get_novel_metadata(output_dir: Path, novel_slug: str) -> dict:
    meta_file = output_dir / "metadata.json"
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            vols = [
                (v["number"], v["title"], v["start"], v["end"])
                for v in data.get("volumes", [])
            ]
            return {
                "title": data.get("title", novel_slug.replace("-", " ").title()),
                "author": data.get("author", "WebNovel Author"),
                "volumes": vols,
            }
        except Exception:
            pass

    slug_key = novel_slug.lower()
    if slug_key in DEFAULT_KNOWN_METADATA:
        known = DEFAULT_KNOWN_METADATA[slug_key]
        return {
            "title": novel_slug.replace("-", " ").title(),
            "author": known.get("author", "WebNovel Author"),
            "volumes": known.get("volumes", []),
        }

    return {
        "title": novel_slug.replace("-", " ").title(),
        "author": "WebNovel Author",
        "volumes": [],
    }


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
