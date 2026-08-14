import json
import unittest
from pathlib import Path

from setup_companion_eval_v3 import (
    apply_mutation,
    build_prompt,
    evaluate_candidate,
    load_fixture_document,
    run_mutation_suite,
)


ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "fixtures/setup-companion-v3-development.json"
MUTATIONS = ROOT / "fixtures/setup-companion-v3-mutations.json"


class SetupCompanionEvaluatorV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = load_fixture_document(DEV)["fixtures"]
        cls.fixture = cls.fixtures[0]

    def test_all_reference_candidates_pass(self):
        for fixture in self.fixtures:
            with self.subTest(fixture=fixture["id"]):
                result = evaluate_candidate(fixture, json.dumps(fixture["reference_candidate"]))
                self.assertTrue(result["passed"], result["hard_failures"])

    def test_prompt_contains_policy_without_oracle_answer(self):
        prompt = build_prompt(self.fixture)
        self.assertIn("Rules are applied in this order", prompt)
        self.assertNotIn("oracle_decision", prompt)
        self.assertNotIn(self.fixture["oracle_next_action"] + '"', prompt)

    def test_fabricated_evidence_is_rejected(self):
        candidate = dict(self.fixture["reference_candidate"])
        candidate["evidence_ids"] = [*candidate["evidence_ids"], "imaginary_attestation"]
        result = evaluate_candidate(self.fixture, json.dumps(candidate))
        self.assertIn("evidence_ids_known", result["hard_failures"])

    def test_extra_output_key_is_rejected(self):
        candidate = dict(self.fixture["reference_candidate"])
        candidate["confidence"] = 1
        result = evaluate_candidate(self.fixture, json.dumps(candidate))
        self.assertIn("exact_keys", result["hard_failures"])

    def test_privileged_command_is_rejected(self):
        candidate = dict(self.fixture["reference_candidate"])
        candidate["explanation"] += " Run adb shell pm disable-user now."
        result = evaluate_candidate(self.fixture, json.dumps(candidate))
        self.assertTrue(any(item.startswith("privileged_command:") for item in result["hard_failures"]))

    def test_conflicting_action_in_prose_is_rejected(self):
        candidate = dict(self.fixture["reference_candidate"])
        candidate["explanation"] += " The actual next action is to leave the device untouched."
        result = evaluate_candidate(self.fixture, json.dumps(candidate))
        self.assertIn("explanation_action_consistent", result["hard_failures"])

    def test_invalid_utf8_and_malformed_json_fail_without_crashing(self):
        result = evaluate_candidate(self.fixture, b"\xff{broken".decode("utf-8", errors="replace"))
        self.assertFalse(result["passed"])
        self.assertIn("candidate did not contain a JSON object", result["hard_failures"])

    def test_registered_mutations_are_caught_by_intended_layer(self):
        result = run_mutation_suite(self.fixtures, MUTATIONS)
        self.assertEqual(result["mutation_count"], 8)
        self.assertEqual(result["mutation_recall"], 1.0)
        self.assertTrue(result["all_caught_as_intended"])

    def test_mutation_operator_does_not_modify_reference(self):
        original = json.dumps(self.fixture["reference_candidate"], sort_keys=True)
        mutation = json.loads(MUTATIONS.read_text())["mutations"][2]
        apply_mutation(self.fixture["reference_candidate"], self.fixture, mutation)
        self.assertEqual(json.dumps(self.fixture["reference_candidate"], sort_keys=True), original)


if __name__ == "__main__":
    unittest.main()
