# Using the V5 explanation compiler

V5 compiles one strictly typed Setup Companion device state into an auditable decision and explanation. It does not download or call a language model, use a network, or operate a device.

## Run one state

From the repository root:

```bash
python3 v5_compiler.py examples/v5-ready-state.json --variant P0
```

Choose `B0` for a brief rendering, `D0` for a detailed rendering, or `P0` for progressive disclosure. Add `--output path/to/result.json` to preserve the output.

Each result includes:

- the authoritative decision and next action;
- every decisive rule and its evidence source;
- a canonical state hash and stable state ID;
- a hash of the complete compiled result.

The compiler accepts exactly the seven registered fields and their registered typed values. A JSON number such as `1` is not accepted where the schema requires `true`.

## Re-run the exhaustive proof harness

```bash
python3 v5_proof.py
```

The harness compiles all 648 registered states through all three variants, checks the invariants, repeats each compilation byte-for-byte, and verifies that all eight registered mutations are rejected.

## Re-run the benchmark

```bash
python3 v5_benchmark.py --output results/v5/summary.json
```

The default benchmark performs five full-domain warmup rounds and 100 measured rounds. That is 194,400 measured compilations across the three variants. The official evidence run uses GitHub's native Ubuntu 22.04 Arm64 runner.

## Scope boundary

Passing the exhaustive harness establishes correctness over the declared finite state space and registered properties. It is not a mathematical proof of the Python interpreter, operating system, hardware, or undeclared product requirements. V5 deliberately makes no claim about whether a person finds its language easy to understand.
