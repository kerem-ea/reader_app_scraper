"""Shared path resolution helpers for the Weaver package."""

import os
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
    checkout; otherwise falls back to the current working directory's data/.
    """
    repo = repo_data_root()
    if repo is not None:
        return repo
    cwd_data = Path.cwd() / "data"
    cwd_data.mkdir(parents=True, exist_ok=True)
    return cwd_data


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
