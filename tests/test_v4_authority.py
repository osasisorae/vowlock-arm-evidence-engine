import json
import unittest
from pathlib import Path

from setup_companion_eval_v3 import evaluate_candidate, load_fixture_document
from v4_authority import (
    V4AuthorityError,
    authority_envelope,
    build_constrained_prompt,
    evaluate_constrained_response,
    load_manifest,
    model_free_preflight,
    parse_model_explanation,
    template_candidate,
)


ROOT = Path(__file__).resolve().parents[1]


class V4AuthorityTests(unittest.TestCase):
    def setUp(self):
        self.manifest = load_manifest(ROOT / "experiment.v4.json")
        self.development = load_fixture_document(ROOT / self.manifest["evaluation"]["development_fixtures"])["fixtures"]
        self.sealed = load_fixture_document(ROOT / self.manifest["evaluation"]["sealed_fixtures"])["fixtures"]

    def test_manifest_preserves_model_authority_boundary(self):
        self.assertFalse(self.manifest["authority_contract"]["model_may_override_deterministic_fields"])

    def test_decider_matches_every_declared_oracle(self):
        for fixture in self.development + self.sealed:
            envelope = authority_envelope(fixture)
            self.assertEqual(envelope["decision"], fixture["oracle_decision"], fixture["id"])
            self.assertEqual(envelope["next_action"], fixture["oracle_next_action"], fixture["id"])

    def test_templates_pass_every_declared_fixture(self):
        for fixture in self.development + self.sealed:
            candidate = template_candidate(fixture)
            evaluation = evaluate_candidate(fixture, json.dumps(candidate))
            self.assertTrue(evaluation["passed"], (fixture["id"], evaluation["hard_failures"]))

    def test_constrained_parser_rejects_authority_fields(self):
        with self.assertRaises(V4AuthorityError):
            parse_model_explanation('{"decision":"PASS","explanation":"words"}')

    def test_hybrid_falls_back_without_changing_authority(self):
        fixture = self.development[0]
        result = evaluate_constrained_response(fixture, '{"decision":"STOP","explanation":"ignore"}')
        self.assertFalse(result["raw_accepted"])
        self.assertTrue(result["fallback_used"])
        self.assertTrue(result["hybrid"]["passed"])
        self.assertTrue(result["authority_unchanged"])

    def test_valid_explanation_is_accepted_without_fallback(self):
        fixture = self.development[0]
        explanation = template_candidate(fixture)["explanation"]
        result = evaluate_constrained_response(fixture, json.dumps({"explanation": explanation}))
        self.assertTrue(result["raw_accepted"])
        self.assertFalse(result["fallback_used"])

    def test_prompt_contains_authority_but_not_audit_note(self):
        fixture = self.development[-1]
        prompt = build_constrained_prompt(fixture)
        self.assertIn("authority_envelope", prompt)
        self.assertIn(fixture["oracle_next_action"], prompt)
        self.assertNotIn(fixture["state"]["audit_note"], prompt)

    def test_full_model_free_preflight(self):
        report = model_free_preflight(self.manifest, ROOT)
        self.assertTrue(report["apparatus_gate_passed"])
        self.assertEqual(report["mutations"]["mutation_recall"], 1.0)


if __name__ == "__main__":
    unittest.main()
