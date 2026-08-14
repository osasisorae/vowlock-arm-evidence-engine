#!/usr/bin/env python3
"""Execute the frozen Version 4 authority-allocation study on native Arm."""

from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from setup_companion_eval_v3 import build_prompt, evaluate_candidate, load_fixture_document  # noqa: E402
from v3_runtime import erase_slot, request_completion  # noqa: E402
from v4_authority import (  # noqa: E402
    AUTHORITY_KEYS,
    authority_envelope,
    build_constrained_prompt,
    evaluate_constrained_response,
    load_manifest,
    model_free_preflight,
    template_candidate,
)
from v4_runtime import registered_decision, summarize_split  # noqa: E402


def write_json(value: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def free_port() -> int:
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        return int(server.getsockname()[1])


def peak_rss_kib(pid: int) -> int | None:
    status = Path(f"/proc/{pid}/status")
    if not status.exists():
        return None
    for line in status.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("VmHWM:"):
            parts = line.split()
            return int(parts[1]) if len(parts) >= 2 else None
    return None


class ServerSession:
    def __init__(self, server_bin: Path, model: Path, runtime: dict[str, Any], log_path: Path):
        self.server_bin = server_bin
        self.model = model
        self.runtime = runtime
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
            str(self.server_bin), "--model", str(self.model), "--device", "none",
            "--host", "127.0.0.1", "--port", str(self.port),
            "--threads", str(self.runtime["decode_threads"]),
            "--threads-batch", str(self.runtime["prompt_threads"]),
            "--ubatch-size", str(self.runtime["physical_micro_batch"]),
            "--ctx-size", "4096", "--parallel", "1", "--slots", "--metrics", "--log-verbosity", "0",
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


def authority_correct(fixture: dict[str, Any], evaluation: dict[str, Any]) -> bool:
    candidate = evaluation.get("candidate")
    envelope = authority_envelope(fixture)
    return isinstance(candidate, dict) and all(candidate.get(key) == envelope[key] for key in AUTHORITY_KEYS)


def template_record(fixture: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    candidate = template_candidate(fixture)
    evaluation = evaluate_candidate(fixture, json.dumps(candidate))
    complete = time.perf_counter() - started
    return {
        "passed": evaluation["passed"],
        "authority_correct": authority_correct(fixture, evaluation),
        "complete_seconds": complete,
        "ttft_seconds": complete,
        "fallback_used": False,
        "candidate": candidate,
        "evaluation": evaluation,
    }


def model_record(base_url: str, fixture: dict[str, Any], manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    erase_f0 = erase_slot(base_url)
    f0_measurement = request_completion(
        base_url,
        build_prompt(fixture),
        n_predict=manifest["evaluation"]["max_generated_tokens_free_form"],
        cache_prompt=False,
    )
    f0_evaluation = evaluate_candidate(fixture, f0_measurement["content"])
    f0 = {
        "passed": f0_evaluation["passed"],
        "authority_correct": authority_correct(fixture, f0_evaluation),
        "complete_seconds": f0_measurement["complete_seconds"],
        "ttft_seconds": f0_measurement["ttft_seconds"],
        "fallback_used": False,
        "slot_erase": erase_f0,
        "candidate_text": f0_measurement["content"],
        "measurement": {key: value for key, value in f0_measurement.items() if key != "content"},
        "evaluation": f0_evaluation,
    }

    erase_m0 = erase_slot(base_url)
    m0_measurement = request_completion(
        base_url,
        build_constrained_prompt(fixture),
        n_predict=manifest["evaluation"]["max_generated_tokens_explanation"],
        cache_prompt=False,
    )
    constrained = evaluate_constrained_response(fixture, m0_measurement["content"])
    raw_evaluation = constrained["raw"]
    m0 = {
        "passed": constrained["raw_accepted"],
        "authority_correct": constrained["authority_unchanged"] if raw_evaluation.get("candidate") else False,
        "complete_seconds": m0_measurement["complete_seconds"],
        "ttft_seconds": m0_measurement["ttft_seconds"],
        "fallback_used": False,
        "slot_erase": erase_m0,
        "candidate_text": m0_measurement["content"],
        "measurement": {key: value for key, value in m0_measurement.items() if key != "content"},
        "evaluation": raw_evaluation,
    }
    fallback_started = time.perf_counter()
    if constrained["fallback_used"]:
        template_candidate(fixture)
    fallback_seconds = time.perf_counter() - fallback_started
    hybrid_complete = m0_measurement["complete_seconds"] + fallback_seconds
    h0 = {
        "passed": constrained["hybrid"]["passed"],
        "authority_correct": constrained["authority_unchanged"],
        "complete_seconds": hybrid_complete,
        "ttft_seconds": hybrid_complete,
        "model_ttft_seconds": m0_measurement["ttft_seconds"],
        "fallback_used": constrained["fallback_used"],
        "fallback_seconds": fallback_seconds,
        "candidate": constrained["hybrid_candidate"],
        "evaluation": constrained["hybrid"],
    }
    return f0, m0, h0


def run_split(base_url: str, fixture_path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    document = load_fixture_document(fixture_path)
    records = []
    for fixture in document["fixtures"]:
        print(f"fixture={fixture['id']}", flush=True)
        t0 = template_record(fixture)
        f0, m0, h0 = model_record(base_url, fixture, manifest)
        records.append({"fixture_id": fixture["id"], "prompt_size": fixture["prompt_size"], "variants": {"F0": f0, "T0": t0, "M0": m0, "H0": h0}})
    return summarize_split(document["split"], records)


def environment_record(host_label: str) -> dict[str, Any]:
    commands = {}
    for name, command in {"uname": ["uname", "-a"], "lscpu": ["lscpu"], "compiler": ["cc", "--version"]}.items():
        try:
            commands[name] = subprocess.run(command, capture_output=True, text=True, timeout=20).stdout.strip()
        except (FileNotFoundError, subprocess.SubprocessError) as error:
            commands[name] = f"unavailable: {error}"
    return {"host_label": host_label, "machine": platform.machine(), "platform": platform.platform(), "logical_cpus": os.cpu_count(), "commands": commands}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "experiment.v4.json")
    parser.add_argument("--server-bin", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--host-label", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    machine = platform.machine().casefold()
    if machine not in {"aarch64", "arm64"}:
        raise SystemExit(f"Refusing V4 native run on non-Arm host: {machine}")
    if (os.cpu_count() or 0) < 4:
        raise SystemExit("V4 requires at least four logical CPUs")
    for path in (args.server_bin, args.model):
        if not path.exists():
            raise SystemExit(f"Missing required artifact: {path}")

    raw = args.output / "raw" / args.host_label
    raw.mkdir(parents=True, exist_ok=True)
    write_json(environment_record(args.host_label), raw / "environment.json")
    preflight = model_free_preflight(manifest, ROOT)
    write_json(preflight, raw / "preflight.json")
    if not preflight["apparatus_gate_passed"]:
        raise SystemExit("V4 model-free apparatus gate failed")

    started = time.monotonic()
    server = ServerSession(args.server_bin, args.model, manifest["runtime"], raw / "llama-server.log")
    with server:
        print("stage=development", flush=True)
        development = run_split(server.base_url, ROOT / manifest["evaluation"]["development_fixtures"], manifest)
        write_json(development, raw / "development.json")
        if development["variants"]["H0"]["valid_rate"] != 1.0:
            raise SystemExit("V4 development hybrid gate failed before sealed model generation")
        print("stage=sealed", flush=True)
        sealed = run_split(server.base_url, ROOT / manifest["evaluation"]["sealed_fixtures"], manifest)
        write_json(sealed, raw / "sealed.json")
        observed_peak = peak_rss_kib(server.process.pid) if server.process else None
    peak_model_rss = observed_peak or server.peak_rss

    decision = registered_decision(manifest, preflight, development, sealed)
    summary = {
        "schema_version": "4.0",
        "study_id": manifest["study_id"],
        "host": args.host_label,
        "status": "complete",
        "elapsed_seconds": time.monotonic() - started,
        "model_artifact_bytes": args.model.stat().st_size,
        "model_server_peak_rss_kib": peak_model_rss,
        "model_free_process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "development": {"fixture_count": development["fixture_count"], "variants": development["variants"]},
        "sealed": {"fixture_count": sealed["fixture_count"], "variants": sealed["variants"]},
        "preflight": {"apparatus_gate_passed": preflight["apparatus_gate_passed"], "mutation_recall": preflight["mutations"]["mutation_recall"]},
        "decision": decision,
        "boundaries": [
            "Synthetic fixtures only; no device was connected or changed.",
            "The sealed fixtures are public and pre-registered, not investigator-blind.",
            "No claim about human comprehension is made without blinded human evaluation.",
        ],
    }
    write_json(summary, args.output / f"summary-{args.host_label}.json")
    print(f"stage=complete retained={decision['retained_default']} model_eligible_for_human_study={str(decision['model_eligible_for_human_study']).lower()}", flush=True)
    return 0 if decision["architecture_safe_for_further_study"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
