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

4. The app will open in a dedicated fullscreen window as a desktop application.

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

- Native desktop window with fullscreen mode
- Persistent toolbar that stays visible while scrolling
- Lightweight Flask backend and single-page frontend
- Table of contents navigation
- Font size, line height, and reading width controls
- Soft font toggle
- Dark theme support
- Keyboard navigation
- Close button to exit the application

### Notes

- The app discovers sites under `scraper/data` that contain a `*_chapters_raw.json` file
- Reading progress is saved manually using the "Mark as last read" button
- Uses pywebview for native desktop window experience

## Building a Standalone Executable

To create a standalone Windows executable that doesn't require Python installation:

1. Install dependencies (including PyInstaller):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Navigate to the reading_app directory:

```powershell
cd reading_app
```

3. Build the executable using the provided spec file:

```powershell
pyinstaller reader_app.spec
```

4. The executable will be created in `reading_app/dist/ReaderApp.exe`


5. **Important**: Copy the generated executable to the project root and rename it to `reader.exe`:

   ```powershell
   cd ..
   Copy-Item .\reading_app\dist\reader.exe .\reader.exe
   ```
   
6. Run the executable from the project root:
   ```powershell
   .\reader.exe
   ```

### Build Details

- **File size**: ~25-35MB (includes Python runtime + Flask + pywebview dependencies)
- **Output**: Single executable file
- **Window**: Opens in a native fullscreen desktop window
- **Console**: Shows Flask server output (set `console=False` in spec file to hide)
- **Data**: Expects `scraper/data/` folder structure in the same directory as the executable

### Customization

To customize the build, edit `reading_app/reader_app.spec`:
- Change `name='ReaderApp'` to rename the executable
- Set `console=False` to hide the console window
- Add `icon='path/to/icon.ico'` to use a custom icon
- Modify `datas` list if you add additional static files

To customize the window behavior, edit `reading_app/app.py`:
- Change `fullscreen=True` to `fullscreen=False` for windowed mode
- Add `width=1200, height=800` for specific window dimensions
- Add `resizable=False` to prevent window resizing

## Project Structure

```
reader_app_scraper/
├── scraper/           # Novel scraping component
│   ├── data/         # Scraped chapter data (gitignored)
│   ├── scrape.py     # Main scraper entry point
│   └── ...
├── reading_app/      # Reader application component
│   ├── app.py        # Flask application
│   ├── reader_app.spec  # PyInstaller build configuration
│   ├── static/       # Frontend assets
│   └── templates/    # HTML templates
└── requirements.txt  # Combined dependencies
```
