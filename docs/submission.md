# Devpost submission copy

## Project name

VowLock Arm Evidence Engine

## Elevator pitch

I came to optimize a local AI on Arm. Five experiments later, the best optimization was deleting the model—and compiling all 648 safety states instead.

## Track

Cloud AI

## The short version

I like AI. I also like evidence enough to fire AI from a job it cannot do.

VowLock Arm Evidence Engine began with a normal optimization question: could Arm's KleidiAI kernels make a small offline language model faster for VowLock Setup Companion?

Five registered experiments later, the answer became much more interesting.

The acceleration switch did not produce a meaningful overall speedup. Quantization saved substantial storage and memory. The smallest model was wonderfully fast and frequently wrong. Runtime tuning made the wrong answers arrive on a better schedule. A deterministic template then beat every model-backed alternative. Finally, I replaced the model with a verified explanation compiler that covered every one of the 648 states in its declared domain.

The winning optimization was not a faster model.

It was discovering that this particular job should not belong to a model at all.

## Inspiration: the question underneath the benchmark

VowLock is voluntary commitment software. A person makes a decision while their intention is clear, chooses a fixed period, and asks the software to make impulsively reversing that decision difficult. The stronger installation process can be technically demanding, especially on Android, so I proposed an offline Setup Companion that could explain the device state to a non-technical user.

The original architecture sounded sensible:

> Detect state → explain → request consent → execute a fixed action → verify the result

The language model would receive no authority to execute privileged commands. Deterministic code would retain that authority. But even an explanation model costs storage, memory, time and power. More importantly, a fluent explanation can still be factually wrong.

So the real question was not simply, “Can I run this model on Arm?”

It was:

> Does this model earn its place in the system?

That question changed the entire project.

## What I built

The repository is an MIT-licensed, native-Arm evidence engine for making and auditing that decision. It contains:

- Pinned baseline and KleidiAI-enabled `llama.cpp` builds.
- Machine-readable experiment manifests instead of hidden benchmark settings.
- Exact model hashes and artifact-size checks.
- Separate prompt-processing and token-generation measurements.
- Cold first-output, complete-response and peak-RSS instrumentation.
- Synthetic Setup Companion fixtures with independent deterministic evaluation.
- Quality gates that can reject a faster model.
- Mutation tests that try to corrupt decisions, actions, evidence and hashes.
- Registered development and sealed evaluation boundaries.
- A model-free explanation compiler over every declared state.
- Fifty-six fast local tests, native Arm workflows and a public evidence replay.

No device is modified and no privileged command is executed. The V5 compiler generates none. The physical-phone experiment remains deliberately out of scope.

## The five-act experiment

### Act I — The optimization switch that was not an optimization

I built the same pinned Qwen2.5 1.5B Q4 model twice on the same native Arm64 runner: once with KleidiAI disabled and once enabled. The optimized condition had to prove that `CPU_KLEIDIAI` and I8MM were genuinely selected.

Three unchanged replications agreed:

| Metric | Baseline | KleidiAI | Change |
|---|---:|---:|---:|
| Prompt processing | 129.9529 tok/s | 131.0815 tok/s | **+0.87%** |
| Token generation | 35.1468 tok/s | 34.5907 tok/s | **−1.58%** |

The backend ran. The workflow was green. The hoped-for result was still unsupported.

That distinction became the first lesson of the project: **a switch being active is not the same as a product becoming better.**

### Act II — The fastest model lost

I registered a wider matrix before running it: Q8 and Q4 quantization, 1.5B and 0.5B models, baseline and KleidiAI paths, three workload shapes and two native Arm Ubuntu images.

This produced the first material win:

| Change | Result |
|---|---:|
| Q8 → Q4 exact artifact size | **43.72% smaller** |
| Q8 → Q4 peak RSS | **34.67–34.68% lower** |
| Retained 1.5B Q4 explanation quality | **3/3 fixtures passed** |

Then the 0.5B model arrived looking like a hero. It was 58–69% faster across the estimated workloads.

It also produced malformed, incomplete or weak explanations and passed at most one of three fixtures.

Fast and wrong is not optimized. It is merely wrong sooner.

The retained model was Qwen2.5 1.5B Q4 on the baseline Arm CPU path—not the fastest condition and not the most fashionable one, but the condition that survived the product gate.

### Act III — Better scheduling could not repair missing capability

Version 3 searched thread counts, micro-batches and runtime policies. The candidate and static baseline both passed **0/6** complete development explanations.

The registered protocol said to stop before opening the sealed split, so I stopped.

This mattered. I could have changed the prompt, weakened the verifier or searched until one output looked attractive. Instead, the failed development gate became the result:

> Runtime optimization cannot rescue a component that does not satisfy the product contract.

### Act IV — The best model was no model

Version 4 changed the architecture rather than the benchmark settings. Deterministic code owned the decision, evidence and next action. The model could only propose prose about that immutable envelope.

| Variant | Sealed result | Median complete time | Decision |
|---|---:|---:|---|
| Free-form model | 0/12 | 6.4348 s | Reject |
| Constrained model prose | 6/12 accepted | 3.0608 s | Below threshold |
| Deterministic template | 12/12 | 0.0816 ms | **Retain** |
| Verified hybrid | 12/12 after 6 fallbacks | 3.0608 s | Model not justified |

Removing the model also removed a 1,066,227,232-byte artifact and a model server that reached approximately 2,050,204 KiB peak RSS.

Those resource figures describe different measured processes rather than a kernel-only comparison. They answer the application-level question: what does this bounded decision cost when it is served by the model-backed path versus the deterministic path?

Then came one final plot twist. A disclosed qualitative review found that some prose accepted by the automatic surface verifier still misstated the underlying facts. Only two of twelve constrained explanations were clearly adequate, one was ambiguous and nine were inadequate.

The structured authority remained correct. The language around it could still lie beautifully.

That is why the deterministic template won.

### Act V — Deleting the model was not enough

“Use a template” is a decision. It is not yet reusable infrastructure.

Version 5 therefore registered the complete finite domain before implementation: seven typed observations with **648 possible combinations**, three explanation forms, nine invariants and eight deliberate corruptions.

The compiler then processed every declared state:

| Result | Native Arm evidence |
|---|---:|
| Unique states checked | **648/648** |
| Compiled outputs across three renderings | **1,944/1,944** |
| Byte-for-byte repeatability | **100%** |
| Registered corruptions rejected | **8/8** |
| Decision distribution | **600 STOP · 47 REQUEST_EVIDENCE · 1 PASS** |
| Model storage | **0 bytes** |
| Network calls | **0** |
| Peak process RSS | **23,168 KiB** |
| Throughput | **33,351–50,378 outputs/s** |

Every output carries its decisive rules, decisive evidence, canonical-state hash and compiled-output hash. A judge can inspect why a decision happened and detect whether the state or result changed.

This is not a claim that Python has been formally verified, that a real phone is safe, or that humans prefer one rendering. It is exhaustive registered-property testing over the declared 648-state domain—and the denominator is visible.

## What the project actually accomplished

The project prevented VowLock from shipping an expensive probabilistic component where verified ordinary software was faster, smaller and more reliable.

It reduced the bounded decision path from:

- a 1.066 GB model,
- roughly 2 GB of model-server resident memory,
- seconds of latency,
- and a free-form factual failure surface

to:

- no model artifact,
- roughly 23 MB peak process RSS in the native V5 run,
- tens of thousands of compiled outputs per second,
- exact provenance,
- deterministic repeatability,
- and complete coverage of the declared state space.

It also produced a reusable method for evaluating future AI components: register the question, verify that the optimization actually ran, measure the complete product event, keep quality independent from speed, mutation-test the verifier, preserve negative results and remove the model when it does not earn its cost.

## Why this matters beyond VowLock

The transferable result is not “robots should not use AI.” Robots need learned systems for open-ended perception, language, planning and manipulation.

The result is about **authority allocation**:

> Let AI perceive, converse and propose. Let verified deterministic software decide whether a bounded, consequential action is permitted.

Imagine a home robot asked to unlock a door, enter a child's room, operate an appliance or administer a scheduled task. A learned model may understand the request and interpret the environment. A deterministic authority layer can still check whether the user is authorized, whether the sensor evidence is fresh, whether the room and action are permitted, whether required confirmation exists and whether the robot must stop or request more evidence.

This resembles runtime-assurance architectures used in safety-critical autonomy: an advanced component may operate, but a trusted monitor constrains it and a safe fallback remains available. On Arm-based robots, allocating work this way may also preserve memory, latency, energy and thermal headroom for perception and control that genuinely require AI.

V5 does **not** prove physical-robot safety. It used synthetic typed states on hosted native Arm hardware, not cameras, motors, continuous dynamics or a home. Its contribution is a concrete, measured example of the architectural pattern and an open apparatus other developers can adapt.

For installation and provisioning, the fit is especially close. A robot or other home AI system may have a finite set of permissions, devices, rooms, users and safety prerequisites. Those configuration decisions should not become probabilistic merely because an AI model is available.

## How I built it

The project uses:

- `llama.cpp`
- Arm KleidiAI
- Official Qwen GGUF artifacts
- Python's standard library
- Bash, CMake and GitHub Actions
- Free standard `ubuntu-22.04-arm` and `ubuntu-24.04-arm` runners

No paid VM, model API, subscription or device was used.

The method grew from my Stanford CS329A self-study: controlled baselines, generator–verifier separation, compute allocation, distribution shift, sealed evaluation and the uncomfortable difference between a successful workflow and a supported claim.

## How to validate it in seconds

The final compiler and tests require no model download:

```bash
git clone https://github.com/osasisorae/vowlock-arm-evidence-engine.git
cd vowlock-arm-evidence-engine
python3 -m unittest discover -s tests -v
python3 v5_proof.py --output results/v5-proof.json
```

To compile one ready state:

```bash
python3 v5_compiler.py \
  --input examples/v5-ready-state.json \
  --rendering progressive \
  --pretty
```

The full language-model matrices can be reproduced on an Arm64 Ubuntu host or through the included GitHub Actions workflows. They are deliberately separate from the seconds-long model-free validation path.

## Challenges

The obvious challenge was making the Arm benchmark run. The more important challenge was refusing to confuse successful execution with scientific support.

- Early workflows failed on build targets and observability assumptions.
- A green run revealed a semantic verifier that was too weak.
- A later verifier became too brittle and rejected valid human-readable evidence.
- Invalid UTF-8 exposed a crash path.
- The fastest model failed quality.
- Runtime search failed its development gate.
- A model constrained to prose still produced factually misleading language.
- The final result contradicted the premise that an AI optimization challenge must end with more AI.

Each failure changed the apparatus instead of being edited out of the story.

## Accomplishments I am proud of

- Preserved a neutral/regressive KleidiAI result instead of cherry-picking prompt throughput.
- Pre-registered every follow-up question before implementing or running it.
- Built and measured 30 native Arm model/runtime/workload conditions across two host images.
- Found a reproducible quantization win.
- Rejected a 58–69% faster model because it failed the behaviour being accelerated.
- Stopped Version 3 before sealed evaluation when the development gate failed.
- Separated generated language from consequential authority.
- Disclosed when the prose verifier overclaimed safety.
- Removed a model that did not earn its place.
- Turned that deletion into a typed, provenance-bearing compiler covering all 648 declared states.
- Packaged the experiment as a public MIT-licensed repository with 56 tests, machine-readable evidence, native Arm workflows and a live evidence page.

## What I learned

An optimization flag is a hypothesis, not a result.

A fast wrong answer is not a performance improvement.

A verifier defines the ceiling of the system around it.

The same model can improve prompt processing while regressing generation.

Scheduling cannot manufacture missing capability.

A correct structured decision does not guarantee truthful prose.

When a domain is finite, exhaustive compilation can be stronger than additional sampling.

Most importantly: using AI well includes knowing when not to use it.

## What is next

The deterministic compiler remains the default for this bounded Setup Companion policy. A language model may return only for a separately registered open-ended task that templates cannot cover, and only with independent factual and human-comprehension evaluation.

Future work includes:

- Testing whether people actually understand the brief, detailed and progressive renderings.
- Expanding the typed state model only from observed real requirements.
- Investigating the Q8 host-image instability as a separate toolchain question.
- Studying a runtime-assurance interface in which an AI proposes and deterministic code authorizes.
- Keeping physical-device work frozen until the separate Android verifier-restoration safety gate is resolved.

## Prior work and submission-period disclosure

VowLock existed before this challenge. I am not presenting the existing application or the separate ADTC Setup Companion concept as hackathon-period work.

The new challenge-period artifact is the Arm Evidence Engine: its manifests, native benchmark harnesses, runtime and semantic verifiers, fixture sets, two-host matrix, resource instrumentation, five registered studies, explanation compiler, evidence reports, public replay and preserved run history.

## Claim boundaries

- The physical-device workflow was not tested.
- The fixtures and 648 states are synthetic and explicitly declared.
- V5 does not prove human comprehension.
- Hosted Arm results are not universal performance or power claims.
- No real energy counter was available, so power savings are not reported.
- Output hashes prove repeatability and tamper evidence, not the truth of undeclared inputs.
- The robotics section describes a transferable design implication, not a robot demonstrated by this submission.

## Links

- Source: https://github.com/osasisorae/vowlock-arm-evidence-engine
- Live evidence: https://osasisorae.github.io/vowlock-arm-evidence-engine/
- Osas Learns living book: https://osaslearns.com
- Judge validation: https://github.com/osasisorae/vowlock-arm-evidence-engine/blob/main/docs/validation.md
- Version 1 replication: https://github.com/osasisorae/vowlock-arm-evidence-engine/blob/main/docs/results.md
- Version 2 result: https://github.com/osasisorae/vowlock-arm-evidence-engine/blob/main/docs/v2-results.md
- Version 3 result: https://github.com/osasisorae/vowlock-arm-evidence-engine/blob/main/docs/v3-results.md
- Version 4 result: https://github.com/osasisorae/vowlock-arm-evidence-engine/blob/main/docs/v4-results.md
- Version 5 result: https://github.com/osasisorae/vowlock-arm-evidence-engine/blob/main/docs/v5-results.md
- Version 4 native run: https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31800634600
- Version 5 native run: https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31803354032
- Final two-host matrix: https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31785110768
- NASA runtime-assurance reference: https://ntrs.nasa.gov/api/citations/20240007986/downloads/DASC_submit_slagel_v01.pdf
- Arm physical-AI overview: https://www.arm.com/markets/physical-ai

## If this changed how you think about AI

If you found this experiment useful, please like the submission and share it with a friend who is building with AI, agents or robotics. The complete learning journey—including the failed hypotheses, measurements, course connections and decisions that produced this result—is preserved in the [Osas Learns living book](https://osaslearns.com).

The next useful optimization may be a faster model. It may be a smaller model. Or it may be having enough confidence in the evidence to remove the model entirely.
