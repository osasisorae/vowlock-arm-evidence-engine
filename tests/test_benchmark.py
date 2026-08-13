import json
import tempfile
import unittest
from pathlib import Path

from benchmark import BenchmarkFormatError, extract_metrics, load_rows, percent_change, summarize


class BenchmarkTests(unittest.TestCase):
    def test_extracts_prompt_and_generation_rows(self):
        rows = [
            {"n_prompt": 512, "n_gen": 0, "avg_ts": 100.0},
            {"n_prompt": 0, "n_gen": 128, "avg_ts": 20.0},
        ]
        self.assertEqual(
            {"prompt_tokens_per_second": 100.0, "generation_tokens_per_second": 20.0},
            extract_metrics(rows),
        )

    def test_rejects_missing_metric(self):
        with self.assertRaises(BenchmarkFormatError):
            extract_metrics([{"n_prompt": 512, "n_gen": 0, "avg_ts": 100.0}])

    def test_loads_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rows.jsonl"
            path.write_text('{"n_prompt": 1, "n_gen": 0, "avg_ts": 2}\n{"n_prompt": 0, "n_gen": 1, "avg_ts": 3}\n')
            self.assertEqual(2, len(load_rows(path)))

    def test_summarizes_relative_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.json"
            optimized = root / "optimized.json"
            baseline.write_text(json.dumps([
                {"n_prompt": 512, "n_gen": 0, "avg_ts": 100},
                {"n_prompt": 0, "n_gen": 128, "avg_ts": 20},
            ]))
            optimized.write_text(json.dumps([
                {"n_prompt": 512, "n_gen": 0, "avg_ts": 125},
                {"n_prompt": 0, "n_gen": 128, "avg_ts": 22},
            ]))
            result = summarize(baseline, optimized)
            self.assertEqual(25.0, result["change_percent"]["prompt_tokens_per_second"])
            self.assertAlmostEqual(10.0, result["change_percent"]["generation_tokens_per_second"])

    def test_percent_change_rejects_nonpositive_baseline(self):
        with self.assertRaises(BenchmarkFormatError):
            percent_change(0, 1)


if __name__ == "__main__":
    unittest.main()
