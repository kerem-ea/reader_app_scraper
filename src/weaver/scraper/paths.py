from dataclasses import dataclass
from pathlib import Path

from .._common import get_data_root
from .site_config import SiteConfig


@dataclass(frozen=True)
class ScrapePaths:
    """All path/URL state for a single scrape run, resolved lazily at run time."""

    SITE_CONFIG: SiteConfig
    NOVEL_NAME: str
    START_CHAPTER: int
    END_CHAPTER: int
    BASE_DIR: Path
    NOVEL_DIR: Path
    OUT_JSON: Path
    TEMP_JSONL: Path
    NOVEL_URL: str
    CHAPTER_URL_TMPL: str

    @classmethod
    def initialize(cls, site_config, novel_name: str, start: int, end: int) -> "ScrapePaths":
        base_dir = get_data_root()
        novel_dir = base_dir / novel_name
        novel_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            SITE_CONFIG=site_config,
            NOVEL_NAME=novel_name,
            START_CHAPTER=start,
            END_CHAPTER=end,
            BASE_DIR=base_dir,
            NOVEL_DIR=novel_dir,
            OUT_JSON=novel_dir / f"{novel_name}_chapters_raw.json",
            TEMP_JSONL=novel_dir / f"{novel_name}_progress.jsonl",
            NOVEL_URL=site_config.novel_url(novel_name),
            CHAPTER_URL_TMPL=site_config.chapter_url(novel_name, "{}"),
        )

    def chapter_url(self, chapter_number: int) -> str:
        return self.CHAPTER_URL_TMPL.format(chapter_number)


_CURRENT: ScrapePaths | None = None


def initialize_paths(site_config, novel_name: str, start: int, end: int) -> ScrapePaths:
    """Configure the current scrape run; resolves the data root lazily."""
    global _CURRENT
    _CURRENT = ScrapePaths.initialize(site_config, novel_name, start, end)
    return _CURRENT


def get_current() -> ScrapePaths:
    if _CURRENT is None:
        raise RuntimeError("paths.initialize_paths() must be called before scraping")
    return _CURRENT


# Legacy attribute access (paths.OUT_JSON etc.) resolves against the current run.
def __getattr__(name: str):
    current = get_current()
    if hasattr(current, name):
        return getattr(current, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")