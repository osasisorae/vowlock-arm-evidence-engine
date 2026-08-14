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
