from PIL import Image
from ebooklib import epub
from epub_builder.constants import COVER_FILE, CSS


def prepare_cover(output_dir):
    cover_path = output_dir / "cover.png"
    if COVER_FILE.exists():
        try:
            image = Image.open(COVER_FILE)
            image = image.convert("RGB")
            image.save(cover_path, "PNG")
            return cover_path
        except Exception:
            pass
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
