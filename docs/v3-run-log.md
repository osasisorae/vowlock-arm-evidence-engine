# Version 3 run log

This append-only log distinguishes apparatus failures from native measurements. The registration remains frozen in commit `5f5f735`.

## Run 1 — GitHub Actions 31794802221

- Host requested: `ubuntu-22.04-arm`.
- Apparatus commit: `e5551e4`.
- Outcome: failed in the model-free preflight before source build, model download or benchmark execution.
- What passed: 38 unit tests, the Version 3 manifest audit and all eight registered verifier mutations.
- Failure: three frozen valid STOP references had the correct structured `leave_device_untouched` action and no contradictory prose, but the evaluator required the prose to repeat that action literally.
- Repair boundary: change only `explanation_action_consistent` so an explanation fails when it names a different registered action; it need not redundantly restate the structured action. Add all sealed reference candidates to unit coverage.
- Experimental status: not a measurement and not included in performance evidence.

## Run 2 — GitHub Actions 31795111653

- Host: native four-core `ubuntu-22.04-arm`.
- Apparatus commit: `3e5b4ff`.
- Outcome: workflow success; registered process stopped before sealed evaluation because no development policy passed every quality check.
- Decode selection: four threads, 35.8232 generation tokens/s.
- Prompt selection: four prompt threads and micro-batch 256; 28.6501 seconds across the three prompt probes versus 29.9763 for static micro-batch 512.
- Development gate: both the Pareto policy and static baseline passed 0/6 complete explanations. The Pareto policy was only 0.521% faster at the median and therefore also missed the 5% performance threshold.
- Verifier: all eight registered mutations were rejected at their intended layer.
- Stop action: no policy selected; no sealed generation, cache comparison, fresh-process comparison or cross-image replication.
- Instrumentation note: slot erase returned HTTP 501 and `tokens_cached` equaled the full evaluated prompt count, so it is not treated as reused-token evidence.
- Full interpretation: [`v3-results.md`](v3-results.md).
