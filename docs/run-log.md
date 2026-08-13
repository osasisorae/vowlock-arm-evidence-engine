# Experimental run log

This log records failed as well as successful runs. A failed setup is evidence about the experiment, not benchmark evidence about KleidiAI performance.

## Run 1 — 2026-08-13

- GitHub Actions run: `31709064793`
- Commit: `70db580b8bdb0c478fedcbec2d0cfef0c541969f`
- Runner: GitHub-hosted `ubuntu-22.04-arm`; the architecture check passed.
- Outcome: setup failure before either benchmark condition ran.
- Cause: the CMake configuration set `LLAMA_BUILD_EXAMPLES=OFF` while requesting the `llama-cli` target, which belongs to llama.cpp's examples. The missing target caused `cmake --build` to exit with status 2.
- Interpretation: this run says nothing about baseline or KleidiAI throughput. No result files were produced, and no performance claim is permitted from it.
- Correction: enable examples so the explicitly requested `llama-cli` smoke-test target exists. Write a stage log under `results/` from the beginning of subsequent runs.
