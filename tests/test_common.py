import os
import sys

from weaver._common import get_data_root, get_progress_file


def test_data_root_uses_appdata_on_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert get_data_root() == tmp_path / "weaver-reader" / "data"


def test_data_root_uses_xdg_on_posix(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert get_data_root() == tmp_path / "weaver-reader" / "data"


def test_data_root_creates_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    get_data_root()
    assert (tmp_path / "weaver-reader" / "data").is_dir()


def test_get_progress_file_lives_outside_data(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert get_progress_file() == tmp_path / "weaver-reader" / "last_read.json"


def test_progress_file_does_not_create_data_root(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    get_progress_file()
    assert not (tmp_path / "weaver-reader" / "data").exists()
