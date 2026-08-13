from PIL import Image
from ebooklib import epub
from epub_builder.constants import COVER_FILE, CSS


def _convert_to_png(src_path, dest_path):
    try:
        image = Image.open(src_path)
        image.convert("RGB").save(dest_path, "PNG")
        return dest_path
    except Exception:
        return None


def prepare_cover(output_dir):
    dest_path = output_dir / "cover.png"

    for candidate in (
        output_dir / "cover.png",
        output_dir / "cover.jpg",
        output_dir / "cover.jpeg",
        output_dir / "cover.webp",
    ):
        if candidate.exists():
            converted = _convert_to_png(candidate, dest_path)
            if converted:
                return converted

    if COVER_FILE.exists():
        return _convert_to_png(COVER_FILE, dest_path)

    return None


def add_cover(book, cover_path):
    if cover_path and cover_path.exists():
        try:
            with open(cover_path, "rb") as file:
                book.set_cover("cover.png", file.read())
        except Exception:
            pass


def create_style():
    return epub.EpubItem(
        uid="style",
        file_name="style.css",
        media_type="text/css",
        content=CSS.encode("utf-8")
    )
