import copy
import unittest
from pathlib import Path

from v5_benchmark import benchmark_compiler
from v5_compiler import STATE_FIELDS, VARIANTS, V5CompilerError, compile_state, enumerate_states, load_manifest
from v5_proof import apply_mutation, exhaustive_proof, verify_compiled


ROOT = Path(__file__).resolve().parents[1]


class V5CompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest(ROOT / "experiment.v5.json")
        cls.states = list(enumerate_states(cls.manifest))

    def test_registered_domain_has_exactly_648_unique_states(self):
        self.assertEqual(len(self.states), 648)
        self.assertEqual(len({tuple(state.items()) for state in self.states}), 648)

    def test_pass_is_one_exact_state(self):
        passed = [state for state in self.states if compile_state(state, "B0")["authority"]["decision"] == "PASS"]
        self.assertEqual(len(passed), 1)
        self.assertEqual(tuple(passed[0]), STATE_FIELDS)

    def test_all_renderings_verify_for_boundary_states(self):
        decisions = {}
        for state in self.states:
            decision = compile_state(state, "B0")["authority"]["decision"]
            decisions.setdefault(decision, state)
        self.assertEqual(set(decisions), {"PASS", "STOP", "REQUEST_EVIDENCE"})
        for state in decisions.values():
            for variant in VARIANTS:
                self.assertEqual(verify_compiled(compile_state(state, variant)), [])

    def test_same_state_compiles_to_same_bytes_and_hash(self):
        state = self.states[0]
        self.assertEqual(compile_state(state, "P0"), compile_state(copy.deepcopy(state), "P0"))
        self.assertEqual(compile_state(dict(reversed(list(state.items()))), "P0"), compile_state(state, "P0"))

    def test_near_states_outside_the_typed_domain_are_rejected(self):
        state = copy.deepcopy(self.states[0])
        state["device_certified"] = 1
        with self.assertRaises(V5CompilerError):
            compile_state(state, "P0")
        state = copy.deepcopy(self.states[0])
        state["device_class"] = "emulator"
        with self.assertRaises(V5CompilerError):
            compile_state(state, "P0")
        state = copy.deepcopy(self.states[0])
        state["unregistered_field"] = True
        with self.assertRaises(V5CompilerError):
            compile_state(state, "P0")

    def test_each_registered_mutation_is_rejected(self):
        pass_state = next(state for state in self.states if compile_state(state, "P0")["authority"]["decision"] == "PASS")
        base = compile_state(pass_state, "P0")
        for mutation in self.manifest["mutations"]:
            self.assertTrue(verify_compiled(apply_mutation(base, mutation)), mutation)

    def test_exhaustive_proof_passes(self):
        report = exhaustive_proof(self.manifest)
        self.assertTrue(report["proof_passed"])
        self.assertEqual(report["state_count"], 648)
        self.assertEqual(report["compiled_output_count"], 1944)
        self.assertEqual(report["decision_counts"], {"PASS": 1, "STOP": 600, "REQUEST_EVIDENCE": 47})

    def test_small_benchmark_records_all_variants(self):
        report = benchmark_compiler(self.manifest, warmup_rounds=0, measured_rounds=1)
        self.assertEqual(report["measured_output_count"], 1944)
        self.assertEqual(set(report["variants"]), set(VARIANTS))
        self.assertTrue(all(row["outputs_per_second"] > 0 for row in report["variants"].values()))


if __name__ == "__main__":
    unittest.main()
