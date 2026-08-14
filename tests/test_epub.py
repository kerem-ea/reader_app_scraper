import re
import sys

from weaver.epub.builder import _epub_identifier
from weaver.epub.constants import get_base_dir, get_novel_metadata, sanitize_filename


def test_sanitize_filename_removes_invalid_chars():
    name = sanitize_filename("Foo/Bar: Baz?*")
    assert not re.search(r'[\/\\:*?"<>|]', name)
    assert name.strip() == name


def test_sanitize_filename_fallback():
    assert sanitize_filename("", fallback="novel") == "novel"


def test_known_metadata_defaults(tmp_path):
    meta = get_novel_metadata(tmp_path, "shadow-slave")
    assert meta["author"] == "Guiltythree"
    assert meta["volumes"]


def test_unknown_metadata_defaults(tmp_path):
    meta = get_novel_metadata(tmp_path, "some-novel")
    assert meta["author"] == "WebNovel Author"
    assert meta["volumes"] == []


def test_get_base_dir_resolves_lazily(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(sys, "platform", "win32")
    assert get_base_dir() == tmp_path / "weaver-reader" / "data"


def test_epub_identifier_is_stable_urn():
    first = _epub_identifier("shadow-slave")
    second = _epub_identifier("shadow-slave")
    assert first == second
    assert first.startswith("urn:uuid:")


def test_epub_identifier_differs_per_slug():
    assert _epub_identifier("shadow-slave") != _epub_identifier("another-novel")
