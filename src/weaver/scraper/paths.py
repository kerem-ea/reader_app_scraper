from pathlib import Path

from .._common import get_data_root
from .site_config import FREEWEBNOVEL, SiteConfig

NOVEL_NAME = ""
START_CHAPTER = 1
END_CHAPTER = 1
NOVEL_DIR = Path()
OUT_JSON = Path()
TEMP_JSONL = Path()
NOVEL_URL = ""
CHAPTER_URL_TMPL = ""
SITE_CONFIG: SiteConfig = FREEWEBNOVEL

BASE_DIR = get_data_root()


# Set up the output paths for the current scrape (data/<novel>/...).
def initialize_paths(site_config: SiteConfig, novel_name: str, start: int, end: int):
    global SITE_CONFIG, NOVEL_NAME, START_CHAPTER, END_CHAPTER
    global NOVEL_DIR, OUT_JSON, TEMP_JSONL, NOVEL_URL
    global CHAPTER_URL_TMPL

    SITE_CONFIG = site_config
    NOVEL_NAME = novel_name
    START_CHAPTER = start
    END_CHAPTER = end
    NOVEL_DIR = BASE_DIR / NOVEL_NAME
    NOVEL_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON = NOVEL_DIR / f"{NOVEL_NAME}_chapters_raw.json"
    TEMP_JSONL = NOVEL_DIR / f"{NOVEL_NAME}_progress.jsonl"
    NOVEL_URL = SITE_CONFIG.novel_url(NOVEL_NAME)
    CHAPTER_URL_TMPL = SITE_CONFIG.chapter_url_template.format(novel=NOVEL_NAME, chapter="{}")
