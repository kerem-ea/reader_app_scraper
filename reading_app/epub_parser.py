import os
import re
import zipfile
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path
from selectolax.parser import HTMLParser
from paths import find_data_root, HERE



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


_EPUB_INFO_CACHE = {}


def parse_epub_info(file_path):
    abs_path = os.path.abspath(file_path)
    try:
        current_mtime = os.path.getmtime(abs_path)
        if abs_path in _EPUB_INFO_CACHE:
            cached_mtime, cached_title, cached_chapters = _EPUB_INFO_CACHE[abs_path]
            if cached_mtime == current_mtime:
                return cached_title, cached_chapters
    except Exception:
        current_mtime = 0.0

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

            _EPUB_INFO_CACHE[abs_path] = (current_mtime, title, chapters)
            return title, chapters
    except Exception:
        fallback_title = Path(file_path).stem
        return fallback_title, []


def extract_chapter_text(file_path, href):
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            content = zf.read(href).decode('utf-8', errors='ignore')
            tree = HTMLParser(content)

            for header in tree.css('h1, h2, h3, h4, h5, h6'):
                header.decompose()

            p_nodes = tree.css('p')
            if p_nodes:
                text_list = []
                for p in p_nodes:
                    p_text = unescape(p.text(strip=True))
                    if p_text:
                        text_list.append(p_text)
                if text_list:
                    return '\n\n'.join(text_list)

            body = tree.body or tree.html
            if body:
                raw_text = unescape(body.text())
                lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
                return '\n\n'.join(lines)

            return ''
    except Exception:
        return ''

