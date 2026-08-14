# Version 3 registered protocol

Registered: 14 August 2026, before Version 3 implementation or native execution.

Status: **frozen protocol**. The machine-readable registration is [`experiment.v3.json`](../experiment.v3.json). The earlier [`v3-research-proposal.md`](v3-research-proposal.md) explains the source-to-design reasoning; this file records the approved experiment.

## Question

On the same native four-core Arm runner and retained Qwen2.5 1.5B Q4_0 model, can bounded host-aware search over `llama.cpp` runtime settings reduce persistent-server first-token and complete-valid-explanation latency relative to the static Version 2 policy while every sealed Setup Companion fixture and verifier mutation test passes?

## Frozen choices

- One model, quantization, pinned `llama.cpp` revision and baseline Arm backend.
- Legal settings only: decode threads `1–4`, prompt threads `1–4`, physical micro-batch `64/128/256/512`, cache off/on.
- Deterministic staged search. No model generates commands or modifies source.
- Six development fixtures may guide selection. Twelve sealed fixtures may not.
- Eight registered one-fault mutations test the verifier before any candidate policy can be retained.
- Primary host: `ubuntu-22.04-arm`. The `ubuntu-24.04-arm` replication is conditional on a sound primary run and remaining time.
- No paid resource and no real device.

## Primary comparison

`B1`, a persistent server using four prompt threads, four decode threads, micro-batch 512 and cache disabled, is compared with `V3-A`, the development-selected policy with cache disabled. `B2` versus `V3-B` is the separately reported cache comparison. `B0` preserves the earlier fresh-process measurement but is not the primary baseline.

## Passing result

A V3 optimization claim passes only when:

1. all retained outputs pass every deterministic hard check;
2. all dangerous registered mutations are caught;
3. median complete-valid latency improves by at least 5% over B1;
4. p95 complete-valid latency does not regress by more than 5%; and
5. any cache claim includes a positive reused-token count.

`safe_fast@5` counts sealed requests that both pass every hard check and improve paired complete latency by at least 5%. A fast invalid response counts as failure, not speedup.

## Amendment rule

Syntax errors or apparatus defects may be repaired in new commits and must be logged. The model, search space, fixture contents, mutations, baseline, metrics, thresholds and selection rule may not change after this registration. If the apparatus cannot implement the registered study, report that limitation and retain Version 2.
