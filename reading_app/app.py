from flask import Flask, jsonify, request, render_template, abort
import os
import sys
import glob
import webview
import time
import threading
import socket
import zipfile
import xml.etree.ElementTree as ET
import re
from html import unescape
from pathlib import Path


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
        os.path.join(cwd, 'data'),
        os.path.join(script_dir, '..', 'data'),
        os.path.join(exe_dir, 'data'),
        os.path.join(exe_dir, '..', 'data'),
        os.path.join(exe_dir, 'scraper', 'data'),
        os.path.join(cwd, 'scraper', 'data'),
        cwd
    ]
    if meipass:
        candidates.insert(0, os.path.join(meipass, 'data'))

    for cand in candidates:
        cand_abs = os.path.abspath(cand)
        if os.path.isdir(cand_abs):
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


def find_all_epub_files():
    current_root = find_data_root()
    search_dirs = [
        current_root,
        os.path.abspath(os.path.join(HERE, '..')),
        os.getcwd()
    ]

    found = {}
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for file in files:
                if file.lower().endswith('.epub'):
                    if re.search(r'\b(volume|vol)\b', file.lower()):
                        continue
                    full_path = os.path.abspath(os.path.join(root, file))
                    rel_key = os.path.relpath(full_path, current_root).replace('\\', '/')
                    if rel_key not in found:
                        found[rel_key] = full_path

    return found


def parse_epub_info(file_path):
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            container_data = zf.read('META-INF/container.xml')
            container_root = ET.fromstring(container_data)
            rootfile = container_root.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
            opf_path = rootfile.attrib['full-path']
            opf_dir = str(Path(opf_path).parent)
            if opf_dir == '.':
                opf_dir = ''

            opf_data = zf.read(opf_path)
            opf_root = ET.fromstring(opf_data)

            ns = {
                'opf': 'http://www.idpf.org/2007/opf',
                'dc': 'http://purl.org/dc/elements/1.1/'
            }

            title_elem = opf_root.find('.//dc:title', ns)
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else Path(file_path).stem

            manifest = {}
            for item in opf_root.findall('.//opf:manifest/opf:item', ns):
                item_id = item.attrib.get('id')
                href = item.attrib.get('href')
                media_type = item.attrib.get('media-type', '')
                properties = item.attrib.get('properties', '')
                if opf_dir:
                    href = f"{opf_dir}/{href}"
                manifest[item_id] = {'href': href, 'media-type': media_type, 'properties': properties, 'id': item_id}

            spine_items = []
            for itemref in opf_root.findall('.//opf:spine/opf:itemref', ns):
                idref = itemref.attrib.get('idref')
                if idref in manifest:
                    spine_items.append(manifest[idref])

            toc_map = {}

            ncx_item = next((item for item in manifest.values() if 'ncx' in item['media-type'] or item['href'].endswith('.ncx')), None)
            if ncx_item:
                try:
                    ncx_data = zf.read(ncx_item['href'])
                    ncx_root = ET.fromstring(ncx_data)
                    ncx_dir = str(Path(ncx_item['href']).parent)
                    if ncx_dir == '.':
                        ncx_dir = ''
                    for nav_point in ncx_root.findall('.//{http://www.daisy.org/z3986/2005/ncx/}navPoint'):
                        text_elem = nav_point.find('.//{http://www.daisy.org/z3986/2005/ncx/}text')
                        content_elem = nav_point.find('.//{http://www.daisy.org/z3986/2005/ncx/}content')
                        if text_elem is not None and content_elem is not None:
                            src = content_elem.attrib.get('src', '')
                            if '#' in src:
                                src = src.split('#')[0]
                            if ncx_dir:
                                src = f"{ncx_dir}/{src}"
                            toc_map[src] = text_elem.text.strip()
                except Exception:
                    pass

            nav_item = next((item for item in manifest.values() if 'nav' in item['properties'] or item['href'].endswith('nav.xhtml')), None)
            if nav_item and not toc_map:
                try:
                    nav_data = zf.read(nav_item['href']).decode('utf-8', errors='ignore')
                    nav_dir = str(Path(nav_item['href']).parent)
                    if nav_dir == '.':
                        nav_dir = ''
                    links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', nav_data, re.IGNORECASE | re.DOTALL)
                    for href_val, text_val in links:
                        clean_text = re.sub(r'<[^>]+>', '', text_val).strip()
                        if '#' in href_val:
                            href_val = href_val.split('#')[0]
                        if nav_dir:
                            href_val = f"{nav_dir}/{href_val}"
                        if href_val and clean_text:
                            toc_map[href_val] = unescape(clean_text)
                except Exception:
                    pass

            chapters = []
            chap_num = 1
            for item in spine_items:
                href = item['href']
                mtype = item['media-type']
                props = item['properties']

                if 'nav' in props or href.endswith(('nav.xhtml', 'nav.html', 'toc.xhtml', 'toc.html', 'cover.xhtml')):
                    continue

                if href.startswith('EPUB/volume-') or 'volume-' in href:
                    continue

                if not ('html' in mtype or href.endswith(('.xhtml', '.html', '.htm'))):
                    continue

                chap_title = toc_map.get(href)
                if not chap_title:
                    try:
                        content = zf.read(href).decode('utf-8', errors='ignore')
                        m_title = re.search(r'<(?:h1|h2|title)[^>]*>(.*?)</(?:h1|h2|title)>', content, re.IGNORECASE | re.DOTALL)
                        if m_title:
                            chap_title = re.sub(r'<[^>]+>', '', m_title.group(1)).strip()
                    except Exception:
                        pass

                if not chap_title:
                    chap_title = f"Chapter {chap_num}"

                m_num = re.search(r'Chapter\s+(\d+)', chap_title, re.IGNORECASE)
                num = int(m_num.group(1)) if m_num else chap_num

                chapters.append({
                    'number': chap_num,
                    'ch_num': num,
                    'title': chap_title,
                    'href': href
                })
                chap_num += 1

            return title, chapters
    except Exception:
        return Path(file_path).stem, []


def extract_chapter_text(file_path, href):
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            content = zf.read(href).decode('utf-8', errors='ignore')

            body_m = re.search(r'<body[^>]*>(.*?)</body>', content, re.IGNORECASE | re.DOTALL)
            if body_m:
                html_body = body_m.group(1)
            else:
                html_body = content

            html_body = re.sub(r'<h[1-6][^>]*>.*?</h[1-6]>', '', html_body, flags=re.IGNORECASE | re.DOTALL)

            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html_body, re.IGNORECASE | re.DOTALL)
            text_list = []
            if paragraphs:
                for p in paragraphs:
                    p_text = re.sub(r'<br\s*/?>', '\n', p, flags=re.IGNORECASE)
                    p_text = re.sub(r'<[^>]+>', '', p_text)
                    p_text = unescape(p_text).strip()
                    if p_text:
                        text_list.append(p_text)
                return '\n\n'.join(text_list)
            else:
                text = re.sub(r'<br\s*/?>', '\n', html_body, flags=re.IGNORECASE)
                text = re.sub(r'<[^>]+>', '', text)
                text = unescape(text)
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                return '\n\n'.join(lines)
    except Exception:
        return ''


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


def get_screen_work_area(win):
    scr = get_current_screen(win)
    if not scr and getattr(webview, 'screens', None):
        scr = webview.screens[0]

    if not scr:
        return 0, 0, 1280, 850

    if sys.platform == 'win32':
        try:
            import ctypes
            from ctypes import wintypes

            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ('cbSize', wintypes.DWORD),
                    ('rcMonitor', wintypes.RECT),
                    ('rcWork', wintypes.RECT),
                    ('dwFlags', wintypes.DWORD),
                ]

            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            cx = win.x + win.width // 2 if win else scr.x + scr.width // 2
            cy = win.y + win.height // 2 if win else scr.y + scr.height // 2
            pt = wintypes.POINT(cx, cy)
            hMon = ctypes.windll.user32.MonitorFromPoint(pt, 1)  # MONITOR_DEFAULTTONEAREST
            if ctypes.windll.user32.GetMonitorInfoW(hMon, ctypes.byref(mi)):
                wx = mi.rcWork.left
                wy = mi.rcWork.top
                ww = mi.rcWork.right - mi.rcWork.left
                wh = mi.rcWork.bottom - mi.rcWork.top
                return wx, wy, ww, wh
        except Exception:
            pass

    return scr.x, scr.y, scr.width, scr.height


class Api:
    def __init__(self):
        self._window = None
        self._is_maximized = False
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
            except Exception:
                pass

    def maximize(self):
        if not self._window:
            return

        try:
            scr = get_current_screen(self._window)
            if not scr and getattr(webview, 'screens', None):
                scr = webview.screens[0]

            if self._is_maximized:
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
                try:
                    self._window.evaluate_js('if (window.setWindowMaximizedState) window.setWindowMaximizedState(false);')
                except Exception:
                    pass
            else:
                if self._window.width > 200 and self._window.height > 200:
                    self._restored_bounds = (self._window.x, self._window.y, self._window.width, self._window.height)
                
                wx, wy, ww, wh = get_screen_work_area(self._window)
                self._window.move(wx, wy)
                self._window.resize(ww, wh)
                self._is_maximized = True
                try:
                    self._window.evaluate_js('if (window.setWindowMaximizedState) window.setWindowMaximizedState(true);')
                except Exception:
                    pass
        except Exception:
            pass


if __name__ == '__main__':
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