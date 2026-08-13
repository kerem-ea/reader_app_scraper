from pathlib import Path
from flask import Flask, jsonify, request, render_template, abort
from epub_parser import find_all_epub_files, parse_epub_info, extract_chapter_text
from multi_progress import get_novel_last_read, save_novel_last_read, get_last_progress

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
    site = request.args.get('site')
    if site:
        chapter = get_novel_last_read(site)
        return jsonify({'site': site, 'chapter': chapter})
    return jsonify(get_last_progress())


@app.route('/api/progress', methods=['POST'])
def api_progress_post():
    data = request.get_json(silent=True) or {}
    site = data.get('site')
    chapter = data.get('chapter')

    if not site or chapter is None:
        abort(400)

    try:
        chapter = int(chapter)
    except (ValueError, TypeError):
        abort(400)

    save_novel_last_read(site, chapter)
    return jsonify({'ok': True})
