from html.parser import HTMLParser
from pathlib import Path
import shutil
import tempfile
import unittest
from urllib.parse import quote, unquote, urlsplit

from scripts.index_common import KINDS, ROOT
from scripts.site import (
    Templates,
    LABELS,
    build_site,
    display_source,
    entry_id,
    metadata_value,
    word_letter,
)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []
        self.ids = []
        self.lyric_text = []
        self.in_lyrics = False
        self.neighbors = {"prev": [], "next": []}
        self.word_targets = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "data-word" in attributes:
            self.word_targets.append(attributes)
        if tag == "a" and attributes.get("rel") in self.neighbors:
            self.neighbors[attributes["rel"]].append(attributes["href"])
        self.targets.extend(value for key, value in attrs if key in ("href", "src"))
        self.ids.extend(value for key, value in attrs if key == "id")
        if tag == "pre":
            self.in_lyrics = True

    def handle_endtag(self, tag):
        if tag == "pre":
            self.in_lyrics = False

    def handle_data(self, data):
        if self.in_lyrics:
            self.lyric_text.append(data)


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.lyrics = self.root / "lyrics"
        self.lyrics.mkdir()
        self.output = self.root / "docs"
        self.fragment_ids = {}
        for suffix in ("b", "t"):
            (self.lyrics / f"027{suffix}.txt").write_text(
                f"""Title: The <Fountain> & Life
Collation: <Fountain> & Life, The
Page: 27{suffix}
Tune Composer: Cowper, William (arranger)
Tune Composition Date: 1779
Lyrics: Cowper, William (1st Verse)
Lyrics Date: 1779
Meter: Common Meter (8,6,8,6)
________________
First line <script>alert("test")</script>
Second line

Another verse & more
""",
                encoding="utf-8",
            )

    def test_site_escapes_content_preserves_metadata_and_verses(self):
        self.assertEqual(build_site(self.lyrics, self.output), 2)
        song = (self.output / "songs/027t.html").read_text()
        self.assertIn("The &lt;Fountain&gt; &amp; Life", song)
        self.assertIn(">William Cowper</a> (1st Verse)", song)
        self.assertNotIn("<dt>Collation</dt>", song)
        self.assertIn(f'../titles.html#{entry_id("<Fountain> & Life, The")}', song)
        self.assertNotIn("<script>", song)
        parser = Links()
        parser.feed(song)
        self.assertEqual(
            "".join(parser.lyric_text),
            'First line <script>alert("test")</script>\nSecond line\n\nAnother verse & more',
        )
        titles = (self.output / "titles.html").read_text()
        self.assertLess(titles.index(">27t</a>"), titles.index(">27b</a>"))
        self.assertRegex(titles, r'>27t</a>,</span>\s+<span class="page-reference"><a ')
        self.assertIn('>27b</a></span>', titles)
        first_lines = (self.output / "first_lines.html").read_text()
        self.assertIn("First line &lt;script&gt;", first_lines)
        self.assertIn('href="songs/027t.html"', first_lines)
        self.assertIn('href="../first_lines.html"', song)

    def test_every_generated_local_link_resolves(self):
        build_site(self.lyrics, self.output)
        self.assertEqual(
            len(list(self.output.rglob("*.html"))), 2 + len(LABELS) + 1 + 26
        )
        for path in self.output.rglob("*.html"):
            links = Links()
            links.feed(path.read_text())
            for target in links.targets:
                self.assert_link_resolves(path, target)

    def assert_link_resolves(self, path, target):
        url = urlsplit(target)
        if url.scheme or url.netloc:
            return
        destination = path.parent / unquote(url.path) if url.path else path
        self.assertTrue(destination.is_file(), (path, target))
        if url.fragment:
            destination = destination.resolve()
            if destination not in self.fragment_ids:
                parser = Links()
                parser.feed(destination.read_text(encoding="utf-8"))
                self.fragment_ids[destination] = set(parser.ids)
            self.assertIn(
                unquote(url.fragment), self.fragment_ids[destination], (path, target)
            )

    def test_index_ids_are_unique_and_metadata_links_keep_annotations(self):
        build_site(self.lyrics, self.output)
        for kind in KINDS:
            if kind == "words":
                continue
            parser = Links()
            parser.feed((self.output / f"{kind}.html").read_text())
            self.assertTrue(parser.ids)
            self.assertEqual(len(parser.ids), len(set(parser.ids)))
        value = "Watts, Isaac (1st Verse); Newton, John (Rev.) (2nd Verse)"
        rendered = metadata_value("Lyrics", value, {})
        self.assertIn(f'../lyrics.html#{entry_id("Watts, Isaac")}', rendered)
        self.assertIn(f'../lyrics.html#{entry_id("Newton, John")}', rendered)
        self.assertIn("</a> (1st Verse); ", rendered)
        self.assertIn("</a> (Rev.) (2nd Verse)", rendered)
        rendered = metadata_value("Lyrics Date", "1706 (verse 1), 1707 (verse 2)", {})
        self.assertIn(f'../lyric_dates.html#{entry_id("1706")}', rendered)
        self.assertIn(f'../lyric_dates.html#{entry_id("1707")}', rendered)

    def test_word_index_letter_pages_and_lyric_links(self):
        build_site(self.lyrics, self.output)
        song = (self.output / "songs/027t.html").read_text()
        self.assertIn(f'../words/v.html#{entry_id("verse")}', song)
        self.assertNotIn(f'#{entry_id("more")}', song)
        words = (self.output / "words/v.html").read_text()
        self.assertIn(f'id="{entry_id("verse")}"', words)
        self.assertIn('href="../songs/027t.html?highlight=verse"', words)
        self.assertLess(words.index(">27t</a>"), words.index(">27b</a>"))
        for letter in "abcdefghijklmnopqrstuvwxyz":
            self.assertTrue((self.output / "words" / f"{letter}.html").is_file())
        self.assertEqual(word_letter("élan"), "e")
        self.assertEqual(word_letter("Ωmega"), "other")

    def test_word_index_uses_readable_highlight_queries_and_tags_matching_words(self):
        path = self.lyrics / "027t.txt"
        path.write_text(
            path.read_text() + "\nAngels angels angel ANGELS heav'nly heav’nly\n"
        )
        build_site(self.lyrics, self.output)
        parser = Links()
        parser.feed((self.output / "songs/027t.html").read_text())
        for word, count in [("angels", 3), ("angel", 1), ("heav’nly", 2)]:
            matches = [
                item for item in parser.word_targets if item["data-word"] == word
            ]
            self.assertEqual(len(matches), count)
            index = self.output / "words" / f"{word_letter(word)}.html"
            link = f"../songs/027t.html?highlight={quote(word, safe='')}"
            self.assertIn(link, index.read_text())
            self.assert_link_resolves(index, link)
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertIn(
            "Angels angels angel ANGELS heav'nly heav’nly", "".join(parser.lyric_text)
        )

    def test_readable_contributor_names_keep_collation_links(self):
        for field, kind in [
            ("Lyrics", "lyrics"),
            ("Tune Composer", "composers"),
            ("Alto Composer", "composers"),
            ("Treble Composer", "composers"),
            ("Bass Composer", "composers"),
            ("Tenor Composer", "composers"),
        ]:
            with self.subTest(field=field):
                rendered = metadata_value(
                    field, "Price, F. (arranger); Watts, Isaac (1st Verse)", {}
                )
                self.assertIn(
                    f'href="../{kind}.html#{entry_id("Price, F.")}">F. Price</a>',
                    rendered,
                )
                self.assertIn(
                    f'href="../{kind}.html#{entry_id("Watts, Isaac")}">Isaac Watts</a>',
                    rendered,
                )
                self.assertIn("</a> (arranger); ", rendered)
                self.assertIn("</a> (1st Verse)", rendered)

    def test_song_index_orders_pages_and_links_to_song_files(self):
        content = (self.lyrics / "027t.txt").read_text().replace("Page: 27t", "Page: 2")
        (self.lyrics / "002.txt").write_text(content)
        build_site(self.lyrics, self.output)
        song_index = (self.output / "songs.html").read_text()
        self.assertLess(
            song_index.index('href="songs/002.html"'),
            song_index.index('href="songs/027t.html"'),
        )
        self.assertLess(
            song_index.index('href="songs/027t.html"'),
            song_index.index('href="songs/027b.html"'),
        )
        self.assertIn(
            '<span class="song-page">27t</span> <span>The &lt;Fountain&gt; &amp; Life</span>',
            song_index,
        )
        self.assertIn('href="songs.html"', (self.output / "index.html").read_text())
        self.assertIn(
            f'../songs.html#{entry_id("27t")}',
            (self.output / "songs/027t.html").read_text(),
        )

    def test_display_names_preserve_sources_suffixes_and_uncertainty(self):
        examples = {
            "Blackshear, Anna L. (Cooper)": "Anna L. (Cooper) Blackshear",
            "White, Benjamin Franklin, Jr.": "Benjamin Franklin White, Jr.",
            "Chapin, (Amzi or Lucius)": "(Amzi or Lucius) Chapin",
            "Jackson, Judge": "Judge Jackson",
            "W. M.": "W. M.",
            "Hollyday": "Hollyday",
            "Sacred Harp, The": "The Sacred Harp",
            "Easy Instructor, Part II, The": "The Easy Instructor, Part II",
            "Wyeth’s Repository of Sacred Music, Part Second": "Wyeth’s Repository of Sacred Music, Part Second",
            "Broaddus and Broaddus’ Collection of Sacred Ballads": "Broaddus and Broaddus’ Collection of Sacred Ballads",
        }
        for key, label in examples.items():
            with self.subTest(key=key):
                self.assertEqual(display_source(key), label)

    def test_editable_templates_and_styles_are_used_on_each_build(self):
        templates = self.root / "templates"
        shutil.copytree(ROOT / "templates", templates)
        replacements = {
            "base.html": ("Back to top ↑", "Return to top"),
            "home.html": ("<h1>", "<h1>My song collection</h1><h1>"),
            "index.html": ("Browse the collection", "Explore this index"),
            "song.html": ("Song details</h2>", "About this song</h2>"),
            "words.html": ("Choose a letter", "Select a letter"),
            "word-letter.html": ("<h1>", '<h1 class="custom-letter">'),
        }
        for name, (before, after) in replacements.items():
            path = templates / name
            path.write_text(path.read_text().replace(before, after))
        (templates / "style.css").write_text("body { color: navy; }\n")
        build_site(self.lyrics, self.output, templates_dir=templates)
        for name, expected in [
            ("index.html", "My song collection"),
            ("titles.html", "Explore this index"),
            ("songs/027t.html", "About this song</h2>"),
            ("words.html", "Select a letter"),
            ("words/a.html", 'class="custom-letter"'),
        ]:
            content = (self.output / name).read_text()
            self.assertIn(expected, content)
            self.assertIn("Return to top", content)
        self.assertEqual(
            (self.output / "style.css").read_text(), "body { color: navy; }\n"
        )
        home = templates / "home.html"
        home.write_text(
            home.read_text().replace("My song collection", "Revised collection")
        )
        build_site(self.lyrics, self.output, templates_dir=templates)
        self.assertIn("Revised collection", (self.output / "index.html").read_text())

    def test_template_values_are_escaped_and_errors_name_the_file(self):
        templates = self.root / "templates"
        templates.mkdir()
        path = templates / "example.html"
        path.write_text("${title} ${body_html} $$")
        self.assertEqual(
            Templates(templates).render(
                "example.html", title='<script>"&', body_html="<p>Safe markup</p>"
            ),
            "&lt;script&gt;&quot;&amp; <p>Safe markup</p> $",
        )
        for content in ("${unknown}", "A literal $ needs escaping"):
            path.write_text(content)
            with self.assertRaisesRegex(ValueError, "example.html"):
                Templates(templates).render("example.html")

    def test_rebuild_is_deterministic(self):
        build_site(self.lyrics, self.output)
        before = {str(p): p.read_bytes() for p in self.output.rglob("*") if p.is_file()}
        build_site(self.lyrics, self.output)
        self.assertEqual(
            before,
            {str(p): p.read_bytes() for p in self.output.rglob("*") if p.is_file()},
        )

    def test_song_neighbors_follow_page_order_and_stop_at_boundaries(self):
        content = (self.lyrics / "027t.txt").read_text()
        for name, page in [("first.txt", "2"), ("last.txt", "28")]:
            (self.lyrics / name).write_text(
                content.replace("Page: 27t", f"Page: {page}")
            )
        build_site(self.lyrics, self.output)
        order = ["first.html", "027t.html", "027b.html", "last.html"]
        for position, filename in enumerate(order):
            parser = Links()
            parser.feed((self.output / "songs" / filename).read_text())
            self.assertEqual(
                parser.neighbors["prev"], [order[position - 1]] * 2 if position else []
            )
            self.assertEqual(
                parser.neighbors["next"],
                [order[position + 1]] * 2 if position + 1 < len(order) else [],
            )

    def test_duplicate_printed_page_is_rejected_before_writing(self):
        (self.lyrics / "copy.txt").write_text((self.lyrics / "027t.txt").read_text())
        with self.assertRaisesRegex(ValueError, "duplicate Page"):
            build_site(self.lyrics, self.output)
        self.assertFalse(self.output.exists())

    def test_complete_collection_builds_and_links_resolve(self):
        count = build_site(ROOT / "lyrics", self.output)
        self.assertEqual(count, len(list((ROOT / "lyrics").glob("*.txt"))))
        extra = int((self.output / "words/other.html").exists())
        self.assertEqual(
            len(list(self.output.rglob("*.html"))), count + len(LABELS) + 1 + 26 + extra
        )
        for path in self.output.rglob("*.html"):
            links = Links()
            links.feed(path.read_text(encoding="utf-8"))
            for target in links.targets:
                self.assert_link_resolves(path, target)
