import json
import tempfile
import unittest
from pathlib import Path

from v2_matrix import ManifestError, load_manifest, parse_elapsed, parse_gnu_time, percent_reduction


class V2MatrixTests(unittest.TestCase):
    def test_manifest_is_valid(self):
        manifest = load_manifest(Path("experiment.v2.json"))
        self.assertEqual("vowlock-arm-evidence-engine-v2", manifest["study_id"])

    def test_elapsed_parser_supports_minute_and_hour_forms(self):
        self.assertEqual(62.5, parse_elapsed("1:02.50"))
        self.assertEqual(3662.0, parse_elapsed("1:01:02"))

    def test_parses_gnu_time(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "time.txt"
            path.write_text("Elapsed (wall clock) time (h:mm:ss or m:ss): 0:03.25\nMaximum resident set size (kbytes): 123456\n")
            self.assertEqual(123456, parse_gnu_time(path)["peak_rss_kib"])
            self.assertEqual(3.25, parse_gnu_time(path)["cold_first_output_seconds"])

    def test_percent_reduction(self):
        self.assertEqual(50.0, percent_reduction(100, 50))
        with self.assertRaises(ManifestError):
            percent_reduction(0, 1)


if __name__ == "__main__":
    unittest.main()
