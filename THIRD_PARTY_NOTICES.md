# Third-party notices

This repository does not vendor the model or `llama.cpp` source. The reproducibility script downloads pinned upstream artifacts at run time.

## llama.cpp

- Source: https://github.com/ggml-org/llama.cpp
- Pinned revision: `1ee1cd9bc65a56ab50e2ed19a48709dc42d1dd9d`
- Upstream license: MIT

The pinned source contains its own third-party components and notices, including the KleidiAI integration used by this experiment. Those upstream license files remain authoritative.

## KleidiAI

- Upstream project: https://github.com/ARM-software/kleidiai
- Description: Arm-optimized AI micro-kernels integrated through the pinned `llama.cpp` source.

This repository enables the upstream integration through `GGML_CPU_KLEIDIAI`; it does not copy or modify KleidiAI source files.

## Qwen2.5 1.5B Instruct GGUF

- Artifact source: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF
- Pinned revision: `91cad51170dc346986eccefdc2dd33a9da36ead9`
- File: `qwen2.5-1.5b-instruct-q4_0.gguf`
- Upstream license: Apache-2.0

The model is downloaded into the ignored `model/` directory and is not redistributed by this repository.
