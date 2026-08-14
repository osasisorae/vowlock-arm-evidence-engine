# Version 5 protocol: the Verified Explanation Compiler

**Status:** pre-registered before implementation and native execution  
**Manifest:** [`experiment.v5.json`](../experiment.v5.json)  
**Prior result boundary:** commit `fa920920b80c5c9c0501a3fff91ee4f93bfd4632`

## Why Version 5 exists

Version 4 found that a deterministic template dominated the local model for the bounded Setup Companion decision task. It was faster, smaller and more reliable. Version 5 asks what should replace the removed model as reusable infrastructure.

The answer under test is a deterministic explanation compiler. It receives a typed device state, applies the registered decision policy, records the decisive rules and evidence, and emits brief, detailed and progressively disclosed representations. Every word that describes state must be compiled from a typed value rather than freely generated.

## Registered question

> Can a deterministic explanation compiler cover the complete declared Setup Companion state space, preserve exact evidence provenance in several presentation forms and execute cheaply on Arm without a language model?

## Complete declared domain

| Field | Values | Count |
|---|---|---:|
| Device class | resettable test, daily use | 2 |
| Certification | true, false, unknown | 3 |
| Original verifier values captured | true, false | 2 |
| Verifier restored | true, false, unknown | 3 |
| Reboot persistence | true, false, unknown | 3 |
| Play Protect scan | passed, failed, not run | 3 |
| Device owner active | true, false | 2 |
| **Cartesian product** | | **648** |

The domain is exhaustive only with respect to these seven fields and listed values. It says nothing about malformed inputs, undeclared Android states or real devices unless separately tested.

## Compiler outputs

| ID | Rendering | Contract |
|---|---|---|
| B0 | Brief | Action plus every decisive reason and exact value |
| D0 | Detailed | Action, decisive reasons and all seven typed evidence values |
| P0 | Progressive | Separately renderable summary, why, complete evidence list and next step |

Each compiled result also includes the decision, action, decisive rule IDs, decisive evidence IDs, stable state ID, canonical-state SHA-256 and compiled-output SHA-256.

These presentations are not ranked for readability or preference. V5 measures correctness, completeness, determinism, size and execution cost. A human study would be a different registration.

## Exhaustive proof harness

The harness must:

1. enumerate exactly 648 unique canonical states;
2. independently check terminal, missing-observation and pass invariants;
3. verify decisive evidence in all three renderings;
4. verify complete typed evidence in D0 and P0;
5. compile every state twice and require byte-identical output;
6. recompute every state and output hash;
7. apply eight authority, evidence and provenance mutations and reject all of them; and
8. stop before benchmarking if any proof gate fails.

This is exhaustive testing of a declared finite domain. It is not described as theorem-prover formal verification.

## Native Arm benchmark

After five warmup rounds, the native four-core Arm runner compiles the entire state space 100 times for each rendering: 194,400 measured outputs. It records nanoseconds per output, outputs per second, p50/p95 complete-round time, serialized bytes, process peak RSS and reproduction time.

No model, model download, network service, paid API or real device is used.

## Claim boundary

V5 may claim complete coverage only for the registered 648-state domain when all invariants and mutations pass. It may report performance only for the named Python implementation and hosted Arm image. It may not claim improved comprehension, accessibility, user preference, real-device safety, therapeutic value, universal Arm performance or proof about undeclared states.
