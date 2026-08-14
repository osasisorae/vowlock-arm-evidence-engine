#!/usr/bin/env python3
"""Verify deterministic baseline and optimized model outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"


class OutputContractError(ValueError):
    pass


def normalize_output(text: str) -> str:
    """Ignore surrounding console whitespace, but preserve generated content."""
    return text.strip()


def verify_outputs(baseline_path: Path, optimized_path: Path, expected: str) -> dict[str, Any]:
    baseline = normalize_output(baseline_path.read_text(encoding="utf-8"))
    optimized = normalize_output(optimized_path.read_text(encoding="utf-8"))

    failures: list[str] = []
    if baseline != expected:
        failures.append(f"baseline output was {baseline!r}, expected {expected!r}")
    if optimized != expected:
        failures.append(f"optimized output was {optimized!r}, expected {expected!r}")
    if baseline != optimized:
        failures.append("baseline and optimized outputs differ")
    if failures:
        raise OutputContractError("; ".join(failures))

    return {
        "schema_version": SCHEMA_VERSION,
        "expected": expected,
        "baseline": baseline,
        "optimized": optimized,
        "equivalent": True,
        "contract_passed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("optimized", type=Path)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        result = verify_outputs(args.baseline, args.optimized, args.expected)
    except (OSError, UnicodeError, OutputContractError) as error:
        parser.error(str(error))

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
