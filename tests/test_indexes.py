import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.index_common import KINDS, ROOT, build_index, contributors, dates, lyric_words, read_metadata


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.lyrics = self.root / "lyrics"
        self.lyrics.mkdir()
        self.write("001.txt", """Title: The Fountain
Collation: Fountain, The
Page: 10t
Tune Composer: Cooper, Wilson Marion (arranger); Walker, William
Tune Composition Date: 1850; 1902 (arrangement)
Alto Composer: Cooper, Wilson Marion
Alto Composition Date: 1902
Treble Composer: Rees, Henry Smith (Rev.)
Treble Composition Date: 1902
Bass Composer: Cooper, Wilson Marion
Bass Composition Date: 1902
Tenor Composer: Rees, Henry Smith
Tenor Composition Date: 1902
Lyrics: Watts, Isaac (1st, 2nd, & 4th Verses); Broaddus and Broaddus’ Collection (3rd Verse)
Lyrics Date: 1706 (verse 1 & chorus), 1707 (verses 2 & 3); c1772
Meter: Common Meter (8,6,8,6)
________________
Lyrics: This is a lyric, not metadata
Page: 999
""")
        self.write("002.txt", """Title: The Fountain
Collation: Fountain, The
Page: 2
Tune Composer: Cooper, Wilson Marion
Tune Composition Date: 1902
Lyrics: Watts, Isaac (Rev.) (Chorus)
Lyrics Date: 1707
Meter: Common Meter (8,6,8,6)
________________
Words
""")
        self.expected = {
            "titles": {"Fountain, The": ["2", "10t"]},
            "first_lines": {"Lyrics: This is a lyric, not metadata": ["10t"], "Words": ["2"]},
            "words": {"lyric": ["10t"], "lyrics": ["10t"], "metadata": ["10t"],
                      "page": ["10t"], "words": ["2"]},
            "lyrics": {"Broaddus and Broaddus’ Collection": ["10t"], "Watts, Isaac": ["2", "10t"]},
            "composers": {"Cooper, Wilson Marion": ["2", "10t"], "Rees, Henry Smith": ["10t"], "Walker, William": ["10t"]},
            "lyric_dates": {"1706": ["10t"], "1707": ["2", "10t"], "c1772": ["10t"]},
            "composition_dates": {"1850": ["10t"], "1902": ["2", "10t"]},
            "meters": {"Common Meter (8,6,8,6)": ["2", "10t"]},
        }

    def write(self, name, content):
        (self.lyrics / name).write_text(content, encoding="utf-8")

    def test_all_index_contents(self):
        for kind, expected in self.expected.items():
            with self.subTest(kind=kind):
                self.assertEqual(build_index(self.lyrics, kind), expected)

    def test_each_command_writes_utf8_json_from_any_directory(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                output = self.root / "out" / f"{kind}.json"
                subprocess.run([sys.executable, str(ROOT / "scripts" / f"{kind}.py"),
                                "--lyrics-dir", str(self.lyrics), "--output", str(output)],
                               cwd=self.root, check=True, capture_output=True, text=True)
                self.assertEqual(json.loads(output.read_text()), self.expected[kind])
                if kind == "lyrics":
                    self.assertIn("Broaddus’", output.read_text())

    def test_preserves_name_parentheses_initials_and_suffixes(self):
        self.assertEqual(contributors("Blackshear, Anna L. (Cooper) (Mrs.) (arranger); "
                                      "Chapin, (Amzi or Lucius); White, Benjamin Franklin, Jr.; "
                                      "W. M.; Smith, Samuel Francis (D. D.)"),
                         ["Blackshear, Anna L. (Cooper)", "Chapin, (Amzi or Lucius)",
                          "White, Benjamin Franklin, Jr.", "W. M.", "Smith, Samuel Francis"])

    def test_date_precision_and_calendar_dates(self):
        self.assertEqual(dates("July 15, 1927; 1779-80 (Verses); abt 1810-1830; "
                               "ca. 1913; c. 1600; 1706 (verse 1), 1707 (verses 2 & 3)"),
                         ["July 15, 1927", "1779-80", "abt 1810-1830", "ca. 1913",
                          "c. 1600", "1706", "1707"])

    def test_missing_optional_fields_and_duplicate_pages(self):
        self.write("003.txt", "Page: 2\nLyrics: Watts, Isaac\n________________\n")
        self.assertEqual(build_index(self.lyrics, "lyrics"), self.expected["lyrics"])
        self.assertEqual(build_index(self.lyrics, "titles"), self.expected["titles"])

    def test_page_collation_places_top_before_bottom(self):
        for page in ["10b", "2b", "10t", "2t", "2"]:
            self.write(f"page-{page}.txt", f"Page: {page}\nCollation: Page order\n________________\n")
        self.assertEqual(build_index(self.lyrics, "titles")["Page order"],
                         ["2", "2t", "2b", "10t", "10b"])

    def test_invalid_metadata_fails_with_filename(self):
        for content in ["Title: Missing page\n", "Page: 1\nPage: 2\n"]:
            self.write("bad.txt", content)
            with self.assertRaisesRegex(ValueError, "bad.txt"):
                read_metadata(self.lyrics / "bad.txt")

    def test_missing_input_directory(self):
        with self.assertRaises(FileNotFoundError):
            build_index(self.root / "missing", "titles")

    def test_word_normalization_and_common_word_filter(self):
        self.assertEqual(lyric_words("Hark! HARK, God, GOD’S, god's; heav’nly, heav'nly; "
                                    "ever-lasting Élan 123. The and thou thy I’ll can't Chorus:"),
                         {"hark", "god", "god’s", "heav’nly", "ever", "lasting", "élan"})

    def test_word_index_uses_only_lyrics_and_deduplicates_pages(self):
        self.write("003.txt", "Page: 2b\nTitle: Metadataonly\n________________\nHark, hark! Love\n")
        self.write("004.txt", "Page: 2t\nLyrics: Metadataonly\n________________\nHARK! love love\n")
        index = build_index(self.lyrics, "words")
        self.assertEqual(index["hark"], ["2t", "2b"])
        self.assertEqual(index["love"], ["2t", "2b"])
        self.assertNotIn("metadataonly", index)
        self.assertFalse(any(key != key.lower() for key in index))

    def test_first_lines_skip_blanks_and_merge_duplicate_openings(self):
        self.write("003.txt", "Page: 2b\n________________\n\n  Words  \nAnother line\n")
        self.write("004.txt", "Page: 2t\n________________\n\nWords\nDifferent verse\n")
        self.write("005.txt", "Page: 3\n________________\n\n  \n")
        self.assertEqual(build_index(self.lyrics, "first_lines"), {
            "Lyrics: This is a lyric, not metadata": ["10t"],
            "Words": ["2", "2t", "2b"],
        })

    def test_first_lines_require_a_lyrics_separator(self):
        self.write("bad.txt", "Page: 4\nTitle: Missing separator\n")
        with self.assertRaisesRegex(ValueError, "missing metadata/lyrics separator"):
            build_index(self.lyrics, "first_lines")

    def test_first_lines_trim_all_trailing_punctuation_and_merge_pages(self):
        for page, line in [("3b", "O, come; sing:"), ("3t", "O, come; sing,"),
                           ("4", "O, come; sing;"), ("5", "O, come; sing!"),
                           ("6", "O, come; sing?"), ("7", "O, come; sing."),
                           ("8", "O, come; sing!’"), ("9", "O, come; sing…"),
                           ("10", "O, come; sing — ")]:
            self.write(f"punctuation-{page}.txt", f"Page: {page}\n________________\n{line}\n")
        index = build_index(self.lyrics, "first_lines")
        self.assertEqual(index["O, come; sing"], ["3t", "3b", "4", "5", "6", "7", "8", "9", "10"])
        self.assertFalse(any(key.startswith("O, come; sing") and key != "O, come; sing" for key in index))

    def test_checked_in_indexes_match_collection(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                output = ROOT / "indexes" / f"{kind}.json"
                self.assertEqual(json.loads(output.read_text(encoding="utf-8")),
                                 build_index(ROOT / "lyrics", kind))


if __name__ == "__main__":
    unittest.main()
