from flask import Flask, jsonify, request, send_from_directory, render_template, abort
import os
import json
import glob

HERE = os.path.abspath(os.path.dirname(__file__))
DATA_ROOT = os.path.abspath(os.path.join(HERE, '..', 'scraper', 'data'))
PROGRESS_FILE = os.path.join(HERE, 'last_read.txt')

app = Flask(__name__, static_folder='static', template_folder='templates')


def find_site_chapters_file(site_dir):
    pattern = os.path.join(site_dir, '*_chapters_raw.json')
    matches = glob.glob(pattern)
    return matches[0] if matches else None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/sites')
def api_sites():
    sites = []
    if not os.path.isdir(DATA_ROOT):
        return jsonify([])
    for name in sorted(os.listdir(DATA_ROOT)):
        path = os.path.join(DATA_ROOT, name)
        if not os.path.isdir(path):
            continue
        chapters_file = find_site_chapters_file(path)
        if chapters_file:
            sites.append({'id': name, 'path': name})
    return jsonify(sites)


@app.route('/api/chapters')
def api_chapters():
    site = request.args.get('site')
    if not site:
        abort(400)
    site_dir = os.path.join(DATA_ROOT, site)
    if not os.path.isdir(site_dir):
        abort(404)
    chapters_file = find_site_chapters_file(site_dir)
    if not chapters_file:
        abort(404)
    with open(chapters_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # data is a dict mapping keys to chapter objects
    chapters = list(data.values())
    chapters.sort(key=lambda c: c.get('chapter_number') or 0)
    out = [{'number': c.get('chapter_number'), 'title': c.get('title'), 'id': c.get('id')} for c in chapters]
    return jsonify(out)


@app.route('/api/chapter')
def api_chapter():
    site = request.args.get('site')
    num = request.args.get('num')
    if not site or not num:
        abort(400)
    try:
        num = int(num)
    except Exception:
        abort(400)
    site_dir = os.path.join(DATA_ROOT, site)
    chapters_file = find_site_chapters_file(site_dir)
    if not chapters_file:
        abort(404)
    with open(chapters_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # find chapter by chapter_number
    for ch in data.values():
        if ch.get('chapter_number') == num:
            return jsonify({'number': ch.get('chapter_number'), 'title': ch.get('title'), 'text': ch.get('text')})
    abort(404)


@app.route('/api/progress', methods=['GET'])
def api_progress_get():
    """Return the last-read {site, chapter}. Both are null if nothing's been saved yet."""
    if not os.path.isfile(PROGRESS_FILE):
        return jsonify({'site': None, 'chapter': None})

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


@app.route('/api/progress', methods=['POST'])
def api_progress_post():
    """Save the current {site, chapter} as two lines in last_read.txt."""
    data = request.get_json(silent=True) or {}
    site = data.get('site')
    chapter = data.get('chapter')

    if not site or chapter is None:
        abort(400)

    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        f.write(f'{site}\n{chapter}\n')

    return jsonify({'ok': True})


if __name__ == '__main__':
    print('Data root:', DATA_ROOT)
    app.run(debug=True)