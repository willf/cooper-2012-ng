# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Generate indexes/composition_dates.json with uv run scripts/composition_dates.py."""

if __package__:
    from .index_common import main
else:
    from index_common import main

if __name__ == "__main__":
    main("composition_dates")
