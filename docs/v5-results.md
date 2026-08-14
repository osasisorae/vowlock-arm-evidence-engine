# Version 5 result: compile the policy, do not narrate it

Version 5 passed its registered claim on native Arm. The model-free compiler covered all **648 declared device states** across three renderings, produced **1,944 distinct provenance-bearing outputs**, repeated every result byte-for-byte and rejected **8/8 registered corruptions**.

Source: [GitHub Actions Run 31803354032](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31803354032). Curated machine evidence: [`evidence/v5-run-1-ubuntu-22.04-arm.json`](../evidence/v5-run-1-ubuntu-22.04-arm.json). Registration: [`experiment.v5.json`](../experiment.v5.json).

## What V5 tested

V4 established that the model did not earn its place in this bounded decision task. V5 tested what should replace it: a reusable deterministic explanation compiler. It accepts exactly seven typed observations, applies the registered policy and emits authority, decisive rules, evidence provenance and a deterministic output hash.

| Rendering | Contract | Outputs/s | Median bytes/output | Full 648-state round p50 |
|---|---|---:|---:|---:|
| B0 · brief | Action + every decisive reason | 50,378 | 799.5 | 12.856 ms |
| D0 · detailed | Decisive reasons + all seven values | 43,359 | 1,052 | 14.947 ms |
| P0 · progressive | Summary, why, evidence and next step | 33,351 | 1,600 | 19.439 ms |

The native four-core `aarch64` runner completed the proof and benchmark in 5.278 seconds. The Python process peaked at 23,168 KiB RSS. The study used zero model bytes and made zero network requests.

## The policy's shape

| Decision | Declared states | Share |
|---|---:|---:|
| STOP | 600 | 92.59% |
| REQUEST_EVIDENCE | 47 | 7.25% |
| PASS | 1 | 0.15% |

Only one complete state permits proceeding: a resettable test device with certification, original values, restoration, reboot persistence and Play Protect all verified, and Device Owner inactive. This distribution explains why a probabilistic narrator was the wrong authority: the useful system is a narrow safety policy with one permissible state, not an open-ended language task.

## What “exhaustive” means here

The harness enumerated the complete Cartesian product declared before implementation:

`2 × 3 × 2 × 3 × 3 × 3 × 2 = 648` states.

For all three representations it independently checked the policy decision, next action, decisive rules, evidence, state ID, canonical state hash, compiled-output hash and repeatability. It then corrupted the decision, action, rule list, evidence, state ID and both hashes; every mutation was rejected.

This is stronger than sampling twelve fixtures, but narrower than it sounds. It establishes the registered properties for these fields and values. It is not a mathematical proof of Python, Android, the device, undeclared states or human understanding.

## Decision

Retain the V5 compiler as the executable reference for this bounded Setup Companion policy. It improves on V4 not by adding intelligence, but by turning a successful template into reusable, strictly typed and exhaustively checked infrastructure.

The model-free compiler can beat the prior model experiments on correctness, coverage, latency, storage, memory, reproducibility and auditability **within this finite task**. It cannot replace a model for open-ended diagnosis, conversation or an undeclared state space, and V5 does not claim that any rendering is easier for people to understand.
