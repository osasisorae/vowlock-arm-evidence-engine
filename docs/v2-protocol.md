# Version 2 pre-registration

Registered before the first Version 2 execution on 14 August 2026.

Version 1 is complete evidence, not a draft to overwrite. Its sealed Runs 4–6 asked whether switching one Qwen2.5 1.5B Q4_0 workload from the baseline Arm CPU path to KleidiAI produced a material throughput gain. The replicated result was mixed and near-neutral. Version 2 does not pool with those runs.

## New question

Can a reusable, manifest-driven Arm inference laboratory expose useful model-size, memory, cold-start and throughput trade-offs while a stricter verifier preserves the bounded behaviour needed by a synthetic Setup Companion?

The machine-readable registration is [`experiment.v2.json`](../experiment.v2.json). It fixes the models, hashes, runtime revision, Arm host images, workloads, metrics, semantic criteria and claim thresholds before execution.

## Declared matrix

| Family | Quantization | Runtime paths | Purpose |
|---|---|---|---|
| Qwen2.5 1.5B Instruct | Q8_0 | baseline | higher-precision size and memory reference |
| Qwen2.5 1.5B Instruct | Q4_0 | baseline + KleidiAI | quantization and kernel comparison |
| Qwen2.5 0.5B Instruct | Q4_0 | baseline + KleidiAI | second model scale |

Each supported runtime condition is tested on balanced, prompt-heavy and generation-heavy workloads. `ubuntu-22.04-arm` is primary; `ubuntu-24.04-arm` is a separately reported cross-image replication. Host-image measurements are never pooled as if they were one machine.

## Measurements and boundaries

- Artifact size is exact bytes from the pinned, hash-verified GGUF.
- Peak RSS is the maximum resident set size reported by `/usr/bin/time -v` for a cold model process.
- Cold first-output time is the wall time of a fresh deterministic process producing one token. It is labelled as a proxy, not an exact server time-to-first-token measurement.
- Power is reported only when the runner exposes a readable hardware or kernel energy counter. Otherwise the evidence says `unavailable` and records what was checked.
- Throughput is reported separately for prompt processing and generation. No composite score will hide a regression.
- The primary size/memory claim requires at least a 20% measured reduction from 1.5B Q8_0 to 1.5B Q4_0 and every hard semantic check to pass.

## Setup Companion evaluation

The end-to-end fixtures are synthetic and safe. They contain observed device state, allowed actions, required facts, forbidden claims and an oracle decision. The model may explain or abstain; it never executes a command. Independent deterministic code checks the decision, evidence references, action boundary, required facts, forbidden claims and presence of an actual reason.

This is stronger than Version 1's one-token `READY` canary, but it is still not proof of free-form factual quality or real-device safety. Any ambiguous language can be routed to human review in the report.

## Judge access and cost

Anonymous workflow dispatch is deliberately not exposed because it would permit strangers to consume repository compute. Judges receive a seconds-long fixture validation command and a browser-readable replay of preserved evidence. Full native measurement remains manually dispatched by the repository owner on GitHub's standard hosted Arm64 runners. No paid resource is permitted.

## Stopping rules

We report the registered matrix even when it is neutral or slower. We do not add workloads after seeing results, replace a model because its result is inconvenient, estimate missing power data, use a real phone, or reinterpret Version 2 as a continuation of Runs 4–6.
