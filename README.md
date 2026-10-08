# Cooper Book Indexes

See https://willf.github.io/cooper-2012-ng/

## Build the site

The source files are in `lyrics/`. Use Python 3.13 or later with
[uv](https://docs.astral.sh/uv/), and run commands from the repository root:

```sh
./scripts/build.sh
```

This rebuilds all JSON indexes in `indexes/` and the static website in `docs/`, including the introduction,
song pages, and all index pages. It reads the current lyrics and metadata
directly, so rebuild after changing a lyrics file. Edit the source files and
templates rather than the generated HTML, which is overwritten on each build.

The build also exports all songs to [indexes/songs.json](indexes/songs.json),
keyed by printed page number (for example, `"30t"`). Each record has a `metadata`
object preserving all source header fields and values, including `Page`,
`Collation`, and annotations, plus a `lyrics` string preserving lyric line and
verse breaks. Records follow book page order.
The website build generates the same export as `docs/songs.json`, linked for
download beneath the home page's index list.

Open `docs/index.html` in a browser, or start a local preview:

```sh
python3 -m http.server 8000 --directory docs
```

Then visit <http://localhost:8000>. Stop the server with Ctrl+C.

The [master build script](scripts/build.sh) stops if any generator fails and can be invoked from any
directory using its absolute path. To rebuild only the website, run
`uv run scripts/site.py`. See [scripts/README.md](scripts/README.md) for the
full build sequence, individual index commands, and details of the indexing rules.
The build does not start a server or run tests; those commands are separate.

## Customize the pages

The website uses editable HTML templates in [templates/](templates/README.md).
Start with [home.html](templates/home.html) for the introduction,
[base.html](templates/base.html) for the shared header and footer,
[index.html](templates/index.html) for the indexes, and
[song.html](templates/song.html) for individual songs. Edit
[style.css](templates/style.css) to change the appearance.

Keep placeholders such as `${song_count}` and `${lyrics_html}` where you want
built content, then run `uv run scripts/site.py` to see your changes.
See the [template guide](templates/README.md) for examples and available placeholders.

## Add stopwords

Edit [scripts/stopwords.txt](scripts/stopwords.txt) to exclude very common words
from the word index. Add one lowercase word per line. Blank lines and lines
starting with `#` are ignored. Use typographic apostrophes for contractions,
such as `can’t`.

Entries match whole words, not prefixes or stems. Add each form separately
when needed; for example, excluding `sing` does not exclude `singing`.
Remove an entry to include that word again.

After editing the list, rebuild both the word JSON index and the website:

```sh
./scripts/build.sh
```

Excluded words also lose their index links on song pages; the lyrics themselves
remain unchanged. Refresh your browser to see the rebuilt site.

## Check the build

After regenerating any JSON indexes affected by your changes, run the tests:

```sh
uv run python -m unittest discover -s tests -v
```

The tests check index generation, page ordering, and links throughout the site,
as well as whether the JSON indexes match the current lyrics.
