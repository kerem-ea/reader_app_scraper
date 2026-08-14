import pytest

from weaver.scraper.site_config import FREEWEBNOVEL, SiteConfig, SiteRegistry


def test_default_min_word_count():
    assert FREEWEBNOVEL.min_word_count == 50


def test_novel_url():
    assert FREEWEBNOVEL.novel_url("shadow-slave") == "https://freewebnovel.com/novel/shadow-slave"


def test_chapter_url():
    assert FREEWEBNOVEL.chapter_url("shadow-slave", 5) == "https://freewebnovel.com/novel/shadow-slave/chapter-5"


def test_extract_novel_slug_from_url():
    assert FREEWEBNOVEL.extract_novel_slug("https://freewebnovel.com/novel/shadow-slave/") == "shadow-slave"


def test_extract_novel_slug_rejects_foreign_domain():
    assert FREEWEBNOVEL.extract_novel_slug("https://example.com/novel/shadow-slave") is None


def test_extract_novel_slug_plain():
    assert FREEWEBNOVEL.extract_novel_slug("shadow-slave") == "shadow-slave"


def test_registry_resolves_slug():
    site, slug = SiteRegistry.get("shadow-slave")
    assert site is FREEWEBNOVEL
    assert slug == "shadow-slave"


def test_registry_resolves_url():
    site, slug = SiteRegistry.get("https://freewebnovel.com/novel/shadow-slave")
    assert site is FREEWEBNOVEL
    assert slug == "shadow-slave"


def test_registry_rejects_unsupported_domain():
    with pytest.raises(ValueError):
        SiteRegistry.get("https://example.com/novel/foo")


def test_custom_site_min_word_count():
    custom = SiteConfig(
        name="custom",
        domain="example.com",
        novel_url_template="https://example.com/novel/{novel}",
        chapter_url_template="https://example.com/novel/{novel}/chapter-{chapter}",
        min_word_count=200,
    )
    assert custom.min_word_count == 200
