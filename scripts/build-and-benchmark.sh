#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
work_dir="${root_dir}/work"
source_dir="${work_dir}/llama.cpp"
baseline_dir="${work_dir}/build-baseline"
optimized_dir="${work_dir}/build-kleidiai"
result_dir="${root_dir}/results"
model_path="${root_dir}/model/qwen2.5-1.5b-instruct-q4_0.gguf"

llama_ref="1ee1cd9bc65a56ab50e2ed19a48709dc42d1dd9d"
model_revision="91cad51170dc346986eccefdc2dd33a9da36ead9"
model_url="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/${model_revision}/qwen2.5-1.5b-instruct-q4_0.gguf?download=true"
model_sha256="dcd819ff094852c38faba6873d8ff0c9d51eadb2844539e52042ae5d647bbfdb"
threads="${BENCH_THREADS:-$(getconf _NPROCESSORS_ONLN)}"
jobs="${BUILD_JOBS:-$(getconf _NPROCESSORS_ONLN)}"

arch="$(uname -m)"
if [[ "${arch}" != "aarch64" && "${arch}" != "arm64" ]]; then
  echo "Refusing performance run: real Arm64 is required; detected ${arch}." >&2
  exit 2
fi

for command in cmake curl git python3 sha256sum; do
  if ! command -v "${command}" >/dev/null 2>&1; then
    echo "Missing required command: ${command}" >&2
    exit 2
  fi
done

mkdir -p "${work_dir}" "${result_dir}" "$(dirname "${model_path}")"
exec > >(tee -a "${result_dir}/run.log") 2>&1
trap 'status=$?; printf "failed_status=%s failed_line=%s\n" "${status}" "${LINENO}" >&2' ERR

printf 'stage=prepare-source\n'

if [[ ! -d "${source_dir}/.git" ]]; then
  git clone --filter=blob:none https://github.com/ggml-org/llama.cpp.git "${source_dir}"
fi
git -C "${source_dir}" fetch --depth 1 origin "${llama_ref}"
git -C "${source_dir}" checkout --detach "${llama_ref}"

if [[ ! -f "${model_path}" ]]; then
  printf 'stage=download-model\n'
  partial_path="${model_path}.partial"
  curl --fail --location --retry 3 --output "${partial_path}" "${model_url}"
  printf '%s  %s\n' "${model_sha256}" "${partial_path}" | sha256sum --check
  mv "${partial_path}" "${model_path}"
fi
printf '%s  %s\n' "${model_sha256}" "${model_path}" | sha256sum --check

common_flags=(
  -DCMAKE_BUILD_TYPE=Release
  -DGGML_NATIVE=ON
  -DGGML_LTO=ON
  -DLLAMA_CURL=OFF
  -DLLAMA_BUILD_SERVER=OFF
  -DLLAMA_BUILD_TESTS=OFF
  -DLLAMA_BUILD_EXAMPLES=OFF
  -DLLAMA_BUILD_TOOLS=ON
)

printf 'stage=build-baseline\n'
cmake -S "${source_dir}" -B "${baseline_dir}" "${common_flags[@]}" -DGGML_CPU_KLEIDIAI=OFF
cmake --build "${baseline_dir}" --config Release --target llama-bench llama-completion --parallel "${jobs}"

printf 'stage=build-kleidiai\n'
cmake -S "${source_dir}" -B "${optimized_dir}" "${common_flags[@]}" -DGGML_CPU_KLEIDIAI=ON
cmake --build "${optimized_dir}" --config Release --target llama-bench llama-completion --parallel "${jobs}"

printf 'stage=backend-verification\n'
backend_args=(
  --device none
  --verbose
  -m "${model_path}"
  -no-cnv
  -p "The"
  -n 1
  --temp 0
)
"${baseline_dir}/bin/llama-completion" "${backend_args[@]}" >"${result_dir}/baseline-smoke.log" 2>&1
"${optimized_dir}/bin/llama-completion" "${backend_args[@]}" >"${result_dir}/optimized-smoke.log" 2>&1

if grep -Eq "load_tensors:.*CPU_KLEIDIAI model buffer" "${result_dir}/baseline-smoke.log"; then
  echo "Baseline unexpectedly selected the CPU_KLEIDIAI model buffer." >&2
  grep -Ei "load_tensors:|KLEIDIAI|system_info" "${result_dir}/baseline-smoke.log" >&2 || true
  exit 3
fi

if ! grep -Eq "load_tensors:.*CPU_KLEIDIAI model buffer" "${result_dir}/optimized-smoke.log"; then
  echo "Optimized build did not prove that the CPU_KLEIDIAI buffer was selected." >&2
  grep -Ei "load_tensors:|KLEIDIAI|system_info" "${result_dir}/optimized-smoke.log" >&2 || true
  exit 3
fi

printf 'stage=output-contract\n'
output_args=(
  --device none
  -m "${model_path}"
  --conversation
  --single-turn
  -p "Reply with exactly READY and nothing else."
  -n 1
  --temp 0
  --seed 424242
  --simple-io
  --no-display-prompt
  --log-verbosity 0
)
"${baseline_dir}/bin/llama-completion" "${output_args[@]}" >"${result_dir}/baseline-output.txt" 2>&1
"${optimized_dir}/bin/llama-completion" "${output_args[@]}" >"${result_dir}/optimized-output.txt" 2>&1
python3 "${root_dir}/output_contract.py" \
  "${result_dir}/baseline-output.txt" \
  "${result_dir}/optimized-output.txt" \
  --expected READY \
  --output "${result_dir}/output-contract.json"

printf 'stage=benchmark\n'
benchmark_args=(
  --device none
  -m "${model_path}"
  -p 512
  -n 128
  -r 5
  -t "${threads}"
  -o json
)
"${baseline_dir}/bin/llama-bench" "${benchmark_args[@]}" >"${result_dir}/baseline.json"
"${optimized_dir}/bin/llama-bench" "${benchmark_args[@]}" >"${result_dir}/optimized.json"

{
  date --iso-8601=seconds
  uname -a
  printf 'architecture=%s\n' "${arch}"
  printf 'threads=%s\n' "${threads}"
  printf 'llama_cpp_commit=%s\n' "$(git -C "${source_dir}" rev-parse HEAD)"
  printf 'model_sha256=%s\n' "$(sha256sum "${model_path}" | cut -d' ' -f1)"
  cmake --version | head -n 1
  cc --version | head -n 1
  command -v lscpu >/dev/null 2>&1 && lscpu
} >"${result_dir}/environment.txt"

python3 "${root_dir}/benchmark.py" \
  "${result_dir}/baseline.json" \
  "${result_dir}/optimized.json" \
  --output "${result_dir}/summary.json"

printf 'stage=complete\n'
