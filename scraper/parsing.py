import re
from selectolax.parser import HTMLParser

from constants import (
    CHAPTER_RE,
    DEFAULT_HEADERS,
    GENERIC_TITLE_BLACKLIST,
    TITLE_RE,
)


def extract_content(html: str) -> tuple[str, int]:
    match = CHAPTER_RE.search(html)

    if match:
        tree = HTMLParser(match.group(1))
        parts = [
            p.text(strip=True)
            for p in tree.css("p")
            if p.text(strip=True)
        ]
        text = "\n\n".join(parts)
        if len(text.split()) > 50:
            return text, len(text.split())

    tree = HTMLParser(html)
    candidates = (
        tree.css("div.chapter-content")
        or tree.css("div#chapter-content")
        or tree.css("div.reading-content")
        or tree.css("article")
        or tree.css("div")
    )

    for node in candidates:
        parts = [
            p.text(strip=True)
            for p in node.css("p")
            if p.text(strip=True)
        ]
        text = "\n\n".join(parts)
        if len(text.split()) > 50:
            return text, len(text.split())

    return "", 0


def extract_title_from_chapter_page(html: str) -> str | None:
    tree = HTMLParser(html)
    for selector in (
        "h1",
        "h2",
        "div.chapter-title",
        "div#chapter-title",
        "div#chapter-name",
        "title",
    ):
        node = tree.css_first(selector)
        if not node:
            continue
        text = node.text(strip=True)
        if not text:
            continue
        match = TITLE_RE.search(text)
        if match:
            return match.group(2).strip(" .")
        cleaned = re.sub(
            r"^Chapter\s+\d+(?:\s*[:\-–—]\s*|\s+)",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip(" .")
        if cleaned:
            return cleaned

    match = TITLE_RE.search(html)
    if match:
        return match.group(2).strip(" .")

    return None


def looks_like_challenge(status_code: int, html: str) -> bool:
    if status_code in (403, 429, 503, 520, 521, 524):
        return True

    lower = html.lower()

    return (
        "just a moment" in lower
        or "checking your browser" in lower
        or "challenges.cloudflare.com" in lower
        or "attention required" in lower
        or "cf-chl-bypass" in lower
        or "error 1015" in lower
        or "you are being rate limited" in lower
        or "rate limited" in lower
        or ("ray id" in lower and "cloudflare" in lower)
    )


def is_rate_limited(status_code: int) -> bool:
    return status_code == 429


def parse_retry_after(headers: dict[str, str]) -> float | None:
    value = headers.get("Retry-After")

    try:
        return float(value) if value else None
    except (ValueError, TypeError):
        return None


def is_generic_chapter_title(text: str) -> bool:
    lower = text.strip().lower()
    if not lower:
        return True
    if lower in GENERIC_TITLE_BLACKLIST:
        return True
    if lower.startswith(("read first", "read now", "read more", "continue reading", "read chapter")):
        return True
    if lower in ("chapter", "chapter one", "chapter 1", "chapter i"):
        return True
    return False


def parse_chapter_titles(html: str) -> dict[int, str]:
    titles = {}
    tree = HTMLParser(html)

    for link in tree.css("a"):
        href = (link.attributes.get("href") or "").strip() if link.attributes else ""
        if not href or "/chapter-" not in href:
            continue

        title_attr = (link.attributes.get("title") or "").strip() if link.attributes else ""
        text = link.text(strip=True)
        raw_text = text or title_attr
        raw_text = re.sub(r"^[^\w\d]+", "", raw_text).strip()
        raw_lower = raw_text.lower()

        href_match = re.search(r"/chapter-(\d+)", href, re.IGNORECASE)
        if not href_match:
            continue

        chapter_number = int(href_match.group(1))

        match = TITLE_RE.search(raw_text)
        if match:
            chapter_title = match.group(2).strip(" .")
            if chapter_title and not is_generic_chapter_title(chapter_title):
                titles[chapter_number] = chapter_title
                continue

        if "chapter" not in raw_lower:
            continue

        clean_text = re.sub(
            r"^Chapter\s+\d+(?:\s*[:\-–—]\s*|\s+)",
            "",
            raw_text,
            flags=re.IGNORECASE,
        ).strip(" .")
        if clean_text and not is_generic_chapter_title(clean_text):
            titles[chapter_number] = clean_text

    return titles
