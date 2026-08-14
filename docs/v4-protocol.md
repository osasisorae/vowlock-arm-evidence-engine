# Version 4 protocol: code decides, the model explains

**Status:** pre-registered before implementation and native execution  
**Manifest:** [`experiment.v4.json`](../experiment.v4.json)  
**Prior result boundary:** commit `9fcda17e9d42c8c441b5ca5a6871f2ce35a0818c`

## Why Version 4 exists

Version 3 asked whether a better Arm runtime policy could reduce complete-valid explanation latency. It stopped correctly: both tested policies produced zero valid development explanations. The failures were not scheduling failures. The unchanged model treated several passing facts like a majority vote and ignored terminal failures such as a failed Play Protect scan or absent reboot persistence.

Version 4 tests the architecture implied by that result. Consequential decisions move out of language generation entirely. Deterministic code owns the decision, next action and evidence identifiers. The local model may only explain an immutable authority envelope. A separate evaluator either accepts the explanation or replaces it with a deterministic template.

This is not a repair or continuation of V3's runtime result. It is a new authority-allocation study.

## Registered question

> Can deterministic code own every safety decision while a small local model is restricted to explaining an immutable authority envelope, and does the model earn its storage, memory and latency cost relative to a deterministic template?

## Four variants

| ID | Variant | Authority | Purpose |
|---|---|---|---|
| F0 | Free-form model | Model proposes decision, evidence, action and explanation | Historical architecture comparison |
| T0 | Deterministic template | Code produces every field | Model-free safety and resource baseline |
| M0 | Constrained explanation | Code fixes authority fields; model proposes explanation only | Measure raw explanation acceptance and cost |
| H0 | Verified hybrid | Code fixes authority fields; accepted model prose or template fallback | Production candidate |

The hybrid does not ask the model to repair itself. Parse errors, contradictions, missing evidence concepts, forbidden claims, privileged commands and timeouts trigger one deterministic fallback. This keeps additional inference compute from becoming additional authority.

## Decision precedence

The decider applies rules in this order:

1. **Terminal stop:** daily-use device, active device owner, explicitly false certification, explicitly false verifier restoration or a failed Play Protect scan.
2. **First missing observation:** original verifier values, certification, verifier restoration, Play Protect scan, then reboot persistence.
3. **Pass:** only a resettable device with every required observation passing and device owner inactive.

The implementation must reproduce every declared fixture oracle before model execution is permitted.

## Data boundary

V4 reuses the six V3 development fixtures. It separately declares the twelve V3 sealed fixtures as its sealed evaluation set. V3 generated no model output against those sealed cases. Reusing them is disclosed rather than pretending a new hidden dataset exists; the fixtures are repository-visible and therefore pre-registered but not investigator-blind.

No V4 sealed model request may run until the deterministic decider, template, constrained parser, fallback and mutation suite pass locally. After that gate, every variant runs once on all twelve sealed cases. The apparatus cannot be changed after viewing those results.

## Gates and interpretation

- The decider must match every declared oracle.
- The template and hybrid must pass every evaluator check.
- Every authority mutation must be rejected.
- Model text can never change the authority envelope.
- Raw constrained-model acceptance is measured, not required for system safety.
- The model must reach at least 80% raw sealed acceptance before it qualifies for a later human study.
- Automatic checks cannot establish that generated prose is clearer or more useful than the template. That requires a separately registered blinded comprehension study.

If the template wins, removing the 1,066,227,232-byte model is an optimization result. If the hybrid remains safe but the model is not clearer, the model still has not earned its place.

## Claim boundary

This is a synthetic Ubuntu-on-Arm experiment. It does not touch a phone, run ADB, alter a security setting, install VowLock or activate a commitment. It cannot prove real-device safety, therapeutic benefit, universal Arm performance or human comprehension improvement.
