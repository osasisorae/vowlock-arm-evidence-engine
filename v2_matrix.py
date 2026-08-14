#!/usr/bin/env python3
"""Manifest utilities and evidence aggregation for the Version 2 Arm matrix."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from benchmark import extract_metrics, load_rows


class ManifestError(ValueError):
    pass


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != "2.0":
        raise ManifestError("manifest must be a Version 2 object")
    models = value.get("models")
    workloads = value.get("workloads")
    hosts = value.get("arm_hosts")
    if not isinstance(models, list) or len(models) < 3:
        raise ManifestError("at least three model/quantization conditions are required")
    if not isinstance(workloads, list) or len(workloads) < 3:
        raise ManifestError("at least three workloads are required")
    if not isinstance(hosts, list) or len(hosts) < 2:
        raise ManifestError("at least two Arm host-image conditions are required")
    for model in models:
        sha = model.get("sha256", "")
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ManifestError(f"invalid SHA-256 for {model.get('id')}")
        if not model.get("runtime_variants"):
            raise ManifestError(f"missing runtime variants for {model.get('id')}")
    return value


def plans(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "model_id": model["id"],
            "runtime": runtime,
            "workload_id": workload["id"],
            "prompt_tokens": workload["prompt_tokens"],
            "generation_tokens": workload["generation_tokens"],
            "repetitions": workload["repetitions"],
        }
        for model in manifest["models"]
        for runtime in model["runtime_variants"]
        for workload in manifest["workloads"]
    ]


def parse_elapsed(value: str) -> float:
    parts = value.strip().split(":")
    try:
        numbers = [float(part) for part in parts]
    except ValueError as error:
        raise ManifestError(f"invalid elapsed time: {value}") from error
    if len(numbers) == 2:
        return numbers[0] * 60 + numbers[1]
    if len(numbers) == 3:
        return numbers[0] * 3600 + numbers[1] * 60 + numbers[2]
    raise ManifestError(f"invalid elapsed time: {value}")


def parse_gnu_time(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    rss_match = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", text)
    elapsed_match = re.search(r"Elapsed \(wall clock\) time .*?:\s*([0-9:.]+)", text)
    if not rss_match or not elapsed_match:
        raise ManifestError(f"missing GNU time metrics in {path}")
    return {
        "peak_rss_kib": int(rss_match.group(1)),
        "cold_first_output_seconds": parse_elapsed(elapsed_match.group(1)),
        "cold_first_output_definition": "fresh-process wall time through one deterministic generated token; proxy, not server TTFT",
    }


def energy_snapshot(root: Path = Path("/sys/class/powercap")) -> dict[str, Any]:
    counters = []
    if root.exists():
        for path in sorted(root.glob("**/energy_uj")):
            try:
                counters.append({"path": str(path), "energy_uj": int(path.read_text().strip())})
            except (OSError, ValueError):
                continue
    return {
        "available": bool(counters),
        "unit": "microjoules",
        "counters": counters,
        "checked_root": str(root),
    }


def percent_reduction(before: float, after: float) -> float:
    if before <= 0:
        raise ManifestError("comparison baseline must be positive")
    return (1 - after / before) * 100


def summarize(manifest: dict[str, Any], raw_root: Path, host: str) -> dict[str, Any]:
    records = []
    for plan in plans(manifest):
        base = raw_root / host / plan["model_id"] / plan["runtime"]
        benchmark_path = base / f"{plan['workload_id']}.json"
        if not benchmark_path.exists():
            raise ManifestError(f"missing benchmark evidence: {benchmark_path}")
        records.append({**plan, **extract_metrics(load_rows(benchmark_path))})

    resources = {}
    semantics = {}
    for model in manifest["models"]:
        for runtime in model["runtime_variants"]:
            condition = f"{model['id']}--{runtime}"
            resource_path = raw_root / host / model["id"] / runtime / "resource.json"
            if not resource_path.exists():
                raise ManifestError(f"missing resource evidence: {resource_path}")
            resources[condition] = json.loads(resource_path.read_text(encoding="utf-8"))
            semantic_path = raw_root / host / model["id"] / runtime / "semantic.json"
            if semantic_path.exists():
                semantics[condition] = json.loads(semantic_path.read_text(encoding="utf-8"))

    q8 = resources["qwen2.5-1.5b-q8_0--baseline"]
    q4 = resources["qwen2.5-1.5b-q4_0--baseline"]
    all_semantics_pass = bool(semantics) and all(item.get("all_passed") for item in semantics.values())
    size_reduction = percent_reduction(q8["artifact_bytes"], q4["artifact_bytes"])
    rss_reduction = percent_reduction(q8["peak_rss_kib"], q4["peak_rss_kib"])
    return {
        "schema_version": "2.0",
        "study_id": manifest["study_id"],
        "host": host,
        "separate_from": manifest["separation"]["prior_study"],
        "performance": records,
        "resources": resources,
        "semantics": semantics,
        "quantization_comparison": {
            "artifact_size_reduction_percent": size_reduction,
            "peak_rss_reduction_percent": rss_reduction,
            "all_available_semantic_checks_passed": all_semantics_pass,
            "registered_claim_threshold_percent": 20,
            "registered_claim_passed": size_reduction >= 20 and rss_reduction >= 20 and all_semantics_pass,
        },
    }


def write_json(value: Any, output: Path | None = None) -> None:
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("experiment.v2.json"))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    subparsers.add_parser("models-tsv")
    subparsers.add_parser("workloads-tsv")
    subparsers.add_parser("plan")
    power_parser = subparsers.add_parser("energy-snapshot")
    power_parser.add_argument("--root", type=Path, default=Path("/sys/class/powercap"))
    power_parser.add_argument("--output", type=Path)
    time_parser = subparsers.add_parser("parse-time")
    time_parser.add_argument("path", type=Path)
    time_parser.add_argument("--artifact", type=Path, required=True)
    time_parser.add_argument("--energy-before", type=Path)
    time_parser.add_argument("--energy-after", type=Path)
    time_parser.add_argument("--output", type=Path)
    summary_parser = subparsers.add_parser("summarize")
    summary_parser.add_argument("raw_root", type=Path)
    summary_parser.add_argument("--host", required=True)
    summary_parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    if args.command == "validate":
        write_json({"valid": True, "study_id": manifest["study_id"], "condition_count": len(plans(manifest))})
    elif args.command == "models-tsv":
        for model in manifest["models"]:
            print("\t".join([model["id"], model["filename"], model["url"], model["sha256"], str(model["bytes"]), ",".join(model["runtime_variants"])]))
    elif args.command == "workloads-tsv":
        for workload in manifest["workloads"]:
            print("\t".join([workload["id"], str(workload["prompt_tokens"]), str(workload["generation_tokens"]), str(workload["repetitions"])]))
    elif args.command == "plan":
        write_json(plans(manifest))
    elif args.command == "energy-snapshot":
        write_json(energy_snapshot(args.root), args.output)
    elif args.command == "parse-time":
        value = {**parse_gnu_time(args.path), "artifact_bytes": args.artifact.stat().st_size}
        if args.energy_before and args.energy_after:
            before = json.loads(args.energy_before.read_text(encoding="utf-8"))
            after = json.loads(args.energy_after.read_text(encoding="utf-8"))
            before_by_path = {item["path"]: item["energy_uj"] for item in before.get("counters", [])}
            deltas = [
                {"path": item["path"], "energy_delta_uj": item["energy_uj"] - before_by_path[item["path"]]}
                for item in after.get("counters", [])
                if item["path"] in before_by_path and item["energy_uj"] >= before_by_path[item["path"]]
            ]
            value["power"] = {"available": bool(deltas), "energy_deltas": deltas, "note": "Unavailable means no readable monotonic powercap counter was exposed; no estimate was substituted."}
        write_json(value, args.output)
    elif args.command == "summarize":
        write_json(summarize(manifest, args.raw_root, args.host), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
