# Lyrics indexes

Run each generator from the repository root:

```sh
uv run scripts/titles.py
uv run scripts/first_lines.py
uv run scripts/words.py
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

Every index is an object mapping a source, title, first line, date, or meter to an array of
unique page strings, sorted numerically by page, with an unsuffixed page first,
then `t` before `b`. Page values
come from `Page` metadata, including suffixes such as `t` and `b`, rather than
filenames. Keys are sorted without regard to case; Unicode punctuation is retained.
Meters use a separate order: Common Meter and its variants, Short Meter and its
variants, Long Meter and its variants, other named meters alphabetically, numeric
meters, Particular Meter patterns, then Irregular and Prose. Numeric patterns sort
by their syllable counts rather than alphabetically.

The first-line index uses the first nonblank line after the metadata separator,
with surrounding whitespace and all trailing punctuation removed, including
sentence endings, typographic quotes, and ellipses. Punctuation within the line is retained.
Songs with the same first line share an entry; songs without lyrics are skipped.

The word index reads only the lyrics. Keys are lowercase; straight and typographic
internal apostrophes combine under a typographic apostrophe. Elisions such as
`heav’nly` remain as written; no stemming or spelling expansion is performed.
Hyphenated forms split into words; digits and surrounding punctuation are omitted.
Repeated occurrences on a page contribute just one page reference. Common words
are excluded using the editable list in `scripts/stopwords.txt`, including archaic
forms and common contractions. Content words such as `god`, `lord`, `jesus`,
`love`, and `heaven` remain indexed. After editing the list, rebuild both the word
JSON index and the website.

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

## Static website

Generate the website (intro, nine indexes, and individual song pages):

```sh
uv run scripts/site.py
```

The site is generated in `docs/`. Open `docs/index.html` directly in a browser,
or serve it locally with `python3 -m http.server 8000 --directory docs`.
All links and styles are local,
so no server or network connection is required. Song pages display metadata except
the internal `Collation` field, and retain the original lyric line and verse breaks.
Contributor names display in reading order (`F. Price`), with links pointing to
their collation keys (`Price, F.`); book titles retain their proper wording.
The site rebuilds indexes
from current lyrics using the same rules as the JSON generators.
The Songs index lists page numbers and titles in page order, with `t` before `b`,
linking each entry directly to its song page.
Each song page has Prev and Next navigation at the top and bottom, following
the same page order. The first and last songs have no link beyond the collection.
Each index entry has a stable ID. Song metadata links to the matching title,
contributor, date, and meter entries, preserving the displayed annotations.
The word index has an overview and separate A–Z pages. Accented initials are grouped
under their corresponding letter; an additional “Other” page is generated if needed.
Included words in each song’s lyrics link to their word-index entry, retaining
original capitalization, punctuation, line breaks, and spacing.

The generator accepts `--lyrics-dir PATH` and `--output PATH`. It overwrites
generated pages on subsequent runs; it does not delete other files in the output
directory or edit lyrics or JSON indexes.
