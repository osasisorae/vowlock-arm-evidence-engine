# Devpost submission copy

## Project name

VowLock Arm Evidence Engine

## Elevator pitch

An Arm64 evidence engine that removed an unearned model, then compiled and exhaustively checked all 648 declared safety states with zero model bytes.

## Track

Cloud AI

## Project overview

VowLock Arm Evidence Engine is a reusable, manifest-driven laboratory for optimizing the small offline explanation model proposed for VowLock Setup Companion. It runs pinned `llama.cpp` conditions on native Arm64, proves which backend actually ran, measures prompt and generation throughput separately, captures model size, peak RSS and cold explanation latency, and checks synthetic Setup Companion answers with an independent deterministic verifier.

The project began with one narrow KleidiAI comparison. Three sealed replications produced the same inconvenient result: +0.87% prompt processing and −1.58% generation. Instead of hiding the regression, I preserved it and pre-registered a separate Version 2 matrix before execution.

Version 2 compared Qwen2.5 1.5B Q8_0, 1.5B Q4_0 and 0.5B Q4_0 across baseline and KleidiAI runtime paths, three workload shapes and two native Arm Ubuntu images. The useful optimization was quantization, not the acceleration switch: Q4 was 43.72% smaller, used 34.67–34.68% less peak RSS, and the retained 1.5B Q4 condition passed all three fixtures with byte-identical explanations across both runtime variants and host images.

The fastest model did not win. Qwen2.5 0.5B reduced estimated workload time by 58–69%, but produced malformed, incomplete or weak explanations and was rejected. KleidiAI remained mixed and did not improve cold explanation latency, so it was rejected for this product slice. The evidence engine turns those trade-offs into an inspectable product decision rather than a benchmark headline.

Version 3 then tested runtime autotuning and stopped before sealed evaluation when both policies failed 0/6 development explanations. Version 4 followed that evidence instead of searching for a larger model: deterministic code owned every consequential field while the model was restricted to prose. On twelve sealed fixtures, the free-form model passed 0/12, constrained prose passed 6/12, and the deterministic template passed 12/12. The hybrid also passed all automatic checks, but only after six fallbacks. The template completed in 0.0816 ms median; the model-backed path took 3.0608 seconds, loaded a 1.066 GB artifact and reached about 2.05 million KiB peak server RSS. The final decision is to remove the model from this bounded task.

Version 5 turned that deletion into reusable infrastructure. Registered before implementation, its compiler enumerated all 648 states in the declared seven-field domain and emitted brief, detailed and progressively disclosed results with exact rules, evidence provenance and deterministic hashes. All 1,944 outputs passed every registered invariant and repeated byte-for-byte; 8/8 authority, evidence and hash corruptions were rejected. On native Arm, it processed 194,400 measured outputs at 33,351–50,378 outputs/s, peaked at 23,168 KiB RSS and used zero model bytes and network calls.

## Functionality and output

- Refuses native performance execution on non-Arm64 hosts.
- Consumes a machine-readable experiment manifest rather than hard-coding one model or workload.
- Verifies pinned model byte sizes and SHA-256 hashes.
- Builds baseline and KleidiAI-enabled binaries from one pinned `llama.cpp` commit.
- Proves `CPU_KLEIDIAI` buffer and I8MM selection in optimized conditions and rejects it in baselines.
- Runs balanced, prompt-heavy and generation-heavy workloads for every declared model/runtime condition.
- Captures exact artifact size, independent peak RSS, cold first-output proxy and cold complete-explanation latency.
- Reads real Linux energy counters when available and records `unavailable` rather than estimating power when absent.
- Generates and evaluates synthetic Setup Companion candidates; no command is executed.
- Independently rejects wrong decisions, wrong actions, missing evidence, token-only explanations, forbidden claims, privileged command patterns and undecodable output.
- Mutation-tests a constrained model boundary and falls back to deterministic prose without allowing the model to alter decisions, evidence or actions.
- Compiles a strictly typed safety policy across its complete 648-state declared domain, with deterministic provenance hashes and three reusable rendering forms.
- Provides a seconds-long, model-free fixture demo and a browser evidence replay for anonymous judges.

## Results

Q8_0→Q4_0 reduced exact artifact size from 1,894,532,128 to 1,066,227,232 bytes. Peak RSS fell from about 4.20 million KiB to 2.74 million KiB on both Arm host images.

Q4 reduced estimated balanced and prompt-heavy workload time by 3.18–6.90%, while generation-heavy time regressed by 4.01–4.87%. This is why the project does not claim a universal speedup.

The retained 1.5B Q4 baseline passed 3/3 fixtures with a 5.77–5.78 second cold mean. KleidiAI also passed but was slightly slower end-to-end. Q8 failed across host images, and 0.5B passed at most 1/3 fixtures. The final choice is Qwen2.5 1.5B Q4_0 baseline.

Version 4 supersedes that model choice for the bounded decision/explanation task. T0 retained exact authority and evidence in 0.0816 ms median with no model. H0 needed about 3.06 seconds and fell back in 6/12 cases. A disclosed, post-result qualitative audit also found that the surface verifier accepted misleading prose, so automatic acceptance is not presented as proof of factual safety or comprehension.

Version 5 supersedes fixture sampling for the declared compiler domain. It found 600 STOP states, 47 REQUEST_EVIDENCE states and exactly one PASS state. Every state passed in B0, D0 and P0; all eight registered corruptions were caught. This establishes exhaustive registered-property coverage for the finite domain—not real-device safety, theorem-prover verification or human comprehension.

## How it was built

The project uses `llama.cpp`, Arm KleidiAI, official Qwen GGUF artifacts, CMake, Bash, Python's standard library and GitHub's free standard `ubuntu-22.04-arm` and `ubuntu-24.04-arm` hosted runners. No paid VM, model API, subscription or device was used.

The method applies ideas from my Stanford CS329A self-study: controlled baselines, generator–verifier separation, sealed replication, distribution shift, adaptive compute boundaries and explicit distinction between operational success and hypothesis support.

## Challenges

Early runs failed on build-target and observability assumptions. Then a green workflow exposed a weak semantic check. After sealing the throughput replications, I repaired the verifier separately.

Version 2 found the opposite verifier problem: valid natural explanations were rejected for not repeating underscore-separated IDs literally, while invalid UTF-8 crashed one evaluation. The repair allowed human-readable evidence concepts and converted invalid bytes into explicit failed candidates without changing any registered model, prompt, fixture, workload or threshold.

The hardest result was accepting that the smallest and fastest model was not the correct product choice. A speedup that destroys the behaviour being accelerated is not an optimization.

Version 4 exposed a deeper verifier limit. Immutable structured authority kept the decision correct, yet automatically accepted prose could still reverse `unknown` into “restored” or “certified.” The project therefore reports the automatic score and the qualitative contradiction instead of letting a 12/12 hybrid badge overstate the evidence.

## Accomplishments

- Preserved a neutral/regressive KleidiAI result instead of cherry-picking prompt throughput.
- Pre-registered Version 2 before execution and kept it separate from the original result.
- Expanded one benchmark into 30 native Arm performance conditions across two host images.
- Added independent resource and end-to-end agent measurements.
- Found a material, reproducible quantization win and a clear product model choice.
- Rejected a 58–69% faster model because it failed the quality gate.
- Packaged the method as an MIT-licensed template with 56 local tests, fast fixture validation, machine summaries and a public evidence page.
- Moved consequential authority out of language generation and mutation-tested the boundary with eight attacks.
- Found that removing a 1.066 GB model produced the strongest latency, memory and reliability result for this bounded task.
- Converted that removal into a reusable compiler with complete declared-domain coverage, evidence provenance and mutation-tested deterministic outputs.

## What was learned

An optimization flag is a hypothesis, not a result. Prompt and generation operations can move in opposite directions. A verifier can be too weak or too brittle. Workflow success describes the apparatus, not whether the claim passed. Quantization, model scale and runtime kernels must be evaluated against the same product behaviour—and sometimes the strongest AI optimization is recognizing that a deterministic program should replace the model. When the domain is truly finite, exhaustive compilation can provide stronger evidence than additional inference-time compute.

## What is next

Use the deterministic template as the default for this bounded Setup Companion task. A language model may return only for a separately registered task that templates cannot cover and only with independent factual and comprehension evaluation. The Q8 host-image instability remains a separate toolchain question. Real-device work remains out of scope until synthetic evidence, verifier-restoration research and explicit safety gates are complete.

## Prior work and hackathon-period disclosure

VowLock existed before the challenge. This submission does not represent the VowLock product or the separate ADTC Setup Companion concept as hackathon-period work. The Arm evidence engine, manifests, native benchmark harnesses, runtime and semantic verifiers, fixture set, two-host matrix, resource instrumentation, evidence reports, live replay and preserved run history are the new challenge-period artifact.

## Links

- Source: https://github.com/osasisorae/vowlock-arm-evidence-engine
- Live evidence: https://osasisorae.github.io/vowlock-arm-evidence-engine/
- Version 2 result: https://github.com/osasisorae/vowlock-arm-evidence-engine/blob/main/docs/v2-results.md
- Version 2 protocol: https://github.com/osasisorae/vowlock-arm-evidence-engine/blob/main/docs/v2-protocol.md
- Version 4 result: https://github.com/osasisorae/vowlock-arm-evidence-engine/blob/main/docs/v4-results.md
- Version 4 native run: https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31800634600
- Version 5 result: https://github.com/osasisorae/vowlock-arm-evidence-engine/blob/main/docs/v5-results.md
- Version 5 native run: https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31803354032
- Final two-host run: https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31785110768
- Version 1 replication: https://github.com/osasisorae/vowlock-arm-evidence-engine/blob/main/docs/results.md
