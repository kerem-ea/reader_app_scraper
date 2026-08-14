import json
import logging
import os
import threading

from .._common import get_progress_file
from .paths import HERE, ensure_progress_dir

logger = logging.getLogger(__name__)

# Serializes read-modify-write cycles on the progress file.
_LOCK = threading.Lock()


# Read the old single-novel last_read.txt format if it still exists.
def _migrate_old_txt() -> dict:
    old_txt = os.path.join(HERE, 'last_read.txt')
    if os.path.isfile(old_txt):
        try:
            with open(old_txt, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            site = lines[0].strip() if len(lines) > 0 and lines[0].strip() else None
            chapter = None
            if len(lines) > 1 and lines[1].strip():
                try:
                    chapter = int(lines[1].strip())
                except ValueError:
                    chapter = None
            if site:
                return {
                    "last_site": site,
                    "novels": {
                        site: {"chapter": chapter or 1}
                    }
                }
        except Exception as e:
            logger.warning("Could not migrate last_read.txt: %s", e)
    return {"last_site": None, "novels": {}}


# Load the full multi-novel progress dict.
def get_all_progress() -> dict:
    progress_file = get_progress_file()
    if progress_file.is_file():
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                if "novels" not in data:
                    data = {"last_site": data.get("last_site") or data.get("site"), "novels": {}}
                return data
        except Exception as e:
            logger.warning("Could not read progress file: %s", e)
    return _migrate_old_txt()


# Persist the full progress dict to the per-user JSON file.
def save_all_progress(data: dict) -> None:
    ensure_progress_dir()
    try:
        with open(get_progress_file(), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning("Could not write progress file: %s", e)


# Last chapter read for one novel (or None).
def get_novel_last_read(site: str) -> int | None:
    if not site:
        return None
    data = get_all_progress()
    novels = data.get("novels", {})
    novel_entry = novels.get(site)
    if isinstance(novel_entry, dict):
        return novel_entry.get("chapter")
    if isinstance(novel_entry, int):
        return novel_entry
    return None


# Record the last chapter read for a novel and mark it as most recent.
def save_novel_last_read(site: str, chapter: int) -> None:
    if not site or chapter is None:
        return
    with _LOCK:
        data = get_all_progress()
        novels = data.setdefault("novels", {})
        novels[site] = {"chapter": chapter}
        data["last_site"] = site
        save_all_progress(data)


# Summary of the most recent novel + all novel progress.
def get_last_progress() -> dict:
    data = get_all_progress()
    last_site = data.get("last_site")
    novels = data.get("novels", {})
    last_chapter = None
    if last_site and last_site in novels:
        last_chapter = novels[last_site].get("chapter")
    return {
        "site": last_site,
        "chapter": last_chapter,
        "novels": novels
    }
