# Version 4 result: the model did not earn its place

Version 4 completed successfully on native Arm. Its strongest result is not a language-model improvement: **the deterministic template dominated the model-backed alternatives for the tested Setup Companion contract.**

Source: [GitHub Actions Run 31800634600](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31800634600). Machine-readable summary: [`evidence/v4-run-1-ubuntu-22.04-arm.json`](../evidence/v4-run-1-ubuntu-22.04-arm.json). Registration: [`experiment.v4.json`](../experiment.v4.json).

## What changed from V3

V3 allowed the model to propose the decision, evidence identifiers, next action and explanation. It passed 0/6 development fixtures. V4 moved the first three fields into deterministic code and restricted the model to one prose field. An invalid explanation triggered a deterministic template without retry.

| Variant | Who owns authority? | Sealed result | Median complete time |
|---|---|---:|---:|
| F0 · free-form model | Model proposes all fields | 0/12 | 6.4348 s |
| T0 · deterministic template | Code produces all fields | 12/12 | 0.0816 ms |
| M0 · constrained model | Code fixes authority; model supplies prose | 6/12 accepted | 3.0608 s |
| H0 · verified hybrid | M0 or deterministic fallback | 12/12 automatic checks; 6 fallbacks | 3.0608 s |

The same pattern appeared on development: F0 passed 0/6, M0 passed 3/6, and T0/H0 passed 6/6 under the automatic evaluator.

## The resource decision

T0 generated a complete, evaluator-valid result in 0.0816 milliseconds at the sealed median. H0 needed 3.0608 seconds: roughly 37,500 times the wall time. The model artifact occupied 1,066,227,232 bytes and its server reached 2,050,204 KiB peak RSS. The Python driver process reached 20,352 KiB.

These figures are not a hardware-energy comparison, and the process RSS figures describe different processes. They nevertheless answer the product question: the tested model adds about a gigabyte of storage, a roughly two-gigabyte resident server and seconds of delay before any demonstrated human benefit.

## The verifier found its own limit

The registered surface evaluator accepted six constrained explanations. A post-result, non-blinded qualitative audit found only two of twelve sealed explanations clearly factually adequate, one ambiguous and nine inadequate.

Examples of automatic false acceptance included:

- converting unknown verifier restoration into “the verifier has been restored” and calling the system ready;
- converting unknown restoration into “has not been restored”;
- requesting evidence for checks that had already passed while omitting the one false value.

The structured decision and action stayed correct in H0, but prose can still mislead a person. Therefore the machine field `architecture_safe_for_further_study: true` means only that the registered automatic gates passed. It is not proof that every accepted explanation was factually safe. Full audit: [`evidence/v4-run-1-qualitative-review.json`](../evidence/v4-run-1-qualitative-review.json).

## Decision

Retain T0, the deterministic template. The model reached only 50% raw automatic acceptance, below the registered 80% threshold for a later blinded human study. More importantly, the qualitative audit showed that even automatic acceptance was not evidence of factual adequacy.

This is an Arm optimization result at the system level:

- remove a 1,066,227,232-byte artifact;
- avoid a roughly 2,050,204 KiB model server;
- replace seconds of generation with sub-millisecond deterministic rendering;
- preserve exact decisions, actions and evidence values; and
- eliminate an unverified natural-language failure surface.

The local model may return only after a new study defines a genuinely generative task that templates cannot handle and registers an independent factual-comprehension evaluation before execution.

## Boundaries

- Synthetic fixtures only; no device was connected or changed.
- The sealed fixtures were public and pre-registered, not investigator-blind.
- The qualitative audit was post-result and non-blinded; it narrows claims rather than becoming a registered score.
- No therapeutic, real-device safety, energy, universal Arm or human-comprehension claim is made.
