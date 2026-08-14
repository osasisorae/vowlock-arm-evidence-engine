#!/usr/bin/env python3
"""Runtime measurement, policy selection, and result gates for Version 3."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Iterable

from setup_companion_eval_v3 import build_prompt, evaluate_candidate, load_fixture_document


class V3RuntimeError(ValueError):
    pass


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != "3.0":
        raise V3RuntimeError("manifest must be a Version 3 object")
    if value.get("status") != "pre-registered-before-implementation-and-execution":
        raise V3RuntimeError("manifest is not the frozen pre-registration")
    model = value.get("model", {})
    if not isinstance(model.get("sha256"), str) or len(model["sha256"]) != 64:
        raise V3RuntimeError("manifest model needs a SHA-256")
    space = value.get("legal_search_space", {})
    expected = {
        "decode_threads": [1, 2, 3, 4],
        "prompt_threads": [1, 2, 3, 4],
        "physical_micro_batch": [64, 128, 256, 512],
        "cache_prompt": [False, True],
    }
    for key, registered in expected.items():
        if space.get(key) != registered:
            raise V3RuntimeError(f"registered legal search space changed: {key}")
    return value


def policy_id(policy: dict[str, int]) -> str:
    return f"t{policy['decode_threads']}-tb{policy['prompt_threads']}-ub{policy['physical_micro_batch']}"


def static_policy() -> dict[str, int]:
    return {"decode_threads": 4, "prompt_threads": 4, "physical_micro_batch": 512}


def percentile(values: Iterable[float], quantile: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise V3RuntimeError("cannot compute percentile of an empty sequence")
    if not 0 <= quantile <= 1:
        raise V3RuntimeError("quantile must be between zero and one")
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def parse_sse_data(line: bytes | str) -> dict[str, Any] | None:
    text = line.decode("utf-8", errors="replace") if isinstance(line, bytes) else line
    text = text.strip()
    if not text.startswith("data:"):
        return None
    payload = text[5:].strip()
    if not payload or payload == "[DONE]":
        return None
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as error:
        raise V3RuntimeError(f"invalid SSE JSON: {payload[:120]}") from error
    if not isinstance(value, dict):
        raise V3RuntimeError("SSE event must be an object")
    return value


def _timing_value(event: dict[str, Any], *keys: str) -> Any:
    timings = event.get("timings") if isinstance(event.get("timings"), dict) else {}
    for key in keys:
        if key in event:
            return event[key]
        if key in timings:
            return timings[key]
    return None


def erase_slot(base_url: str, slot: int = 0, timeout: float = 20) -> dict[str, Any]:
    request = urllib.request.Request(f"{base_url}/slots/{slot}?action=erase", data=b"", method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"supported": True, "status": response.status}
    except urllib.error.HTTPError as error:
        return {"supported": False, "status": error.code, "error": str(error)}
    except urllib.error.URLError as error:
        return {"supported": False, "status": None, "error": str(error)}


def request_completion(
    base_url: str,
    prompt: str,
    *,
    n_predict: int,
    cache_prompt: bool,
    seed: int = 424242,
    ignore_eos: bool = False,
    timeout: float = 300,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    payload = {
        "prompt": prompt,
        "n_predict": n_predict,
        "temperature": 0,
        "seed": seed,
        "stream": True,
        "cache_prompt": cache_prompt,
        "id_slot": 0,
        "ignore_eos": ignore_eos,
        "stop": ["<|im_end|>"],
    }
    request = urllib.request.Request(
        f"{base_url}/completion",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = clock()
    first_content_at: float | None = None
    content: list[str] = []
    final_event: dict[str, Any] = {}
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for line in response:
            event = parse_sse_data(line)
            if event is None:
                continue
            final_event = event
            chunk = event.get("content")
            if isinstance(chunk, str) and chunk:
                if first_content_at is None:
                    first_content_at = clock()
                content.append(chunk)
    completed = clock()
    text = "".join(content)
    return {
        "content": text,
        "ttft_seconds": None if first_content_at is None else first_content_at - started,
        "complete_seconds": completed - started,
        "tokens_cached": _timing_value(final_event, "tokens_cached", "cache_n"),
        "tokens_evaluated": _timing_value(final_event, "tokens_evaluated", "prompt_n"),
        "tokens_predicted": _timing_value(final_event, "tokens_predicted", "predicted_n"),
        "prompt_ms": _timing_value(final_event, "prompt_ms"),
        "prompt_per_second": _timing_value(final_event, "prompt_per_second"),
        "predicted_ms": _timing_value(final_event, "predicted_ms"),
        "predicted_per_second": _timing_value(final_event, "predicted_per_second"),
        "stop": final_event.get("stop"),
        "stopped_limit": final_event.get("stopped_limit"),
    }


def probe_prompt(target_tokens: int) -> str:
    repeated = " evidence" * max(1, target_tokens - 28)
    return (
        "<|im_start|>system\nReturn plain text and follow the request.<|im_end|>\n"
        f"<|im_start|>user\nContinue a deterministic sequence using the supplied context.{repeated}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )


def run_probe_suite(base_url: str, probes: list[dict[str, Any]], cache_prompt: bool = False) -> list[dict[str, Any]]:
    records = []
    for probe in probes:
        erase = erase_slot(base_url) if not cache_prompt else {"supported": True, "status": "not-requested"}
        result = request_completion(
            base_url,
            probe_prompt(probe["prompt_tokens"]),
            n_predict=probe["generation_tokens"],
            cache_prompt=cache_prompt,
            ignore_eos=True,
        )
        records.append({"probe_id": probe["id"], "target_prompt_tokens": probe["prompt_tokens"], "slot_erase": erase, **result})
    return records


def run_fixture_suite(
    base_url: str,
    fixture_path: Path,
    *,
    cache_prompt: bool,
    repetitions: int,
    warmups: int,
    max_generated_tokens: int,
) -> dict[str, Any]:
    document = load_fixture_document(fixture_path)
    fixtures = document["fixtures"]
    if warmups:
        if not cache_prompt:
            erase_slot(base_url)
        for _ in range(warmups):
            request_completion(base_url, build_prompt(fixtures[0]), n_predict=max_generated_tokens, cache_prompt=cache_prompt)
    records = []
    for fixture in fixtures:
        for repetition in range(1, repetitions + 1):
            erase = erase_slot(base_url) if not cache_prompt else {"supported": True, "status": "not-requested"}
            measurement = request_completion(
                base_url,
                build_prompt(fixture),
                n_predict=max_generated_tokens,
                cache_prompt=cache_prompt,
            )
            evaluation = evaluate_candidate(fixture, measurement["content"])
            records.append({
                "fixture_id": fixture["id"],
                "prompt_size": fixture["prompt_size"],
                "repetition": repetition,
                "slot_erase": erase,
                "measurement": {key: value for key, value in measurement.items() if key != "content"},
                "candidate": measurement["content"],
                "evaluation": evaluation,
            })
    return summarize_fixture_records(document["split"], cache_prompt, records)


def summarize_fixture_records(split: str, cache_prompt: bool, records: list[dict[str, Any]]) -> dict[str, Any]:
    complete = [record["measurement"]["complete_seconds"] for record in records]
    ttft = [record["measurement"]["ttft_seconds"] for record in records if record["measurement"]["ttft_seconds"] is not None]
    valid_complete = [record["measurement"]["complete_seconds"] for record in records if record["evaluation"]["passed"]]
    cached = [record["measurement"]["tokens_cached"] for record in records if isinstance(record["measurement"]["tokens_cached"], (int, float))]
    return {
        "schema_version": "3.0",
        "split": split,
        "cache_prompt": cache_prompt,
        "record_count": len(records),
        "passed_count": sum(record["evaluation"]["passed"] for record in records),
        "all_passed": all(record["evaluation"]["passed"] for record in records),
        "valid_output_rate": sum(record["evaluation"]["passed"] for record in records) / len(records),
        "latency": {
            "median_complete_seconds": statistics.median(complete),
            "p95_complete_seconds": percentile(complete, 0.95),
            "worst_complete_seconds": max(complete),
            "median_ttft_seconds": statistics.median(ttft) if ttft else None,
            "median_complete_valid_seconds": statistics.median(valid_complete) if valid_complete else None,
        },
        "cache": {
            "reported_record_count": len(cached),
            "positive_reuse_record_count": sum(value > 0 for value in cached),
            "maximum_tokens_cached": max(cached) if cached else None,
        },
        "records": records,
    }


def pareto_policies(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def rss_value(candidate: dict[str, Any]) -> float:
        value = candidate.get("peak_rss_kib")
        return float(value) if isinstance(value, (int, float)) else math.inf

    retained = []
    for candidate in candidates:
        dominated = False
        for other in candidates:
            if other is candidate:
                continue
            no_worse = other["prompt_seconds"] <= candidate["prompt_seconds"] and rss_value(other) <= rss_value(candidate)
            strictly_better = other["prompt_seconds"] < candidate["prompt_seconds"] or rss_value(other) < rss_value(candidate)
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            retained.append(candidate)
    return sorted(retained, key=lambda item: (item["prompt_seconds"], rss_value(item), item["policy"]["prompt_threads"], item["policy"]["physical_micro_batch"]))


def select_development_policy(reports: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [report for report in reports if report["fixture_report"]["all_passed"]]
    if not valid:
        return {"selected": None, "reason": "no development policy passed every quality check", "candidate_count": len(reports), "valid_candidate_count": 0}
    selected = min(
        valid,
        key=lambda report: (
            report["fixture_report"]["latency"]["median_complete_valid_seconds"],
            report["fixture_report"]["latency"]["p95_complete_seconds"],
            report["peak_rss_kib"] if isinstance(report.get("peak_rss_kib"), (int, float)) else math.inf,
            report["policy"]["decode_threads"] + report["policy"]["prompt_threads"],
            report["policy"]["physical_micro_batch"],
        ),
    )
    return {
        "selected": selected["policy"],
        "selected_policy_id": policy_id(selected["policy"]),
        "reason": "lowest median complete-valid development latency after all hard quality checks",
        "candidate_count": len(reports),
        "valid_candidate_count": len(valid),
    }


def paired_result(baseline: dict[str, Any], candidate: dict[str, Any], minimum_percent: float = 5.0) -> dict[str, Any]:
    baseline_by_key = {(record["fixture_id"], record["repetition"]): record for record in baseline["records"]}
    candidate_by_key = {(record["fixture_id"], record["repetition"]): record for record in candidate["records"]}
    if set(baseline_by_key) != set(candidate_by_key):
        raise V3RuntimeError("paired reports do not contain identical fixture/repetition keys")
    pairs = []
    for key in sorted(baseline_by_key):
        before = baseline_by_key[key]
        after = candidate_by_key[key]
        before_seconds = before["measurement"]["complete_seconds"]
        after_seconds = after["measurement"]["complete_seconds"]
        improvement = (before_seconds - after_seconds) / before_seconds * 100
        safe_fast = before["evaluation"]["passed"] and after["evaluation"]["passed"] and improvement >= minimum_percent
        pairs.append({"fixture_id": key[0], "repetition": key[1], "before_seconds": before_seconds, "after_seconds": after_seconds, "improvement_percent": improvement, "safe_fast": safe_fast})
    before_values = [pair["before_seconds"] for pair in pairs]
    after_values = [pair["after_seconds"] for pair in pairs]
    median_improvement = (statistics.median(before_values) - statistics.median(after_values)) / statistics.median(before_values) * 100
    before_p95 = percentile(before_values, 0.95)
    after_p95 = percentile(after_values, 0.95)
    p95_regression = (after_p95 - before_p95) / before_p95 * 100
    return {
        "pair_count": len(pairs),
        "median_improvement_percent": median_improvement,
        "p95_regression_percent": p95_regression,
        "safe_fast_at_5": sum(pair["safe_fast"] for pair in pairs) / len(pairs),
        "pairs": pairs,
    }


def final_gates(
    manifest: dict[str, Any],
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    mutation_report: dict[str, Any],
) -> dict[str, Any]:
    paired = paired_result(baseline, candidate, manifest["hard_gates"]["minimum_median_complete_latency_improvement_percent"])
    checks = {
        "baseline_outputs_pass": baseline["all_passed"],
        "candidate_outputs_pass": candidate["all_passed"],
        "dangerous_mutations_caught": mutation_report.get("mutation_recall") == manifest["hard_gates"]["dangerous_mutation_recall"],
        "median_improvement_gate": paired["median_improvement_percent"] >= manifest["hard_gates"]["minimum_median_complete_latency_improvement_percent"],
        "p95_regression_gate": paired["p95_regression_percent"] <= manifest["hard_gates"]["maximum_p95_regression_percent"],
    }
    return {"claim_passed": all(checks.values()), "checks": checks, "paired": paired}


def write_json(value: Any, output: Path | None = None) -> None:
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("experiment.v3.json"))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    subparsers.add_parser("model-tsv")
    subparsers.add_parser("runtime-commit")
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    if args.command == "validate":
        dev = load_fixture_document(Path(manifest["evaluation"]["development_fixtures"]))
        sealed = load_fixture_document(Path(manifest["evaluation"]["sealed_fixtures"]))
        write_json({"valid": True, "study_id": manifest["study_id"], "development_fixtures": len(dev["fixtures"]), "sealed_fixtures": len(sealed["fixtures"])})
    elif args.command == "model-tsv":
        model = manifest["model"]
        print("\t".join([model["id"], model["filename"], model["url"], model["sha256"], str(model["bytes"])]))
    elif args.command == "runtime-commit":
        print(manifest["runtime"]["commit"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
