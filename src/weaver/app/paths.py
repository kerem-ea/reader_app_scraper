import os
import sys

from .._common import get_data_root, get_progress_file


# Resolve the runtime data root for EPUB discovery.
def find_data_root() -> str:
    return str(get_data_root())


DATA_ROOT = find_data_root()

HERE = os.path.abspath(os.path.dirname(__file__))
if getattr(sys, 'frozen', False):
    HERE = os.path.dirname(sys.executable)

PROGRESS_FILE = str(get_progress_file())


# Make sure the per-user progress directory exists.
def ensure_progress_dir():
    try:
        os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    except Exception:
        pass