# Version 2 result: quantization wins, the smaller model does not

Version 2 was [registered before execution](v2-protocol.md) and remains separate from the sealed Version 1 Runs 4–6. The final two-host apparatus run is [GitHub Actions Run 31785110768](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31785110768), executed from commit `6dceab7` on native `ubuntu-22.04-arm` and `ubuntu-24.04-arm` standard hosted runners.

## Decision

**Retain Qwen2.5 1.5B Q4_0 on the baseline Arm CPU path for the next synthetic Setup Companion experiment. Do not enable KleidiAI for this pinned workload. Reject the 0.5B model and the tested Q8_0 condition.**

Q4_0 produced the useful Pareto move: materially lower storage and memory, modestly better balanced and prompt-heavy estimated time, and more stable fixture behaviour. The 0.5B model was dramatically faster but did not cross the quality boundary. KleidiAI again produced small prompt gains and generation regressions without improving cold explanation time.

## Q8_0 → Q4_0 resource effect

| Native Arm host image | Artifact reduction | Peak RSS reduction | Cold one-token process | Registered all-condition claim |
|---|---:|---:|---:|---|
| Ubuntu 22.04 | 43.72% | 34.67% | 2.09s → 1.58s | Not supported |
| Ubuntu 24.04 | 43.72% | 34.68% | 1.99s → 1.53s | Not supported |

Artifact bytes are exact: Q8_0 is 1,894,532,128 bytes and Q4_0 is 1,066,227,232 bytes. Peak RSS is independently captured from a fresh process with GNU `time -v`. Cold one-token time includes model loading and is a proxy, not streaming server TTFT.

The registered all-condition claim remains false because not every model condition passed semantic evaluation. That strict result does not erase the narrower product decision supported by the Q4_0 condition.

## Operation-weighted estimated workload time

Estimated time is `prompt tokens ÷ prompt tokens/s + generated tokens ÷ generation tokens/s`. It prevents a small prompt gain from hiding a generation regression.

| Workload | Ubuntu 22.04 Q8→Q4 | Ubuntu 24.04 Q8→Q4 | Interpretation |
|---|---:|---:|---|
| Balanced: 512 prompt / 128 generation | 8.03s → 7.57s (5.63% less) | 7.79s → 7.54s (3.18% less) | modest improvement |
| Prompt-heavy: 2048 / 32 | 36.41s → 33.90s (6.90% less) | 35.68s → 33.92s (4.94% less) | clearest Q4 benefit |
| Generation-heavy: 128 / 256 | 7.90s → 8.21s (4.01% more) | 7.77s → 8.15s (4.87% more) | Q4 regression |

There is no universal speedup. The operation mix determines the outcome.

## End-to-end synthetic explanation result

Each number below is a fresh process from prompt submission through a complete explanation, followed immediately by independent deterministic verification.

| Condition | Ubuntu 22.04 | Ubuntu 24.04 | Decision |
|---|---:|---:|---|
| 1.5B Q4_0 baseline | 3/3 · mean 5.77s | 3/3 · mean 5.78s | retain |
| 1.5B Q4_0 + KleidiAI | 3/3 · mean 5.84s | 3/3 · mean 5.82s | reject runtime switch |
| 1.5B Q8_0 baseline | 0/3 · mean 9.36s | 2/3 · mean 6.41s | reject |
| 0.5B Q4_0 baseline | 0/3 · mean 3.35s | 1/3 · mean 2.08s | reject |
| 0.5B Q4_0 + KleidiAI | 1/3 · mean 2.73s | 1/3 · mean 2.51s | reject |

All six 1.5B Q4_0 candidates were byte-identical between baseline and KleidiAI. They were also byte-identical across both host images. This supports runtime equivalence for the three registered fixtures; it does not prove general factual quality.

The 0.5B model reduced estimated workload time by roughly 58–69%, but malformed or weak outputs make that gain unusable. The Q8_0 condition emitted invalid text on Ubuntu 22.04 and showed a prose/action contradiction on Ubuntu 24.04. The latter came from a non-blinded developer-side qualitative audit and still needs independent human review.

## KleidiAI result across workloads

For 1.5B Q4_0, KleidiAI improved prompt throughput by 0.42–1.13% but reduced generation throughput by 0.54–4.01%. It improved estimated prompt-heavy time by only 0.34–0.39%, while balanced and generation-heavy time regressed. Cold explanation means were 0.6–1.2% slower. This confirms Version 1's conclusion across a broader matrix: the backend is active, but it is not the useful optimization for this product slice.

## Power and host boundary

Neither GitHub-hosted Arm image exposed a readable `/sys/class/powercap` energy counter. Power is therefore `unavailable`; no estimate or proxy was substituted. The two jobs use different supported Ubuntu Arm images but the same advertised four-core, 16 GB standard runner specification. This is cross-image replication, not evidence across two hardware classes.

## Preserved evidence

- [Ubuntu 22.04 machine summary](../evidence/v2-run-2-ubuntu-22.04-arm.json)
- [Ubuntu 24.04 machine summary](../evidence/v2-run-2-ubuntu-24.04-arm.json)
- [Qualitative audit and its limitations](../evidence/v2-run-2-qualitative-review.json)
- [Version 2 run log](v2-run-log.md)
- [Full workflow and downloadable raw artifacts](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31785110768)

## Claim boundary

This is synthetic, model-level evidence. No phone was connected, no privileged command was generated or executed, and no real-device safety claim follows. The next experiment may use only the retained 1.5B Q4_0 condition, a sealed fixture set and independent human review before any device study is considered.
