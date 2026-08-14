import pytest

from weaver import _common


@pytest.fixture(autouse=True)
def _disable_repo_data_root(monkeypatch):
    """Force tests to exercise the per-user data root fallback.

    When running the suite from a source checkout, repo_data_root() resolves
    the repository's own data/ directory, which would shadow the APPDATA/XDG
    paths these tests assert on. Disabling it keeps data-root resolution
    deterministic regardless of where pytest runs.
    """
    monkeypatch.setattr(_common, "repo_data_root", lambda: None)