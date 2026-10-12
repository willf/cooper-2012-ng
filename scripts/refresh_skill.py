# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Refresh the distributable Cooper Book skill's data snapshot."""

import hashlib
import json
import subprocess
from pathlib import Path
from urllib.parse import quote

if __package__:
    from .index_common import ROOT, page_sort_key, read_metadata
    from .songs import build_songs
else:
    from index_common import ROOT, page_sort_key, read_metadata
    from songs import build_songs


def main() -> None:
    data = (ROOT / "indexes/songs.json").read_bytes()
    songs = json.loads(data)
    if songs != build_songs(ROOT / "lyrics"):
        raise ValueError("indexes/songs.json is stale; regenerate with scripts/songs.py first")
    urls = {}
    for path in sorted((ROOT / "lyrics").glob("*.txt")):
        page = read_metadata(path)["Page"]
        urls[page] = f"https://willf.github.io/cooper-2012-ng/songs/{quote(path.stem)}.html"
    urls = {page: urls[page] for page in sorted(urls, key=page_sort_key)}
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    destination = ROOT / "skills/cooper-book/references"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "songs.json").write_bytes(data)
    for name, value in {
        "sources.json": urls,
        "provenance.json": {
            "repository": "https://github.com/willf/cooper-2012-ng",
            "base_revision": revision,
            "songs_sha256": hashlib.sha256(data).hexdigest(),
            "sources_sha256": hashlib.sha256(
                (json.dumps(urls, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            ).hexdigest(),
            "song_count": len(songs),
            "edition": "The Sacred Harp, 2012 Cooper Book Edition",
        },
    }.items():
        (destination / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"{destination}: refreshed {len(songs)} songs")


if __name__ == "__main__":
    main()
