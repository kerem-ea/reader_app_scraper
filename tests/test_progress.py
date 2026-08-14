import json

from weaver.scraper.progress import compile_json, iter_jsonl, load_done


def test_iter_jsonl_sorted_by_chapter(tmp_path):
    p = tmp_path / "p.jsonl"
    p.write_text(
        '{"id":"chapter-2","status":"success"}\n'
        '{"id":"chapter-1","status":"success"}\n'
        '{"id":"chapter-3","status":"failed"}\n',
        encoding="utf-8",
    )
    items = list(iter_jsonl(p))
    assert [i["id"] for i in items] == ["chapter-1", "chapter-2", "chapter-3"]


def test_iter_jsonl_skips_malformed_lines(tmp_path):
    p = tmp_path / "p.jsonl"
    p.write_text(
        '{"id":"chapter-1","status":"success"}\n'
        "not json\n"
        '\n'
        '{"id":"chapter-2","status":"success"}\n',
        encoding="utf-8",
    )
    items = list(iter_jsonl(p))
    assert [i["id"] for i in items] == ["chapter-1", "chapter-2"]


def test_iter_jsonl_missing_file(tmp_path):
    assert list(iter_jsonl(tmp_path / "nope.jsonl")) == []


def test_load_done(tmp_path):
    p = tmp_path / "p.jsonl"
    p.write_text(
        '{"id":"chapter-1","status":"success"}\n'
        '{"id":"chapter-2","status":"failed"}\n',
        encoding="utf-8",
    )
    assert load_done(p) == {"chapter-1"}


def test_compile_json_writes_ordered_output(tmp_path):
    p = tmp_path / "p.jsonl"
    p.write_text(
        '{"id":"chapter-2","status":"success","text":"b"}\n'
        '{"id":"chapter-1","status":"success","text":"a"}\n'
        '{"id":"chapter-9","status":"failed","text":"x"}\n',
        encoding="utf-8",
    )
    out = tmp_path / "out.json"
    compile_json(p, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert list(data.keys()) == ["chapter-1", "chapter-2"]
    assert "chapter-9" not in data


def test_compile_json_empty_input_creates_nothing(tmp_path):
    p = tmp_path / "p.jsonl"
    p.write_text('{"id":"chapter-1","status":"failed"}\n', encoding="utf-8")
    out = tmp_path / "out.json"
    compile_json(p, out)
    assert not out.exists()


def test_compile_json_tolerates_malformed_id(tmp_path):
    p = tmp_path / "p.jsonl"
    p.write_text(
        '{"id":"chapter-2","status":"success","text":"b"}\n'
        '{"id":"weird-key","status":"success","text":"x"}\n'
        '{"id":"chapter-1","status":"success","text":"a"}\n',
        encoding="utf-8",
    )
    out = tmp_path / "out.json"
    compile_json(p, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert list(data.keys()) == ["chapter-1", "chapter-2", "weird-key"]
