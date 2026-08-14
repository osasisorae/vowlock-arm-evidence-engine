import json
import unittest
from pathlib import Path

from v3_runtime import (
    V3RuntimeError,
    final_gates,
    load_manifest,
    paired_result,
    pareto_policies,
    parse_sse_data,
    percentile,
    policy_id,
    select_development_policy,
)


ROOT = Path(__file__).resolve().parents[1]


def fixture_report(seconds, passed=True):
    records = []
    for index, value in enumerate(seconds):
        records.append({
            "fixture_id": f"fixture-{index}",
            "repetition": 1,
            "measurement": {"complete_seconds": value},
            "evaluation": {"passed": passed},
        })
    return {
        "all_passed": passed,
        "records": records,
        "latency": {
            "median_complete_valid_seconds": sorted(seconds)[len(seconds) // 2] if passed else None,
            "p95_complete_seconds": percentile(seconds, 0.95),
        },
    }


class V3RuntimeTests(unittest.TestCase):
    def test_registered_manifest_is_valid(self):
        manifest = load_manifest(ROOT / "experiment.v3.json")
        self.assertEqual(manifest["model"]["id"], "qwen2.5-1.5b-q4_0")

    def test_percentile_interpolates(self):
        self.assertEqual(percentile([1, 2, 3], 0.5), 2)
        self.assertAlmostEqual(percentile([1, 2], 0.95), 1.95)
        with self.assertRaises(V3RuntimeError):
            percentile([], 0.5)

    def test_sse_parser_accepts_data_and_done(self):
        self.assertEqual(parse_sse_data(b'data: {"content":"x"}\n'), {"content": "x"})
        self.assertIsNone(parse_sse_data("data: [DONE]"))
        self.assertIsNone(parse_sse_data("event: message"))

    def test_policy_identifier_is_stable(self):
        self.assertEqual(policy_id({"decode_threads": 2, "prompt_threads": 4, "physical_micro_batch": 128}), "t2-tb4-ub128")

    def test_pareto_rejects_dominated_policy(self):
        candidates = [
            {"policy": {"prompt_threads": 1, "physical_micro_batch": 64}, "prompt_seconds": 2, "peak_rss_kib": 100},
            {"policy": {"prompt_threads": 2, "physical_micro_batch": 128}, "prompt_seconds": 3, "peak_rss_kib": 110},
            {"policy": {"prompt_threads": 4, "physical_micro_batch": 512}, "prompt_seconds": 1, "peak_rss_kib": 130},
        ]
        retained = pareto_policies(candidates)
        self.assertEqual(len(retained), 2)

    def test_selection_rejects_fast_invalid_policy(self):
        invalid = {"policy": {"decode_threads": 1, "prompt_threads": 1, "physical_micro_batch": 64}, "peak_rss_kib": 90, "fixture_report": fixture_report([1], False)}
        valid = {"policy": {"decode_threads": 2, "prompt_threads": 2, "physical_micro_batch": 128}, "peak_rss_kib": 100, "fixture_report": fixture_report([2], True)}
        selected = select_development_policy([invalid, valid])
        self.assertEqual(selected["selected_policy_id"], "t2-tb2-ub128")

    def test_paired_result_requires_same_keys(self):
        baseline = fixture_report([10, 20])
        candidate = fixture_report([9])
        with self.assertRaises(V3RuntimeError):
            paired_result(baseline, candidate)

    def test_final_gate_passes_quality_gated_improvement(self):
        manifest = load_manifest(ROOT / "experiment.v3.json")
        baseline = fixture_report([10, 10])
        candidate = fixture_report([9, 9])
        result = final_gates(manifest, baseline, candidate, {"mutation_recall": 1.0})
        self.assertTrue(result["claim_passed"])
        self.assertEqual(result["paired"]["safe_fast_at_5"], 1.0)


if __name__ == "__main__":
    unittest.main()
