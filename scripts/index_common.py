"""Shared metadata parsing and deterministic JSON index generation."""

import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KINDS = ("titles", "first_lines", "words", "lyrics", "composers", "lyric_dates", "composition_dates", "meters")
WORD_PATTERN = re.compile(r"[^\W\d_]+(?:[’'][^\W\d_]+)*", re.UNICODE)
STOPWORDS = frozenset(
    line.strip() for line in (Path(__file__).parent / "stopwords.txt").read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.startswith("#")
)
ANNOTATION = re.compile(
    r"\s*\((?:arranger|arrangement|alteration|Mrs\.|Miss|Rev\.|Dr\.|Eld\.|"
    r"Sir|Judge|D\. D\.|[^()]*(?:verse|chorus|half)[^()]*)\)",
    re.IGNORECASE,
)


def read_metadata(path: Path) -> dict[str, str]:
    """Read only the header; lyric lines containing colons are not metadata."""
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.fullmatch(r"_{3,}", line.strip()):
            break
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        if key in fields:
            raise ValueError(f"{path}: duplicate metadata field {key!r}")
        fields[key] = value.strip()
    if not fields.get("Page"):
        raise ValueError(f"{path}: missing Page metadata")
    return fields


def lyric_body(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    separator = re.search(r"^_{3,}[ \t]*\r?$", source, re.MULTILINE)
    if not separator:
        raise ValueError(f"{path}: missing metadata/lyrics separator")
    return source[separator.end():].strip("\r\n")


def first_line(path: Path) -> str:
    """Return the first lyric line without trailing punctuation."""
    line = next((line.strip() for line in lyric_body(path).splitlines() if line.strip()), "")
    while line and (line[-1].isspace() or unicodedata.category(line[-1]).startswith("P")):
        line = line[:-1]
    return line


def normalize_word(word: str) -> str:
    return word.lower().replace("'", "’")


def lyric_words(body: str) -> set[str]:
    """Index lyric vocabulary, retaining internal apostrophes and elisions."""
    return {word for match in WORD_PATTERN.finditer(body)
            if (word := normalize_word(match[0])) not in STOPWORDS}


def contributors(value: str) -> list[str]:
    """Semicolons separate sources; commas and book-title conjunctions do not."""
    return [name for part in value.split(";") if (name := ANNOTATION.sub("", part).strip())]


def dates(value: str) -> list[str]:
    """Keep date precision, splitting the legacy comma-separated verse dates."""
    result = []
    year = r"(?:(?:abt|ca\.|c\.)\s*|c)?\d{4}\b"
    for part in value.split(";"):
        cleaned = ANNOTATION.sub("", part).strip()
        # A full calendar date such as July 15, 1927 must remain one key.
        parts = re.split(r",\s*(?=" + year + r")", cleaned) if re.match(year, cleaned) else [cleaned]
        result.extend(part.strip() for part in parts if part.strip())
    return result


def index_keys(metadata: dict[str, str], kind: str) -> list[str]:
    if kind == "titles":
        return [metadata["Collation"]] if metadata.get("Collation") else []
    if kind == "meters":
        return [metadata["Meter"]] if metadata.get("Meter") else []
    if kind == "lyrics":
        return contributors(metadata.get("Lyrics", ""))
    if kind == "lyric_dates":
        return dates(metadata.get("Lyrics Date", ""))
    if kind == "composers":
        return [name for key, value in metadata.items() if key.endswith(" Composer")
                for name in contributors(value)]
    if kind == "composition_dates":
        return [date for key, value in metadata.items() if key.endswith(" Composition Date")
                for date in dates(value)]
    raise ValueError(f"Unknown index kind: {kind}")


def page_sort_key(page: str) -> tuple:
    """Sort page numbers numerically, followed by their printed suffixes."""
    match = re.fullmatch(r"(\d+)(.*)", page)
    if match:
        suffix = match[2]
        return (0, int(match[1]), {"": 0, "t": 1, "b": 2}.get(suffix, 3), suffix, page)
    return (1, 0, 0, page, page)


def meter_sort_key(meter: str) -> tuple:
    """Lead with Common, Short, and Long Meter and their variants."""
    for rank, family in enumerate(("Common Meter", "Short Meter", "Long Meter")):
        if meter == family or meter.startswith(family + " "):
            return (rank, (), meter.casefold(), meter)
    if meter in ("Irregular", "Prose"):
        return (6 if meter == "Irregular" else 7, (), meter.casefold(), meter)
    if meter.startswith("Particular Meter:"):
        pattern = meter.split(":", 1)[1]
        return (5, tuple(map(int, re.findall(r"\d+", pattern))), meter.casefold(), meter)
    if meter[:1].isdigit():
        pattern = meter.split("(", 1)[0]
        return (4, tuple(map(int, re.findall(r"\d+", pattern))), meter.casefold(), meter)
    return (3, (), meter.casefold(), meter)


def build_index(lyrics_dir: Path, kind: str) -> dict[str, list[str]]:
    if kind not in KINDS:
        raise ValueError(f"Unknown index kind: {kind}")
    if not lyrics_dir.is_dir():
        raise FileNotFoundError(f"Lyrics directory does not exist: {lyrics_dir}")
    pages_by_key = {}
    for path in sorted(lyrics_dir.glob("*.txt")):
        metadata = read_metadata(path)
        if kind == "first_lines":
            line = first_line(path)
            keys = [line] if line else []
        elif kind == "words":
            keys = lyric_words(lyric_body(path))
        else:
            keys = index_keys(metadata, kind)
        for key in keys:
            pages_by_key.setdefault(key, set()).add(metadata["Page"])
    key_order = meter_sort_key if kind == "meters" else lambda key: (key.casefold(), key)
    return {
        key: sorted(pages_by_key[key], key=page_sort_key)
        for key in sorted(pages_by_key, key=key_order)
    }


def main(kind: str) -> None:
    parser = argparse.ArgumentParser(description=f"Generate the {kind} JSON index.")
    parser.add_argument("--lyrics-dir", type=Path, default=ROOT / "lyrics")
    parser.add_argument("--output", type=Path, default=ROOT / "indexes" / f"{kind}.json")
    args = parser.parse_args()
    index = build_index(args.lyrics_dir, kind)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{args.output}: {len(index)} entries")
