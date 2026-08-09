# Novel Scraper

A FreeWebNovel chapter scraper for novels like `shadow-slave`.

## Structure

- `scrape.py`: main entry point for the scraper.
- `debug_chapter.py`: helper for debugging a single chapter fetch in HTTP or browser mode.
- `catalog.py`: fetches chapter title metadata from the novel catalog.
- `fetch.py`: HTTP fetch logic, retries, and failure tracking.
- `browser.py`: browser-mode chapter fetching and page pooling.
- `session.py`: session bootstrap, cookie caching, and camoufox helpers.
- `parsing.py`: HTML extraction and challenge detection utilities.
- `paths.py`: path and URL configuration for the current novel.
- `constants.py`: shared constants and mode settings.
- `progress.py`: progress writing and output compilation.

## Usage

From the project root:

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

## Notes

- The scraper uses `camoufox` for browser-based interactions and `curl_cffi` for HTTP requests.
- Chapter progress is stored in `data/<novel-name>/<novel-name>_progress.jsonl`.
- Final output is written to `data/<novel-name>/<novel-name>_chapters_raw.json`.
