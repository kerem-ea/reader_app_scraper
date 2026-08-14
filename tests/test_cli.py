import sys

from weaver import cli


def test_cli_help_lists_subcommands(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["weaver", "--help"])
    cli.main()
    out = capsys.readouterr().out
    assert "weaver-scraper" in out
    assert "weaver-epub" in out
    assert "weaver-app" in out


def test_cli_prints_version(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["weaver", "--version"])
    cli.main()
    assert capsys.readouterr().out.startswith("weaver-reader ")


def test_cli_dispatches_scraper(monkeypatch):
    called = {}
    monkeypatch.setattr(sys, "argv", ["weaver", "scraper", "shadow-slave", "1", "10", "1"])

    def fake_main():
        called["argv"] = list(sys.argv)

    monkeypatch.setattr("weaver.scraper.main", fake_main)
    cli.main()
    assert called["argv"] == ["weaver-scraper", "shadow-slave", "1", "10", "1"]


def test_cli_dispatches_epub(monkeypatch):
    called = {}
    monkeypatch.setattr(sys, "argv", ["weaver", "epub", "shadow-slave"])

    def fake_main():
        called["argv"] = list(sys.argv)

    monkeypatch.setattr("weaver.epub.main", fake_main)
    cli.main()
    assert called["argv"] == ["weaver-epub", "shadow-slave"]


def test_cli_dispatches_app(monkeypatch):
    called = {}
    monkeypatch.setattr(sys, "argv", ["weaver", "app"])

    def fake_main():
        called["argv"] = list(sys.argv)

    monkeypatch.setattr("weaver.app.main", fake_main)
    cli.main()
    assert called["argv"] == ["weaver-app"]


def test_cli_falls_back_to_scraper(monkeypatch):
    called = {}
    monkeypatch.setattr(sys, "argv", ["weaver", "shadow-slave", "1", "10", "1"])

    def fake_main():
        called["argv"] = list(sys.argv)

    monkeypatch.setattr("weaver.scraper.main", fake_main)
    cli.main()
    assert called["argv"] == ["weaver", "shadow-slave", "1", "10", "1"]