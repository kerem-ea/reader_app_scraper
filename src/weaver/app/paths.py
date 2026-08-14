import logging
import os
import sys

from .._common import get_data_root, get_progress_file

logger = logging.getLogger(__name__)


# Resolve the runtime data root for EPUB discovery.
def find_data_root() -> str:
    return str(get_data_root())


HERE = os.path.abspath(os.path.dirname(__file__))
if getattr(sys, 'frozen', False):
    HERE = os.path.dirname(sys.executable)


# Resolve the per-user progress file path lazily (no import-time side effects).
def get_progress_file_path() -> str:
    return str(get_progress_file())


# Make sure the per-user progress directory exists.
def ensure_progress_dir():
    try:
        os.makedirs(os.path.dirname(get_progress_file_path()), exist_ok=True)
    except Exception as e:
        logger.warning("Could not create progress dir: %s", e)
