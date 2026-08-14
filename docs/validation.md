# Judge validation guide

The fastest audit path takes under five minutes and does not require trusting the headline.

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

This validates one model, quantization, source revision, workload and Arm runner class. It does not establish universal KleidiAI performance, peak-memory savings, free-form explanation quality or physical-device safety.
