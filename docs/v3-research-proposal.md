# Version 3 research proposal: optimize the runtime policy, not another model

Status: **research draft, not pre-registered and not executed**. Written 14 August 2026 after Version 2 was frozen. None of the paper previews below changes the reading status in OsasLearns; only the authors' abstracts and directly relevant official documentation were reviewed for this design.

## Decision in one sentence

Version 3 should keep the Version 2 winner—Qwen2.5 1.5B Q4_0 on the baseline Arm CPU path—and test whether a small host-aware autotuner can choose better `llama.cpp` thread, batch and prompt-cache settings for the Setup Companion's actual request shape while every sealed explanation still passes.

It should not add another model, quantization or acceleration backend before the deadline. Version 2 already answered that layer.

## What Arm's documentation teaches us

### 1. KleidiAI is deliberately only one layer

[KleidiAI](https://github.com/ARM-software/kleidiai) supplies Arm-specific micro-kernels for operations such as packing and matrix multiplication. It has no internal scheduling, threading, memory allocation or memory management. The surrounding framework owns those decisions. Its variants target architectural features including DotProd, I8MM, SVE, SME and SME2.

This changes how Version 1 should be interpreted. We tested a genuine I8MM micro-kernel switch while holding the framework policy fixed at four threads. A near-neutral end-to-end result does not mean Arm optimization is exhausted; it means the micro-kernel was not the useful control for that model, runner and operation mix. The next honest layer is the runtime policy that dispatches work to those kernels.

### 2. Prefill and decode are different systems problems

Arm's [Streamline analysis of llama.cpp prefill and decode](https://learn.arm.com/learning-paths/servers-and-cloud-computing/llama_cpp_streamline/4_analyze_token_prefill_decode/) reports that prefill performs substantial GEMM work and is comparatively compute-heavy, while token-by-token decode performs substantial GEMV work and experiences far more last-level-cache misses and memory stalls. In Arm's example, memory-related backend stalls were about 10% during prefill and about 50% during decode.

The accompanying [operator-level analysis](https://learn.arm.com/learning-paths/servers-and-cloud-computing/llama_cpp_streamline/5_operator_deepdive/) attributes most prefill time to matrix-multiplication GEMM nodes in attention and feed-forward layers, while decode is dominated by GEMV. This is a mechanistic explanation for our repeated observation that prompt processing improved slightly while generation regressed. Averaging both into one throughput number would erase the architecture.

### 3. The framework exposes separate controls for the two phases

Arm's [multi-threading guide](https://learn.arm.com/learning-paths/servers-and-cloud-computing/llama_cpp_streamline/6_multithread_analyze/) shows that `llama.cpp` owns a threadpool, exposes thread count and CPU-affinity controls, and divides large matrix operations across threads. The official [`llama.cpp` completion documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/completion/README.md) separately exposes generation threads (`-t`) and prompt/batch threads (`-tb`), noting that some systems benefit from more threads for prompt processing than generation. It also exposes physical micro-batch size (`-ub`), which can improve prompt throughput at a memory cost.

Version 2 fixed all of these instead of measuring them. That was correct for isolating quantization and KleidiAI. It is now the clearest untested Arm optimization surface.

### 4. Our end-to-end metric was still a cold-process proxy

The official [`llama.cpp` benchmark documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/llama-bench/README.md) warns that `llama-bench` excludes tokenization and sampling. Version 2 compensated with fresh-process explanation timing, but that includes model loading and is unlike the persistent local service a Setup Companion would use.

The official [`llama-server` documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) provides internal prompt and generation timings, streaming responses, prompt-cache reuse, cache-hit token counts and Prometheus metrics. V3 can therefore measure actual request-to-first-token and request-to-complete-response latency in a persistent process, while retaining separate prompt and generation evidence.

### 5. Repeated instructions are an optimization opportunity

Every Setup Companion request shares a long system policy, output schema and safety boundary. The server enables prompt caching by default and reports reused tokens. The unread [CacheBlend](https://arxiv.org/abs/2405.16444) paper studies the broader problem of composing cached context chunks and reports large TTFT improvements in its own RAG settings. V3 will not claim to reproduce CacheBlend; it borrows only the experimentally useful question: how much of our repeated prefix is actually reused, and what paired latency change follows in `llama-server`?

### 6. Arm asks for an optimization story that can be validated

The challenge organizer's [optimization reminder](https://arm-ai-optimization-challenge.devpost.com/updates) says a strong entry should identify the technical change and show how it improved latency, throughput, memory, model size, power, deployment time, developer workflow, setup complexity or another declared metric. V3's reusable artifact is therefore not another favorable number. It is a one-command, host-aware tuning report whose selected policy can be replayed and whose quality boundary can fail.

## What the unread papers suggest—not what I have finished reading

These are research previews from the papers' abstracts and directly relevant public material. They identify hypotheses worth testing; they are not substitutes for OsasLearns' seven-question reading protocol.

| Unread paper | Previewed idea | V3 translation | What V3 must not claim |
|---|---|---|---|
| [Archon](https://arxiv.org/abs/2409.15254) | Search over modular inference architectures under a compute budget can find task-specific Pareto improvements. | Treat runtime settings as a bounded architecture search and retain the Pareto frontier instead of one universal winner. | That a small runtime grid reproduces Archon's model/operation architecture search. |
| [Shrinking the Generation-Verification Gap with Weak Verifiers](https://arxiv.org/abs/2506.18203) | Differently accurate weak verifiers can be combined more effectively than a naive unweighted vote. | Keep schema, evidence, action, forbidden-command and contradiction checks as separately reported signals; add mutation tests for each. | That our hand-written checks form a learned Weaver ensemble. |
| [Training Verifiers to Solve Math Word Problems](https://arxiv.org/abs/2110.14168) | Candidate generation becomes useful when a verifier can select correct outputs, and verifier scaling can outperform a finetuning baseline in that domain. | A faster runtime policy is eligible only after the verifier accepts its outputs. | Cross-domain transfer from mathematical verification to device guidance. |
| [Let's Verify Step by Step](https://arxiv.org/abs/2305.20050) | Process supervision can outperform outcome-only supervision in multi-step mathematics. | Verify intermediate contracts—parse, cited evidence, allowed action and explanation consistency—not only the final PASS/STOP label. | That deterministic program checks are a process reward model. |
| [Math-Shepherd](https://arxiv.org/abs/2312.08935) | Automatically constructed process supervision can reduce dependence on human labels. | Generate known-bad mutations from valid fixtures to test whether each verifier layer catches its intended failure. | That synthetic mutations replace independent human factual review. |
| [ADaPT](https://arxiv.org/abs/2311.05772) | Decompose only when the executor fails, adapting work to task and model capability. | Run cheap deterministic checks first; spend model or human effort only on unresolved or contradictory cases. | That V3 implements recursive language-agent planning. |
| [Wider or Deeper?](https://arxiv.org/abs/2503.04412) | External feedback can decide between exploring new candidates and refining existing ones. | Preserve per-fixture failure types so a later companion can choose retry, request evidence or stop. | That a runtime autotuner is Monte Carlo tree search. |
| [CodeMonkeys](https://arxiv.org/abs/2501.14723) | Repository-scale agents benefit from executable tests, multiple trajectories and a dedicated selection step. | Make the tuner emit candidates, replay tests and a separate selection report rather than silently rewriting settings. | That more tuning candidates automatically improve a weak evaluator. |
| [KernelBench](https://arxiv.org/abs/2502.10517) | `fast_p` counts solutions only when they are correct and exceed a speed threshold. | Introduce `safe_fast@p`: a request counts only if all hard checks pass and paired latency improves by at least `p`. | GPU-kernel performance or direct comparability with KernelBench scores. |
| [Improving Parallel Program Performance with LLM Optimizers via Agent-System Interfaces](https://arxiv.org/abs/2410.15625) | A structured search space plus rich execution feedback can outperform optimization from a scalar score alone. | The manifest defines legal settings; the report returns prompt/decode speed, TTFT, RSS, cache reuse and quality failures—not one reward. | That an LLM should autonomously edit low-level Arm code before submission. |
| [How Do Large Language Monkeys Get Their Power (Laws)?](https://arxiv.org/abs/2502.17578) | Aggregate scaling can hide a heavy tail of very difficult problems. | Report paired per-fixture latency and failures, p50/p95 and worst cases; do not optimize only the mean. | That twelve fixtures establish a scaling law. |

### What the rest of the unread library changes

The wider library is useful here mainly as a boundary around the experiment:

| Unread family | Previewed lesson | Use now | Defer until after the deadline |
|---|---|---|---|
| [AlphaCode](https://arxiv.org/abs/2203.07814) and [AlphaCode 2](https://storage.googleapis.com/deepmind-media/AlphaCode2/AlphaCode2_Tech_Report.pdf) | Diversity, executable filtering, behavioural clustering and reranking turn large candidate sets into a few useful choices. | Preserve candidate policies, reject invalid ones and select from measured behaviour. | Massive sampling, model finetuning and learned reranking; our tiny grid does not need them. |
| [Search-o1](https://arxiv.org/abs/2501.05366) and [ReAct](https://arxiv.org/abs/2210.03629) | External information and execution feedback should enter at the point of uncertainty rather than being silently invented. | Give the tuner structured host and benchmark feedback; fail explicitly when a fact is unavailable. | Open-web retrieval or free-form model tool use in the deterministic benchmark path. |
| [MemGPT](https://arxiv.org/abs/2310.08560), [Cartridges](https://arxiv.org/abs/2506.06266) and CacheBlend | Memory placement and reuse are part of system design, not merely larger context windows. | Keep a resident server and measure actual repeated-prefix reuse. | Training corpus-specific KV representations or implementing new cache-composition algorithms. |
| [Measuring AI Ability to Complete Long Software Tasks](https://arxiv.org/abs/2503.14499) | Real capability depends on reliable completion, adaptation to mistakes and the human time represented by a task. | Measure the complete valid product event, reproduction time and failures—not only token speed. | Claiming a general autonomy time horizon from this narrow harness. |
| [GDPval](https://arxiv.org/abs/2510.04374) | Useful evaluation should resemble economically meaningful deliverables and can improve with context and scaffolding. | Keep the workload tied to a Setup Companion explanation rather than an arbitrary language prompt. | Claiming labour substitution or economic value from synthetic fixtures. |
| [DeepScholar-Bench](https://arxiv.org/abs/2508.20033) | Research synthesis needs separate evidence for retrieval, synthesis and verifiability. | Keep source provenance and claim boundaries separate from benchmark performance. | Treating this abstract audit as a completed literature review. |
| STaR, DeepSeekMath, DAPO, SWiRL and related post-training work | Iterative data generation and reinforcement learning can alter the model itself. | None in V3; retain the already selected model so the runtime question stays identifiable. | Training, finetuning or RL under a fourteen-hour, zero-cost deadline. |
| Darwin Godel Machine, AlphaEvolve and AI Scientist | Open-ended improvement needs an archive, evaluators, sandboxing and empirical validation; the evaluator can become the real bottleneck. | Archive configurations and measurements, keep execution bounded and make the evaluator fail loudly. | Autonomous source mutation or a claim that this bounded tuner is self-improving research software. |

This review changes the design without changing any paper's reading status. The recurring lesson is not “add an agent.” It is: define the legal search space, preserve diverse candidates, expose execution feedback, select with an independent quality boundary and evaluate the complete useful event. V3 can implement that small loop honestly.

## V3: Arm Runtime Policy Autotuner

### Research question

On the same native four-core Arm runner and retained Qwen2.5 1.5B Q4_0 model, can a bounded, host-aware search over `llama.cpp` runtime settings reduce persistent-server first-token and complete-explanation latency relative to the static Version 2 policy while every sealed Setup Companion fixture and verifier mutation test passes?

### Artifact

A developer runs one command. The tool:

1. records the host architecture, CPU features, core count, cache information, compiler, kernel and pinned `llama.cpp` revision;
2. refuses non-Arm native performance claims;
3. benchmarks a declared grid rather than allowing arbitrary code or flags;
4. separates prefill settings (`-tb`, `-ub`) from decode settings (`-t`);
5. emits every candidate measurement and the non-dominated Pareto set;
6. selects a policy for the declared Setup Companion request distribution;
7. launches a persistent local `llama-server` with that policy;
8. compares cache disabled and enabled on a declared repeated-prefix sequence;
9. streams responses to capture actual first-token time;
10. verifies the complete output and publishes machine-readable and browser-readable evidence.

The selector is deterministic code. No model invents shell commands or privileged actions.

### Frozen model and backend

| Dimension | V3 value | Reason |
|---|---|---|
| Model | Qwen2.5 1.5B Instruct | V2's only stable scale |
| Quantization | Q4_0 | 43.72% smaller and about 34.68% lower peak RSS than tested Q8_0 |
| Runtime backend | baseline Arm CPU | KleidiAI did not improve cold explanation latency in V1–V2 |
| Host images | Ubuntu 22.04 Arm primary; Ubuntu 24.04 Arm replication if time permits | preserve the established cross-image boundary |
| Device interaction | none | synthetic model-level study only |

### Bounded tuning space

- Decode threads: `1, 2, 3, 4`.
- Prompt/batch threads: `1, 2, 3, 4`.
- Physical micro-batch: `64, 128, 256, 512`.
- CPU affinity: report support first; compare default placement with a declared pinned mask only if the hosted runner permits it.
- Prompt cache: disabled versus enabled in a separate paired server experiment.

The search should be staged rather than a wasteful Cartesian product. First tune decode threads on generation. Then tune prompt threads and micro-batch jointly on short, medium and long prompts. Combine only the non-dominated settings and validate the resulting policy end to end.

### Evaluation data

- A development split used to select settings.
- A sealed test split written before native execution.
- At least twelve synthetic states spanning PASS, STOP and REQUEST_EVIDENCE decisions, short and long evidence, contradictory evidence and irrelevant fields.
- A mutation suite that changes one valid output at a time: wrong decision, wrong action, missing evidence ID, fabricated evidence, forbidden command, empty rationale, prose/action contradiction and malformed bytes/JSON.
- No real device data, command execution or claim of installation safety.

### Baselines and variants

| Variant | Purpose |
|---|---|
| B0: Version 2-style fresh process | preserves continuity with the old cold metric |
| B1: persistent server, static 4/4/512, cache off | production-like static baseline |
| B2: persistent server, static 4/4/512, cache on | isolates prefix reuse |
| V3-A: persistent server, autotuned policy, cache off | isolates runtime-policy tuning |
| V3-B: persistent server, autotuned policy, cache on | tests the complete proposed policy |

### Metrics

- Request-to-first-generated-token latency measured from streaming responses.
- Request-to-complete-valid-explanation latency.
- Prompt and generation tokens per second from server timings.
- Prompt tokens evaluated versus reused.
- Persistent-server peak RSS.
- p50, p95, worst case and paired per-fixture changes; no mean-only claim.
- Verifier mutation recall and valid-output false-rejection rate.
- `safe_fast@5`: percentage of sealed requests that pass every hard check and improve paired latency by at least 5%.
- Autotuning time and one-command reproduction time as developer-experience costs.

### Hard gates

1. Every retained output passes every deterministic hard check.
2. Every dangerous mutation is rejected by its intended verifier layer.
3. The selected policy improves median complete-valid-response latency by at least 5% over B1 without a greater than 5% p95 regression.
4. Cache claims require reported reused-token counts, not only faster wall time.
5. Unsupported affinity, PMU or power measurements are recorded as unavailable.
6. Host images are never called separate hardware classes.

If quality passes but the performance gate fails, V3 is a valid negative result. If quality fails, the faster policy is rejected.

## What we can finish responsibly in the remaining window

| Time box | Work |
|---|---|
| Hour 0–1 | Review this proposal, freeze the V3 manifest, fixtures, mutation suite and thresholds. |
| Hour 1–4 | Implement the bounded autotuner, server harness, streaming TTFT capture and unit tests. |
| Hour 4–7 | Run development search on the primary native Arm image; inspect without changing sealed data. |
| Hour 7–9 | Execute sealed primary evaluation and one unchanged replication. |
| Hour 9–11 | Run cross-image replication only if the primary apparatus is sound and time remains. |
| Hour 11–13 | Generate evidence replay, result tables, claim boundaries and submission copy. |
| Final hour | Submission validation and buffer. No new experiment begins. |

## Stop conditions

- Do not add models, quantizations, backends or workloads after seeing native results.
- Do not install or depend on paid services.
- Do not treat an unread paper preview as a completed reading.
- Do not call prompt caching a model-quality improvement.
- Do not use a real phone.
- Do not let the autotuner modify source code or execute generated commands.
- Do not proceed to native execution until the V3 manifest and sealed test split are committed.

## Recommended next decision

Proceed only with this narrow V3. It addresses the mechanism exposed by Arm's documentation, turns the Version 2 limitation into a reusable developer tool and directly applies the course's ideas about modular search, adaptive compute and verifier-gated optimization. If the apparatus cannot be frozen within the first four hours, submit Version 2 rather than rushing an uninspectable Version 3.
