import unittest
from pathlib import Path

from v4_authority import load_manifest
from v4_runtime import registered_decision, summarize_split


ROOT = Path(__file__).resolve().parents[1]


def row(f0=False, m0=True, fallback=False):
    base = {"complete_seconds": 1.0, "ttft_seconds": 0.5, "fallback_used": False, "authority_correct": True}
    return {
        "fixture_id": "x",
        "variants": {
            "F0": base | {"passed": f0},
            "T0": base | {"passed": True, "complete_seconds": 0.001, "ttft_seconds": 0.001},
            "M0": base | {"passed": m0},
            "H0": base | {"passed": True, "fallback_used": fallback},
        },
    }


class V4RuntimeTests(unittest.TestCase):
    def test_split_summary_keeps_fallback_rate(self):
        report = summarize_split("test", [row(m0=False, fallback=True), row()])
        self.assertEqual(report["variants"]["H0"]["fallback_rate"], 0.5)
        self.assertEqual(report["variants"]["M0"]["valid_rate"], 0.5)

    def test_registered_decision_never_prefers_model_automatically(self):
        manifest = load_manifest(ROOT / "experiment.v4.json")
        split = summarize_split("test", [row(), row()])
        preflight = {"apparatus_gate_passed": True, "mutations": {"mutation_recall": 1.0}}
        decision = registered_decision(manifest, preflight, split, split)
        self.assertTrue(decision["model_eligible_for_human_study"])
        self.assertFalse(decision["model_preferred"])
        self.assertEqual(decision["retained_default"], "T0")


if __name__ == "__main__":
    unittest.main()
