import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

try:
    import scrape
    print('import_ok')
    print('BASE_DIR', scrape.BASE_DIR)
except Exception as e:
    print('import_fail', type(e).__name__, e)