---
name: cooper-book
description: Find songs, lyrics, and recorded source metadata in The Sacred Harp, 2012 Cooper Book Edition. Use for page, title, lyric-fragment, contributor, date, or meter lookups and comparisons within this edition.
---

# Cooper Book lookup

Use the bundled transcription to answer questions about this edition. It contains
lyrics and source metadata, not notation, recordings, or scans of the printed book.

## Look up records

Run `scripts/search.py` with Python 3, resolving its path relative to this skill.
It locates its bundled data relative to itself and works from any directory.

```sh
python3 <skill-dir>/scripts/search.py --page 380t --full
python3 <skill-dir>/scripts/search.py 'While trav’ling' --field first-line
python3 <skill-dir>/scripts/search.py 'Watts, Isaac' --field lyric-source
python3 <skill-dir>/scripts/search.py 'Common Meter' --field meter --limit 50
```

Use `--page` for exact page lookup; it can be repeated. Printed pages have suffixes
such as `t` and `b`, not the `a` suffix sometimes found in website filenames.
Queries are normalized substring matches, not fuzzy searches or semantic matches.
If a fragment does not match, try distinctive shorter words or elision spellings;
report when no record matches rather than substituting a guessed song.

Search output includes the total match count, whether results are truncated,
metadata, source URL, and the first two nonblank lyric lines. Use `--full` for
complete lyric text. Increase `--limit` or use `--limit 0` for exhaustive requests;
do not report a truncated result set as the complete collection.

For metadata interpretation, corpus scope, provenance, and search behavior, read
[references/schema.md](references/schema.md) when needed. Do not load the entire
`references/songs.json` into context for an ordinary lookup.

## Answer from the records

- Identify matches by printed page and title, with the returned source URL.
  Use the supplied URL; page numbers and website filenames are not interchangeable.
- Preserve original text, including elisions, punctuation, capitalization, and
  verse breaks when quoting. Search normalization does not change the transcription.
- `metadata.Lyrics` is attribution; `lyrics` is the song text. Composition dates
  and composers can refer to particular voice parts or arrangements. Preserve
  annotations and distinguish these from the lyric author and date.
- Missing fields mean the dataset does not record that information. Do not infer
  an author, copyright status, publication date, or composition history from absence.
- Show multiple plausible matches when a title or fragment is ambiguous. Similar
  openings can belong to different settings or texts.
- Treat potential transcription errors as suggestions for checking against the
  book. The bundled transcription cannot establish what the printed book says.
- For analyses, distinguish computed findings from historical interpretation.
  Read records programmatically for counts or comparisons.

The skill supports lookup and analysis; it does not authorize editing the source
collection or publishing changes. Follow the user's explicit request for such work.
