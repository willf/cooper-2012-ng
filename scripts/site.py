# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Build the static lyrics website with uv run scripts/site.py."""

import argparse
import json
from hashlib import sha256
from html import escape
from pathlib import Path
import re
from string import Template, ascii_lowercase
import unicodedata
from urllib.parse import quote

if __package__:
    from .index_common import (
        KINDS,
        ROOT,
        WORD_PATTERN,
        alphabetical_text,
        build_index,
        contributors,
        dates,
        lyric_body,
        normalize_word,
        page_sort_key,
        read_metadata,
    )
else:
    from index_common import (
        KINDS,
        ROOT,
        WORD_PATTERN,
        alphabetical_text,
        build_index,
        contributors,
        dates,
        lyric_body,
        normalize_word,
        page_sort_key,
        read_metadata,
    )

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

SONG_JUMP_INTERVAL = 50


class Templates:
    """Render editable templates; only *_html values contain trusted markup."""

    def __init__(self, directory: Path = ROOT / "templates"):
        self.directory = directory
        self.cache: dict[str, Template] = {}

    def render(self, name: str, **values: object) -> str:
        if name not in self.cache:
            self.cache[name] = Template(
                (self.directory / name).read_text(encoding="utf-8")
            )
        context = {
            key: str(value) if key.endswith("_html") else escape(str(value))
            for key, value in values.items()
        }
        try:
            return self.cache[name].substitute(context)
        except (KeyError, ValueError) as error:
            raise ValueError(f"{self.directory / name}: {error}") from error


def document(
    title: str, body: str, prefix: str = "", *, templates: Templates | None = None
) -> str:
    templates = templates or Templates()
    nav = " ".join(
        templates.render("nav-link.html", href=f"{prefix}{kind}.html", label=label)
        for kind, label in LABELS.items()
    )
    return templates.render(
        "base.html", title=title, prefix=prefix, nav_html=nav, body_html=body
    )


def entry_id(key: str) -> str:
    """An entry keeps its ID when other entries are added or reordered."""
    return "entry-" + sha256(key.encode("utf-8")).hexdigest()[:12]


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
        pieces.append(escape(body[cursor : match.start()]))
        word = normalize_word(match[0])
        if word in word_index:
            pieces.append(
                f'<a href="../words/{word_letter(word)}.html#{entry_id(word)}" data-word="{escape(word)}">{escape(match[0])}</a>'
            )
        else:
            pieces.append(escape(match[0]))
        cursor = match.end()
    pieces.append(escape(body[cursor:]))
    return "".join(pieces)


def index_items(
    index: dict[str, list[str]],
    by_page: dict,
    prefix: str = "",
    *,
    words: bool = False,
    linked_labels: bool = False,
    templates: Templates | None = None,
) -> str:
    templates = templates or Templates()
    items = []
    for key, pages in index.items():
        links = []
        for position, page in enumerate(pages):
            filename, title = by_page[page]
            links.append(
                templates.render(
                    "page-link.html",
                    href=prefix
                    + quote(filename)
                    + ("?highlight=" + quote(key, safe="") if words else ""),
                    title=title,
                    page=page,
                    separator="," if position + 1 < len(pages) else "",
                )
            )
        label = templates.render("word-label.html", word=key) if words else escape(key)
        if linked_labels:
            label = templates.render(
                "index-label-link.html", label=key,
                href=prefix + quote(by_page[pages[0]][0]),
            )
        items.append(
            templates.render(
                "index-item.html",
                id=entry_id(key),
                label_html=label,
                links_html=" ".join(links),
            )
        )
    return templates.render("index-list.html", items_html="\n".join(items))


def alphabetical_index(index: dict, by_page: dict, templates: Templates) -> tuple[str, str]:
    groups = {letter: {} for letter in ascii_lowercase}
    for key, pages in index.items():
        initial = alphabetical_text(key)[:1]
        groups.setdefault(initial if initial in ascii_lowercase else "other", {})[key] = pages
    letters = []
    sections = []
    for letter, entries in groups.items():
        label = letter.upper() if letter != "other" else "#"
        letters.append(templates.render(
            "index-letter.html" if entries else "index-letter-empty.html",
            letter=letter, label=label,
        ))
        if entries:
            sections.append(templates.render(
                "index-section.html", letter=letter, label=label,
                top_html=templates.render("index-top.html") if letter != "a" else "",
                entries_html=index_items(entries, by_page, linked_labels=True, templates=templates),
            ))
    return templates.render("index-alphabet.html", letters_html="".join(letters)), "\n".join(sections)


def build_word_pages(
    output: Path,
    index: dict[str, list[str]],
    by_page: dict,
    *,
    templates: Templates | None = None,
) -> None:
    templates = templates or Templates()
    groups = {letter: {} for letter in ascii_lowercase}
    for word, pages in index.items():
        groups.setdefault(word_letter(word), {})[word] = pages
    (output / "words").mkdir(exist_ok=True)
    letters = list(groups)
    links = "".join(
        templates.render(
            "letter-item.html",
            letter=letter,
            label=letter.upper(),
            count=len(groups[letter]),
        )
        for letter in letters
    )
    body = templates.render("words.html", count=len(index), letters_html=links)
    (output / "words.html").write_text(
        document("Words", body, templates=templates), encoding="utf-8"
    )
    for letter, words in groups.items():
        title = f"Words — {letter.upper()}"
        links = " ".join(
            templates.render(
                "letter-link.html",
                letter=initial,
                label=initial.upper(),
                current_html=' aria-current="page"' if initial == letter else "",
            )
            for initial in letters
        )
        body = templates.render(
            "word-letter.html",
            title=title,
            letters_html=links,
            entries_html=index_items(
                words, by_page, "../", words=True, templates=templates
            )
            if words
            else templates.render("empty-words.html"),
        )
        (output / "words" / f"{letter}.html").write_text(
            document(title, body, "../", templates=templates), encoding="utf-8"
        )


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
    pattern = "|".join(
        re.escape(key) for key in sorted(set(keys), key=len, reverse=True)
    )
    pieces = []
    cursor = 0
    for match in re.finditer(pattern, value):
        pieces.append(escape(value[cursor : match.start()]))
        label = (
            display_source(match[0]) if kind in ("lyrics", "composers") else match[0]
        )
        pieces.append(index_link(kind, match[0], label))
        cursor = match.end()
    pieces.append(escape(value[cursor:]))
    return "".join(pieces)


def song_navigation(
    songs: list,
    position: int,
    *,
    bottom: bool = False,
    templates: Templates | None = None,
) -> str:
    templates = templates or Templates()
    items = []
    for offset, rel, label in [(-1, "prev", "← Prev"), (1, "next", "Next →")]:
        neighbor = position + offset
        if 0 <= neighbor < len(songs):
            filename, metadata, _ = songs[neighbor]
            title = f'{metadata["Page"]} {metadata["Title"]}'
            items.append(
                templates.render(
                    "song-neighbor.html",
                    href=quote(Path(filename).name),
                    rel=rel,
                    label=label,
                    title=title,
                )
            )
        else:
            items.append(templates.render("song-unavailable.html", label=label))
    css_class = (
        "song-pagination song-pagination-bottom" if bottom else "song-pagination"
    )
    return templates.render(
        "song-navigation.html", css_class=css_class, neighbors_html="".join(items)
    )


def build_site(
    lyrics_dir: Path, output: Path, *, templates_dir: Path = ROOT / "templates"
) -> int:
    """Generate relative links and song pages without modifying the lyrics."""
    if not lyrics_dir.is_dir():
        raise FileNotFoundError(f"Lyrics directory does not exist: {lyrics_dir}")
    templates = Templates(templates_dir)
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
    (output / "songs.json").write_text(
        json.dumps(
            {metadata["Page"]: {"metadata": metadata, "lyrics": body}
             for _, metadata, body in songs},
            ensure_ascii=False, indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    (output / "songs").mkdir(exist_ok=True)
    (output / "style.css").write_text(
        (templates_dir / "style.css").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (output / "song.js").write_text(
        (templates_dir / "song.js").read_text(encoding="utf-8"), encoding="utf-8"
    )
    descriptions = {
        "songs": "Browse every song in page order.",
        "titles": "Browse by tune title.",
        "first_lines": "Browse by first line.",
        "words": "Search by word.",
        "lyrics": "Browse poets and published lyric sources.",
        "composers": "Browse composers and arrangers.",
        "lyric_dates": "Browse the dates of the words.",
        "composition_dates": "Browse composition and arrangement dates.",
        "meters": "Find songs with the same poetic meter.",
    }
    counts = {
        "songs": len(songs),
        **{kind: len(index) for kind, index in indexes.items()},
    }
    intro_links = "\n".join(
        templates.render(
            "directory-item.html",
            kind=kind,
            label=LABELS[kind],
            count=f"{counts[kind]:,}",
            description=descriptions[kind],
        )
        for kind in LABELS
    )
    intro = templates.render(
        "home.html", song_count=len(songs), directory_html=intro_links
    )
    (output / "index.html").write_text(
        document("Home", intro, templates=templates), encoding="utf-8"
    )
    song_entries = []
    ordered_pages = sorted(by_page, key=page_sort_key)
    for page in ordered_pages:
        filename, title = by_page[page]
        song_entries.append(
            templates.render(
                "song-item.html",
                id=entry_id(page),
                href=quote(filename),
                page=page,
                title=title,
            )
        )
    jumps = "".join(
        templates.render("song-jump.html", id=entry_id(page), page=page)
        for page in ordered_pages[SONG_JUMP_INTERVAL::SONG_JUMP_INTERVAL]
    )
    song_body = templates.render(
        "songs.html", count=f"{len(songs):,}", entries_html="\n".join(song_entries),
        jumps_html=templates.render("song-jumps.html", links_html=jumps, interval=SONG_JUMP_INTERVAL),
    )
    (output / "songs.html").write_text(
        document("Songs", song_body, templates=templates), encoding="utf-8"
    )
    for kind, index in indexes.items():
        if kind == "words":
            build_word_pages(output, index, by_page, templates=templates)
            continue
        letters_html = ""
        entries_html = index_items(index, by_page, templates=templates)
        if kind in ("titles", "first_lines"):
            letters_html, entries_html = alphabetical_index(index, by_page, templates)
        body = templates.render(
            "index.html",
            kind=kind,
            title=LABELS[kind],
            count=f"{len(index):,}",
            letters_html=letters_html,
            entries_html=entries_html,
        )
        (output / f"{kind}.html").write_text(
            document(LABELS[kind], body, templates=templates), encoding="utf-8"
        )
    for position, (filename, metadata, lyrics) in enumerate(songs):
        fields = "\n".join(
            templates.render(
                "metadata-field.html",
                label=key,
                value_html=metadata_value(key, value, metadata),
            )
            for key, value in metadata.items()
            if key != "Collation"
        )
        body = templates.render(
            "song.html",
            page=metadata["Page"],
            title=metadata["Title"],
            navigation_html=song_navigation(songs, position, templates=templates),
            lyrics_html=word_links(lyrics, indexes["words"]),
            metadata_html=fields,
            bottom_navigation_html=song_navigation(
                songs, position, bottom=True, templates=templates
            ),
        )
        (output / filename).write_text(
            document(metadata["Title"], body, "../", templates=templates),
            encoding="utf-8",
        )
    return len(songs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the static lyrics website.")
    parser.add_argument("--lyrics-dir", type=Path, default=ROOT / "lyrics")
    parser.add_argument("--output", type=Path, default=ROOT / "docs")
    parser.add_argument(
        "--templates-dir",
        type=Path,
        default=ROOT / "templates",
        help="Folder containing editable HTML templates and style.css",
    )
    args = parser.parse_args()
    count = build_site(args.lyrics_dir, args.output, templates_dir=args.templates_dir)
    print(
        f"Built {args.output}: {count} song pages, {len(LABELS)} indexes, and an intro page"
    )


if __name__ == "__main__":
    main()
