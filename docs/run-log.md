# Experimental run log

This log records failed as well as successful runs. A failed setup is evidence about the experiment, not benchmark evidence about KleidiAI performance.

## Run 1 — 2026-08-13

- GitHub Actions run: `31709064793`
- Commit: `70db580b8bdb0c478fedcbec2d0cfef0c541969f`
- Runner: GitHub-hosted `ubuntu-22.04-arm`; the architecture check passed.
- Outcome: setup failure before either benchmark condition ran.
- Cause: the configuration set `LLAMA_BUILD_SERVER=OFF` while requesting `llama-cli`. In the pinned llama.cpp revision, `tools/cli` is only added when the server option is enabled. The missing target caused `cmake --build` to exit with status 2.
- Interpretation: this run says nothing about baseline or KleidiAI throughput. No result files were produced, and no performance claim is permitted from it.
- Initial correction: examples were enabled under the mistaken assumption that the CLI was an example target. Stage logging was also added so subsequent failures would be inspectable.

## Run 2 — 2026-08-13

- GitHub Actions run: `31711976309`
- Commit: `789d9ab7332c5a9aba94660947a8cf94b4aee99a`
- Runner: GitHub-hosted `ubuntu-22.04-arm`; architecture, dependency and summarizer checks passed.
- Outcome: setup failure before either benchmark condition ran.
- Evidence: the baseline configuration and `llama-bench` target built successfully. The build then reported `No rule to make target 'llama-cli'` and the stage log recorded status 2 at line 66.
- Cause: enabling examples did not affect the pinned revision's CLI gate. The upstream `tools/CMakeLists.txt` adds `tools/cli` only inside `if (LLAMA_BUILD_SERVER)`.
- Interpretation: this run also says nothing about KleidiAI performance. It validates the new failure-log path but provides no baseline or optimized measurement.
- Correction: use the standalone `llama-completion` target for smoke inference. It is part of the enabled tools tree and does not require the server or examples.

## Run 3 — 2026-08-13

- GitHub Actions run: `31716397091`
- Commit: `f773e49a82d21b00f6ae22e1d8260a52d03fca29`
- Runner: GitHub-hosted `ubuntu-22.04-arm`; architecture, dependency and summarizer checks passed.
- Outcome: verification failure after both builds and both smoke inferences completed, but before the paired throughput benchmark began.
- Evidence: the optimized smoke log reports `KLEIDIAI = 1` in `system_info`, while the baseline log does not. The optimized log also reports that Q6_K tensors are not accelerated because KleidiAI kernels are available for Q4_0 and Q8_0. The script then exited with status 3 because it could not find the literal string `CPU_KLEIDIAI`.
- Cause: the runtime guard expected llama.cpp's detailed `load_tensors: CPU_KLEIDIAI model buffer` message, but the pinned tool's default verbosity omitted the detailed model-buffer lines from both smoke logs. The check therefore confused missing log evidence with a missing backend: a verifier false negative.
- Interpretation: this run proves that the optimized binary was compiled with and exposed KleidiAI, but `KLEIDIAI = 1` alone does not satisfy the stricter claim that the model's Q4_0 tensors selected the KleidiAI buffer. No throughput claim is permitted because `llama-bench` never ran.
- Correction: rerun smoke inference with verbose logging and `--device none`, retain the strict `CPU_KLEIDIAI` buffer-selection gate, and print the relevant smoke log when that gate fails. Apply the same device restriction to both benchmark conditions so the registered comparison remains fact-equivalent.

## What the failures are teaching us

The first three runs are not three failed optimization results. They are three failures of the experimental apparatus: an unavailable target, a mistaken correction to that target, and a verifier that rejected a valid intermediate state because its expected evidence was hidden. This distinction matters. A benchmark can only answer the optimization question after its build, workload and verifier are trustworthy. Until then, improving the experiment is the result.
