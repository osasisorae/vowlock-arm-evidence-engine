# Arm64 optimization experiment

## Question

On one real Arm64 cloud host, how much does the KleidiAI CPU backend change Qwen2.5 1.5B Q4_0 prompt-processing and generation throughput relative to an otherwise identical `llama.cpp` build?

## Hypothesis

The optimized build will improve mean prompt-processing and/or generation throughput without changing the model hash or causing the fixed explanation contract to regress.

Protocol correction recorded after Runs 4–6: the original text said "median," but the implemented and reported `llama-bench` field is `avg_ts`, the arithmetic mean of five internal samples. No median was calculated. The correction changes the description to match the evidence; it does not alter or rerun the measurements.

## Independent variable

Only `GGML_CPU_KLEIDIAI` changes between the primary baseline and optimized builds.

## Controls

- exact `llama.cpp` revision: `1ee1cd9bc65a56ab50e2ed19a48709dc42d1dd9d`;
- exact model revision, file and SHA-256;
- one GitHub-hosted `ubuntu-22.04-arm` job, with both conditions run sequentially on that same ephemeral host;
- identical prompt-token and generation-token counts;
- five repetitions after an explicit smoke/warm-up run;
- raw JSON retained before any summary is written.

## Primary metrics

1. Prompt-processing tokens per second at 512 prompt tokens.
2. Generation tokens per second at 128 generated tokens.
3. Relative improvement: `(optimized / baseline - 1) × 100`.

## Secondary gates

- optimized log proves that `CPU_KLEIDIAI` was selected;
- no crash or out-of-memory run;
- same model SHA-256 in both conditions;
- a deterministic one-token chat contract requires both conditions to return exactly `READY` and to match each other;
- environment, compiler and source revision are recorded.

The one-token contract is a narrow equivalence canary, not an evaluation of explanation usefulness or safety. Backend selection is verified in a separate verbose raw-completion run so runtime diagnostics cannot be mistaken for generated text. The output-contract run uses the model's chat template, greedy decoding, a fixed seed, output-only log verbosity and a standalone verifier that rejects two matching-but-wrong outputs as well as backend divergence.

## Interpretation

A speed increase is an inference-runtime result, not evidence that the explanation is safer or more useful. Quality is evaluated separately. A result from QEMU or another emulator may validate the script but cannot support a performance claim.

## Stop conditions

Stop and report the limitation if the host is not real Arm64, the model hash differs, the source revisions differ, KleidiAI is not actually selected, either build fails, or the experiment requires changing more than the registered variable.

## Resource boundary

This experiment must not create a paid cloud VM or invoke a metered API. The intended target is GitHub's standard hosted Arm64 runner in a public repository. If that free runner is unavailable or unsuitable, the run stops until another explicitly free real-Arm target is verified.
