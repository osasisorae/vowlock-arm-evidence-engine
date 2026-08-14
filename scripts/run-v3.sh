#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
manifest="${V3_MANIFEST:-${root_dir}/experiment.v3.json}"
host_label="${V3_HOST_LABEL:-ubuntu-22.04-arm}"
work_dir="${root_dir}/work/v3"
source_dir="${work_dir}/llama.cpp"
build_dir="${work_dir}/build"
model_dir="${root_dir}/model"
result_root="${root_dir}/results/v3"
jobs="${BUILD_JOBS:-$(getconf _NPROCESSORS_ONLN)}"
llama_ref="$(python3 "${root_dir}/v3_runtime.py" --manifest "${manifest}" runtime-commit)"

arch="$(uname -m)"
if [[ "${arch}" != "aarch64" && "${arch}" != "arm64" ]]; then
  echo "Refusing Version 3 performance run: real Arm64 is required; detected ${arch}." >&2
  exit 2
fi

for command in cmake curl git python3 sha256sum; do
  if ! command -v "${command}" >/dev/null 2>&1; then
    echo "Missing required command: ${command}" >&2
    exit 2
  fi
done

mkdir -p "${work_dir}" "${model_dir}" "${result_root}/raw/${host_label}"
exec > >(tee -a "${result_root}/raw/${host_label}/run.log") 2>&1
trap 'status=$?; printf "failed_status=%s failed_line=%s\n" "${status}" "${LINENO}" >&2' ERR

python3 "${root_dir}/v3_runtime.py" --manifest "${manifest}" validate
python3 "${root_dir}/setup_companion_eval_v3.py" \
  --fixtures "${root_dir}/fixtures/setup-companion-v3-development.json" \
  mutation-test --mutations "${root_dir}/fixtures/setup-companion-v3-mutations.json" \
  --output "${result_root}/raw/${host_label}/preflight-mutations.json" >/dev/null

printf 'stage=prepare-source host=%s\n' "${host_label}"
if [[ ! -d "${source_dir}/.git" ]]; then
  git clone --filter=blob:none https://github.com/ggml-org/llama.cpp.git "${source_dir}"
fi
git -C "${source_dir}" fetch --depth 1 origin "${llama_ref}"
git -C "${source_dir}" checkout --detach "${llama_ref}"

cmake -S "${source_dir}" -B "${build_dir}" \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_NATIVE=ON \
  -DGGML_LTO=ON \
  -DGGML_CPU_KLEIDIAI=OFF \
  -DLLAMA_CURL=OFF \
  -DLLAMA_BUILD_SERVER=ON \
  -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_BUILD_EXAMPLES=OFF \
  -DLLAMA_BUILD_TOOLS=ON
cmake --build "${build_dir}" --config Release --target llama-server llama-bench llama-completion --parallel "${jobs}"

IFS=$'\t' read -r model_id filename model_url model_sha model_bytes < <(python3 "${root_dir}/v3_runtime.py" --manifest "${manifest}" model-tsv)
model_path="${model_dir}/${filename}"
if [[ ! -f "${model_path}" ]]; then
  partial_path="${model_path}.partial"
  curl --fail --location --retry 3 --output "${partial_path}" "${model_url}"
  printf '%s  %s\n' "${model_sha}" "${partial_path}" | sha256sum --check
  mv "${partial_path}" "${model_path}"
fi
printf '%s  %s\n' "${model_sha}" "${model_path}" | sha256sum --check
actual_bytes="$(wc -c < "${model_path}" | tr -d ' ')"
if [[ "${actual_bytes}" != "${model_bytes}" ]]; then
  echo "Size mismatch for ${model_id}: ${actual_bytes} != ${model_bytes}" >&2
  exit 3
fi

printf 'stage=execute-registered-v3\n'
python3 "${root_dir}/scripts/run-v3.py" \
  --manifest "${manifest}" \
  --server-bin "${build_dir}/bin/llama-server" \
  --bench-bin "${build_dir}/bin/llama-bench" \
  --completion-bin "${build_dir}/bin/llama-completion" \
  --model "${model_path}" \
  --host-label "${host_label}" \
  --output "${result_root}"
