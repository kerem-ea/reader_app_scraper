import io
from pathlib import Path
from PIL import Image
from ebooklib import epub

from .._common import repo_data_root
from .constants import COVER_FILE, CSS, BASE_DIR


# Convert any image file to PNG (fall back to the original on failure).
def _convert_to_png(src_path: Path, dest_path: Path) -> Path | None:
    try:
        with open(src_path, "rb") as f:
            data = f.read()

        with Image.open(io.BytesIO(data)) as image:
            rgb_image = image.convert("RGB")
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            rgb_image.save(dest_path, "PNG")
        return dest_path
    except Exception:
        if src_path.exists():
            return src_path
        return None


# Locate/convert a usable cover PNG for the given novel output dir.
def prepare_cover(output_dir: Path) -> Path | None:
    dest_path = output_dir / "cover.png"

    candidates = [
        output_dir / "cover.png",
        output_dir / "cover.jpg",
        output_dir / "cover.jpeg",
        output_dir / "cover.webp",
    ]

    # Also search for any image in the output_dir
    try:
        for f in output_dir.iterdir():
            if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp") and f not in candidates:
                candidates.append(f)
    except Exception:
        pass

    # Repository assets cover fallback (source checkout)
    repo = repo_data_root()
    if repo is not None:
        assets_cover = repo.parent / "assets" / "cover.png"
        if assets_cover.exists():
            candidates.append(assets_cover)

    # App icon fallback
    if COVER_FILE.exists():
        candidates.append(COVER_FILE)

    for candidate in candidates:
        if candidate.exists() and candidate.stat().st_size > 0:
            converted = _convert_to_png(candidate, dest_path)
            if converted and converted.exists():
                return converted

    return None


# Embed the cover image into the EpubBook.
def add_cover(book, cover_path: Path | None) -> None:
    if cover_path and Path(cover_path).exists():
        try:
            with open(cover_path, "rb") as file:
                book.set_cover("cover.png", file.read())
        except Exception as e:
            print(f"Warning: Could not embed cover into EPUB: {e}")


# Build the shared CSS EpubItem used by all chapters.
def create_style():
    return epub.EpubItem(
        uid="style",
        file_name="style.css",
        media_type="text/css",
        content=CSS.encode("utf-8")
    )