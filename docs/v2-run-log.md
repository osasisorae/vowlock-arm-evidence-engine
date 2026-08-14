# Version 2 run log

Version 2 is separate from the sealed Version 1 Runs 4–6. Failures here are not pooled into or used to reinterpret that earlier result.

## Run 1 — registered matrix, claim not supported

- Workflow: [31782781033](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31782781033)
- Commit: `dc1d32d`
- Hosts: `ubuntu-22.04-arm` and `ubuntu-24.04-arm`
- Apparatus: completed the 15 registered throughput conditions per host and preserved summaries and raw evidence; jobs ended red because the first harness version mapped semantic failure to process exit 4.
- Resource result: Q8_0 to Q4_0 reduced exact artifact size by 43.72%. Cold peak RSS fell by 34.67% on Ubuntu 22.04 and 34.68% on Ubuntu 24.04. Both exceed the registered 20% resource threshold.
- Power: neither hosted runner exposed a readable `/sys/class/powercap` energy counter. The result is `unavailable`; no power estimate was substituted.
- Semantic result: the registered claim did not pass. Qwen2.5 0.5B produced malformed or incomplete candidates; Qwen2.5 1.5B Q8_0 emitted invalid bytes on one host; and one Q8_0 explanation contradicted its own STOP action in prose. These remain model-quality evidence.

Run 1 also found two evaluator defects. First, the evaluator required literal underscore-separated evidence IDs inside prose even when the candidate's dedicated `evidence_ids` array was correct and the explanation expressed the same facts naturally. That rule was stricter and more brittle than the registered requirement. Second, invalid UTF-8 raised an exception instead of becoming a clean failed candidate. The next harness version repairs those two observations without changing any registered model, hash, prompt, fixture, workload, threshold or host.

The workflow exit policy is also corrected: an experimental claim failure now leaves a successful apparatus run whose summary says `registered_claim_passed: false`. Operational success and hypothesis support are different outcomes.
