# Corpus and schema

The bundled data is a snapshot of the transcription in
https://github.com/willf/cooper-2012-ng for The Sacred Harp, 2012 Cooper Book Edition.
It contains 613 song records. It is not a scan or an independent transcription
check. It does not contain musical notation. See `provenance.json` for the
snapshot's repository revision and data checksum; that revision identifies the
base checkout, while the checksum identifies the actual bundled data.

`songs.json` is keyed by printed page strings. Each value has:

- `metadata`: original header fields, all string values. Optional fields are absent.
- `lyrics`: full lyric text, preserving verse breaks, spacing, punctuation, and
  capitalization. Surrounding newlines are removed. Empty text is an empty string.

`metadata.Page` matches the outer page key. Suffixes `t` and `b` indicate the top
and bottom of the printed page. Records are in numeric book order, with an
unsuffixed page first, then top before bottom. Titles are not unique identifiers.

Useful metadata fields include `Title`, `Alternative Title`, `Collation`, `Lyrics`,
`Lyrics Date`, `Meter`, `Tune Composer`, and `Tune Composition Date`. Separate
Alto, Bass, Tenor, and Treble composer and composition-date fields may appear.
`Collation` is the title's indexing form. `Lyrics` holds author or source
attribution, not lyric text. Semicolons and parenthetical annotations in attribution
or date fields can distinguish contributors, verses, roles, and arrangements.
Dates can be approximate, ranges, or full calendar dates; preserve their precision.

`sources.json` maps each printed page to its actual website song URL, generated
from source filenames. Do not derive URLs by substituting the printed page into
a filename: for example, page 380t is `songs/380a.html`.

## Search behavior

The helper uses case-insensitive substring matching, removes diacritics and
apostrophes, treats other punctuation as spaces, and collapses whitespace.
It does not expand elisions, equate `thru` with `through`, stem words, implement
index collation, or infer synonyms. Use shorter fragments for spelling variants.
Field searches select specific metadata or lyric text; `all` searches individual
metadata values and the lyric text. Page filters and text queries are combined
with AND. Results preserve the original data; normalization affects matching only.

## Attribution and reuse

The website's footer displays CC BY-NC-SA 4.0, while its introduction states that
some lyrics are not public domain and are included under a fair-use rationale.
This package does not establish song-by-song rights or grant additional reuse
permissions. Cite the project and the song page; do not describe all bundled
lyrics as public domain or uniformly licensed. No copyright status field exists.

## Refreshing this package in the source repository

Regenerate the data with `python3 scripts/songs.py`, then run
`python3 scripts/refresh_skill.py` from the repository root. The latter copies
`indexes/songs.json`, regenerates source URLs, and updates provenance. It does
not install or publish the skill. A separately installed copy remains a snapshot
until replaced.
