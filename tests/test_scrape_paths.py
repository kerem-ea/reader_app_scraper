import sys

from weaver.scraper import paths
from weaver.scraper.site_config import FREEWEBNOVEL


def test_initialize_paths_resolves_data_root_lazily(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(sys, "platform", "win32")

    scrape_paths = paths.initialize_paths(FREEWEBNOVEL, "shadow-slave", 1, 100)

    assert scrape_paths.NOVEL_NAME == "shadow-slave"
    assert scrape_paths.START_CHAPTER == 1
    assert scrape_paths.END_CHAPTER == 100
    assert scrape_paths.NOVEL_URL == "https://freewebnovel.com/novel/shadow-slave"
    assert scrape_paths.CHAPTER_URL_TMPL.format(5) == "https://freewebnovel.com/novel/shadow-slave/chapter-5"
    assert scrape_paths.OUT_JSON == tmp_path / "weaver-reader" / "data" / "shadow-slave" / "shadow-slave_chapters_raw.json"
    assert scrape_paths.TEMP_JSONL.name == "shadow-slave_progress.jsonl"


def test_module_facade_mirrors_current_run(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(sys, "platform", "win32")

    paths.initialize_paths(FREEWEBNOVEL, "shadow-slave", 1, 100)
    assert paths.NOVEL_NAME == "shadow-slave"
    assert paths.START_CHAPTER == 1
    assert paths.END_CHAPTER == 100
    assert paths.NOVEL_URL == "https://freewebnovel.com/novel/shadow-slave"
    assert paths.OUT_JSON.parent.name == "shadow-slave"


def test_chapter_url_helper(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(sys, "platform", "win32")
    scrape_paths = paths.initialize_paths(FREEWEBNOVEL, "shadow-slave", 1, 100)
    assert scrape_paths.chapter_url(42) == "https://freewebnovel.com/novel/shadow-slave/chapter-42"
