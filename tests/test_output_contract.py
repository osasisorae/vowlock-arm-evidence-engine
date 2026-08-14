import tempfile
import unittest
from pathlib import Path

from output_contract import OutputContractError, normalize_output, verify_outputs


class OutputContractTests(unittest.TestCase):
    def test_normalizes_only_surrounding_whitespace(self):
        self.assertEqual("READY", normalize_output(" \nREADY\r\n"))
        self.assertEqual("NOT  READY", normalize_output("NOT  READY"))

    def test_accepts_matching_expected_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.txt"
            optimized = root / "optimized.txt"
            baseline.write_text("READY\n", encoding="utf-8")
            optimized.write_text(" READY \n", encoding="utf-8")
            result = verify_outputs(baseline, optimized, "READY")
            self.assertTrue(result["equivalent"])
            self.assertTrue(result["contract_passed"])

    def test_rejects_two_matching_but_wrong_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.txt"
            optimized = root / "optimized.txt"
            baseline.write_text("NOT READY", encoding="utf-8")
            optimized.write_text("NOT READY", encoding="utf-8")
            with self.assertRaisesRegex(OutputContractError, "baseline output"):
                verify_outputs(baseline, optimized, "READY")

    def test_rejects_backend_divergence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.txt"
            optimized = root / "optimized.txt"
            baseline.write_text("READY", encoding="utf-8")
            optimized.write_text("WAIT", encoding="utf-8")
            with self.assertRaisesRegex(OutputContractError, "outputs differ"):
                verify_outputs(baseline, optimized, "READY")


if __name__ == "__main__":
    unittest.main()
