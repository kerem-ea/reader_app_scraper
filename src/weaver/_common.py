"""Shared helpers for the Weaver package."""

import os
import re
import sys
from pathlib import Path


def repo_data_root() -> Path | None:
    """Return the repository data/ directory when running from a source checkout."""
    package_dir = Path(__file__).resolve().parent
    for candidate in (package_dir, *package_dir.parents):
        if (candidate / "data").is_dir() and (candidate / "pyproject.toml").is_file():
            return candidate / "data"
    return None


def get_data_root() -> Path:
    """Resolve the runtime data directory.

    Prefers the repository data/ directory when running from a source
    checkout; otherwise falls back to a stable per-user data directory
    that is independent of the current working directory. This keeps the
    scraper, EPUB builder and reader app all pointing at the same data,
    no matter where each command is launched from.
    """
    repo = repo_data_root()
    if repo is not None:
        return repo

    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent / "data"
    elif sys.platform == "win32":
        appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        base = appdata / "weaver-reader" / "data"
    else:
        xdg = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        base = xdg / "weaver-reader" / "data"

    base.mkdir(parents=True, exist_ok=True)
    return base


def get_version() -> str:
    """Return the installed weaver-reader version.

    Uses importlib.metadata when the package is installed; otherwise falls
    back to parsing pyproject.toml in a source checkout.
    """
    try:
        from importlib.metadata import version as _version
        return _version("weaver-reader")
    except Exception:
        pass

    package_dir = Path(__file__).resolve().parent
    for candidate in (package_dir, *package_dir.parents):
        pyproject = candidate / "pyproject.toml"
        if pyproject.is_file():
            try:
                text = pyproject.read_text(encoding="utf-8")
                match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
                if match:
                    return match.group(1)
            except OSError:
                pass
            break
    return "unknown"


def get_progress_file() -> Path:
    """Return the path to the per-user reading progress file.

    Progress state is stored outside the repository so user-generated reading
    data never pollutes the tracked sample (Shadow Slave) data.
    """
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    elif sys.platform == "win32":
        appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        base = appdata / "weaver-reader"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "weaver-reader"
    base.mkdir(parents=True, exist_ok=True)
    return base / "last_read.json"
