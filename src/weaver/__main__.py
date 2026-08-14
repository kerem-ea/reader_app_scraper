# Allow `python -m weaver` to act as the scraper CLI.
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .scraper import main as scraper_main

if __name__ == "__main__":
    scraper_main()