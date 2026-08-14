#!/usr/bin/env python3
"""Version 4 measurement summaries and registered decision gates."""

from __future__ import annotations

import statistics
from typing import Any

from v3_runtime import percentile


def summarize_variant(records: list[dict[str, Any]], variant: str) -> dict[str, Any]:
    rows = [record["variants"][variant] for record in records]
    complete = [float(row["complete_seconds"]) for row in rows]
    ttft = [float(row["ttft_seconds"]) for row in rows if isinstance(row.get("ttft_seconds"), (int, float))]
    return {
        "variant": variant,
        "record_count": len(rows),
        "passed_count": sum(bool(row["passed"]) for row in rows),
        "valid_rate": sum(bool(row["passed"]) for row in rows) / len(rows),
        "authority_accuracy": sum(bool(row["authority_correct"]) for row in rows) / len(rows),
        "fallback_count": sum(bool(row.get("fallback_used")) for row in rows),
        "fallback_rate": sum(bool(row.get("fallback_used")) for row in rows) / len(rows),
        "latency": {
            "median_complete_seconds": statistics.median(complete),
            "p95_complete_seconds": percentile(complete, 0.95),
            "worst_complete_seconds": max(complete),
            "median_ttft_seconds": statistics.median(ttft) if ttft else None,
        },
    }


def summarize_split(split: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "4.0",
        "split": split,
        "fixture_count": len(records),
        "variants": {variant: summarize_variant(records, variant) for variant in ("F0", "T0", "M0", "H0")},
        "records": records,
    }


def registered_decision(manifest: dict[str, Any], preflight: dict[str, Any], development: dict[str, Any], sealed: dict[str, Any]) -> dict[str, Any]:
    threshold = 0.8
    hybrid_valid = sealed["variants"]["H0"]["valid_rate"]
    mutation_recall = preflight["mutations"]["mutation_recall"]
    raw_acceptance = sealed["variants"]["M0"]["valid_rate"]
    checks = {
        "apparatus_gate": preflight["apparatus_gate_passed"],
        "development_hybrid_valid": development["variants"]["H0"]["valid_rate"] == 1.0,
        "sealed_hybrid_valid": hybrid_valid == manifest["hard_gates"]["hybrid_valid_output_rate"],
        "authority_mutations_caught": mutation_recall == manifest["hard_gates"]["authority_mutation_recall"],
        "sealed_authority_immutable": sealed["variants"]["H0"]["authority_accuracy"] == 1.0,
    }
    architecture_safe_for_further_study = all(checks.values())
    model_eligible_for_human_study = architecture_safe_for_further_study and raw_acceptance >= threshold
    return {
        "checks": checks,
        "architecture_safe_for_further_study": architecture_safe_for_further_study,
        "raw_model_acceptance": raw_acceptance,
        "registered_model_threshold": threshold,
        "model_eligible_for_human_study": model_eligible_for_human_study,
        "model_preferred": False,
        "retained_default": "T0",
        "reason": "Automatic evidence cannot establish a comprehension advantage. Retain the deterministic template unless a separately registered blinded human study justifies the model.",
    }
