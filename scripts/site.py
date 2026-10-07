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
    from .index_common import KINDS, ROOT, WORD_PATTERN, build_index, contributors, dates, lyric_body, normalize_word, page_sort_key, read_metadata
else:
    from index_common import KINDS, ROOT, WORD_PATTERN, build_index, contributors, dates, lyric_body, normalize_word, page_sort_key, read_metadata

LABELS = {
    "songs": "Songs",
    "titles": "Titles",
    "first_lines": "First lines",
    "words": "Words",
    "lyrics": "Poets and lyric sources",
    "composers": "Composers",
    "lyric_dates": "Lyric dates",
    "composition_dates": "Composition dates",
    "meters": "Meters",
}

CSS = """:root {
  color-scheme: light dark;
  --paper: #faf9f6; --ink: #252421; --quiet: #252421b8;
  --line: #25242129; --accent: #28566c; --wash: #28566c0d;
  --ui: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
html { scroll-padding-top: 2rem; }
body { margin: 0; color: var(--ink); background: var(--paper);
  font: 18px/1.65 Georgia, "Times New Roman", serif; }
header, main, footer { max-width: 72rem; margin: auto;
  padding-inline: max(1.25rem, env(safe-area-inset-left)); }
header { padding-block: 1rem .5rem; border-bottom: 1px solid var(--line); }
.topbar { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; }
.brand { color: var(--ink); font: 500 1rem/1.4 var(--ui); text-decoration: none; }
.edition, .eyebrow, .index-note, footer { font: .8rem/1.6 var(--ui); color: var(--quiet); }
.edition { display: none; }
.desktop-nav { display: none; }
.mobile-nav { font: .9rem/1.5 var(--ui); }
summary { cursor: pointer; padding: .5rem 0; min-height: 44px; color: var(--accent); }
.mobile-nav nav { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: .25rem 1rem; padding-block: .75rem; }
.mobile-nav nav a { min-height: 44px; display: flex; align-items: center; }
main { padding-block: 1.5rem 2.5rem; min-height: 65vh; }
a { color: var(--accent); text-underline-offset: .2em; text-decoration-thickness: 1px;
  touch-action: manipulation; -webkit-tap-highlight-color: #28566c26; }
a:hover { text-decoration-thickness: 2px; }
a:focus-visible, summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; }
.skip-link { position: absolute; top: -8rem; left: 1rem; background: var(--paper); padding: .75rem; z-index: 5; }
.skip-link:focus { top: 1rem; }
h1 { font-size: clamp(2.15rem, 5vw, 3.4rem); font-weight: 400;
  letter-spacing: -.025em; line-height: 1.15; margin: .25rem 0 1rem; text-wrap: balance; }
h2 { font: 500 .85rem/1.5 var(--ui); margin: 0 0 .75rem;
  letter-spacing: .06em; text-transform: uppercase; }
p { max-width: 60ch; text-wrap: pretty; }
.eyebrow { letter-spacing: .09em; text-transform: uppercase; margin: 0 0 .5rem; }
.lead { font-size: 1.15rem; max-width: 52ch; }
.directory { list-style: none; padding: 0; margin: 1.5rem 0; display: grid; gap: 0 2rem; }
.directory li { border-top: 1px solid var(--line); min-width: 0; }
.directory a { padding: .75rem 0; display: grid; grid-template-columns: 1fr auto;
  gap: .25rem 1rem; text-decoration: none; }
.directory .name { font-size: 1.3rem; }
.directory .description { font: .85rem/1.5 var(--ui); color: var(--quiet); grid-column: 1 / -1; }
.directory .count { font: .8rem/1.5 var(--ui); color: var(--quiet); align-self: center; font-variant-numeric: tabular-nums; }
.directory a:hover .name { text-decoration: underline; text-underline-offset: .2em; }
.index-note { margin-bottom: 1rem; }
.index-list { list-style: none; padding: 0; margin: 1.25rem 0; }
.index-list li { border-top: 1px solid var(--line); padding: .5rem 0;
  display: grid; gap: .25rem 2rem; overflow-wrap: anywhere;
  content-visibility: auto; contain-intrinsic-size: auto 5rem; scroll-margin-top: 2rem; }
.index-list li:target { background: var(--wash); box-shadow: -.5rem 0 var(--accent); }
.index-label { min-width: 0; }
.index-word { font-variant-caps: small-caps; font-size: 1.15em; }
.song-list li { display: block; padding: 0; }
.song-list a { display: grid; grid-template-columns: 4rem minmax(0, 1fr);
  min-height: 44px; padding-block: .5rem; text-decoration: none; }
.song-list a:hover { background: var(--wash); text-decoration: underline; }
.song-page { font: .9rem/1.8 var(--ui); color: var(--quiet); font-variant-numeric: tabular-nums; }
.page-links { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0 .25rem;
  font: .9rem/1.5 var(--ui); font-variant-numeric: tabular-nums; }
.page-links a { min-height: 44px; min-width: 44px; display: inline-flex;
  align-items: center; justify-content: center; text-decoration: none; padding: .25rem; }
.page-links a:hover { background: var(--wash); text-decoration: underline; }
.letter-nav { display: flex; flex-wrap: wrap; gap: .25rem; margin: 1rem 0 1.25rem; }
.letter-nav a { display: inline-flex; align-items: center; justify-content: center;
  min-width: 44px; min-height: 44px; border: 1px solid var(--line); text-decoration: none;
  font: .9rem/1 var(--ui); }
.letter-nav a:hover, .letter-nav a[aria-current] { background: var(--accent); color: var(--paper); }
.letter-directory { list-style: none; padding: 0; display: grid;
  grid-template-columns: repeat(auto-fit, minmax(5rem, 1fr)); gap: .5rem; max-width: 48rem; }
.letter-directory a { display: flex; align-items: baseline; justify-content: space-between;
  padding: .75rem; min-height: 44px; border-bottom: 1px solid var(--line); text-decoration: none; }
.letter-directory small { color: var(--quiet); font: .75rem/1.5 var(--ui); }
.song-jumps { font: .85rem/1.5 var(--ui); margin: 0 0 1rem; }
.song-jumps a { display: inline-block; padding-block: .5rem; min-height: 44px; margin-right: 1.5rem; }
.song-pagination { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem; font: .85rem/1.5 var(--ui); margin-bottom: 1rem; }
.song-pagination a, .song-pagination .unavailable { padding-block: .5rem;
  min-height: 44px; text-decoration: none; }
.song-pagination a:hover { text-decoration: underline; }
.song-pagination small { display: block; color: var(--quiet); margin-top: .25rem; overflow-wrap: anywhere; }
.song-pagination > :last-child { text-align: right; }
.song-pagination .unavailable { color: var(--quiet); }
.song-pagination-bottom { border-top: 1px solid var(--line); margin-top: 2rem; margin-bottom: 0; }
.song-layout { display: grid; gap: 2rem; }
.song-layout > * { min-width: 0; }
.lyrics { white-space: pre-wrap; overflow-wrap: anywhere;
  font: 1.1rem/1.8 Georgia, "Times New Roman", serif; margin: 0; max-width: 60ch; }
.lyrics a { text-decoration-color: #28566c66; }
.lyrics a:hover { text-decoration-color: var(--accent); }
.metadata { border-top: 1px solid var(--line); padding-top: 1rem; }
dl { font: .9rem/1.65 var(--ui); margin: 0; }
dt { color: var(--quiet); font-size: .75rem; margin: .75rem 0 .125rem; }
dd { margin: 0; overflow-wrap: anywhere; }
footer { border-top: 1px solid var(--line); padding-block: 1rem 1.5rem;
  display: flex; flex-wrap: wrap; gap: .75rem 2rem; }
footer a { min-height: 44px; display: inline-flex; align-items: center; }
@media (min-width: 48rem) {
  header, main, footer { padding-inline: 2rem; }
  main { padding-block: 2rem 3rem; }
  .edition { display: block; }
  .mobile-nav { display: none; }
  .desktop-nav { display: flex; flex-wrap: wrap; gap: .25rem 1.25rem; margin-top: .75rem;
    font: .85rem/1.5 var(--ui); }
  .desktop-nav a { display: inline-flex; min-height: 44px; align-items: center; text-decoration: none; }
  .desktop-nav a:hover { text-decoration: underline; }
  .directory { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .index-list li { grid-template-columns: minmax(0, 2fr) minmax(0, 3fr); align-items: baseline; }
}
@media (min-width: 62rem) {
  .song-layout { grid-template-columns: minmax(0, 1fr) 18rem; gap: 2.5rem; }
  .metadata { border-top: 0; border-left: 1px solid var(--line); padding: 0 0 0 1.5rem; }
}
@media (prefers-color-scheme: dark) {
  :root { --paper: #1c1b19; --ink: #efede6; --quiet: #efede6b8;
    --line: #efede62e; --accent: #a2c4d3; --wash: #a2c4d312; }
  .lyrics a { text-decoration-color: #a2c4d366; }
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
<meta name="color-scheme" content="light dark">
<title>{escape(title)} — Cooper 2012 Lyrics</title>
<link rel="stylesheet" href="{prefix}style.css">
</head>
<body id="top">
<a class="skip-link" href="#main">Skip to content</a>
<header>
<div class="topbar">
<a class="brand" href="{prefix}index.html">Cooper 2012 Lyrics</a>
<span class="edition">The Sacred Harp · 2012 Cooper edition</span>
</div>
<nav class="desktop-nav" aria-label="Browse indexes">{nav}</nav>
<details class="mobile-nav"><summary>Browse indexes</summary>
<nav aria-label="Browse indexes on mobile">{nav}</nav></details>
</header>
<main id="main">{body}</main>
<footer><a href="{prefix}index.html">Cooper 2012 Lyrics</a>
<a href="#top">Back to top ↑</a></footer>
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
        items.append(f'<li id="{entry_id(key)}"><span class="index-label">{label}</span><span class="page-links">{" ".join(links)}</span></li>')
    return '<ul class="index-list">' + "\n".join(items) + "</ul>"


def build_word_pages(output: Path, index: dict[str, list[str]], by_page: dict) -> None:
    groups = {letter: {} for letter in ascii_lowercase}
    for word, pages in index.items():
        groups.setdefault(word_letter(word), {})[word] = pages
    (output / "words").mkdir(exist_ok=True)
    letters = list(groups)
    intro = (f'<h1>Words</h1><p>{len(index)} words from the lyrics, with common words omitted. '
             'Choose a letter to browse, or select a word within a song’s lyrics.</p>')
    links = "".join(f'<li><a href="words/{letter}.html"><span>{letter.upper()}</span>'
                    f'<small>{len(groups[letter])}</small></a></li>' for letter in letters)
    (output / "words.html").write_text(document("Words", intro + f'<ul class="letter-directory">{links}</ul>'), encoding="utf-8")
    for letter, words in groups.items():
        title = f"Words — {letter.upper()}"
        nav = '<nav class="letter-nav" aria-label="Word index letters">' + " ".join(
            f'<a href="{initial}.html"' + (' aria-current="page"' if initial == letter else '')
            + f'>{initial.upper()}</a>' for initial in letters) + '</nav>'
        body = f'<h1>{title}</h1>{nav}'
        body += index_items(words, by_page, "../", words=True) if words else '<p>No indexed words for this letter.</p>'
        (output / "words" / f"{letter}.html").write_text(document(title, body, "../"), encoding="utf-8")


def metadata_value(field: str, value: str, metadata: dict[str, str]) -> str:
    """Link index keys, displaying contributor names in normal reading order."""
    if field in ("Title", "Collation") and metadata.get("Collation"):
        return index_link("titles", metadata["Collation"], value)
    if field == "Meter":
        return index_link("meters", value, value)
    if field == "Page":
        return index_link("songs", value, value)
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


def song_navigation(songs: list, position: int, *, bottom: bool = False) -> str:
    items = []
    for offset, rel, label in [(-1, "prev", "← Prev"), (1, "next", "Next →")]:
        neighbor = position + offset
        if 0 <= neighbor < len(songs):
            filename, metadata, _ = songs[neighbor]
            title = f'{metadata["Page"]} {metadata["Title"]}'
            items.append(f'<a href="{quote(Path(filename).name)}" rel="{rel}">{label}'
                         f'<small>{escape(title)}</small></a>')
        else:
            items.append(f'<span class="unavailable" aria-disabled="true">{label}</span>')
    css_class = "song-pagination song-pagination-bottom" if bottom else "song-pagination"
    return f'<nav class="{css_class}" aria-label="Previous and next songs">' + "".join(items) + '</nav>'


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
    songs.sort(key=lambda song: page_sort_key(song[1]["Page"]))
    indexes = {kind: build_index(lyrics_dir, kind) for kind in KINDS}
    # Parse and validate all input before writing the generated site.
    output.mkdir(parents=True, exist_ok=True)
    (output / "songs").mkdir(exist_ok=True)
    (output / "style.css").write_text(CSS, encoding="utf-8")
    descriptions = {
        "songs": "Browse every song in page order.",
        "titles": "Find a song by its tune title.",
        "first_lines": "Find the opening words you remember.",
        "words": "Explore the vocabulary, from A to Z.",
        "lyrics": "Browse poets and published lyric sources.",
        "composers": "Find composers and arrangers of every part.",
        "lyric_dates": "Browse the dates of the words.",
        "composition_dates": "Browse composition and arrangement dates.",
        "meters": "Find songs with the same poetic meter.",
    }
    counts = {"songs": len(songs), **{kind: len(index) for kind, index in indexes.items()}}
    intro_links = "\n".join(
        f'<li><a href="{kind}.html"><span class="name">{escape(LABELS[kind])}</span>'
        f'<span class="count">{counts[kind]:,}</span>'
        f'<span class="description">{descriptions[kind]}</span></a></li>' for kind in LABELS)
    intro = f'''<p class="eyebrow">The Sacred Harp · 2012 Cooper edition</p>
<h1>A companion to the songs.</h1>
<p class="lead">Lyrics and source information for {len(songs)} songs.
Find a familiar tune, follow a poet, or explore the words.</p>
<ul class="directory">{intro_links}</ul>
<p class="index-note">Follow a page number in any index to read a song.
Page suffixes <strong>t</strong> and <strong>b</strong> indicate top and bottom;
top entries appear before bottom entries.</p>'''
    (output / "index.html").write_text(document("Home", intro), encoding="utf-8")
    song_entries = []
    for page in sorted(by_page, key=page_sort_key):
        filename, title = by_page[page]
        song_entries.append(f'<li id="{entry_id(page)}"><a href="{quote(filename)}">'
                            f'<span class="song-page">{escape(page)}</span> '
                            f'<span>{escape(title)}</span></a></li>')
    song_body = (f'<p class="eyebrow">Browse the collection</p><h1>Songs</h1>'
                 f'<p class="index-note">{len(songs):,} songs in page order · Select a song to read its lyrics.</p>'
                 '<ul class="index-list song-list">' + "\n".join(song_entries) + '</ul>')
    (output / "songs.html").write_text(document("Songs", song_body), encoding="utf-8")
    for kind, index in indexes.items():
        if kind == "words":
            build_word_pages(output, index, by_page)
            continue
        body = (f'<p class="eyebrow">Browse the collection</p><h1>{escape(LABELS[kind])}</h1>'
                f'<p class="index-note">{len(index):,} entries · Select a page number to read a song.</p>') + index_items(index, by_page)
        (output / f"{kind}.html").write_text(document(LABELS[kind], body), encoding="utf-8")
    for position, (filename, metadata, lyrics) in enumerate(songs):
        fields = "\n".join(
            f"<dt>{escape(key)}</dt><dd>{metadata_value(key, value, metadata)}</dd>"
            for key, value in metadata.items() if key != "Collation"
        )
        body = (song_navigation(songs, position) + f'<p class="eyebrow">Song · Page {escape(metadata["Page"])}</p>'
                f'<h1>{escape(metadata["Title"])}</h1>\n'
                '<nav class="song-jumps" aria-label="Song sections"><a href="#lyrics">Lyrics</a>'
                '<a href="#details">Song details</a></nav><div class="song-layout">'
                f'<section id="lyrics" aria-label="Song lyrics"><h2>Lyrics</h2><pre class="lyrics">{word_links(lyrics, indexes["words"])}</pre></section>'
                f'<aside id="details" class="metadata" aria-label="Song metadata"><h2>Song details</h2><dl>{fields}</dl></aside></div>'
                + song_navigation(songs, position, bottom=True))
        (output / filename).write_text(document(metadata["Title"], body, "../"), encoding="utf-8")
    return len(songs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the static lyrics website.")
    parser.add_argument("--lyrics-dir", type=Path, default=ROOT / "lyrics")
    parser.add_argument("--output", type=Path, default=ROOT / "docs")
    args = parser.parse_args()
    count = build_site(args.lyrics_dir, args.output)
    print(f"Built {args.output}: {count} song pages, {len(LABELS)} indexes, and an intro page")


if __name__ == "__main__":
    main()
