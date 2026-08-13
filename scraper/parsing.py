import re
from selectolax.parser import HTMLParser

from constants import (
    CHAPTER_RE,
    DEFAULT_HEADERS,
    GENERIC_TITLE_BLACKLIST,
    MIN_WORD_COUNT,
    TITLE_RE,
)
from site_config import SiteConfig, FREEWEBNOVEL


def extract_content(html: str, site_config: SiteConfig | None = None) -> tuple[str, int]:
    config = site_config or FREEWEBNOVEL
    chapter_regex = re.compile(config.chapter_regex, re.DOTALL | re.IGNORECASE)
    match = chapter_regex.search(html)

    if match:
        tree = HTMLParser(match.group(1))
        parts = [
            p.text(strip=True)
            for p in tree.css("p")
            if p.text(strip=True)
        ]
        text = "\n\n".join(parts)
        if len(text.split()) >= MIN_WORD_COUNT:
            return text, len(text.split())

    tree = HTMLParser(html)
    candidates = []
    for sel in config.content_css_selectors:
        res = tree.css(sel)
        if res:
            candidates.extend(res)
            break

    for node in candidates:
        parts = [
            p.text(strip=True)
            for p in node.css("p")
            if p.text(strip=True)
        ]
        text = "\n\n".join(parts)
        if len(text.split()) >= MIN_WORD_COUNT:
            return text, len(text.split())

    return "", 0


def extract_title_from_chapter_page(html: str, site_config: SiteConfig | None = None) -> str | None:
    config = site_config or FREEWEBNOVEL
    tree = HTMLParser(html)
    for selector in config.title_css_selectors:
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


def parse_chapter_titles(html: str, site_config: SiteConfig | None = None) -> dict[int, str]:
    config = site_config or FREEWEBNOVEL
    titles = {}
    tree = HTMLParser(html)

    for link in tree.css("a"):
        href = (link.attributes.get("href") or "").strip() if link.attributes else ""
        if not href or config.chapter_link_href_pattern not in href:
            continue

        title_attr = (link.attributes.get("title") or "").strip() if link.attributes else ""
        text = link.text(strip=True)
        raw_text = text or title_attr
        raw_text = re.sub(r"^[^\w\d]+", "", raw_text).strip()
        raw_lower = raw_text.lower()

        href_match = re.search(config.chapter_link_regex, href, re.IGNORECASE)
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


import json
from pathlib import Path


def extract_novel_metadata(html: str, url: str, site_config: SiteConfig | None = None) -> dict:
    config = site_config or FREEWEBNOVEL
    tree = HTMLParser(html)
    metadata = {}

    title = None
    for sel in config.title_main_selectors:
        node = tree.css_first(sel)
        if node and node.text(strip=True):
            title = node.text(strip=True)
            break

    if not title:
        og_title = tree.css_first("meta[property='og:title']")
        if og_title and og_title.attributes.get("content"):
            title = og_title.attributes.get("content").strip()

    if title:
        metadata["title"] = title

    author = None
    for sel in config.author_css_selectors:
        node = tree.css_first(sel)
        if node and node.text(strip=True):
            raw_author = node.text(strip=True)
            cleaned = re.sub(r"^Author\s*:\s*", "", raw_author, flags=re.IGNORECASE).strip()
            if cleaned:
                author = cleaned
                break

    if not author:
        og_author = tree.css_first("meta[property='og:novel:author']") or tree.css_first("meta[name='author']")
        if og_author and og_author.attributes.get("content"):
            author = og_author.attributes.get("content").strip()

    if author:
        metadata["author"] = author

    cover_url = None
    for sel in config.cover_css_selectors:
        node = tree.css_first(sel)
        if not node:
            continue
        if sel.startswith("meta"):
            src = node.attributes.get("content")
        else:
            src = node.attributes.get("src") or node.attributes.get("data-src")
        if src:
            cover_url = src.strip()
            if cover_url.startswith("//"):
                cover_url = "https:" + cover_url
            break

    if cover_url:
        metadata["cover_url"] = cover_url

    return metadata


def save_scraped_metadata(output_dir: Path, novel_slug: str, metadata: dict, site_name: str, novel_url: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    meta_file = output_dir / "metadata.json"

    existing = {}
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    title = metadata.get("title") or existing.get("title") or novel_slug.replace("-", " ").title()
    author = existing.get("author") or metadata.get("author") or "WebNovel Author"

    merged = {
        "title": title,
        "author": author,
        "site": site_name,
        "url": novel_url,
        "volumes": existing.get("volumes", []),
    }

    try:
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
    except Exception as e:
        print(f"[metadata] Warning: Could not write metadata.json: {e}")


