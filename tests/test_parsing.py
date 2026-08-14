from weaver.scraper.parsing import (
    _clean_chapter_title,
    extract_content,
    is_generic_chapter_title,
    looks_like_challenge,
    parse_chapter_titles,
)


def _content_html(num_words: int) -> str:
    words = " ".join(["word"] * num_words)
    return f'<html><body><div class="chapter-content"><p>{words}</p></div></body></html>'


def test_extract_content_above_threshold():
    text, wc = extract_content(_content_html(60))
    assert wc == 60
    assert text


def test_extract_content_below_threshold_returns_empty():
    text, wc = extract_content(_content_html(20))
    assert wc == 0
    assert text == ""


def test_extract_content_respects_site_min_word_count():
    from weaver.scraper.site_config import SiteConfig

    strict = SiteConfig(
        name="strict",
        domain="example.com",
        novel_url_template="https://example.com/novel/{novel}",
        chapter_url_template="https://example.com/novel/{novel}/chapter-{chapter}",
        min_word_count=100,
    )
    text, wc = extract_content(_content_html(60), site_config=strict)
    assert text == ""
    assert wc == 0


def test_extract_content_from_chapter_start_blocks():
    html = (
        '<div class="chapter-start"><p>'
        + " ".join(["word"] * 60)
        + '</p><div class="chapter-end">'
    )
    text, wc = extract_content(html)
    assert wc == 60
    assert text


def test_parse_chapter_titles():
    html = (
        '<a href="/novel/shadow-slave/chapter-1" title="Chapter 1 The Awakening">'
        "Chapter 1 The Awakening</a>"
        '<a href="/novel/shadow-slave/chapter-2">Read More</a>'
    )
    titles = parse_chapter_titles(html)
    assert titles == {1: "The Awakening"}


def test_clean_chapter_title():
    assert _clean_chapter_title("Chapter 5: The Gate") == "The Gate"


def test_is_generic_chapter_title():
    assert is_generic_chapter_title("Continue Reading") is True
    assert is_generic_chapter_title("Read First") is True
    assert is_generic_chapter_title("The Cursed Sword") is False


def test_looks_like_challenge():
    assert looks_like_challenge(403, "") is True
    assert looks_like_challenge(200, "just a moment...") is True
    assert looks_like_challenge(200, "normal page content") is False
