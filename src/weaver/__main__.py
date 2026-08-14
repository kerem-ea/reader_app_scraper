# Allow `python -m weaver` to act as the scraper CLI.
from .scraper import main as scraper_main

if __name__ == "__main__":
    scraper_main()