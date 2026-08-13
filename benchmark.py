#!/usr/bin/env python3
"""Summarize paired llama-bench JSON without hiding the raw evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"


class BenchmarkFormatError(ValueError):
    pass


def load_rows(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise BenchmarkFormatError(f"{path} is empty")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        try:
            value = [json.loads(line) for line in text.splitlines() if line.strip()]
        except json.JSONDecodeError as error:
            raise BenchmarkFormatError(f"{path} is not valid JSON or JSONL") from error
    if isinstance(value, dict):
        value = value.get("results", [value])
    if not isinstance(value, list) or not value or not all(isinstance(row, dict) for row in value):
        raise BenchmarkFormatError(f"{path} does not contain benchmark rows")
    return value


def _number(row: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = row.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def extract_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    prompt_values: list[float] = []
    generation_values: list[float] = []
    for row in rows:
        prompt_tokens = _number(row, "n_prompt", "prompt_tokens") or 0
        generated_tokens = _number(row, "n_gen", "generation_tokens") or 0
        throughput = _number(row, "avg_ts", "tokens_per_second", "tps")
        if throughput is None or throughput <= 0:
            continue
        if prompt_tokens > 0 and generated_tokens == 0:
            prompt_values.append(throughput)
        if generated_tokens > 0 and prompt_tokens == 0:
            generation_values.append(throughput)
    if not prompt_values or not generation_values:
        raise BenchmarkFormatError("rows must include positive prompt and generation throughput")
    return {
        "prompt_tokens_per_second": sum(prompt_values) / len(prompt_values),
        "generation_tokens_per_second": sum(generation_values) / len(generation_values),
    }


def percent_change(baseline: float, optimized: float) -> float:
    if baseline <= 0:
        raise BenchmarkFormatError("baseline must be positive")
    return (optimized / baseline - 1) * 100


def summarize(baseline_path: Path, optimized_path: Path) -> dict[str, Any]:
    baseline = extract_metrics(load_rows(baseline_path))
    optimized = extract_metrics(load_rows(optimized_path))
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline_file": str(baseline_path),
        "optimized_file": str(optimized_path),
        "baseline": baseline,
        "optimized": optimized,
        "change_percent": {
            key: percent_change(baseline[key], optimized[key])
            for key in baseline
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("optimized", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = summarize(args.baseline, args.optimized)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
