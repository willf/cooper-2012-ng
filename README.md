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
scripts rather than the generated HTML, which is overwritten on each build.

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
