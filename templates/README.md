# Edit the website

Edit these source templates, then run `uv run scripts/site.py` from the repository
root. Your changes will appear in `docs/`. You can also run `./scripts/build.sh`
to rebuild the JSON indexes along with the website. Do not edit `docs/` directly:
its generated pages are overwritten when you rebuild.

Start with these files:

| File | Controls |
| --- | --- |
| `home.html` | The introduction on `docs/index.html` |
| `base.html` | The shared page shell: title, header, navigation, footer, stylesheet |
| `index.html` | Titles, first lines, contributors, dates, and meter index pages |
| `songs.html` | The song directory in page order |
| `song.html` | Each individual song page |
| `words.html` | The word index overview |
| `word-letter.html` | Each letter of the word index |
| `style.css` | Colors, fonts, spacing, responsive layout, and dark mode |

The smaller templates control repeated pieces: `directory-item.html` for home
page directory cards, `song-item.html` for song directory rows, `index-list.html`
and `index-item.html` for index lists and rows, `page-link.html` for page-number
links, `nav-link.html` for header links, `letter-item.html` and `letter-link.html`
for the word directory and letter navigation, `word-label.html` for indexed
words, `empty-words.html` for empty letter pages, `metadata-field.html` for song
details, and `song-navigation.html`, `song-neighbor.html`, and
`song-unavailable.html` for previous/next song navigation.

## Home page index descriptions

The text beneath each main index item, such as “Browse every song in page
order,” comes from the `descriptions` dictionary inside `build_site()` in
[scripts/site.py](../scripts/site.py). To change the Songs description, edit:

```python
"songs": "Browse every song in page order.",
```

The other index descriptions are in the same dictionary. The item labels
(“Songs,” “Titles,” and so on) come from the `LABELS` dictionary near the top
of that file. Counts are calculated automatically from the collection.

[directory-item.html](directory-item.html) controls the layout of these items,
using `${label}`, `${count}`, and `${description}` to insert their text.
After editing the descriptions or labels, rebuild from the repository root:

```sh
uv run scripts/site.py
```

## Placeholders

Templates are ordinary HTML with Python `string.Template` placeholders such as
`${title}`. Edit wording and HTML freely around them. For example, in `home.html`:

```html
<h1>A companion to the songs.</h1>
<p>Explore all ${song_count} songs in the Cooper Book.</p>
```

There are no template loops or conditionals: Python prepares repeated pieces and
inserts them into placeholders. Values are escaped for HTML automatically.
Placeholders ending in `_html` insert already-rendered HTML; keep these intact
when you want the corresponding content or links. Use `$$` for a literal dollar
sign in an HTML template. CSS is copied directly, so dollar signs in `style.css`
do not need escaping. Unknown placeholders or invalid dollar expressions cause
a build error naming the template.

| Template | Available placeholders |
| --- | --- |
| `base.html` | `title`, `prefix`, `nav_html`, `body_html` |
| `home.html` | `song_count`, `directory_html` |
| `index.html` | `title`, `count`, `entries_html` |
| `songs.html` | `count`, `entries_html` |
| `song.html` | `page`, `title`, `navigation_html`, `lyrics_html`, `metadata_html`, `bottom_navigation_html` |
| `words.html` | `count`, `letters_html` |
| `word-letter.html` | `title`, `letters_html`, `entries_html` |

Smaller templates show their available placeholders directly in their source.
Keep `${prefix}` on shared local links in `base.html` so links work on nested
song and word pages. Keep the `main`, `top`, `lyrics`, and `details` IDs and the
`${id}` placeholders on index entries so existing navigation still works.
Keep `${lyrics_html}` immediately inside `<pre>` without adding indentation or
extra line breaks; whitespace there is displayed as part of the lyrics.

For a separate design, copy this entire folder and pass its location:

```sh
uv run scripts/site.py --templates-dir my-templates --output preview
```

Template paths default to this repository's `templates/` folder, regardless of
which directory you run the script from. Each build rereads the templates.
