import os
import sys


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
