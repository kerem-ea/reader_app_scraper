"""Volume planning for EPUB builds.

FreeWebNovel has no volume concept, so chapter ranges can't be discovered from
the site. Volume structure is therefore resolved from three sources, in
priority order:

1. The novel's ``metadata.json`` ``volumes`` key (user-editable data).
2. Built-in curated defaults for a few known novels (see constants).
3. Auto-generated contiguous splits derived from the chapter count, so every
   novel can be split consistently without any site knowledge.

Auto-generated volumes are written back to ``metadata.json`` so the user owns
them and can edit or delete them afterwards.
"""

import json
from pathlib import Path

from .constants import get_novel_metadata

DEFAULT_CHAPTERS_PER_VOLUME = 250
MIN_VOLUMES = 1
MAX_VOLUMES = 20


def auto_volumes(
    chapter_count: int,
    *,
    volume_count: int | None = None,
    chapters_per_volume: int | None = None,
) -> list[tuple[int, str, int, int]]:
    """Split chapters 1..chapter_count into roughly equal contiguous volumes."""
    if chapter_count <= 0:
        return []

    if volume_count:
        count = max(MIN_VOLUMES, min(volume_count, chapter_count, MAX_VOLUMES))
    else:
        cps = chapters_per_volume or DEFAULT_CHAPTERS_PER_VOLUME
        count = max(MIN_VOLUMES, min((chapter_count + cps - 1) // cps, MAX_VOLUMES))

    volumes = []
    start = 1
    for v in range(1, count + 1):
        remaining = count - v + 1
        end = start + (chapter_count - start + 1) // remaining - 1
        volumes.append((v, f"Volume {v}", start, end))
        start = end + 1
    return volumes


def resolve_volumes(
    output_dir: Path,
    novel_slug: str,
    chapter_count: int,
    *,
    volume_count: int | None = None,
    force: str | None = None,
) -> list[tuple[int, str, int, int]]:
    """Return the volume list to use when building a novel's EPUB.

    ``force``: ``None`` (normal precedence), ``"auto"`` (ignore stored volumes
    and regenerate), or ``"flat"`` (no volumes at all).
    """
    if force == "flat":
        return []

    metadata = get_novel_metadata(output_dir, novel_slug)
    stored = list(metadata.get("volumes") or [])

    if stored and force != "auto":
        return stored

    volumes = auto_volumes(chapter_count, volume_count=volume_count)
    if volumes and not stored:
        _persist_volumes(output_dir, volumes)
    return volumes


def _persist_volumes(output_dir: Path, volumes) -> None:
    """Write auto-generated volumes into metadata.json so the user can edit them."""
    meta_file = Path(output_dir) / "metadata.json"
    data = {}
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    if not isinstance(data, dict):
        data = {}

    data["volumes"] = [
        {"number": v[0], "title": v[1], "start": v[2], "end": v[3]} for v in volumes
    ]

    try:
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[volumes] Warning: could not persist volumes to {meta_file}: {e}")