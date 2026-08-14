#!/usr/bin/env python3
"""Independent exhaustive invariants and mutation checks for Version 5."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from v5_compiler import (
    ACTION_TEXT,
    STATE_FIELDS,
    VARIANTS,
    canonical_bytes,
    compile_state,
    enumerate_states,
    evidence_clause,
    load_manifest,
    sha256,
)


def expected_authority(state: dict[str, Any]) -> tuple[str, str, list[str], list[str]]:
    terminal = [
        (state["device_class"] == "daily_use", "daily_use_device", "device_class"),
        (state["device_owner_active"] is True, "active_device_owner", "device_owner_active"),
        (state["device_certified"] is False, "certification_false", "device_certified"),
        (state["verifier_restored"] is False, "verifier_restoration_false", "verifier_restored"),
        (state["play_protect_scan"] == "failed", "play_protect_failed", "play_protect_scan"),
    ]
    matched = [(rule, evidence) for condition, rule, evidence in terminal if condition]
    if matched:
        return "STOP", "leave_device_untouched", [item[0] for item in matched], [item[1] for item in matched]
    missing = [
        (state["original_verifier_values_captured"] is not True, "missing_original_verifier_values", "original_verifier_values_captured", "capture_original_verifier_values"),
        (state["device_certified"] is not True, "missing_certification", "device_certified", "confirm_google_certification"),
        (state["verifier_restored"] is not True, "missing_verifier_restoration", "verifier_restored", "verify_verifier_restoration"),
        (state["play_protect_scan"] != "passed", "missing_play_protect_scan", "play_protect_scan", "run_play_protect_scan"),
        (state["reboot_persistence_checked"] is not True, "missing_reboot_persistence", "reboot_persistence_checked", "verify_reboot_persistence"),
    ]
    for condition, rule, evidence, action in missing:
        if condition:
            return "REQUEST_EVIDENCE", action, [rule], [evidence]
    return "PASS", "request_activation_consent", ["all_checks_pass"], list(STATE_FIELDS)


def verify_compiled(result: dict[str, Any]) -> list[str]:
    failures = []
    state = result.get("state")
    if not isinstance(state, dict) or tuple(state) != STATE_FIELDS:
        return ["state_shape"]
    expected_decision, expected_action, expected_rules, expected_evidence = expected_authority(state)
    authority = result.get("authority") if isinstance(result.get("authority"), dict) else {}
    checks = {
        "schema_version": result.get("schema_version") == "5.0",
        "variant": result.get("variant") in VARIANTS,
        "decision": authority.get("decision") == expected_decision,
        "next_action": authority.get("next_action") == expected_action,
        "decisive_rules": authority.get("decisive_rule_ids") == expected_rules,
        "decisive_evidence": authority.get("decisive_evidence_ids") == expected_evidence,
        "state_hash": result.get("canonical_state_sha256") == sha256(state),
        "state_id": result.get("state_id") == f"state-{sha256(state)[:16]}",
    }
    failures.extend(name for name, passed in checks.items() if not passed)
    without_hash = {key: copy.deepcopy(value) for key, value in result.items() if key != "compiled_output_sha256"}
    if result.get("compiled_output_sha256") != sha256(without_hash):
        failures.append("compiled_output_hash")

    variant = result.get("variant")
    rendering = result.get("rendering")
    decisive_clauses = [evidence_clause(field, state) for field in expected_evidence]
    if variant in {"B0", "D0"}:
        if not isinstance(rendering, str):
            failures.append("rendering_type")
        else:
            if ACTION_TEXT[expected_action] not in rendering:
                failures.append("rendering_action")
            if not all(clause in rendering for clause in decisive_clauses):
                failures.append("rendering_decisive_evidence")
            if variant == "D0" and not all(evidence_clause(field, state) in rendering for field in STATE_FIELDS):
                failures.append("rendering_complete_evidence")
    elif variant == "P0":
        if not isinstance(rendering, dict) or set(rendering) != {"summary", "why", "evidence", "next_step"}:
            failures.append("progressive_shape")
        else:
            if rendering["summary"] != f"Decision: {expected_decision}.":
                failures.append("progressive_summary")
            if rendering["next_step"] != ACTION_TEXT[expected_action]:
                failures.append("progressive_action")
            if not all(clause in rendering["why"] for clause in decisive_clauses):
                failures.append("progressive_decisive_evidence")
            evidence = rendering.get("evidence")
            if not isinstance(evidence, list) or [item.get("id") for item in evidence if isinstance(item, dict)] != list(STATE_FIELDS):
                failures.append("progressive_evidence_shape")
            elif any(item.get("value") != state[item["id"]] for item in evidence):
                failures.append("progressive_evidence_values")
    return sorted(set(failures))


def apply_mutation(base: dict[str, Any], mutation: str) -> dict[str, Any]:
    changed = copy.deepcopy(base)
    if mutation == "replace_decision":
        changed["authority"]["decision"] = "STOP" if changed["authority"]["decision"] != "STOP" else "PASS"
    elif mutation == "replace_next_action":
        changed["authority"]["next_action"] = "leave_device_untouched" if changed["authority"]["next_action"] != "leave_device_untouched" else "request_activation_consent"
    elif mutation == "remove_decisive_rule":
        changed["authority"]["decisive_rule_ids"] = []
    elif mutation == "replace_decisive_evidence_value":
        changed["rendering"]["evidence"][0]["value"] = "tampered"
    elif mutation == "remove_evidence_key":
        changed["rendering"]["evidence"].pop()
    elif mutation == "replace_state_id":
        changed["state_id"] = "state-tampered"
    elif mutation == "replace_canonical_state_sha256":
        changed["canonical_state_sha256"] = "0" * 64
    elif mutation == "replace_compiled_output_sha256":
        changed["compiled_output_sha256"] = "0" * 64
    else:
        raise ValueError(f"unknown mutation: {mutation}")
    return changed


def run_mutations(manifest: dict[str, Any], states: list[dict[str, Any]]) -> dict[str, Any]:
    pass_state = next(state for state in states if expected_authority(state)[0] == "PASS")
    base = compile_state(pass_state, "P0")
    rows = []
    for mutation in manifest["mutations"]:
        failures = verify_compiled(apply_mutation(base, mutation))
        rows.append({"mutation": mutation, "rejected": bool(failures), "failures": failures})
    return {
        "mutation_count": len(rows),
        "rejected_count": sum(row["rejected"] for row in rows),
        "mutation_recall": sum(row["rejected"] for row in rows) / len(rows),
        "rows": rows,
    }


def exhaustive_proof(manifest: dict[str, Any]) -> dict[str, Any]:
    states = list(enumerate_states(manifest))
    state_ids = [sha256(state) for state in states]
    decision_counts = {"PASS": 0, "STOP": 0, "REQUEST_EVIDENCE": 0}
    failures = []
    output_hashes = set()
    repeated_count = 0
    for state in states:
        for variant in VARIANTS:
            first = compile_state(state, variant)
            second = compile_state(state, variant)
            decision_counts[first["authority"]["decision"]] += 1 if variant == "B0" else 0
            checks = verify_compiled(first)
            if canonical_bytes(first) != canonical_bytes(second):
                checks.append("repeatability")
            else:
                repeated_count += 1
            output_hash = first["compiled_output_sha256"]
            if output_hash in output_hashes:
                checks.append("duplicate_compiled_output")
            output_hashes.add(output_hash)
            if checks:
                failures.append({"state_id": first["state_id"], "variant": variant, "failures": sorted(set(checks))})
    mutations = run_mutations(manifest, states)
    expected_states = manifest["hard_gates"]["state_count"]
    expected_outputs = expected_states * len(VARIANTS)
    invariant_pass_rate = (expected_outputs - len(failures)) / expected_outputs
    repeatability_rate = repeated_count / expected_outputs
    checks = {
        "state_count": len(states) == expected_states,
        "unique_states": len(set(state_ids)) == expected_states,
        "compiled_output_count": len(output_hashes) == expected_outputs,
        "all_invariants": not failures,
        "invariant_pass_rate": invariant_pass_rate == manifest["hard_gates"]["invariant_pass_rate"],
        "deterministic_repeatability_rate": repeatability_rate == manifest["hard_gates"]["deterministic_repeatability_rate"],
        "mutation_recall": mutations["mutation_recall"] == manifest["hard_gates"]["mutation_recall"],
    }
    return {
        "schema_version": "5.0",
        "state_count": len(states),
        "compiled_output_count": len(output_hashes),
        "decision_counts": decision_counts,
        "invariant_pass_rate": invariant_pass_rate,
        "deterministic_repeatability_rate": repeatability_rate,
        "checks": checks,
        "proof_passed": all(checks.values()),
        "failure_count": len(failures),
        "failures": failures,
        "mutations": mutations,
    }


def load_and_prove(manifest_path: Path) -> dict[str, Any]:
    return exhaustive_proof(load_manifest(manifest_path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Exhaustively verify the registered V5 finite domain.")
    parser.add_argument("--manifest", type=Path, default=Path("experiment.v5.json"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = load_and_prove(args.manifest)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["proof_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
