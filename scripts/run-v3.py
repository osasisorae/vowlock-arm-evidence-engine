#!/usr/bin/env python3
"""Execute the frozen Version 3 study on a prepared native Arm host."""

from __future__ import annotations

import argparse
import json
import os
import platform
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark import extract_metrics, load_rows  # noqa: E402
from setup_companion_eval_v3 import (  # noqa: E402
    build_prompt,
    evaluate_candidate,
    load_fixture_document,
    run_mutation_suite,
)
from v3_runtime import (  # noqa: E402
    final_gates,
    load_manifest,
    paired_result,
    pareto_policies,
    policy_id,
    run_fixture_suite,
    run_probe_suite,
    select_development_policy,
    static_policy,
    summarize_fixture_records,
)


def write_json(value: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def free_port() -> int:
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        return int(server.getsockname()[1])


def peak_rss_kib(pid: int) -> int | None:
    path = Path(f"/proc/{pid}/status")
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("VmHWM:"):
            parts = line.split()
            return int(parts[1]) if len(parts) >= 2 else None
    return None


class ServerSession:
    def __init__(self, server_bin: Path, model: Path, policy: dict[str, int], log_path: Path):
        self.server_bin = server_bin
        self.model = model
        self.policy = policy
        self.log_path = log_path
        self.port = free_port()
        self.process: subprocess.Popen[bytes] | None = None
        self.log_handle = None
        self.peak_rss: int | None = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def __enter__(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_handle = self.log_path.open("wb")
        command = [
            str(self.server_bin),
            "--model", str(self.model),
            "--device", "none",
            "--host", "127.0.0.1",
            "--port", str(self.port),
            "--threads", str(self.policy["decode_threads"]),
            "--threads-batch", str(self.policy["prompt_threads"]),
            "--ubatch-size", str(self.policy["physical_micro_batch"]),
            "--ctx-size", "4096",
            "--parallel", "1",
            "--slots",
            "--metrics",
            "--log-verbosity", "0",
        ]
        self.process = subprocess.Popen(command, stdout=self.log_handle, stderr=subprocess.STDOUT, start_new_session=True)
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self.log_handle.flush()
                tail = self.log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
                raise RuntimeError(f"llama-server exited during startup ({self.process.returncode})\n{tail}")
            try:
                with urllib.request.urlopen(f"{self.base_url}/health", timeout=2) as response:
                    if response.status == 200:
                        return self
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
                time.sleep(0.5)
        raise RuntimeError("llama-server did not become healthy within 180 seconds")

    def __exit__(self, exc_type, exc, traceback):
        if self.process is not None and self.process.poll() is None:
            self.peak_rss = peak_rss_kib(self.process.pid)
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
                self.process.wait(timeout=20)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(self.process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                self.process.wait(timeout=10)
        if self.log_handle is not None:
            self.log_handle.close()
        return False


def with_server(
    server_bin: Path,
    model: Path,
    policy: dict[str, int],
    log_path: Path,
    operation: Callable[[str], Any],
) -> tuple[Any, int | None]:
    session = ServerSession(server_bin, model, policy, log_path)
    with session:
        result = operation(session.base_url)
        observed_peak = peak_rss_kib(session.process.pid) if session.process else None
    return result, observed_peak or session.peak_rss


def run_bench(bench_bin: Path, model: Path, output: Path, threads: int) -> dict[str, Any]:
    command = [
        str(bench_bin), "--model", str(model), "--device", "none",
        "-p", "128", "-n", "256", "-r", "3", "-t", str(threads), "-o", "json",
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=900)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(completed.stdout, encoding="utf-8")
    metrics = extract_metrics(load_rows(output))
    return {"decode_threads": threads, **metrics}


def run_fresh_suite(completion_bin: Path, model: Path, fixture_path: Path, repetitions: int, max_tokens: int, output_dir: Path) -> dict[str, Any]:
    document = load_fixture_document(fixture_path)
    records = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for fixture in document["fixtures"]:
        prompt_path = output_dir / f"{fixture['id']}.prompt.txt"
        prompt_path.write_text(build_prompt(fixture), encoding="utf-8")
        for repetition in range(1, repetitions + 1):
            started = time.monotonic()
            completed = subprocess.run(
                [
                    str(completion_bin), "--device", "none", "--model", str(model),
                    "--file", str(prompt_path), "--n-predict", str(max_tokens),
                    "--temp", "0", "--seed", "424242", "--simple-io",
                    "--no-display-prompt", "--log-verbosity", "0",
                ],
                capture_output=True,
                text=True,
                timeout=600,
            )
            elapsed = time.monotonic() - started
            candidate = completed.stdout
            evaluation = evaluate_candidate(fixture, candidate)
            records.append({
                "fixture_id": fixture["id"],
                "prompt_size": fixture["prompt_size"],
                "repetition": repetition,
                "slot_erase": {"supported": False, "status": "fresh-process"},
                "measurement": {
                    "complete_seconds": elapsed,
                    "ttft_seconds": None,
                    "tokens_cached": 0,
                    "tokens_evaluated": None,
                    "tokens_predicted": None,
                    "prompt_ms": None,
                    "prompt_per_second": None,
                    "predicted_ms": None,
                    "predicted_per_second": None,
                    "returncode": completed.returncode,
                },
                "candidate": candidate,
                "evaluation": evaluation,
            })
    return summarize_fixture_records(document["split"], False, records)


def environment_record(host_label: str) -> dict[str, Any]:
    commands = {}
    for name, command in {
        "uname": ["uname", "-a"],
        "lscpu": ["lscpu"],
        "cmake": ["cmake", "--version"],
        "compiler": ["cc", "--version"],
    }.items():
        try:
            commands[name] = subprocess.run(command, capture_output=True, text=True, timeout=20).stdout.strip()
        except (FileNotFoundError, subprocess.SubprocessError) as error:
            commands[name] = f"unavailable: {error}"
    return {
        "host_label": host_label,
        "machine": platform.machine(),
        "platform": platform.platform(),
        "logical_cpus": os.cpu_count(),
        "commands": commands,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "experiment.v3.json")
    parser.add_argument("--server-bin", type=Path, required=True)
    parser.add_argument("--bench-bin", type=Path, required=True)
    parser.add_argument("--completion-bin", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--host-label", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    machine = platform.machine().casefold()
    if machine not in {"aarch64", "arm64"}:
        raise SystemExit(f"Refusing V3 performance run on non-Arm host: {machine}")
    if (os.cpu_count() or 0) < 4:
        raise SystemExit("Refusing V3 registered grid: host exposes fewer than four logical CPUs")
    for path in (args.server_bin, args.bench_bin, args.completion_bin, args.model):
        if not path.exists():
            raise SystemExit(f"Missing required artifact: {path}")

    root = args.output
    raw = root / "raw" / args.host_label
    raw.mkdir(parents=True, exist_ok=True)
    write_json(environment_record(args.host_label), raw / "environment.json")
    started_all = time.monotonic()

    mutation_report = run_mutation_suite(
        load_fixture_document(ROOT / manifest["evaluation"]["development_fixtures"])["fixtures"],
        ROOT / manifest["evaluation"]["mutations"],
    )
    write_json(mutation_report, raw / "mutation-report.json")
    if not mutation_report["all_caught_as_intended"]:
        raise SystemExit("Registered verifier mutation suite failed before tuning")

    print("stage=decode-screen", flush=True)
    decode_records = []
    for threads in manifest["legal_search_space"]["decode_threads"]:
        decode_records.append(run_bench(args.bench_bin, args.model, raw / "decode" / f"t{threads}.json", threads))
    selected_decode = min(decode_records, key=lambda item: (-item["generation_tokens_per_second"], item["decode_threads"]))["decode_threads"]
    decode_report = {"records": decode_records, "selected_decode_threads": selected_decode, "rule": "highest registered generation throughput; fewer threads break a tie"}
    write_json(decode_report, raw / "decode-screen.json")

    print(f"stage=prompt-screen selected_decode_threads={selected_decode}", flush=True)
    prompt_probes = [probe for probe in manifest["registered_probes"] if probe["id"].startswith("prompt-")]
    prompt_candidates = []
    for prompt_threads in manifest["legal_search_space"]["prompt_threads"]:
        for micro_batch in manifest["legal_search_space"]["physical_micro_batch"]:
            policy = {"decode_threads": selected_decode, "prompt_threads": prompt_threads, "physical_micro_batch": micro_batch}
            candidate_id = policy_id(policy)
            records, rss = with_server(
                args.server_bin,
                args.model,
                policy,
                raw / "prompt-screen" / f"{candidate_id}.server.log",
                lambda url: run_probe_suite(url, prompt_probes, cache_prompt=False),
            )
            prompt_seconds = sum((record["prompt_ms"] / 1000) if isinstance(record["prompt_ms"], (int, float)) else record["complete_seconds"] for record in records)
            candidate = {"policy": policy, "policy_id": candidate_id, "prompt_seconds": prompt_seconds, "peak_rss_kib": rss, "probes": records}
            prompt_candidates.append(candidate)
            write_json(candidate, raw / "prompt-screen" / f"{candidate_id}.json")
    retained = pareto_policies(prompt_candidates)
    prompt_report = {"candidate_count": len(prompt_candidates), "pareto_count": len(retained), "pareto_policy_ids": [item["policy_id"] for item in retained], "candidates": prompt_candidates}
    write_json(prompt_report, raw / "prompt-screen.json")

    print(f"stage=development-evaluation pareto_count={len(retained)}", flush=True)
    policies = [item["policy"] for item in retained]
    if static_policy() not in policies:
        policies.append(static_policy())
    development_reports = []
    for policy in policies:
        candidate_id = policy_id(policy)
        fixture_report, rss = with_server(
            args.server_bin,
            args.model,
            policy,
            raw / "development" / f"{candidate_id}.server.log",
            lambda url: run_fixture_suite(
                url,
                ROOT / manifest["evaluation"]["development_fixtures"],
                cache_prompt=False,
                repetitions=1,
                warmups=manifest["evaluation"]["warmup_requests_per_policy"],
                max_generated_tokens=manifest["evaluation"]["max_generated_tokens"],
            ),
        )
        report = {"policy": policy, "policy_id": candidate_id, "peak_rss_kib": rss, "fixture_report": fixture_report}
        development_reports.append(report)
        write_json(report, raw / "development" / f"{candidate_id}.json")
    selection = select_development_policy(development_reports)
    write_json({"selection": selection, "reports": development_reports}, raw / "development-selection.json")
    if selection["selected"] is None:
        summary = {
            "schema_version": "3.0",
            "study_id": manifest["study_id"],
            "host": args.host_label,
            "status": "stopped-before-sealed-evaluation",
            "reason": selection["reason"],
            "selection": selection,
            "mutation_report": mutation_report,
            "autotuning_seconds": time.monotonic() - started_all,
            "claim_passed": False,
        }
        write_json(summary, root / f"summary-{args.host_label}.json")
        print("stage=complete claim_passed=false reason=no-valid-development-policy", flush=True)
        return 0

    print(f"stage=sealed-evaluation selected_policy={selection['selected_policy_id']}", flush=True)
    selected = selection["selected"]
    variants = {
        "B1": (static_policy(), False),
        "B2": (static_policy(), True),
        "V3-A": (selected, False),
        "V3-B": (selected, True),
    }
    sealed_reports = {}
    peak_rss = {}
    for variant, (policy, cache_prompt) in variants.items():
        report, rss = with_server(
            args.server_bin,
            args.model,
            policy,
            raw / "sealed" / f"{variant}.server.log",
            lambda url, cache_prompt=cache_prompt: run_fixture_suite(
                url,
                ROOT / manifest["evaluation"]["sealed_fixtures"],
                cache_prompt=cache_prompt,
                repetitions=manifest["evaluation"]["sealed_repetitions"],
                warmups=manifest["evaluation"]["warmup_requests_per_policy"],
                max_generated_tokens=manifest["evaluation"]["max_generated_tokens"],
            ),
        )
        sealed_reports[variant] = report
        peak_rss[variant] = rss
        write_json({"variant": variant, "policy": policy, "peak_rss_kib": rss, "fixture_report": report}, raw / "sealed" / f"{variant}.json")

    print("stage=fresh-process-continuity", flush=True)
    b0 = run_fresh_suite(
        args.completion_bin,
        args.model,
        ROOT / manifest["evaluation"]["sealed_fixtures"],
        manifest["evaluation"]["sealed_repetitions"],
        manifest["evaluation"]["max_generated_tokens"],
        raw / "sealed" / "B0-candidates",
    )
    write_json({"variant": "B0", "policy": static_policy(), "fixture_report": b0}, raw / "sealed" / "B0.json")

    gates = final_gates(manifest, sealed_reports["B1"], sealed_reports["V3-A"], mutation_report)
    cache_static = paired_result(sealed_reports["B1"], sealed_reports["B2"])
    cache_selected = paired_result(sealed_reports["V3-A"], sealed_reports["V3-B"])
    cache_evidence = {
        "static": cache_static,
        "selected": cache_selected,
        "B2_positive_reuse_records": sealed_reports["B2"]["cache"]["positive_reuse_record_count"],
        "V3-B_positive_reuse_records": sealed_reports["V3-B"]["cache"]["positive_reuse_record_count"],
        "cache_claim_eligible": sealed_reports["B2"]["cache"]["positive_reuse_record_count"] > 0 and sealed_reports["V3-B"]["cache"]["positive_reuse_record_count"] > 0,
    }
    summary = {
        "schema_version": "3.0",
        "study_id": manifest["study_id"],
        "host": args.host_label,
        "status": "sealed-evaluation-complete",
        "selection": selection,
        "decode_screen": decode_report,
        "prompt_pareto_policy_ids": prompt_report["pareto_policy_ids"],
        "mutation_report": mutation_report,
        "variant_peak_rss_kib": peak_rss,
        "variant_summaries": {variant: {key: value for key, value in report.items() if key != "records"} for variant, report in {"B0": b0, **sealed_reports}.items()},
        "primary_gates": gates,
        "cache_evidence": cache_evidence,
        "autotuning_and_evaluation_seconds": time.monotonic() - started_all,
        "claim_passed": gates["claim_passed"],
    }
    write_json(summary, root / f"summary-{args.host_label}.json")
    print(f"stage=complete claim_passed={str(gates['claim_passed']).lower()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
