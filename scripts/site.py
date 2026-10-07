# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Build the static lyrics website with uv run scripts/site.py."""

import argparse
from hashlib import sha256
from html import escape
from pathlib import Path
import re
from string import ascii_lowercase
import unicodedata
from urllib.parse import quote

if __package__:
    from .index_common import KINDS, ROOT, WORD_PATTERN, build_index, contributors, dates, lyric_body, normalize_word, read_metadata
else:
    from index_common import KINDS, ROOT, WORD_PATTERN, build_index, contributors, dates, lyric_body, normalize_word, read_metadata

LABELS = {
    "titles": "Titles",
    "first_lines": "First lines",
    "words": "Words",
    "lyrics": "Poets and lyric sources",
    "composers": "Composers",
    "lyric_dates": "Lyric dates",
    "composition_dates": "Composition dates",
    "meters": "Meters",
}

CSS = """body { margin: 0; color: #252525; background: #faf9f6;
  font: 17px/1.6 Georgia, serif; }
header, main, footer { max-width: 64rem; margin: auto; padding: 1.5rem; }
header { border-bottom: 1px solid #d8d5cd; }
nav { display: flex; flex-wrap: wrap; gap: .4rem 1.2rem; margin-top: .75rem; }
a { color: #28566c; text-underline-offset: .15em; }
a:hover { color: #122e3d; }
a:focus-visible { outline: 2px solid #28566c; outline-offset: 3px; }
h1 { line-height: 1.2; margin: .5rem 0 1.5rem; }
h2 { margin-top: 2rem; }
.brand { font-weight: bold; }
.index-list { padding-left: 1.5rem; }
.index-list li { margin: .65rem 0; overflow-wrap: anywhere; }
.index-list li:target { background: #eee9dc; outline: 2px solid #d8d5cd; }
.index-word { font-variant-caps: small-caps; font-size: 1.15em; }
.page-links a { white-space: nowrap; }
dl { display: grid; grid-template-columns: minmax(9rem, 12rem) 1fr;
  gap: .4rem 1rem; font-size: .95rem; }
dt { font-weight: bold; }
dd { margin: 0; overflow-wrap: anywhere; }
.lyrics { white-space: pre-wrap; overflow-wrap: anywhere;
  font: inherit; max-width: 52rem; }
footer { border-top: 1px solid #d8d5cd; font-size: .9rem; }
@media (max-width: 40rem) {
  dl { display: block; }
  dd { margin-bottom: .75rem; }
  header, main, footer { padding: 1rem; }
}
"""


def document(title: str, body: str, prefix: str = "") -> str:
    nav = " ".join(
        f'<a href="{prefix}{kind}.html">{escape(label)}</a>'
        for kind, label in LABELS.items()
    )
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} — Cooper 2012 Lyrics</title>
<link rel="stylesheet" href="{prefix}style.css">
</head>
<body>
<header>
<a class="brand" href="{prefix}index.html">Cooper 2012 Lyrics</a>
<nav aria-label="Browse indexes">{nav}</nav>
</header>
<main>{body}</main>
<footer><a href="{prefix}index.html">Home</a> · Cooper 2012 lyrics collection</footer>
</body>
</html>
'''


def entry_id(key: str) -> str:
    """An entry keeps its ID when other entries are added or reordered."""
    return "entry-" + sha256(key.encode("utf-8")).hexdigest()


def index_link(kind: str, key: str, label: str) -> str:
    return f'<a href="../{kind}.html#{entry_id(key)}">{escape(label)}</a>'


def display_source(key: str) -> str:
    """Restore personal-name order without rearranging commas in book titles."""
    title, separator, article = key.rpartition(", ")
    if separator and article in ("The", "A", "An"):
        return f"{article} {title}"
    surname, separator, given = key.partition(", ")
    if separator and re.fullmatch(r"[^\W\d_]+(?:[’'-][^\W\d_]+)*", surname):
        given, suffix_separator, suffix = given.partition(", ")
        return f"{given} {surname}" + (f", {suffix}" if suffix_separator else "")
    return key


def word_letter(word: str) -> str:
    initial = unicodedata.normalize("NFKD", word)[0]
    return initial if initial in ascii_lowercase else "other"


def word_links(body: str, word_index: dict[str, list[str]]) -> str:
    """Preserve lyric text, capitalization, whitespace, and punctuation."""
    pieces = []
    cursor = 0
    for match in WORD_PATTERN.finditer(body):
        pieces.append(escape(body[cursor:match.start()]))
        word = normalize_word(match[0])
        if word in word_index:
            pieces.append(f'<a href="../words/{word_letter(word)}.html#{entry_id(word)}">{escape(match[0])}</a>')
        else:
            pieces.append(escape(match[0]))
        cursor = match.end()
    pieces.append(escape(body[cursor:]))
    return "".join(pieces)


def index_items(index: dict[str, list[str]], by_page: dict, prefix: str = "", *, words: bool = False) -> str:
    items = []
    for key, pages in index.items():
        links = []
        for page in pages:
            filename, title = by_page[page]
            links.append(f'<a href="{prefix}{quote(filename)}" title="{escape(title, quote=True)}">{escape(page)}</a>')
        label = f'<span class="index-word">{escape(key)}</span>' if words else escape(key)
        items.append(f'<li id="{entry_id(key)}">{label} — <span class="page-links">{", ".join(links)}</span></li>')
    return '<ul class="index-list">' + "\n".join(items) + "</ul>"


def build_word_pages(output: Path, index: dict[str, list[str]], by_page: dict) -> None:
    groups = {letter: {} for letter in ascii_lowercase}
    for word, pages in index.items():
        groups.setdefault(word_letter(word), {})[word] = pages
    (output / "words").mkdir(exist_ok=True)
    letters = list(groups)
    intro = (f'<h1>Words</h1><p>{len(index)} words from the lyrics, with common words omitted. '
             'Choose a letter to browse, or select a word within a song’s lyrics.</p>')
    links = "".join(f'<li><a href="words/{letter}.html">{letter.upper()}</a> '
                    f'({len(groups[letter])} words)</li>' for letter in letters)
    (output / "words.html").write_text(document("Words", intro + f"<ul>{links}</ul>"), encoding="utf-8")
    nav = '<nav aria-label="Word index letters">' + " ".join(
        f'<a href="{letter}.html">{letter.upper()}</a>' for letter in letters) + '</nav>'
    for letter, words in groups.items():
        title = f"Words — {letter.upper()}"
        body = f'<h1>{title}</h1>{nav}'
        body += index_items(words, by_page, "../", words=True) if words else '<p>No indexed words for this letter.</p>'
        (output / "words" / f"{letter}.html").write_text(document(title, body, "../"), encoding="utf-8")


def metadata_value(field: str, value: str, metadata: dict[str, str]) -> str:
    """Link index keys, displaying contributor names in normal reading order."""
    if field in ("Title", "Collation") and metadata.get("Collation"):
        return index_link("titles", metadata["Collation"], value)
    if field == "Meter":
        return index_link("meters", value, value)
    if field == "Lyrics":
        kind, keys = "lyrics", contributors(value)
    elif field.endswith(" Composer"):
        kind, keys = "composers", contributors(value)
    elif field == "Lyrics Date":
        kind, keys = "lyric_dates", dates(value)
    elif field.endswith(" Composition Date"):
        kind, keys = "composition_dates", dates(value)
    else:
        return escape(value)
    if not keys:
        return escape(value)
    # Longest first avoids matching a short key inside a longer source or range.
    pattern = "|".join(re.escape(key) for key in sorted(set(keys), key=len, reverse=True))
    pieces = []
    cursor = 0
    for match in re.finditer(pattern, value):
        pieces.append(escape(value[cursor:match.start()]))
        label = display_source(match[0]) if kind in ("lyrics", "composers") else match[0]
        pieces.append(index_link(kind, match[0], label))
        cursor = match.end()
    pieces.append(escape(value[cursor:]))
    return "".join(pieces)


def build_site(lyrics_dir: Path, output: Path) -> int:
    """Generate relative links and song pages without modifying the lyrics."""
    if not lyrics_dir.is_dir():
        raise FileNotFoundError(f"Lyrics directory does not exist: {lyrics_dir}")
    songs = []
    by_page = {}
    for path in sorted(lyrics_dir.glob("*.txt")):
        metadata = read_metadata(path)
        body = lyric_body(path)
        if not metadata.get("Title"):
            raise ValueError(f"{path}: missing Title metadata")
        page = metadata["Page"]
        if page in by_page:
            raise ValueError(f"{path}: duplicate Page {page!r}")
        filename = f"songs/{path.stem}.html"
        by_page[page] = (filename, metadata["Title"])
        songs.append((filename, metadata, body))
    indexes = {kind: build_index(lyrics_dir, kind) for kind in KINDS}
    # Parse and validate all input before writing the generated site.
    output.mkdir(parents=True, exist_ok=True)
    (output / "songs").mkdir(exist_ok=True)
    (output / "style.css").write_text(CSS, encoding="utf-8")
    intro_links = "\n".join(
        f'<li><a href="{kind}.html">{escape(LABELS[kind])}</a> '
        f'({len(indexes[kind])} entries)</li>' for kind in KINDS
    )
    intro = f'''<h1>Cooper 2012 Lyrics</h1>
<p>Browse the lyrics and source information for {len(songs)} songs in the
2012 Cooper edition of The Sacred Harp.</p>
<p>Choose an index below, then follow a page number to read a song’s metadata and lyrics.
Page suffixes <strong>t</strong> and <strong>b</strong> indicate top and bottom;
top entries appear before bottom entries.</p>
<ul>{intro_links}</ul>'''
    (output / "index.html").write_text(document("Home", intro), encoding="utf-8")
    for kind, index in indexes.items():
        if kind == "words":
            build_word_pages(output, index, by_page)
            continue
        body = f'<h1>{escape(LABELS[kind])}</h1>\n' + index_items(index, by_page)
        (output / f"{kind}.html").write_text(document(LABELS[kind], body), encoding="utf-8")
    for filename, metadata, lyrics in songs:
        fields = "\n".join(
            f"<dt>{escape(key)}</dt><dd>{metadata_value(key, value, metadata)}</dd>"
            for key, value in metadata.items() if key != "Collation"
        )
        body = (f'<h1>{escape(metadata["Title"])}</h1>\n'
                f'<section aria-label="Song metadata"><h2>Metadata</h2><dl>{fields}</dl></section>\n'
                f'<section aria-label="Song lyrics"><h2>Lyrics</h2><pre class="lyrics">{word_links(lyrics, indexes["words"])}</pre></section>')
        (output / filename).write_text(document(metadata["Title"], body, "../"), encoding="utf-8")
    return len(songs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the static lyrics website.")
    parser.add_argument("--lyrics-dir", type=Path, default=ROOT / "lyrics")
    parser.add_argument("--output", type=Path, default=ROOT / "index")
    args = parser.parse_args()
    count = build_site(args.lyrics_dir, args.output)
    print(f"Built {args.output}: {count} song pages, {len(KINDS)} indexes, and an intro page")


if __name__ == "__main__":
    main()
