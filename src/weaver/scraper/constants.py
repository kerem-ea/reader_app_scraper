import re
from dataclasses import dataclass

REBOOTSTRAP_EVERY_N = 85
BOOTSTRAP_HEADLESS = True
IMPERSONATE_CANDIDATES = [
    "firefox135",
    "firefox133",
    "firefox117",
    "chrome131",
]
IMPERSONATE = IMPERSONATE_CANDIDATES[0]

REQUEST_TIMEOUT = 45
FAIL_STREAK_LIMIT = 2
RATE_LIMIT_STREAK_LIMIT = 4
MIN_WORD_COUNT = 50

DEFAULT_HEADERS = {
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1",
}

TITLE_RE = re.compile(
    r"Chapter\s+(\d+)(?:\s*[:\-–—]\s*|\s+)\s*(.*)$",
    re.IGNORECASE,
)

GENERIC_TITLE_BLACKLIST = {
    "read first",
    "read now",
    "read more",
    "continue reading",
    "continue",
    "chapter 1",
    "chapter one",
    "chapter i",
}

# Per-mode tuning presets: concurrency, delays, retries and cooldowns.
MODE_SETTINGS = {
    "fast": dict(
        max_concurrent=2,
        delay_between=1.2,
        min_delay=0.6,
        ramp_down_every=3,
        ramp_down_factor=0.99,
        max_retries=6,
        challenge_wait=(2.5, 4.0),
        global_cooldown=60.0,
    ),
    "slow": dict(
        max_concurrent=1,
        delay_between=6.0,
        min_delay=6.0,
        ramp_down_every=10**9,
        ramp_down_factor=1.0,
        max_retries=1,
        challenge_wait=(3.0, 6.0),
        global_cooldown=120.0,
    ),
    "browser_only": dict(
        max_concurrent=2,
        delay_between=0.42,
        min_delay=0.24,
        ramp_down_every=10**9,
        ramp_down_factor=1.0,
        max_retries=4,
        challenge_wait=(1.0, 2.0),
        global_cooldown=30.0,
    ),
}

# Runtime settings bundle for the current scrape mode.
@dataclass
class Settings:
    mode: str
    max_concurrent: int
    delay_between: float
    min_delay: float
    ramp_down_every: int
    ramp_down_factor: float
    max_retries: int
    challenge_wait: tuple[float, float]
    global_cooldown: float
