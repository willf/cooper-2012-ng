# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Generate indexes/lyrics.json with uv run scripts/lyrics.py."""

if __package__:
    from .index_common import main
else:
    from index_common import main

if __name__ == "__main__":
    main("lyrics")
