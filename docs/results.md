# Replicated benchmark result

Runs 4–6 execute the same repository commit, pinned model, `llama.cpp` revision, flags, workload and four-core `ubuntu-22.04-arm` runner class. Each workflow completed and preserved its raw artifact. The run links remain the source for the complete logs; the run-level summaries are also retained in [`evidence/benchmark-runs.json`](../evidence/benchmark-runs.json).

| Run | Baseline prompt | KleidiAI prompt | Change | Baseline generation | KleidiAI generation | Change |
|---|---:|---:|---:|---:|---:|---:|
| [4](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31741649412) | 129.9568 | 131.2192 | +0.97% | 35.6226 | 35.4291 | -0.54% |
| [5](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31776041675) | 129.6878 | 130.7124 | +0.79% | 34.0039 | 33.1110 | -2.63% |
| [6](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31776057917) | 130.2142 | 131.3129 | +0.84% | 35.8139 | 35.2321 | -1.62% |
| Pooled means | 129.9529 | 131.0815 | +0.87% | 35.1468 | 34.5907 | -1.58% |

All rates are tokens per second. The pooled percentage compares the mean optimized rate with the mean baseline rate across the three independent workflows; it does not treat the five internal `llama-bench` repetitions as five independent machines.

## Interpretation

The direction replicated: KleidiAI produced a small prompt-processing increase and a small generation decrease in every workflow. This does not support the broad product hypothesis that enabling KleidiAI makes this registered local-model workload materially faster. It supports a narrower systems result: the backend and I8MM kernels were genuinely selected, but their benefit depends on the operation, and the existing baseline Arm CPU repacking path is already competitive here.

No statistical-significance or universal KleidiAI claim is made from three hosted-runner observations. The result is scoped to Qwen2.5 1.5B Instruct Q4_0, the pinned `llama.cpp` revision, four threads, a 512-token prompt-processing test and a 128-token generation test on this runner class.

The initial experiment document used the word "median," but the implemented `llama-bench` metric was `avg_ts`, the arithmetic mean of five internal samples. This post-run terminology correction is recorded explicitly rather than silently describing a statistic that was never calculated.

## Claim boundaries

- Runtime selection is verified: optimized logs contain `KLEIDIAI = 1`, select I8MM Q4/Q8 kernels and load a `CPU_KLEIDIAI` model buffer; baseline logs do not.
- No independent peak-process-memory measurement was collected.
- Runs 4–6 contain a known semantic-gate defect. Their raw completion did not satisfy the requested `READY` contract and the script did not assert it. The throughput result remains valid, but those runs do not establish semantic output equivalence.
- The semantic gate was repaired in separately versioned Run 7. Both conditions returned exactly `READY`, and the independent verifier confirmed expected content and equivalence. Run 7's performance result is not silently pooled with Runs 4–6.
- The repaired one-token canary tests a narrow deterministic contract. It does not establish the factual accuracy, safety or usefulness of free-form product explanations.
