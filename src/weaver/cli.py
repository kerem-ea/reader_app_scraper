"""Top-level `weaver` command: dispatch to the scraper, EPUB builder, or reader app."""

import sys

from ._common import get_version

PROG = "weaver"

USAGE = f"""Usage:
  {PROG} --version                          Print the version and exit
  {PROG} --help                             Show this help
  {PROG} <subcommand> [args...]             Run a subcommand

Subcommands (also available as standalone commands):
  scraper | {PROG}-scraper   Scrape novel chapters from supported sites
  epub    | {PROG}-epub      Convert scraped data to EPUB
  app     | {PROG}-app       Launch the desktop reader

Example:
  {PROG} scraper shadow-slave 1 10 1
  {PROG} epub shadow-slave
  {PROG} app

Run `{PROG} <subcommand> --help` for subcommand usage.
"""

_SUBCOMMANDS = {
    "scraper": "weaver.scraper",
    "scrape": "weaver.scraper",
    "s": "weaver.scraper",
    "epub": "weaver.epub",
    "e": "weaver.epub",
    "app": "weaver.app",
    "a": "weaver.app",
}


def _run(module_name: str, prog_name: str) -> None:
    module = __import__(module_name, fromlist=["main"])
    sys.argv = [prog_name, *sys.argv[2:]]
    module.main()


def main() -> None:
    args = sys.argv[1:]

    if not args:
        from .scraper import main as scraper_main

        scraper_main()
        return

    first = args[0]
    if first in ("-h", "--help"):
        print(USAGE)
        return
    if first in ("-V", "--version"):
        print(f"{PROG}-reader {get_version()}")
        return

    if first.lower() in _SUBCOMMANDS:
        module_name = _SUBCOMMANDS[first.lower()]
        prog = f"{PROG}-{module_name.rsplit('.', 1)[1]}"
        _run(module_name, prog)
        return

    from .scraper import main as scraper_main

    scraper_main()


if __name__ == "__main__":
    main()
