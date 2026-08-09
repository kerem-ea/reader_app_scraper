from flask import Flask, jsonify, request, send_from_directory, render_template, abort
import os
import json
import glob

HERE = os.path.abspath(os.path.dirname(__file__))
DATA_ROOT = os.path.abspath(os.path.join(HERE, '..', 'scraper', 'data'))

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


if __name__ == '__main__':
    print('Data root:', DATA_ROOT)
    app.run(debug=True)
