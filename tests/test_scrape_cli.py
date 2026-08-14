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
