#!/usr/bin/env python3
"""Deterministic, provenance-preserving explanation compiler for Version 5."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "5.0"
STATE_FIELDS = (
    "device_class",
    "device_certified",
    "original_verifier_values_captured",
    "verifier_restored",
    "reboot_persistence_checked",
    "play_protect_scan",
    "device_owner_active",
)
VARIANTS = ("B0", "D0", "P0")
EXPECTED_DOMAIN = {
    "device_class": ["resettable_test", "daily_use"],
    "device_certified": [True, False, "unknown"],
    "original_verifier_values_captured": [True, False],
    "verifier_restored": [True, False, "unknown"],
    "reboot_persistence_checked": [True, False, "unknown"],
    "play_protect_scan": ["passed", "failed", "not_run"],
    "device_owner_active": [True, False],
}
ACTION_TEXT = {
    "request_activation_consent": "Request activation consent only.",
    "leave_device_untouched": "Leave the device untouched.",
    "capture_original_verifier_values": "Capture the original verifier values.",
    "confirm_google_certification": "Confirm Google certification.",
    "verify_verifier_restoration": "Verify verifier restoration.",
    "run_play_protect_scan": "Run the Play Protect scan.",
    "verify_reboot_persistence": "Verify reboot persistence.",
}
FIELD_LABELS = {
    "device_class": "device class",
    "device_certified": "device certification",
    "original_verifier_values_captured": "original verifier values captured",
    "verifier_restored": "verifier restoration",
    "reboot_persistence_checked": "reboot persistence",
    "play_protect_scan": "Play Protect status",
    "device_owner_active": "device owner active",
}
RULE_TO_EVIDENCE = {
    "daily_use_device": "device_class",
    "active_device_owner": "device_owner_active",
    "certification_false": "device_certified",
    "verifier_restoration_false": "verifier_restored",
    "play_protect_failed": "play_protect_scan",
    "missing_original_verifier_values": "original_verifier_values_captured",
    "missing_certification": "device_certified",
    "missing_verifier_restoration": "verifier_restored",
    "missing_play_protect_scan": "play_protect_scan",
    "missing_reboot_persistence": "reboot_persistence_checked",
}


class V5CompilerError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _is_registered_value(value: Any, allowed: list[Any]) -> bool:
    """Keep JSON booleans distinct from integers such as 0 and 1."""
    return any(type(value) is type(candidate) and value == candidate for candidate in allowed)


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise V5CompilerError("manifest must be a Version 5 object")
    if value.get("status") != "pre-registered-before-implementation-and-execution":
        raise V5CompilerError("manifest is not the frozen pre-registration")
    if tuple(value.get("state_space", {}).keys()) != STATE_FIELDS + ("expected_cartesian_states",):
        raise V5CompilerError("registered state-space fields or order changed")
    for field in STATE_FIELDS:
        if value["state_space"][field] != EXPECTED_DOMAIN[field]:
            raise V5CompilerError(f"registered values changed: {field}")
    if tuple(item.get("id") for item in value.get("variants", [])) != VARIANTS:
        raise V5CompilerError("registered compiler variants changed")
    expected = value["state_space"]["expected_cartesian_states"]
    actual = 1
    for field in STATE_FIELDS:
        actual *= len(value["state_space"][field])
    if expected != 648 or actual != expected:
        raise V5CompilerError(f"registered state count changed: {actual} != {expected}")
    return value


def enumerate_states(manifest: dict[str, Any]) -> Iterable[dict[str, Any]]:
    values = [manifest["state_space"][field] for field in STATE_FIELDS]
    for combination in itertools.product(*values):
        yield dict(zip(STATE_FIELDS, combination, strict=True))


def value_text(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value).replace("_", "-")


def evidence_clause(field: str, state: dict[str, Any]) -> str:
    return f"{FIELD_LABELS[field]} is {value_text(state[field])}"


def classify_state(state: dict[str, Any]) -> dict[str, Any]:
    terminal_rules = []
    if state["device_class"] == "daily_use":
        terminal_rules.append("daily_use_device")
    if state["device_owner_active"] is True:
        terminal_rules.append("active_device_owner")
    if state["device_certified"] is False:
        terminal_rules.append("certification_false")
    if state["verifier_restored"] is False:
        terminal_rules.append("verifier_restoration_false")
    if state["play_protect_scan"] == "failed":
        terminal_rules.append("play_protect_failed")
    if terminal_rules:
        return {
            "decision": "STOP",
            "next_action": "leave_device_untouched",
            "decisive_rule_ids": terminal_rules,
            "decisive_evidence_ids": [RULE_TO_EVIDENCE[rule] for rule in terminal_rules],
        }

    missing_checks = (
        (state["original_verifier_values_captured"] is not True, "missing_original_verifier_values", "capture_original_verifier_values"),
        (state["device_certified"] is not True, "missing_certification", "confirm_google_certification"),
        (state["verifier_restored"] is not True, "missing_verifier_restoration", "verify_verifier_restoration"),
        (state["play_protect_scan"] != "passed", "missing_play_protect_scan", "run_play_protect_scan"),
        (state["reboot_persistence_checked"] is not True, "missing_reboot_persistence", "verify_reboot_persistence"),
    )
    for missing, rule, action in missing_checks:
        if missing:
            return {
                "decision": "REQUEST_EVIDENCE",
                "next_action": action,
                "decisive_rule_ids": [rule],
                "decisive_evidence_ids": [RULE_TO_EVIDENCE[rule]],
            }

    return {
        "decision": "PASS",
        "next_action": "request_activation_consent",
        "decisive_rule_ids": ["all_checks_pass"],
        "decisive_evidence_ids": list(STATE_FIELDS),
    }


def _reason_text(state: dict[str, Any], authority: dict[str, Any]) -> str:
    return "; ".join(evidence_clause(field, state) for field in authority["decisive_evidence_ids"])


def render_brief(state: dict[str, Any], authority: dict[str, Any]) -> str:
    return f"{ACTION_TEXT[authority['next_action']]} Reason: {_reason_text(state, authority)}."


def render_detailed(state: dict[str, Any], authority: dict[str, Any]) -> str:
    full = "; ".join(evidence_clause(field, state) for field in STATE_FIELDS)
    return f"{ACTION_TEXT[authority['next_action']]} Decisive evidence: {_reason_text(state, authority)}. Full evidence: {full}."


def render_progressive(state: dict[str, Any], authority: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": f"Decision: {authority['decision']}.",
        "why": f"Decisive evidence: {_reason_text(state, authority)}.",
        "evidence": [{"id": field, "label": FIELD_LABELS[field], "value": state[field], "rendered_value": value_text(state[field])} for field in STATE_FIELDS],
        "next_step": ACTION_TEXT[authority["next_action"]],
    }


def compile_state(state: dict[str, Any], variant: str) -> dict[str, Any]:
    if set(state) != set(STATE_FIELDS):
        raise V5CompilerError("state fields do not match the registered domain")
    normalized = {field: state[field] for field in STATE_FIELDS}
    for field, value in normalized.items():
        if not _is_registered_value(value, EXPECTED_DOMAIN[field]):
            raise V5CompilerError(f"state value is outside the registered domain: {field}={value!r}")
    if variant not in VARIANTS:
        raise V5CompilerError(f"unknown compiler variant: {variant}")
    state = normalized
    authority = classify_state(state)
    state_hash = sha256(state)
    if variant == "B0":
        rendering: Any = render_brief(state, authority)
    elif variant == "D0":
        rendering = render_detailed(state, authority)
    else:
        rendering = render_progressive(state, authority)
    result = {
        "schema_version": SCHEMA_VERSION,
        "variant": variant,
        "state_id": f"state-{state_hash[:16]}",
        "canonical_state_sha256": state_hash,
        "state": dict(state),
        "authority": authority,
        "rendering": rendering,
    }
    result["compiled_output_sha256"] = sha256(result)
    return result


def serialized_size(result: dict[str, Any]) -> int:
    return len(canonical_bytes(result))


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile one typed Setup Companion state without a language model.")
    parser.add_argument("state", type=Path, help="JSON object containing the seven registered state fields")
    parser.add_argument("--variant", choices=VARIANTS, default="P0")
    parser.add_argument("--manifest", type=Path, default=Path("experiment.v5.json"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    load_manifest(args.manifest)
    state = json.loads(args.state.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise V5CompilerError("state file must contain one JSON object")
    compiled = compile_state(state, args.variant)
    rendered = json.dumps(compiled, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
