from flask import Flask, jsonify, request, send_from_directory, render_template, abort
import os
import sys
import json
import glob
import webview
import time
import threading

HERE = os.path.abspath(os.path.dirname(__file__))
if getattr(sys, 'frozen', False):
    HERE = os.path.dirname(sys.executable)

DATA_ROOT = os.path.abspath(os.path.join(HERE, 'scraper', 'data'))
PROGRESS_FILE = os.path.join(HERE, 'reading_app', 'last_read.txt')

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
    for ch in data.values():
        if ch.get('chapter_number') == num:
            return jsonify({'number': ch.get('chapter_number'), 'title': ch.get('title'), 'text': ch.get('text')})
    abort(404)


@app.route('/api/progress', methods=['GET'])
def api_progress_get():
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
    
    def start_flask():
        app.run(debug=False, use_reloader=False, port=5000)
    
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    time.sleep(2)
    
    class Api:
        def close(self):
            try:
                if webview.windows:
                    webview.windows[0].destroy()
            except Exception:
                pass
            os._exit(0)
    
    webview.create_window('Reader App', 'http://127.0.0.1:5000', width=1200, height=800, resizable=True, frameless=True, easy_drag=True, js_api=Api())
    webview.start()