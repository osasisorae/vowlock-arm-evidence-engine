# Version 4 run log

## Registration

Version 4 was registered in commit [`f3f3678`](https://github.com/osasisorae/vowlock-arm-evidence-engine/commit/f3f3678) before its implementation existed. The apparatus was then implemented and tested in commit [`15b894a`](https://github.com/osasisorae/vowlock-arm-evidence-engine/commit/15b894a).

## Run 1 — complete

- Workflow: [GitHub Actions Run 31800634600](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31800634600)
- Host: native `aarch64`, `ubuntu-22.04-arm`, four logical CPUs
- Workflow duration: 7 minutes 23 seconds
- Registered study execution: 173.32 seconds
- Conclusion: workflow success; T0 retained; model not eligible for the later human study

The model-free gate matched all 18 fixture oracles, passed all 18 generated templates and caught all eight authority mutations. Development then completed automatically before sealed execution. H0 passed the registered automatic gate, so the unchanged apparatus continued to all twelve sealed fixtures.

No repair was made after model output appeared. The source workflow, artifact and curated evidence preserve the first run.

## Post-result qualitative boundary

The automatic evaluator reported H0 at 12/12 because immutable structured authority remained correct and rejected prose fell back to T0. It accepted six raw M0 explanations. Manual inspection showed that several accepted explanations still inverted `unknown` into a positive or negative fact, or failed to identify the decisive missing observation. This does not alter the registered automatic result; it narrows what that result permits us to claim.

The non-blinded review found two clearly adequate explanations, one ambiguous explanation and nine inadequate explanations. A later independent blinded review could disagree with individual classifications, but it cannot make the current automatic verifier evidence of factual adequacy.
