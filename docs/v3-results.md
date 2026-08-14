# Version 3 result: the quality gate stopped the search

Version 3 is a valid negative result. The native workflow completed successfully, but the registered research process stopped before sealed evaluation because **no development policy passed the explanation-quality gate**.

Source: [GitHub Actions Run 31795111653](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31795111653). Curated machine-readable evidence: [`evidence/v3-run-2-ubuntu-22.04-arm.json`](../evidence/v3-run-2-ubuntu-22.04-arm.json).

## What ran

- Native four-core `aarch64` GitHub runner on Ubuntu 22.04.
- The pinned Qwen2.5 1.5B Q4_0 model and baseline Arm CPU backend retained from Version 2.
- Four decode-thread settings.
- Sixteen prompt-thread and physical-micro-batch settings.
- Eight independent verifier mutations.
- Complete development explanations for the sole Pareto policy and the static baseline.

The run took 1,291.88 seconds (21.53 minutes). The frozen sealed split was not used for model generation or policy selection.

## Decode search

| Decode threads | Prompt tok/s | Generation tok/s | Decision |
|---:|---:|---:|---|
| 1 | 47.5999 | 10.3719 | reject |
| 2 | 92.2795 | 19.1233 | reject |
| 3 | 141.0010 | 27.7196 | reject |
| 4 | 163.0303 | 35.8232 | retain |

On this four-core runner, generation throughput increased monotonically through all four available threads. V3 therefore retained four decode threads. This is a host/workload result, not a universal rule that maximum thread count always wins.

## Prompt search

The sole non-dominated prompt policy used four prompt threads and physical micro-batch 256. Its summed processing time across the registered short, medium and long probes was 28.6501 seconds, compared with 29.9763 seconds for the static micro-batch 512 policy: a 4.424% screening improvement. Both reported the same 2,016,484 KiB server high-water RSS.

| Rank | Policy | Summed prompt time | Peak RSS |
|---:|---|---:|---:|
| 1 | t4 / tb4 / ub256 | 28.6501 s | 2,016,484 KiB |
| 2 | t4 / tb4 / ub512 | 29.9763 s | 2,016,484 KiB |
| 3 | t4 / tb4 / ub128 | 34.7387 s | 2,016,484 KiB |
| 4 | t4 / tb3 / ub256 | 37.1898 s | 2,016,484 KiB |
| 5 | t4 / tb3 / ub128 | 37.2588 s | 2,016,484 KiB |

The rest of the 16-policy ranking remains in the curated evidence. More prompt threads mattered far more than micro-batch within the tested range; micro-batch 256 was best only after four prompt threads were selected.

## Development explanations

| Policy | Valid fixtures | Median complete | Median TTFT | p95 complete | Peak RSS |
|---|---:|---:|---:|---:|---:|
| t4 / tb4 / ub256 | 0 / 6 | 6.3620 s | 3.2449 s | 7.2144 s | 2,016,484 KiB |
| t4 / tb4 / ub512 | 0 / 6 | 6.3953 s | 3.2316 s | 7.2460 s | 2,016,484 KiB |

Micro-batch 256 reduced median complete wall time by only 0.521% and p95 by 0.437%, while median TTFT regressed by 0.411%. Those differences are far below the registered 5% gate. More importantly, neither policy produced one fully valid explanation.

The deterministic outputs were identical across the two policies, as expected for unchanged model and sampling settings. Per policy, failures included:

- wrong decision on four fixtures;
- wrong next action on five;
- missing required evidence on four;
- insufficient evidence explanation on three;
- one fabricated evidence identifier; and
- one forbidden claim that an unknown-certification device was certified.

The model often treated passing facts as a majority vote and ignored a single terminal failure. For example, it returned PASS when Play Protect had failed and when reboot persistence was false. This is precisely why performance selection was placed behind the development quality gate.

## What did not run

No development policy passed. Under the registration, that means:

- no policy was selected;
- no sealed model outputs were generated;
- B0, B1, B2, V3-A and V3-B sealed comparisons did not run;
- `safe_fast@5` is undefined rather than zero;
- no cache experiment or cache claim exists; and
- no Ubuntu 24.04 replication is justified.

Running the second image cannot repair an invalid deterministic generation policy. It would repeat compute after the registered stop condition.

## Cache instrumentation limitation

During cache-disabled prompt screening, the slot-erasure endpoint returned HTTP 501. The response field named `tokens_cached` equaled the full number of evaluated prompt tokens (258, 770 and 1,538), so it cannot be interpreted as a count of tokens reused from a previous request. The full prompt was reported as evaluated on each probe.

This did not affect a cache conclusion because cache variants never ran. A future apparatus must identify a supported cache-reset mechanism and distinguish tokens resident after evaluation from tokens actually reused before it may make a cache claim.

## Decision

Retain Version 2 as the submission result. Version 3 adds a reusable runtime-search apparatus and an important negative finding: optimizing the scheduler cannot rescue a model that fails the product contract. The next research version should address model/prompt capability on development data as a separate question; it must not retroactively loosen Version 3 or touch its sealed split.
