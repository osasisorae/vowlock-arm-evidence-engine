#!/usr/bin/env python3
"""Exhaustive proof and native Arm benchmark for the frozen Version 5 study."""

from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import statistics
import subprocess
import time
from pathlib import Path
from typing import Any

from v3_runtime import percentile
from v5_compiler import VARIANTS, canonical_bytes, compile_state, enumerate_states, load_manifest, serialized_size, sha256
from v5_proof import exhaustive_proof


def environment_record() -> dict[str, Any]:
    commands = {}
    for name, command in {"uname": ["uname", "-a"], "lscpu": ["lscpu"], "python": ["python3", "--version"]}.items():
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=20)
            commands[name] = (completed.stdout or completed.stderr).strip()
        except (FileNotFoundError, subprocess.SubprocessError) as error:
            commands[name] = f"unavailable: {error}"
    return {
        "machine": platform.machine(),
        "platform": platform.platform(),
        "logical_cpus": os.cpu_count(),
        "commands": commands,
    }


def peak_rss_kib() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value // 1024 if platform.system() == "Darwin" else value


def benchmark_compiler(manifest: dict[str, Any], *, warmup_rounds: int | None = None, measured_rounds: int | None = None) -> dict[str, Any]:
    states = list(enumerate_states(manifest))
    warmups = manifest["benchmark"]["warmup_complete_state_space_rounds"] if warmup_rounds is None else warmup_rounds
    rounds = manifest["benchmark"]["measured_complete_state_space_rounds"] if measured_rounds is None else measured_rounds
    order = manifest["benchmark"]["variant_order_per_round"]
    for _ in range(warmups):
        for variant in order:
            for state in states:
                compile_state(state, variant)

    round_times: dict[str, list[int]] = {variant: [] for variant in order}
    for _ in range(rounds):
        for variant in order:
            started = time.perf_counter_ns()
            for state in states:
                compile_state(state, variant)
            round_times[variant].append(time.perf_counter_ns() - started)

    variants = {}
    corpus_hashes = []
    for variant in order:
        outputs = [compile_state(state, variant) for state in states]
        sizes = [serialized_size(output) for output in outputs]
        corpus_hashes.extend(output["compiled_output_sha256"] for output in outputs)
        total_ns = sum(round_times[variant])
        output_count = len(states) * rounds
        variants[variant] = {
            "state_count": len(states),
            "measured_rounds": rounds,
            "measured_output_count": output_count,
            "total_nanoseconds": total_ns,
            "nanoseconds_per_output": total_ns / output_count,
            "outputs_per_second": output_count / (total_ns / 1_000_000_000),
            "round_latency": {
                "p50_nanoseconds": statistics.median(round_times[variant]),
                "p95_nanoseconds": percentile(round_times[variant], 0.95),
                "worst_nanoseconds": max(round_times[variant]),
            },
            "serialized_output_bytes": {
                "complete_state_space": sum(sizes),
                "minimum": min(sizes),
                "median": statistics.median(sizes),
                "maximum": max(sizes),
            },
        }
    return {
        "warmup_rounds": warmups,
        "measured_rounds": rounds,
        "measured_output_count": len(states) * rounds * len(order),
        "variant_order": order,
        "variants": variants,
        "compiled_corpus_sha256": sha256(corpus_hashes),
    }


def boundary_samples(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    samples = []
    seen = set()
    for state in enumerate_states(manifest):
        result = compile_state(state, "P0")
        decision = result["authority"]["decision"]
        if decision not in seen:
            samples.append(result)
            seen.add(decision)
        if len(seen) == 3:
            break
    return samples


def run(manifest: dict[str, Any], require_native_arm: bool) -> dict[str, Any]:
    environment = environment_record()
    if require_native_arm and environment["machine"].casefold() not in {"aarch64", "arm64"}:
        raise SystemExit(f"Refusing V5 native benchmark on {environment['machine']}")
    if require_native_arm and (environment["logical_cpus"] or 0) < manifest["host"]["minimum_logical_cpus"]:
        raise SystemExit("V5 native host exposes fewer than four logical CPUs")
    started = time.monotonic()
    proof_started = time.monotonic()
    proof = exhaustive_proof(manifest)
    proof_seconds = time.monotonic() - proof_started
    if not proof["proof_passed"]:
        return {"schema_version": "5.0", "status": "stopped-before-benchmark", "proof": proof, "environment": environment}
    benchmark_started = time.monotonic()
    benchmark = benchmark_compiler(manifest)
    benchmark_seconds = time.monotonic() - benchmark_started
    return {
        "schema_version": "5.0",
        "study_id": manifest["study_id"],
        "status": "complete",
        "environment": environment,
        "proof": proof,
        "benchmark": benchmark,
        "samples": boundary_samples(manifest),
        "resources": {
            "model_artifact_bytes": 0,
            "network_requests": 0,
            "process_peak_rss_kib": peak_rss_kib(),
            "proof_seconds": proof_seconds,
            "benchmark_seconds": benchmark_seconds,
            "total_seconds": time.monotonic() - started,
        },
        "claim_passed": proof["proof_passed"] and proof["mutations"]["mutation_recall"] == manifest["hard_gates"]["mutation_recall"],
        "boundaries": [manifest["claims"]["performance"], manifest["claims"]["human_boundary"], manifest["claims"]["formal_boundary"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("experiment.v5.json"))
    parser.add_argument("--output", type=Path, default=Path("results/v5/summary-ubuntu-22.04-arm.json"))
    parser.add_argument("--native-arm", action="store_true")
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    result = run(manifest, args.native_arm)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "claim_passed": result.get("claim_passed", False),
        "state_count": result.get("proof", {}).get("state_count"),
        "measured_output_count": result.get("benchmark", {}).get("measured_output_count"),
        "output": str(args.output),
    }, indent=2))
    return 0 if result.get("claim_passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
