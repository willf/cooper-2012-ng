# Lyrics indexes

Run each generator from the repository root:

```sh
uv run scripts/titles.py
uv run scripts/lyrics.py
uv run scripts/composers.py
uv run scripts/lyric_dates.py
uv run scripts/composition_dates.py
uv run scripts/meters.py
```

Each writes its corresponding JSON file in `indexes/`. The scripts use only the
Python standard library. Defaults are relative to the repository, so commands
also work from another directory when given the script's absolute path.
Use `--lyrics-dir PATH` and `--output PATH` for custom input and output locations.

Every index is an object mapping a source, title, date, or meter to an array of
unique page strings, sorted numerically by page, with an unsuffixed page first,
then `t` before `b`. Page values
come from `Page` metadata, including suffixes such as `t` and `b`, rather than
filenames. Keys are sorted without regard to case; Unicode punctuation is retained.

Contributor lists split on semicolons. Verse labels, roles, and honorifics are
omitted from index keys to combine repeated contributors. Maiden names, uncertain
given names, initials, and suffixes remain. Book sources are included alongside
poets in the lyrics index. All composer parts are combined in the composers
index; all composition-date fields are combined in the composition dates index.

Date indexes omit verse and arrangement annotations, retain calendar dates,
circa markers and ranges as written, and split multiple dates. They do not expand
ranges or guess missing dates. Missing optional fields are skipped. Duplicate
metadata fields and missing page numbers cause an error.

Run the tests, including a check that the generated indexes match the collection:

```sh
uv run python -m unittest discover -s tests -v
```
