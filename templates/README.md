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
| `song.js` | Highlights all occurrences of the word selected in the word index |

The smaller templates control repeated pieces: `directory-item.html` for home
page directory rows, `song-item.html` for song directory rows, `index-list.html`
and `index-item.html` for index lists and rows, `page-link.html` for page-number
links, `nav-link.html` for header links, `letter-item.html` and `letter-link.html`
for the word directory and letter navigation, `word-label.html` for indexed
words, `empty-words.html` for empty letter pages, `metadata-field.html` for song
details, and `song-navigation.html`, `song-neighbor.html`, and
`song-unavailable.html` for previous/next song navigation.
In `page-link.html`, `${separator}` inserts a comma after each reference except
the last. Keep it inside the `page-reference` span with the link so Safari and
other browsers wrap between references instead of separating a comma from its
page number.

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

### Pocket guide styling

The design uses spaced lists, serif lyrics, and compact navigation, with no external
fonts or assets. In `style.css`, edit the variables at the top to change the
palette, `--measure` to change the maximum page width, and `--label-width` to
change the maximum width of the right-aligned index labels.
The desktop first-lines index has its own wider `--label-width` setting in
`.index-first_lines` and uses up to 48% of the content width for its labels.
Dark-mode colors are
in the `prefers-color-scheme: dark` block at the bottom; the browser follows the
reader’s system preference. Index rows use compact 32-pixel targets with
44-pixel targets on touchscreens. Navigation keeps at least 44 pixels of vertical
touch space. The mobile Songs/Words shortcuts are in `base.html`;
the large song page number is in `song.html`.

### Template syntax

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
| `index.html` | `kind`, `title`, `count`, `letters_html`, `entries_html` |
| `songs.html` | `count`, `entries_html` |
| `song.html` | `page`, `title`, `navigation_html`, `lyrics_html`, `metadata_html`, `bottom_navigation_html` |
| `words.html` | `count`, `letters_html` |
| `word-letter.html` | `title`, `letters_html`, `entries_html` |

Smaller templates show their available placeholders directly in their source.
Titles and first lines use `index-alphabet.html`, `index-letter.html`,
`index-letter-empty.html`, and `index-section.html` for A–Z jumps and letter
sections. Letters with no entries are shown without links.
`index-top.html` provides the “Top ↑” link beside each letter heading except A.
`index-label-link.html` makes their text a song link; when an entry has multiple pages, its text opens
the first song in page order and the individual page links select the others.
Opening punctuation and spaces are ignored when sorting and choosing the letter,
while the displayed text and existing entry IDs are preserved.
Keep `${prefix}` on shared local links in `base.html` so links work on nested
song and word pages. Keep the `main`, `top`, `lyrics`, and `details` IDs and the
`${id}` placeholders on index entries so existing navigation still works.
Keep `${lyrics_html}` immediately inside `<pre>` without adding indentation or
extra line breaks; whitespace there is displayed as part of the lyrics.
Word-index page links jump to the first matching lyric word and subtly highlight
every occurrence, including different capitalization. The highlight colors are
set by `--highlight` in `style.css` for light and dark mode. Keep the `song.js`
script link in `song.html` for this behavior. Links use a readable query string,
such as `songs/030a.html?highlight=angels`. Highlighting and scrolling require
JavaScript; the lyrics and their links remain available without it.

For a separate design, copy this entire folder and pass its location:

```sh
uv run scripts/site.py --templates-dir my-templates --output preview
```

Template paths default to this repository's `templates/` folder, regardless of
which directory you run the script from. Each build rereads the templates.
