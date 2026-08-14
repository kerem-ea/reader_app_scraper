import json
import logging
import re
from pathlib import Path

from .._common import get_data_root

logger = logging.getLogger(__name__)

COVER_FILE = Path(__file__).resolve().parent.parent / "app" / "weaver.ico"


def get_base_dir() -> Path:
    """Resolve the data root lazily (avoids import-time side effects)."""
    return get_data_root()

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

# Curated volume defaults for a few known novels. This is a fallback only:
# a novel's own metadata.json `volumes` key takes priority (see volumes.py),
# and any novel without explicit volumes gets auto-generated splits.
DEFAULT_KNOWN_METADATA = {
    "shadow-slave": {
        "author": "Guiltythree",
        "volumes": VOLUMES,
    }
}


# Make a title safe to use as a filename on Windows/POSIX.
def sanitize_filename(name: str, fallback: str = "novel") -> str:
    """Sanitize novel and volume titles so they are valid filenames across all operating systems."""
    if not name or not str(name).strip():
        return fallback
    cleaned = str(name).strip()
    # Replace characters that are invalid in Windows and POSIX filenames (\ / : * ? " < > |)
    cleaned = re.sub(r'[\/\\:\*\?"<>\|]', ' - ', cleaned)
    # Normalize multiple dashes and spaces
    cleaned = re.sub(r'\s*-\s*', ' - ', cleaned)
    cleaned = re.sub(r'-+', '-', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip('. -')
    return cleaned if cleaned else fallback


# Load title/author/volumes from metadata.json or built-in known defaults.
def get_novel_metadata(output_dir: Path, novel_slug: str) -> dict:
    meta_file = output_dir / "metadata.json"
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw_vols = data.get("volumes", [])
            vols = []
            for v in raw_vols:
                if isinstance(v, dict) and "number" in v and "title" in v and "start" in v and "end" in v:
                    vols.append((int(v["number"]), str(v["title"]), int(v["start"]), int(v["end"])))
                elif isinstance(v, (list, tuple)) and len(v) >= 4:
                    vols.append((int(v[0]), str(v[1]), int(v[2]), int(v[3])))

            title = data.get("title")
            if not title or not str(title).strip():
                title = novel_slug.replace("-", " ").title()

            author = data.get("author")
            if not author or not str(author).strip():
                author = "WebNovel Author"

            return {
                "title": str(title).strip(),
                "author": str(author).strip(),
                "volumes": vols,
                "site": data.get("site", ""),
                "url": data.get("url", ""),
            }
        except Exception as e:
            logger.warning("Could not read %s: %s", meta_file, e)

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