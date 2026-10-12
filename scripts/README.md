# Lyrics indexes

## Full build

Use [build.sh](build.sh) after editing lyrics, metadata, stopwords, templates, or generator
code. It requires Bash, `uv` on your PATH, and Python 3.13 or later. From the
repository root, rebuild all JSON indexes and the static website together:

```sh
./scripts/build.sh
```

The script runs these generators in order:

1. `titles.py`
2. `first_lines.py`
3. `words.py`
4. `lyrics.py`
5. `composers.py`
6. `lyric_dates.py`
7. `composition_dates.py`
8. `meters.py`
9. `songs.py`
10. `refresh_skill.py`
11. `site.py`

The first nine write JSON files to `indexes/`; `refresh_skill.py` updates the
bundled data and source links in `skills/cooper-book/references/`; the last writes the website to
`docs/`. Existing generated files are overwritten. The source lyrics and
stopword list are not modified. Each generator reports its output, followed by
a `Build complete` message when all steps succeed.

If a step fails, the script exits immediately with a nonzero status. Earlier
steps may already have updated their outputs; fix the reported error and run
the script again to complete the build.

The script locates the repository relative to itself, so it also works from
another directory when invoked using its absolute path. It uses the default
input and output folders; run the individual generators below for custom paths.
It does not run tests or start a preview server. After building, run the tests
shown below, then open `docs/index.html` or serve `docs/` locally.

## Individual JSON indexes

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
uv run scripts/songs.py
```

Each writes its corresponding JSON file in `indexes/`. The scripts use only the
Python standard library. Defaults are relative to the repository, so commands
also work from another directory when given the script's absolute path.
Use `--lyrics-dir PATH` and `--output PATH` for custom input and output locations.

`songs.json` is an object keyed by printed page number, such as `"30t"`.
Each value has a `metadata` object and a `lyrics` string. The metadata contains
every header field as a string, preserving original field names, Unicode,
contributor annotations, dates, and separate voice parts, including `Page` and
`Collation`. Missing optional fields remain absent. The lyrics preserve line
breaks, blank lines between verses, punctuation, and spacing; only surrounding
newlines after the separator and at the end of the file are removed. The
`metadata.Lyrics` field remains the attribution; `lyrics` holds the song text.
Songs without lyric text have an empty string. Records are sorted in book page order, with an unsuffixed
page first, then `t` before `b`. Duplicate page numbers cause an error rather
than overwriting a song. Rebuild only this export with `uv run scripts/songs.py`;
it accepts the same `--lyrics-dir` and `--output` options as the other generators.

For a JSONL export, run:

```sh
uv run scripts/songs.py --format jsonl
```

This writes `indexes/songs.jsonl`, with one complete song per line in book page
order. Each record has `page`, `metadata`, and `lyrics` fields. The `page` string
matches `metadata.Page`; lyric newlines are escaped within the JSON string so
each record occupies a single physical line. Unicode is retained. An empty
collection produces an empty JSONL file. Use `--output PATH` for another
destination. The default format remains JSON; the full build generates JSON.

Every other index is an object mapping a source, title, first line, date, or meter to an array of
unique page strings, sorted numerically by page, with an unsuffixed page first,
then `t` before `b`. Page values
come from `Page` metadata, including suffixes such as `t` and `b`, rather than
filenames. Alphabetic keys are sorted without regard to case, ignoring opening
punctuation. Commas interrupt collation: compare the text before the first comma,
then subsequent comma-separated parts only when earlier parts match. Thus
`New, Zoe` precedes `New Deal`, and `New, Arthur` precedes `New, Zoe`.
Unqualified entries precede their comma-qualified forms. Other internal punctuation
and spaces retain their existing sort behavior; displayed text is preserved.
The same rule applies to alphabetic meter ordering and same-year date ordering
on the website. Numeric page, date-century, and meter-pattern ordering retain
their numeric priorities.
Meters use a separate order: Common Meter and its variants, Short Meter and its
variants, Long Meter and its variants, other named meters alphabetically, numeric
meters, Particular Meter patterns, then Irregular and Prose. Numeric patterns sort
by their syllable counts rather than alphabetically.

The first-line index uses the first nonblank line after the metadata separator,
with surrounding whitespace and all trailing punctuation removed, including
sentence endings, typographic quotes, and ellipses. Punctuation within the line is retained.
Songs with the same first line share an entry; songs without lyrics are skipped.
When first lines compare equally for grouping but their second nonblank lyric
lines differ, entries include both lines, separated by ` / `.
Each line has trailing punctuation removed. A song without a second line keeps
its first line alone. Case and opening punctuation do not create a difference
for grouping. Grouping also ignores commas and normalizes whitespace; the special
comma sorting rule still applies when ordering the resulting index entries.
Displayed spelling and capitalization are retained, so differently written
labels remain separate entries even when they collate equally.

The word index reads only the lyrics. Keys are lowercase; straight and typographic
internal apostrophes combine under a typographic apostrophe. Elisions such as
`heav’nly` remain as written; no stemming or spelling expansion is performed.
Hyphenated forms split into words; digits and surrounding punctuation are omitted.
Repeated occurrences on a page contribute just one page reference. Common words
are excluded using the editable list in `scripts/stopwords.txt`, including archaic
forms and common contractions. Content words such as `god`, `lord`, `jesus`,
`love`, and `heaven` remain indexed. After editing the list, rebuild both the word
JSON index and the website with `./scripts/build.sh`.

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

The home page includes download links to `songs.json` and `songs.jsonl`, containing
all song metadata and lyrics. The website generator writes both files from the current
source collection, including when using custom `--lyrics-dir` and `--output`
paths; it does not depend on a previously generated `indexes/songs.json`.

The site is generated in `docs/`. Open `docs/index.html` directly in a browser,
or serve it locally with `python3 -m http.server 8000 --directory docs`.
All links and styles are local,
so no server or network connection is required. Song pages display metadata except
the internal `Collation` field, and retain the original lyric line and verse breaks.
Contributor names display in reading order (`F. Price`), with links pointing to
their collation keys (`Price, F.`); book titles retain their proper wording.
The site rebuilds indexes
from current lyrics using the same rules as the JSON generators.
The Titles, First Lines, Composers, and Lyrics indexes have A–Z jump links and
letter headings. Contributors are grouped by their collation names (surname first).
The Lyrics Dates and Composition Dates indexes have century headings and jump
links, with entries ordered by their first stated year. Approximate dates and
ranges retain their original labels and are grouped by that year.
The Songs index lists page numbers and titles in page order, with `t` before `b`,
linking each entry directly to its song page.
Each song page has Prev and Next navigation at the top and bottom, following
the same page order. The first and last songs have no link beyond the collection.
Each index entry has a short, stable ID (`entry-` plus 12 hexadecimal characters
derived from its key). Song metadata links to the matching title,
contributor, date, and meter entries, preserving the displayed annotations.
The word index has an overview and separate A–Z pages. Accented initials are grouped
under their corresponding letter; an additional “Other” page is generated if needed.
Included words in each song’s lyrics link to their word-index entry, retaining
original capitalization, punctuation, line breaks, and spacing.
Following a page number from a word index jumps to the first matching word in
the song and subtly highlights every occurrence, using a readable URL such as
`songs/030a.html?highlight=angels`. Highlighting and scrolling use JavaScript.

Page layouts and styles come from the editable files in `templates/`; see the
[template guide](../templates/README.md) for customization instructions.

The generator accepts `--lyrics-dir PATH`, `--output PATH`, and
`--templates-dir PATH` (defaults to the repository’s `templates/` folder). It overwrites
generated pages on subsequent runs; it does not delete other files in the output
directory or edit lyrics or JSON indexes.
