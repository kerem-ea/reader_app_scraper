# Reader App Scraper

A complete system for scraping novel chapters from FreeWebNovel and reading them locally. This project consists of two main components:

- **scraper**: A web scraper for downloading novel chapters from FreeWebNovel
- **reading_app**: A lightweight Flask-based reader for viewing scraped chapters

## Quick Start

1. Create a virtualenv and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Scrape novel chapters:

```powershell
cd scraper
python scrape.py
```

Follow the prompts for novel slug, start/end chapter, and mode.

3. Run the reader app:

```powershell
cd reading_app
python app.py
```

4. Open http://127.0.0.1:5000 in your browser.

## Scraper Component

### Structure

- `scrape.py`: main entry point for the scraper
- `debug_chapter.py`: helper for debugging a single chapter fetch in HTTP or browser mode
- `catalog.py`: fetches chapter title metadata from the novel catalog
- `fetch.py`: HTTP fetch logic, retries, and failure tracking
- `browser.py`: browser-mode chapter fetching and page pooling
- `session.py`: session bootstrap, cookie caching, and camoufox helpers
- `parsing.py`: HTML extraction and challenge detection utilities
- `paths.py`: path and URL configuration for the current novel
- `constants.py`: shared constants and mode settings
- `progress.py`: progress writing and output compilation

### Usage

From the scraper directory:

```powershell
python scrape.py
```

Then follow prompts for novel slug, start/end chapter, and mode.

### Debug a problem chapter

```powershell
python debug_chapter.py shadow-slave 2420 --mode browser --save-html --save-screenshot
```

or

```powershell
python debug_chapter.py shadow-slave 2420 --mode http --save-html
```

### Notes

- The scraper uses `camoufox` for browser-based interactions and `curl_cffi` for HTTP requests
- Chapter progress is stored in `data/<novel-name>/<novel-name>_progress.jsonl`
- Final output is written to `data/<novel-name>/<novel-name>_chapters_raw.json`

## Reading App Component

### Features

- Lightweight Flask backend and single-page frontend
- Table of contents navigation
- Font size, line height, and reading width controls
- Soft font toggle
- Dark theme support
- Keyboard navigation

### Notes

- The app discovers sites under `scraper/data` that contain a `*_chapters_raw.json` file
- Reading progress is saved automatically

## Project Structure

```
reader_app_scraper/
├── scraper/           # Novel scraping component
│   ├── data/         # Scraped chapter data (gitignored)
│   ├── scrape.py     # Main scraper entry point
│   └── ...
├── reading_app/      # Reader application component
│   ├── app.py        # Flask application
│   ├── static/       # Frontend assets
│   └── templates/    # HTML templates
└── requirements.txt  # Combined dependencies
```
