# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Export every song's metadata and lyrics as JSON or JSONL."""

import argparse
import json
from pathlib import Path
from typing import TypedDict

if __package__:
    from .index_common import ROOT, lyric_body, page_sort_key, read_metadata
else:
    from index_common import ROOT, lyric_body, page_sort_key, read_metadata


class Song(TypedDict):
    metadata: dict[str, str]
    lyrics: str


def build_songs(lyrics_dir: Path) -> dict[str, Song]:
    if not lyrics_dir.is_dir():
        raise FileNotFoundError(f"Lyrics directory does not exist: {lyrics_dir}")
    songs = {}
    sources = {}
    for path in sorted(lyrics_dir.glob("*.txt")):
        metadata = read_metadata(path)
        page = metadata["Page"]
        if page in songs:
            raise ValueError(f"{path}: duplicate Page {page!r} (also in {sources[page]})")
        songs[page] = Song(metadata=metadata, lyrics=lyric_body(path))
        sources[page] = path
    return {page: songs[page] for page in sorted(songs, key=page_sort_key)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lyrics-dir", type=Path, default=ROOT / "lyrics")
    parser.add_argument("--format", choices=("json", "jsonl"), default="json",
                        help="Export format (default: json).")
    parser.add_argument("--output", type=Path,
                        help="Output path (default: indexes/songs.<format>).")
    args = parser.parse_args()
    songs = build_songs(args.lyrics_dir)
    output = args.output or ROOT / "indexes" / f"songs.{args.format}"
    if args.format == "jsonl":
        content = "".join(
            json.dumps({"page": page, **song}, ensure_ascii=False) + "\n"
            for page, song in songs.items()
        )
    else:
        content = json.dumps(songs, ensure_ascii=False, indent=2) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"{output}: {len(songs)} songs")


if __name__ == "__main__":
    main()
