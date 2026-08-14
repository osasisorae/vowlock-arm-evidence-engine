# Reuse the Version 2 harness

`experiment.v2.json` is both this study's immutable registration and a working example of the harness format. To run a different study, copy it to a new filename rather than editing the preserved registration.

The runner reads these values from the selected manifest:

- pinned `llama.cpp` commit;
- model IDs, URLs, SHA-256 hashes, expected byte sizes and runtime variants;
- prompt, generation and repetition counts for every workload;
- Setup Companion-style fixture path.

Run a custom manifest on native Arm64 Ubuntu with:

```bash
V2_MANIFEST=/absolute/path/to/experiment.json \
V2_HOST_LABEL=my-arm-host \
./scripts/run-v2.sh
```

The summarizer discovers a same-family Q8_0-to-Q4_0 baseline pair from the manifest rather than depending on the registered Qwen filenames. Add or remove models and workloads in the copied manifest; the execution plan expands automatically.

The GitHub Actions file is intentionally a thin owner-dispatched wrapper. Forks can change its runner matrix without changing the experimental runner. Unauthenticated dispatch is not exposed because it would let strangers consume repository compute.

## Fixture contract

Each fixture supplies observed synthetic state, an oracle decision, an allowed next action, required evidence IDs and forbidden claims. The generated candidate must contain:

```json
{
  "decision": "STOP",
  "evidence_ids": ["example"],
  "next_action": "leave_device_untouched",
  "explanation": "A substantive reason grounded in the observed evidence."
}
```

The evaluator rejects wrong decisions, wrong actions, missing evidence, token-only explanations, forbidden claims and privileged command patterns. These deterministic checks do not replace human evaluation of nuanced free-form factuality.
