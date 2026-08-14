# Version 5 run log

## Registration boundary

Version 5 was registered in commit [`846e693`](https://github.com/osasisorae/vowlock-arm-evidence-engine/commit/846e693) before the compiler, proof harness, tests or workflow existed. The apparatus was added later in commit [`d05242d`](https://github.com/osasisorae/vowlock-arm-evidence-engine/commit/d05242d).

The registration froze the 648-state typed domain, B0/D0/P0 rendering contracts, nine exhaustive invariants, eight mutations, five warmup rounds, 100 measured rounds and the limits on human and formal-verification claims.

## Run 1 — claim passed

- Workflow: [GitHub Actions Run 31803354032](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31803354032)
- Host: native `aarch64`, Ubuntu 22.04, four logical CPUs
- Python: 3.10.12
- Tests: 56 passed
- Proof: 648 states, 1,944 compiled outputs, zero failures
- Mutations: 8/8 rejected
- Measured compilations: 194,400
- Study time: 5.278 seconds
- Peak process RSS: 23,168 KiB
- Model/network: 0 bytes / 0 requests

This was the first native execution of the registered apparatus. No result-dependent repair or rerun was required.

## Interpretation boundary

The green workflow supports the registered finite-domain claim because the proof gates passed, not merely because the job completed. It does not establish real-device correctness or human comprehension. Those questions require different evidence and must not be retrofitted onto this run.
