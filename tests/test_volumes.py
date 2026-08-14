import json

from weaver.epub.volumes import auto_volumes, resolve_volumes


def test_auto_volumes_covers_all_chapters():
    vols = auto_volumes(1000)
    assert vols[0][2] == 1
    assert vols[-1][3] == 1000
    prev_end = 0
    for _v, _title, start, end in vols:
        assert start == prev_end + 1
        assert start <= end
        prev_end = end


def test_auto_volumes_respects_volume_count():
    vols = auto_volumes(100, volume_count=4)
    assert len(vols) == 4
    assert vols[-1][3] == 100


def test_auto_volumes_empty_input():
    assert auto_volumes(0) == []


def test_auto_volumes_capped():
    vols = auto_volumes(100000)
    assert len(vols) <= 20


def test_resolve_volumes_prefers_stored(tmp_path):
    novel = tmp_path / "novel"
    novel.mkdir()
    (novel / "metadata.json").write_text(
        json.dumps({"volumes": [{"number": 1, "title": "A", "start": 1, "end": 10}]}),
        encoding="utf-8",
    )
    assert resolve_volumes(novel, "novel", 100) == [(1, "A", 1, 10)]


def test_resolve_volumes_auto_and_persists(tmp_path):
    novel = tmp_path / "novel"
    novel.mkdir()
    vols = resolve_volumes(novel, "novel", 100)
    assert vols
    persisted = json.loads((novel / "metadata.json").read_text(encoding="utf-8"))
    assert len(persisted["volumes"]) == len(vols)


def test_resolve_volumes_flat(tmp_path):
    novel = tmp_path / "novel"
    novel.mkdir()
    (novel / "metadata.json").write_text(
        json.dumps({"volumes": [{"number": 1, "title": "A", "start": 1, "end": 10}]}),
        encoding="utf-8",
    )
    assert resolve_volumes(novel, "novel", 100, force="flat") == []


def test_resolve_volumes_auto_regenerates_over_stored(tmp_path):
    novel = tmp_path / "novel"
    novel.mkdir()
    (novel / "metadata.json").write_text(
        json.dumps({"volumes": [{"number": 1, "title": "A", "start": 1, "end": 10}]}),
        encoding="utf-8",
    )
    vols = resolve_volumes(novel, "novel", 100, force="auto", volume_count=5)
    assert len(vols) == 5