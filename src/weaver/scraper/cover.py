import io
from pathlib import Path
from urllib.parse import urljoin
from selectolax.parser import HTMLParser

from .constants import DEFAULT_HEADERS, IMPERSONATE
from .site_config import SiteConfig


def _http_get(url: str, headers: dict, timeout: int):
    from curl_cffi.requests import get as http_get

    return http_get(url, headers=headers, timeout=timeout, impersonate=IMPERSONATE)


# GET the novel landing page HTML (used to locate the cover image).
def fetch_novel_landing_page(site_config: SiteConfig, novel_slug: str, novel_url: str) -> str:
    landing_url = site_config.novel_url(novel_slug)
    try:
        headers = dict(DEFAULT_HEADERS)
        headers["Referer"] = novel_url
        response = _http_get(landing_url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"[cover] Failed to fetch landing page for {novel_slug}: {e}")
        return ""


# Find the cover image URL from og:/twitter: meta tags or site selectors.
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


# Download the cover image and save it as PNG (fallback: raw bytes).
def download_cover_image(cover_url: str, output_path: Path) -> bool:
    try:
        headers = dict(DEFAULT_HEADERS)
        response = _http_get(cover_url, headers=headers, timeout=15)
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


# End-to-end: fetch landing page, find cover URL, download to output_dir/cover.png.
def download_novel_cover(site_config: SiteConfig, novel_slug: str, novel_url: str, output_dir: Path) -> bool:
    landing_html = fetch_novel_landing_page(site_config, novel_slug, novel_url)
    if not landing_html:
        return False

    cover_url = extract_cover_url_from_landing_page(landing_html, site_config, novel_url)
    if not cover_url:
        return False

    cover_path = output_dir / "cover.png"
    return download_cover_image(cover_url, cover_path)