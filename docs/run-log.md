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
