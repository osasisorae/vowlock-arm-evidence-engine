# Experimental run log

This log records failed as well as successful runs. A failed setup is evidence about the experiment, not benchmark evidence about KleidiAI performance.

## Run 1 — 2026-08-13

- GitHub Actions run: `31709064793`
- Commit: `70db580b8bdb0c478fedcbec2d0cfef0c541969f`
- Runner: GitHub-hosted `ubuntu-22.04-arm`; the architecture check passed.
- Outcome: setup failure before either benchmark condition ran.
- Cause: the configuration set `LLAMA_BUILD_SERVER=OFF` while requesting `llama-cli`. In the pinned llama.cpp revision, `tools/cli` is only added when the server option is enabled. The missing target caused `cmake --build` to exit with status 2.
- Interpretation: this run says nothing about baseline or KleidiAI throughput. No result files were produced, and no performance claim is permitted from it.
- Initial correction: examples were enabled under the mistaken assumption that the CLI was an example target. Stage logging was also added so subsequent failures would be inspectable.

## Run 2 — 2026-08-13

- GitHub Actions run: `31711976309`
- Commit: `789d9ab7332c5a9aba94660947a8cf94b4aee99a`
- Runner: GitHub-hosted `ubuntu-22.04-arm`; architecture, dependency and summarizer checks passed.
- Outcome: setup failure before either benchmark condition ran.
- Evidence: the baseline configuration and `llama-bench` target built successfully. The build then reported `No rule to make target 'llama-cli'` and the stage log recorded status 2 at line 66.
- Cause: enabling examples did not affect the pinned revision's CLI gate. The upstream `tools/CMakeLists.txt` adds `tools/cli` only inside `if (LLAMA_BUILD_SERVER)`.
- Interpretation: this run also says nothing about KleidiAI performance. It validates the new failure-log path but provides no baseline or optimized measurement.
- Correction: use the standalone `llama-completion` target for smoke inference. It is part of the enabled tools tree and does not require the server or examples.

## Run 3 — 2026-08-13

- GitHub Actions run: `31716397091`
- Commit: `f773e49a82d21b00f6ae22e1d8260a52d03fca29`
- Runner: GitHub-hosted `ubuntu-22.04-arm`; architecture, dependency and summarizer checks passed.
- Outcome: verification failure after both builds and both smoke inferences completed, but before the paired throughput benchmark began.
- Evidence: the optimized smoke log reports `KLEIDIAI = 1` in `system_info`, while the baseline log does not. The optimized log also reports that Q6_K tensors are not accelerated because KleidiAI kernels are available for Q4_0 and Q8_0. The script then exited with status 3 because it could not find the literal string `CPU_KLEIDIAI`.
- Cause: the runtime guard expected llama.cpp's detailed `load_tensors: CPU_KLEIDIAI model buffer` message, but the pinned tool's default verbosity omitted the detailed model-buffer lines from both smoke logs. The check therefore confused missing log evidence with a missing backend: a verifier false negative.
- Interpretation: this run proves that the optimized binary was compiled with and exposed KleidiAI, but `KLEIDIAI = 1` alone does not satisfy the stricter claim that the model's Q4_0 tensors selected the KleidiAI buffer. No throughput claim is permitted because `llama-bench` never ran.
- Correction: rerun smoke inference with verbose logging and `--device none`, retain the strict `CPU_KLEIDIAI` buffer-selection gate, and print the relevant smoke log when that gate fails. Apply the same device restriction to both benchmark conditions so the registered comparison remains fact-equivalent.

## Run 4 — 2026-08-13

- GitHub Actions run: [`31741649412`](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31741649412)
- Commit: `cf3ab598f0769089e866bdd15d903d39fe347160`
- Runner: GitHub-hosted `ubuntu-22.04-arm`; `aarch64`, four CPU cores, with Arm features including ASIMDDP, SVE, SVE2 and I8MM.
- Outcome: both conditions built, runtime backend selection was verified, and the paired `llama-bench` measurement completed. This is the first performance result from the experiment.
- Runtime evidence: the optimized log reports `KLEIDIAI = 1`, selects I8MM Q4 and Q8 kernels, and loads `702.86 MiB` through the `CPU_KLEIDIAI` model buffer. The baseline has no `CPU_KLEIDIAI` buffer. This satisfies the strict backend-selection gate that stopped Run 3.

| Metric | Baseline | KleidiAI | Change |
|---|---:|---:|---:|
| Prompt processing | 129.9568 tokens/s | 131.2192 tokens/s | +0.97% |
| Token generation | 35.6226 tokens/s | 35.4291 tokens/s | -0.54% |

- Preliminary interpretation: under this one registered workload on this runner, KleidiAI is approximately neutral. Prompt processing improved slightly while generation regressed slightly; neither difference is yet large enough to claim a material product benefit. Identical reruns are required before treating the direction or size as stable.
- Memory boundary: the optimized model allocation is split between `CPU_KLEIDIAI` (`702.86 MiB`) and `CPU_REPACK` (`182.57 MiB`), approximately equal in total to the baseline `CPU_REPACK` allocation (`885.41 MiB`). This run did not measure independent peak process memory, so it does not support a memory-saving claim.
- Output-quality limitation: the smoke commands completed, but the raw completion tool generated `Return only the word READY. The word is not` rather than the requested word `READY`. The script checked backend evidence but did not assert the generated text. Run 4 therefore validates the build, runtime selection and throughput path—not semantic output equivalence or the advertised fixed output contract.
- Next decision: rerun this exact performance comparison twice without changing the workload, and repair the output-quality gate as a separate harness correction. Do not discard or tune away a neutral result merely because the optimization hypothesis was not confirmed.

### Replication protocol after Run 4

Runs 5 and 6 must execute the exact remote commit used by Run 4 (`cf3ab598f0769089e866bdd15d903d39fe347160`). No benchmark, workflow, prompt, build flag, model, verifier or documentation commit may be pushed before both workflows have captured their artifacts. The semantic-gate defect is known, but repairing it first would create a new experimental version and prevent the next measurements from being strict replications of Run 4. After both artifacts are preserved, the gate repair will be versioned separately and its later runs will not be silently pooled with Runs 4–6.

## Run 5 — 2026-08-14

- GitHub Actions run: [`31776041675`](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31776041675)
- Commit: `cf3ab598f0769089e866bdd15d903d39fe347160`, identical to Run 4.
- Outcome: success; raw artifact preserved.
- Prompt processing: 129.6878 baseline versus 130.7124 KleidiAI tokens/s, a change of +0.79%.
- Generation: 34.0039 baseline versus 33.1110 KleidiAI tokens/s, a change of -2.63%.
- Interpretation: the same mixed direction as Run 4, with a larger generation regression.

## Run 6 — 2026-08-14

- GitHub Actions run: [`31776057917`](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31776057917)
- Commit: `cf3ab598f0769089e866bdd15d903d39fe347160`, identical to Runs 4 and 5.
- Outcome: success; raw artifact preserved.
- Prompt processing: 130.2142 baseline versus 131.3129 KleidiAI tokens/s, a change of +0.84%.
- Generation: 35.8139 baseline versus 35.2321 KleidiAI tokens/s, a change of -1.62%.
- Interpretation: the same mixed direction as Runs 4 and 5.

## Replication conclusion

Across Runs 4–6, the pooled means changed from 129.9529 to 131.0815 prompt-processing tokens/s (+0.87%) and from 35.1468 to 34.5907 generation tokens/s (-1.58%). All three independent workflows agree on direction. The registered comparison therefore does not demonstrate a material overall speedup for this workload. See [`docs/results.md`](results.md) for the result table and claim boundaries.

## Run 7 — 2026-08-14

- GitHub Actions run: [`31777533677`](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31777533677)
- Commit: `5e4d58a`, the separately versioned output-contract repair.
- Outcome: success; raw artifact preserved.
- Backend verification: passed independently through the verbose `CPU_KLEIDIAI` selection gate.
- Semantic contract: baseline output `READY`; optimized output `READY`; exact expected-output and equivalence checks both passed. The machine-readable report is retained in [`evidence/harness-validation-run-7.json`](../evidence/harness-validation-run-7.json).
- Prompt processing: 130.1884 baseline versus 131.1367 KleidiAI tokens/s, a change of +0.73%.
- Generation: 36.3025 baseline versus 34.6287 KleidiAI tokens/s, a change of -4.61%.
- Interpretation: the repaired observable works and rejects wrong content rather than treating successful execution as quality. Its throughput result again has the same mixed direction, but Run 7 is not pooled with Runs 4–6 because the preceding harness operations changed.
- Limitation: one token of deterministic equivalence is a canary, not evidence that free-form VowLock explanations are accurate, safe or useful.

## Run 8 — 2026-08-14

- GitHub Actions run: [`31779088483`](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31779088483)
- Commit: `cd59de9`, the judge-facing submission package with updated GitHub Action runtimes.
- Outcome: success; raw artifact preserved; no deprecated Node 20 action warning.
- Runtime selection: optimized logs selected the I8MM Q4 kernel, `CPU_KLEIDIAI` model buffer and `KLEIDIAI = 1` path.
- Semantic contract: both conditions returned exactly `READY`; expected content and equivalence passed.
- Prompt processing: 130.0288 baseline versus 131.2159 KleidiAI tokens/s, a change of +0.91%.
- Generation: 35.9257 baseline versus 35.4040 KleidiAI tokens/s, a change of -1.45%.
- Interpretation: final submission validation passed and again produced the same mixed direction. It is not pooled into Runs 4–6 because it belongs to the repaired harness and submission version.

## What the runs are teaching us

The first three runs are not three failed optimization results. They are three failures of the experimental apparatus: an unavailable target, a mistaken correction to that target, and a verifier that rejected a valid intermediate state because its expected evidence was hidden. Run 4 finally measured the optimization and produced a useful near-neutral result, while also revealing that a green workflow can contain an unverified secondary claim. This distinction matters: workflow success, runtime selection, throughput performance and semantic validity are separate claims and need separate evidence.
