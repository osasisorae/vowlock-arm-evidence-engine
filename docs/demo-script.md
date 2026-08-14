# Demo script — target 2 minutes 15 seconds

Record at 1080p with no copyrighted music. Show the actual repository, GitHub Actions run and evidence page. Do not show unrelated VowLock customer or device data.

## 0:00–0:20 — Hook

On screen: the result card.

> An optimization flag is a hypothesis, not a result. I wanted to know whether Arm KleidiAI actually makes the small local model proposed for VowLock's offline Setup Companion faster. So I built an evidence engine that refuses to call the switch a win until the runtime, benchmark and output all agree.

## 0:20–0:48 — Controlled comparison

On screen: README comparison table, then `scripts/build-and-benchmark.sh`.

> The same pinned Qwen model and llama.cpp revision are built twice on one real Arm64 cloud runner. The only experimental variable is KleidiAI off versus on. The script verifies the model hash, CPU architecture, thread count and workload before it permits a result.

## 0:48–1:12 — Prove Arm optimization

On screen: optimized Run 7 log lines containing I8MM, `KLEIDIAI = 1`, and `CPU_KLEIDIAI`; then the baseline absence.

> I do not infer acceleration from a build flag. The optimized log must select I8MM kernels and the CPU_KLEIDIAI buffer, while the baseline must not. The workflow stops if that evidence is missing.

## 1:12–1:38 — Result

On screen: the three-run table.

> Runs four, five and six used the exact same commit. Prompt processing improved by about zero point eight seven percent, but generation slowed by one point five eight percent. The direction repeated every time. So the honest conclusion is not 'KleidiAI made VowLock faster.' It is that this workload received no material overall speedup.

## 1:38–1:58 — Verifier lesson

On screen: `output-contract.json` from Run 7.

> A green workflow also hid a bad semantic smoke test. I preserved the replications first, then repaired the gate separately. Run seven proves both runtimes returned exactly READY, while the verifier also rejects two answers that match each other but are wrong.

## 1:58–2:15 — Close

On screen: evidence page and public repository.

> This is the VowLock Arm Evidence Engine: an open, zero-cost pattern for proving what ran, what changed and what did not. Negative results stay visible, because optimization without an evidence trail is only a story.
