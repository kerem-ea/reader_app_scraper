import sys

import pytest

from weaver.scraper import scrape


def test_collect_inputs_cli_valid(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["weaver-scraper", "shadow-slave", "1", "10", "1"])
    site, slug, start, end, mode = scrape.collect_inputs()
    assert slug == "shadow-slave"
    assert start == 1 and end == 10
    assert mode == "1"


def test_collect_inputs_cli_rejects_zero_start(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["weaver-scraper", "shadow-slave", "0", "10", "1"])
    with pytest.raises(ValueError):
        scrape.collect_inputs()


def test_collect_inputs_cli_rejects_reversed_range(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["weaver-scraper", "shadow-slave", "10", "5", "1"])
    with pytest.raises(ValueError):
        scrape.collect_inputs()


def test_collect_inputs_cli_rejects_bad_mode(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["weaver-scraper", "shadow-slave", "1", "10", "9"])
    with pytest.raises(ValueError):
        scrape.collect_inputs()


def test_main_prints_version_on_version_flag(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["weaver", "--version"])
    with pytest.raises(SystemExit) as exc:
        scrape.main()
    assert exc.value.code == 0
    assert capsys.readouterr().out.startswith("weaver-reader ")


def test_main_prints_version_on_short_flag(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["weaver", "-V"])
    with pytest.raises(SystemExit) as exc:
        scrape.main()
    assert exc.value.code == 0


def test_main_prints_usage_on_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["weaver", "--help"])
    scrape.main()
    assert "Usage:" in capsys.readouterr().out


def test_main_rejects_unknown_option(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["weaver", "----version"])
    with pytest.raises(SystemExit) as exc:
        scrape.main()
    assert exc.value.code == 2
    assert "unknown option ----version" in capsys.readouterr().err


def test_main_rejects_missing_arguments(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["weaver", "hello"])
    with pytest.raises(SystemExit) as exc:
        scrape.main()
    assert exc.value.code == 2
    assert "usage: weaver" in capsys.readouterr().err


def test_main_rejects_too_many_arguments(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["weaver", "a", "b", "c", "d", "e"])
    with pytest.raises(SystemExit) as exc:
        scrape.main()
    assert exc.value.code == 2
