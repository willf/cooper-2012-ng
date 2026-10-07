# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Generate indexes/first_lines.json with uv run scripts/first_lines.py."""

if __package__:
    from .index_common import main
else:
    from index_common import main

if __name__ == "__main__":
    main("first_lines")
