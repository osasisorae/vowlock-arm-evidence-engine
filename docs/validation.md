# Judge validation guide

The fastest audit path takes under five minutes, downloads no model and does not require trusting the headline.

## Seconds-long Version 2 audit

```bash
git clone https://github.com/osasisorae/vowlock-arm-evidence-engine.git
cd vowlock-arm-evidence-engine
python3 v2_matrix.py validate
python3 setup_companion_eval.py demo
python3 -m unittest discover -s tests -v
```

Then inspect the [Version 2 decision](v2-results.md), the two preserved machine summaries under `evidence/`, and [Run 31785110768](https://github.com/osasisorae/vowlock-arm-evidence-engine/actions/runs/31785110768). The live page replays the headline evidence without requiring a GitHub login.

## Inspect existing evidence

1. Open the [replicated result table](results.md).
2. Follow any Run 4–6 link and confirm its commit is `cf3ab598f0769089e866bdd15d903d39fe347160`.
3. In an optimized smoke log, find `primary q4 kernel feature I8MM`, `KLEIDIAI = 1` and the `CPU_KLEIDIAI` model buffer.
4. Confirm that the corresponding baseline log does not select `CPU_KLEIDIAI`.
5. Inspect `evidence/benchmark-runs.json` rather than relying on rounded prose.
6. Open Run 7's `output-contract.json`: baseline and optimized outputs must both equal `READY`, with `equivalent` and `contract_passed` set to `true`.

## Reproduce through GitHub Actions

The public repository cannot grant anonymous visitors workflow-write access. To reproduce without an Arm machine:

1. Fork the repository.
2. Open **Actions → Arm64 benchmark → Run workflow** in the fork.
3. Wait for the `Baseline vs KleidiAI` job to complete.
4. Download the `arm64-benchmark-evidence-*` artifact.

The workflow uses GitHub's standard `ubuntu-22.04-arm` runner and no repository secret, paid API or external account credential.

For the full Version 2 matrix, fork the repository and dispatch **Arm64 V2 matrix**. It runs separately on `ubuntu-22.04-arm` and `ubuntu-24.04-arm`. The public source repository deliberately does not expose unauthenticated workflow dispatch because that would permit strangers to consume repository compute.

## Reproduce on Arm64 Ubuntu

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake curl git python3
git clone https://github.com/osasisorae/vowlock-arm-evidence-engine.git
cd vowlock-arm-evidence-engine
python3 -m unittest discover -s tests -v
./scripts/build-and-benchmark.sh
```

Expected evidence under `results/`:

- `baseline.json` and `optimized.json`: raw `llama-bench` rows;
- `summary.json`: rates and relative changes;
- `baseline-smoke.log` and `optimized-smoke.log`: runtime-selection evidence;
- `baseline-output.txt` and `optimized-output.txt`: output-only semantic canaries;
- `output-contract.json`: machine-checked expected output and equivalence;
- `environment.txt`: architecture, compiler, source revision and model hash;
- `run.log`: stage-by-stage build and execution history.

## Claim boundaries

Version 1 validates one model and workload. Version 2 broadens this to three model/quantization conditions, three workload shapes and two Arm Ubuntu images, with independent peak RSS and cold explanation measurement. It still does not establish universal Arm or KleidiAI performance, power savings, independent human-rated free-form quality or physical-device safety.
