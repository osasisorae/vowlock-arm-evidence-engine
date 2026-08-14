# Devpost submission copy

## Project name

VowLock Arm Evidence Engine

## Tagline

An Arm64 benchmark that refuses to call an optimization a win until runtime selection, replicated speed and output validity all agree.

## Track

Cloud AI

## Project overview

VowLock Arm Evidence Engine is a reproducible CPU-inference experiment for the small offline model proposed for VowLock Setup Companion. It builds the same pinned `llama.cpp` revision twice on a real four-core Arm64 cloud runner, changing only `GGML_CPU_KLEIDIAI`. It proves that the optimized binary selects KleidiAI I8MM kernels, benchmarks both conditions, preserves failed and successful runs, and independently checks a deterministic output contract.

The interesting result is not a convenient victory. Across three identical workflows, KleidiAI improved prompt processing by 0.87% and reduced token-generation speed by 1.58%. The backend genuinely ran, but this workload did not receive a material overall speedup. The project turns that mixed result into a reusable developer artifact rather than hiding it or selecting only the flattering metric.

It should win because Arm optimization needs trustworthy evidence as much as it needs fast kernels. A developer can reuse this pattern to freeze a comparison, prove that an accelerated backend was selected, preserve raw evidence, replicate the result and prevent a green workflow badge from standing in for output quality.

## Functionality and output

- Refuses performance execution on non-Arm64 hosts.
- Downloads one pinned Qwen2.5 1.5B Instruct Q4_0 artifact and verifies its SHA-256.
- Builds baseline and KleidiAI-enabled `llama.cpp` binaries from the same source revision.
- Requires the optimized log to select `CPU_KLEIDIAI` and rejects that selection in the baseline.
- Runs fact-equivalent 512-token prompt-processing and 128-token generation benchmarks with five internal repetitions.
- Produces raw JSON plus a machine-readable relative-change summary.
- Runs a deterministic chat-template canary and independently rejects unequal outputs or two equal-but-wrong outputs.
- Publishes the complete eight-run history, including three setup failures and the known limitation in Runs 4–6.

The final output is an MIT-licensed evidence engine, a replicated benchmark dataset, a corrected semantic verifier and a judge-facing evidence report.

## How it was built

The project uses `llama.cpp`, its KleidiAI CPU integration, Qwen2.5 1.5B Instruct Q4_0, CMake, Bash, Python's standard library and GitHub's `ubuntu-22.04-arm` hosted runner. No paid VM, metered model API or subscription was used.

The experimental method was influenced by Stanford CS329A study: controlled baselines, generator–verifier separation, sealed replications, distribution/observable mismatch, and explicit claim boundaries. KleidiAI kernel acceleration is a systems-layer optimization rather than an inference-time agent architecture.

## Challenges

The first two runs misunderstood which `llama.cpp` target was available under the chosen build flags. Run 3 exposed a verifier false negative: KleidiAI was compiled in, but the detailed buffer-selection evidence was hidden at default log verbosity. Run 4 finally measured performance and exposed the opposite problem—the workflow was green even though the supposed semantic smoke prompt was not obeyed. Runs 5 and 6 intentionally preserved Run 4 unchanged for strict replication. Only then was the semantic gate repaired and validated separately in Run 7.

## Accomplishments

- Obtained three independent, directionally consistent measurements from the exact same commit.
- Verified actual KleidiAI I8MM selection rather than inferring acceleration from a build flag.
- Preserved a mixed/near-neutral result without cherry-picking prompt throughput.
- Built an independent output verifier that rejects equal-but-wrong answers.
- Created a reusable, zero-cost Arm64 developer workflow and a public evidence trail.

## What was learned

An optimization flag is a hypothesis, not a result. Prompt processing and generation can react differently to the same kernel path. A verifier must observe the output it claims to judge. Replication should happen before repairing a known secondary defect when the goal is to preserve a strict comparison. Most importantly, a negative or neutral result can still improve a product decision when its scope is precise.

## What is next

The registered performance hypothesis is closed as mixed/near-neutral for this model, quantization, workload and runner class. Future work will be separately registered: workload mixes closer to Setup Companion explanations, independent peak-memory and end-to-end latency measurement, and a fixture set evaluating factuality, missing-evidence abstention and action boundaries. Those later results will not be silently pooled with this experiment.

## Prior work and hackathon-period disclosure

VowLock existed before the challenge. This submission does not claim that the VowLock product or the separate ADTC Setup Companion concept was created during the hackathon. The VowLock Arm Evidence Engine repository, controlled Arm64 benchmark harness, summarizer, runtime-selection verifier, output-contract verifier, eight-run evidence trail, result report and submission assets were created as a new optimization artifact during the challenge period.

## Links

- Source: https://github.com/osasisorae/vowlock-arm-evidence-engine
- Evidence report: https://osasisorae.github.io/vowlock-arm-evidence-engine/
- Cover image: https://github.com/osasisorae/vowlock-arm-evidence-engine/blob/main/docs/assets/result-card.png
- Replicated results: https://github.com/osasisorae/vowlock-arm-evidence-engine/blob/main/docs/results.md
- Validated Run 7: https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31777533677
- Final submission validation: https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31779088483
