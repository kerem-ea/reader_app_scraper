# reading_app

Lightweight reader for local scraped chapters. Reads chapter JSONs saved by the `scraper` project in `../scraper/data`.

Quick start:

1. Create a virtualenv and install deps:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the app:

```powershell
python app.py
```

3. Open http://127.0.0.1:5000 in your browser.

Notes:
- The app discovers sites under `../scraper/data` that contain a `*_chapters_raw.json` file.
- Minimal, lightweight Flask backend and a single-page frontend with controls: TOC, font size, line height, reading width, soft font toggle, dark theme, keyboard navigation.