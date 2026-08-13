import os
from pathlib import Path
from flask import Flask, jsonify, request, render_template, abort
from paths import PROGRESS_FILE, ensure_progress_dir
from epub_parser import find_all_epub_files, parse_epub_info, extract_chapter_text

app = Flask(__name__, static_folder='static', template_folder='templates')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/sites')
def api_sites():
    epubs = find_all_epub_files()
    sites = []
    for key, path in sorted(epubs.items()):
        title, _ = parse_epub_info(path)
        sites.append({'id': key, 'name': title or Path(path).stem, 'path': key})
    return jsonify(sites)


@app.route('/api/chapters')
def api_chapters():
    site = request.args.get('site')
    if not site:
        abort(400)
    epubs = find_all_epub_files()
    if site not in epubs:
        abort(404)
    _, chapters = parse_epub_info(epubs[site])
    return jsonify(chapters)


@app.route('/api/chapter')
def api_chapter():
    site = request.args.get('site')
    num = request.args.get('num')
    if not site or num is None:
        abort(400)
    try:
        num = int(num)
    except Exception:
        abort(400)

    epubs = find_all_epub_files()
    if site not in epubs:
        abort(404)

    _, chapters = parse_epub_info(epubs[site])
    ch = next((c for c in chapters if c['number'] == num), None)
    if not ch:
        abort(404)

    text = extract_chapter_text(epubs[site], ch['href'])
    return jsonify({
        'number': ch['number'],
        'title': ch['title'],
        'text': text
    })


@app.route('/api/progress', methods=['GET'])
def api_progress_get():
    if not os.path.isfile(PROGRESS_FILE):
        return jsonify({'site': None, 'chapter': None})

    try:
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()

        site = lines[0].strip() if len(lines) > 0 and lines[0].strip() else None
        chapter = None
        if len(lines) > 1 and lines[1].strip():
            try:
                chapter = int(lines[1].strip())
            except ValueError:
                chapter = None
        return jsonify({'site': site, 'chapter': chapter})
    except Exception:
        return jsonify({'site': None, 'chapter': None})


@app.route('/api/progress', methods=['POST'])
def api_progress_post():
    data = request.get_json(silent=True) or {}
    site = data.get('site')
    chapter = data.get('chapter')

    if not site or chapter is None:
        abort(400)

    ensure_progress_dir()
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            f.write(f'{site}\n{chapter}\n')
    except Exception:
        pass

    return jsonify({'ok': True})
