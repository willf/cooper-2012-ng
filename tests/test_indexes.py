import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.index_common import KINDS, ROOT, build_index, contributors, dates, read_metadata


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

    def test_checked_in_indexes_match_collection(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                output = ROOT / "indexes" / f"{kind}.json"
                self.assertEqual(json.loads(output.read_text(encoding="utf-8")),
                                 build_index(ROOT / "lyrics", kind))


if __name__ == "__main__":
    unittest.main()
