import io
import os
import sys
from pathlib import Path
from urllib.parse import urljoin
import requests
from selectolax.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from constants import DEFAULT_HEADERS
from site_config import SiteConfig


def fetch_novel_landing_page(site_config: SiteConfig, novel_slug: str, novel_url: str) -> str:
    landing_url = site_config.novel_url(novel_slug)
    try:
        headers = dict(DEFAULT_HEADERS)
        headers["Referer"] = novel_url
        response = requests.get(landing_url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"[cover] Failed to fetch landing page for {novel_slug}: {e}")
        return ""


def extract_cover_url_from_landing_page(html: str, site_config: SiteConfig, novel_url: str) -> str | None:
    if not html:
        return None
    tree = HTMLParser(html)
    cover_url = None

    for meta_prop in ("og:image", "twitter:image", "image"):
        og_image = tree.css_first(f"meta[property='{meta_prop}']") or tree.css_first(f"meta[name='{meta_prop}']")
        if og_image and og_image.attributes.get("content"):
            content_val = og_image.attributes.get("content", "").strip()
            if content_val and not content_val.endswith("logo.png"):
                cover_url = content_val
                break

    if not cover_url:
        for sel in site_config.cover_css_selectors:
            if sel.startswith("meta"):
                continue
            for node in tree.css(sel):
                src = node.attributes.get("src") or node.attributes.get("data-src")
                if src:
                    src_clean = src.strip()
                    if src_clean and not src_clean.endswith("logo.png"):
                        cover_url = src_clean
                        break
            if cover_url:
                break

    if cover_url:
        if cover_url.startswith("//"):
            cover_url = "https:" + cover_url
        elif cover_url.startswith("/"):
            cover_url = urljoin(novel_url, cover_url)

    return cover_url


def download_cover_image(cover_url: str, output_path: Path) -> bool:
    try:
        headers = dict(DEFAULT_HEADERS)
        response = requests.get(cover_url, headers=headers, timeout=15)
        response.raise_for_status()
        if not response.content or len(response.content) < 100:
            return False

        try:
            from PIL import Image
            image = Image.open(io.BytesIO(response.content))
            image.convert("RGB").save(output_path, "PNG")
        except Exception:
            with open(output_path, "wb") as f:
                f.write(response.content)
        return True
    except Exception as e:
        print(f"[cover] Failed to download cover from {cover_url}: {e}")
        return False


def download_novel_cover(site_config: SiteConfig, novel_slug: str, novel_url: str, output_dir: Path) -> bool:
    landing_html = fetch_novel_landing_page(site_config, novel_slug, novel_url)
    if not landing_html:
        return False

    cover_url = extract_cover_url_from_landing_page(landing_html, site_config, novel_url)
    if not cover_url:
        return False

    cover_path = output_dir / "cover.png"
    return download_cover_image(cover_url, cover_path)