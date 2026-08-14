import re
from dataclasses import dataclass
from urllib.parse import urlparse


# Immutable description of how a novel site is structured.
@dataclass(frozen=True)
class SiteConfig:
    name: str
    domain: str
    novel_url_template: str
    chapter_url_template: str
    novel_path_regex: str = r"/novel/([^/?#]+)"
    chapter_regex: str = r'<div\s+class="chapter-start"\s*>(.*?)<div\s+class="chapter-end"\s*>'
    content_css_selectors: tuple[str, ...] = (
        "div.chapter-content",
        "div#chapter-content",
        "div.reading-content",
        "article",
        "div",
    )
    title_css_selectors: tuple[str, ...] = (
        "h1",
        "h2",
        "div.chapter-title",
        "div#chapter-title",
        "div#chapter-name",
        "title",
    )
    catalog_select_selector: str = "#indexselect"
    chapter_link_href_pattern: str = "/chapter-"
    chapter_link_regex: str = r"/chapter-(\d+)"
    catalog_page_size: int = 40
    min_word_count: int = 50
    author_css_selectors: tuple[str, ...] = (
        "span.author a",
        "div.property a[href*='/author/']",
        "a[href*='/author/']",
        "span[itemprop='author']",
        "div.author",
    )
    cover_css_selectors: tuple[str, ...] = (
        "meta[property='og:image']",
        "meta[name='twitter:image']",
        "div.pic img",
        "div.book-img img",
        "div.imgbox img",
        "div.books-img img",
        "img.cover",
    )
    title_main_selectors: tuple[str, ...] = (
        "h1.tit",
        "h3.tit",
        "h1.book-name",
        "h1",
    )

    def novel_url(self, novel_name: str) -> str:
        return self.novel_url_template.format(novel=novel_name)

    def chapter_url(self, novel_name: str, chapter_number: int) -> str:
        return self.chapter_url_template.format(novel=novel_name, chapter=chapter_number)

    # Extract a bare novel slug from a URL or a plain slug string.
    def extract_novel_slug(self, value: str) -> str | None:
        value = value.strip()

        if value.startswith(("http://", "https://")):
            parsed = urlparse(value)
            if parsed.netloc.lower().endswith(self.domain.lower()):
                match = re.search(self.novel_path_regex, parsed.path)
                if match:
                    return match.group(1).strip("/")
            return None

        if re.match(r"^[A-Za-z0-9_-]+$", value):
            return value.strip("/")

        return None


FREEWEBNOVEL = SiteConfig(
    name="freewebnovel",
    domain="freewebnovel.com",
    novel_url_template="https://freewebnovel.com/novel/{novel}",
    chapter_url_template="https://freewebnovel.com/novel/{novel}/chapter-{chapter}",
)


# Registry that resolves user input (URL or slug) to a SiteConfig + slug.
class SiteRegistry:
    _sites = {
        "freewebnovel.com": FREEWEBNOVEL,
        "www.freewebnovel.com": FREEWEBNOVEL,
    }

    # Resolve user input to a supported SiteConfig and extracted novel slug.
    @classmethod
    def get(cls, user_input: str) -> tuple[SiteConfig, str]:
        value = user_input.strip()
        if not value:
            raise ValueError("Empty site input is not supported.")

        if value.startswith(("http://", "https://")):
            parsed = urlparse(value)
            domain = parsed.netloc.lower().split(":")[0]
            site = cls._sites.get(domain)
            if site is None:
                raise ValueError(
                    f"Unsupported website domain '{domain}'. "
                    "Supported sites: " + ", ".join(sorted({s.domain for s in cls._sites.values()}))
                )
            slug = site.extract_novel_slug(value)
            if not slug:
                raise ValueError(
                    f"Could not extract novel slug from URL for site '{site.name}'."
                )
            return site, slug

        if re.match(r"^[A-Za-z0-9_-]+$", value):
            return FREEWEBNOVEL, value

        raise ValueError(
            "Could not determine the novel site or slug from input. "
            "Use a supported novel URL or a valid slug."
        )
