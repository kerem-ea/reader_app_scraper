from flask import Flask, jsonify, request, render_template, abort
import os
import sys
import json
import glob
import webview
import time
import threading
import socket


def find_data_root():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        meipass = getattr(sys, '_MEIPASS', '')
    else:
        exe_dir = os.path.abspath(os.path.dirname(__file__))
        meipass = ''

    cwd = os.getcwd()
    script_dir = os.path.abspath(os.path.dirname(__file__))

    candidates = [
        os.path.join(exe_dir, 'scraper', 'data'),
        os.path.join(exe_dir, '..', 'scraper', 'data'),
        os.path.join(exe_dir, 'data'),
        os.path.join(script_dir, '..', 'scraper', 'data'),
        os.path.join(script_dir, 'scraper', 'data'),
        os.path.join(cwd, 'scraper', 'data'),
        os.path.join(cwd, 'data'),
    ]
    if meipass:
        candidates.insert(0, os.path.join(meipass, 'scraper', 'data'))

    candidates.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scraper', 'data')))

    for cand in candidates:
        cand_abs = os.path.abspath(cand)
        if os.path.isdir(cand_abs):
            subdirs = [d for d in os.listdir(cand_abs) if os.path.isdir(os.path.join(cand_abs, d))]
            if subdirs:
                return cand_abs

    return os.path.abspath(candidates[0])


DATA_ROOT = find_data_root()

HERE = os.path.abspath(os.path.dirname(__file__))
if getattr(sys, 'frozen', False):
    HERE = os.path.dirname(sys.executable)

PROGRESS_FILE = os.path.join(HERE, 'last_read.txt')


def ensure_progress_dir():
    try:
        os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    except Exception:
        pass


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
    current_data_root = find_data_root()
    sites = []
    if not os.path.isdir(current_data_root):
        return jsonify([])
    for name in sorted(os.listdir(current_data_root)):
        path = os.path.join(current_data_root, name)
        if not os.path.isdir(path):
            continue
        chapters_file = find_site_chapters_file(path)
        if chapters_file:
            sites.append({'id': name, 'name': name.replace('-', ' ').title(), 'path': name})
    return jsonify(sites)


@app.route('/api/chapters')
def api_chapters():
    site = request.args.get('site')
    if not site:
        abort(400)
    current_data_root = find_data_root()
    site_dir = os.path.join(current_data_root, site)
    if not os.path.isdir(site_dir):
        abort(404)
    chapters_file = find_site_chapters_file(site_dir)
    if not chapters_file:
        abort(404)
    with open(chapters_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chapters = []
    if isinstance(data, dict):
        for k, c in data.items():
            if isinstance(c, dict):
                num = c.get('chapter_number')
                if num is None:
                    try:
                        num = int(k.replace('chapter-', ''))
                    except Exception:
                        num = 0
                chapters.append({
                    'number': num,
                    'title': c.get('title') or f'Chapter {num}',
                    'id': c.get('id') or k
                })
    elif isinstance(data, list):
        for c in data:
            if isinstance(c, dict):
                chapters.append({
                    'number': c.get('chapter_number', 0),
                    'title': c.get('title', ''),
                    'id': c.get('id', '')
                })

    chapters.sort(key=lambda c: c.get('number') or 0)
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

    current_data_root = find_data_root()
    site_dir = os.path.join(current_data_root, site)
    chapters_file = find_site_chapters_file(site_dir)
    if not chapters_file:
        abort(404)

    with open(chapters_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, dict):
        items = data.values()
    elif isinstance(data, list):
        items = data
    else:
        items = []

    for ch in items:
        if isinstance(ch, dict) and ch.get('chapter_number') == num:
            return jsonify({
                'number': ch.get('chapter_number'),
                'title': ch.get('title') or f'Chapter {num}',
                'text': ch.get('text', '')
            })

    abort(404)


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
    except Exception as e:
        print('Error saving progress:', e)

    return jsonify({'ok': True})


def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def get_current_screen(win):
    if not win or not getattr(webview, 'screens', None):
        return None
    try:
        cx = win.x + win.width // 2
        cy = win.y + win.height // 2
        for s in webview.screens:
            if (s.x <= cx < s.x + s.width) and (s.y <= cy < s.y + s.height):
                return s
        return webview.screens[0]
    except Exception:
        return None


class Api:
    def __init__(self):
        self._window = None
        self._is_maximized = True
        self._restored_bounds = None

    def set_window(self, window):
        self._window = window

    def close(self):
        if self._window:
            try:
                self._window.destroy()
            except Exception:
                pass
        os._exit(0)

    def minimize(self):
        if self._window:
            try:
                self._window.minimize()
            except Exception as e:
                print("Minimize error:", e)

    def maximize(self):
        if not self._window:
            return

        try:
            scr = get_current_screen(self._window)
            if not scr and getattr(webview, 'screens', None):
                scr = webview.screens[0]

            if self._is_maximized:
                # Restore window to floating mode centered on current screen
                if self._restored_bounds:
                    rx, ry, rw, rh = self._restored_bounds
                    self._window.move(rx, ry)
                    self._window.resize(rw, rh)
                else:
                    if scr:
                        rw, rh = int(scr.width * 0.8), int(scr.height * 0.8)
                        rx = scr.x + (scr.width - rw) // 2
                        ry = scr.y + (scr.height - rh) // 2
                        self._window.move(rx, ry)
                        self._window.resize(rw, rh)
                self._is_maximized = False
            else:
                # Save current floating bounds before maximizing
                if self._window.width > 200 and self._window.height > 200:
                    self._restored_bounds = (self._window.x, self._window.y, self._window.width, self._window.height)
                
                # Fit 100% cleanly to current monitor's working area
                if scr:
                    self._window.move(scr.x, scr.y)
                    self._window.resize(scr.width, scr.height - 40)
                self._is_maximized = True
        except Exception as e:
            print("Maximize error:", e)


if __name__ == '__main__':
    print('Resolved Data Root:', DATA_ROOT)
    port = 5000
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 5000))
        s.close()
    except OSError:
        port = get_free_port()

    def start_flask():
        app.run(debug=False, use_reloader=False, host='127.0.0.1', port=port)

    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    time.sleep(1)

    api_instance = Api()
    win = webview.create_window(
        'Weaver Reader',
        f'http://127.0.0.1:{port}',
        width=1280,
        height=850,
        min_size=(480, 360),
        resizable=True,
        maximized=False,
        frameless=True,
        easy_drag=False,
        js_api=api_instance
    )
    api_instance.set_window(win)

    def init_maximized():
        time.sleep(0.5)
        api_instance.maximize()

    threading.Thread(target=init_maximized, daemon=True).start()
    webview.start()

