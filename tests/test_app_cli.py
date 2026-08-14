import sys

from weaver.app.app import main as app_main


def test_app_main_prints_version(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["weaver-app", "--version"])
    app_main()
    assert capsys.readouterr().out.startswith("weaver-app ")


def test_app_main_prints_usage_on_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["weaver-app", "--help"])
    app_main()
    assert "Usage:" in capsys.readouterr().out


def test_app_main_rejects_unknown_option(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["weaver-app", "garbage"])
    try:
        app_main()
        raised = False
    except SystemExit as exc:
        raised = exc.code == 2
    assert raised
    assert "unknown option garbage" in capsys.readouterr().err