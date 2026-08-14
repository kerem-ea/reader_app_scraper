import sys

from weaver.app.multi_progress import (
    get_all_progress,
    get_last_progress,
    get_novel_last_read,
    save_all_progress,
    save_novel_last_read,
)


def test_save_and_read_progress(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(sys, "platform", "win32")

    save_novel_last_read("shadow-slave", 42)

    assert get_novel_last_read("shadow-slave") == 42
    assert get_novel_last_read("missing") is None

    summary = get_last_progress()
    assert summary["site"] == "shadow-slave"
    assert summary["chapter"] == 42
    assert summary["novels"]["shadow-slave"] == {"chapter": 42}


def test_get_all_progress_without_novels_key(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(sys, "platform", "win32")

    save_all_progress({"site": "shadow-slave"})
    data = get_all_progress()
    assert data["last_site"] == "shadow-slave"
    assert data["novels"] == {}
