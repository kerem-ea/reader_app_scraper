import sys


def _chapters(n):
    return [
        {
            "id": f"chapter-{i}",
            "chapter_number": i,
            "title": f"Chapter {i} - Title {i}",
            "text": " ".join(["word"] * 30),
            "status": "success",
        }
        for i in range(1, n + 1)
    ]


def test_build_then_discover_and_parse(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(sys, "platform", "win32")

    from weaver.epub.builder import create_full_book

    data_dir = tmp_path / "weaver-reader" / "data"
    novel_dir = data_dir / "test-novel"
    novel_dir.mkdir(parents=True)

    out = create_full_book(
        "Test Novel",
        _chapters(5),
        None,
        novel_dir,
        metadata={"author": "Tester", "volumes": []},
    )
    assert out.exists()
    assert out.suffix == ".epub"

    from weaver.app import epub_parser

    # Point discovery exclusively at our temp data dir (avoid scanning site-packages/cwd).
    monkeypatch.setattr(epub_parser, "HERE", str(data_dir))
    monkeypatch.setattr(epub_parser, "find_data_root", lambda: str(data_dir))
    monkeypatch.setattr(epub_parser.os, "getcwd", lambda: str(data_dir))

    epubs = epub_parser.find_all_epub_files()
    assert "test-novel" in epubs

    title, parsed = epub_parser.parse_epub_info(epubs["test-novel"])
    assert title == "Test Novel"
    assert len(parsed) == 5
    assert parsed[0]["title"].startswith("Chapter 1")

    text = epub_parser.extract_chapter_text(epubs["test-novel"], parsed[0]["href"])
    assert text.strip()
