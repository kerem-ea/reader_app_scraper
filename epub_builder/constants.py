from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / "data"
COVER_FILE = Path(__file__).resolve().parent.parent / "reading_app" / "weaver.ico"

VOLUMES = [
    (1, "Child of Shadows", 1, 95),
    (2, "Demon of Change", 96, 350),
    (3, "Prince of Nothing", 351, 600),
    (4, "Chain Breaker", 601, 750),
    (5, "Dread Night", 751, 1060),
    (6, "All the Devils Are Here", 1061, 1230),
    (7, "The Tomb of Ariel", 1231, 1590),
    (8, "Lord of Shadows", 1591, 1840),
    (9, "Throne of War", 1841, 2260),
    (10, "Dark Lord's Dreadful Travelogue", 2261, 2720),
    (11, "The Song of Ariadne", 2721, 3000),
    (12, "Untitled", 3001, 999999),
]

CSS = """
body {
    font-family: serif;
    line-height: 1.6;
    margin: 5%;
}

h1 {
    text-align: center;
    margin-top: 2em;
    margin-bottom: 2em;
}

h2 {
    text-align: center;
    margin-top: 2em;
    margin-bottom: 1.5em;
}

p {
    margin-top: 0;
    margin-right: 0;
    margin-bottom: 1em;
    margin-left: 0;
    text-indent: 0;
}

.toc-chapter {
    text-indent: 0;
    margin-left: 1.5em;
    margin-bottom: 0.4em;
}
"""
