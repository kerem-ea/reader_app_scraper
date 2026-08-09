import asyncio
import json
import re
from dataclasses import dataclass
from pathlib import Path
import sys
import time


def print_progress_line(chapter_id: str, chapter_title: str | None, n: int, total: int, t0: float) -> None:
    elapsed = time.time() - t0
    rate = n / elapsed if elapsed else 0
    eta = (total - n) / rate if rate else 0
    line = (
        f"[{n}/{total}] "
        f"{rate:.1f} ch/s | "
        f"ETA {eta:.0f}s | "
        f"{chapter_id} | "
        f"{chapter_title or 'No title'}"
    )

    if sys.stdout.isatty():
        print(f"\r\033[2K{line}", end="", flush=True)
        if n == total:
            print()
    else:
        if n % 50 == 0 or n == total:
            print(line)


@dataclass
class ProgressWriter:
    path: Path

    def __post_init__(self):
        self.buffer: list[str] = []
        self.lock = asyncio.Lock()
        self.file = open(self.path, "a", encoding="utf-8")

    async def add(self, data: dict) -> None:
        async with self.lock:
            self.buffer.append(json.dumps(data, ensure_ascii=False) + "\n")
            if len(self.buffer) >= 10:
                self.file.writelines(self.buffer)
                self.file.flush()
                self.buffer.clear()

    def flush(self) -> None:
        if self.buffer:
            self.file.writelines(self.buffer)
            self.buffer.clear()
        self.file.flush()

    def close(self) -> None:
        self.flush()
        self.file.close()


def iter_jsonl(path: Path):
    if not path.exists():
        return

    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    def sort_key(item: dict) -> tuple[float, str]:
        item_id = item.get("id") if isinstance(item, dict) else None
        if isinstance(item_id, str):
            match = re.match(r"chapter-(\d+)$", item_id)
            if match:
                return (int(match.group(1)), item_id)
        return (float("inf"), "")

    for item in sorted(items, key=sort_key):
        yield item


def load_done(path: Path) -> set[str]:
    return {
        item["id"]
        for item in iter_jsonl(path)
        if item.get("status") == "success"
    }


def compile_json(temp_jsonl: Path, out_json: Path) -> None:
    results = {
        item["id"]: item
        for item in iter_jsonl(temp_jsonl)
        if item.get("status") == "success"
    }

    if not results:
        return

    keys = sorted(results, key=lambda k: int(k.split("-")[1]))
    output = {key: results[key] for key in keys}

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[json] {len(output)} chapters -> {out_json.name}")
