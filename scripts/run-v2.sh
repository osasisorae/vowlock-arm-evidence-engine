#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
manifest="${V2_MANIFEST:-${root_dir}/experiment.v2.json}"
host_label="${V2_HOST_LABEL:-unknown-arm64-host}"
work_dir="${root_dir}/work/v2"
source_dir="${work_dir}/llama.cpp"
baseline_dir="${work_dir}/build-baseline"
optimized_dir="${work_dir}/build-kleidiai"
model_dir="${root_dir}/model"
result_root="${root_dir}/results/v2"
raw_root="${result_root}/raw"
host_root="${raw_root}/${host_label}"
threads="${BENCH_THREADS:-$(getconf _NPROCESSORS_ONLN)}"
jobs="${BUILD_JOBS:-$(getconf _NPROCESSORS_ONLN)}"
llama_ref="1ee1cd9bc65a56ab50e2ed19a48709dc42d1dd9d"

arch="$(uname -m)"
if [[ "${arch}" != "aarch64" && "${arch}" != "arm64" ]]; then
  echo "Refusing Version 2 performance run: real Arm64 is required; detected ${arch}." >&2
  exit 2
fi

for command in cmake curl git python3 sha256sum /usr/bin/time; do
  if ! command -v "${command}" >/dev/null 2>&1; then
    echo "Missing required command: ${command}" >&2
    exit 2
  fi
done

mkdir -p "${work_dir}" "${model_dir}" "${host_root}"
exec > >(tee -a "${host_root}/run.log") 2>&1
trap 'status=$?; printf "failed_status=%s failed_line=%s\n" "${status}" "${LINENO}" >&2' ERR

python3 "${root_dir}/v2_matrix.py" --manifest "${manifest}" validate

printf 'stage=prepare-source host=%s\n' "${host_label}"
if [[ ! -d "${source_dir}/.git" ]]; then
  git clone --filter=blob:none https://github.com/ggml-org/llama.cpp.git "${source_dir}"
fi
git -C "${source_dir}" fetch --depth 1 origin "${llama_ref}"
git -C "${source_dir}" checkout --detach "${llama_ref}"

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

printf 'stage=download-and-verify-models\n'
while IFS=$'\t' read -r model_id filename model_url model_sha model_bytes runtime_variants; do
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
done < <(python3 "${root_dir}/v2_matrix.py" --manifest "${manifest}" models-tsv)

semantic_failed=0

while IFS=$'\t' read -r model_id filename model_url model_sha model_bytes runtime_variants; do
  model_path="${model_dir}/${filename}"
  IFS=',' read -r -a runtimes <<< "${runtime_variants}"
  for runtime in "${runtimes[@]}"; do
    if [[ "${runtime}" == "baseline" ]]; then
      build_dir="${baseline_dir}"
    elif [[ "${runtime}" == "kleidiai" ]]; then
      build_dir="${optimized_dir}"
    else
      echo "Unknown runtime: ${runtime}" >&2
      exit 3
    fi
    condition_dir="${host_root}/${model_id}/${runtime}"
    mkdir -p "${condition_dir}/candidates"

    printf 'stage=backend-verification model=%s runtime=%s\n' "${model_id}" "${runtime}"
    "${build_dir}/bin/llama-completion" \
      --device none --verbose -m "${model_path}" -no-cnv -p "The" -n 1 --temp 0 \
      >"${condition_dir}/backend.log" 2>&1
    if [[ "${runtime}" == "baseline" ]] && grep -Eq "load_tensors:.*CPU_KLEIDIAI model buffer" "${condition_dir}/backend.log"; then
      echo "Baseline unexpectedly selected CPU_KLEIDIAI for ${model_id}." >&2
      exit 3
    fi
    if [[ "${runtime}" == "kleidiai" ]] && ! grep -Eq "load_tensors:.*CPU_KLEIDIAI model buffer" "${condition_dir}/backend.log"; then
      echo "Optimized build did not select CPU_KLEIDIAI for ${model_id}." >&2
      exit 3
    fi

    printf 'stage=resource-measurement model=%s runtime=%s\n' "${model_id}" "${runtime}"
    python3 "${root_dir}/v2_matrix.py" --manifest "${manifest}" energy-snapshot --output "${condition_dir}/energy-before.json" >/dev/null
    /usr/bin/time -v -o "${condition_dir}/time.txt" \
      "${build_dir}/bin/llama-completion" \
      --device none -m "${model_path}" --conversation --single-turn \
      -p "Reply with exactly READY and nothing else." -n 1 --temp 0 --seed 424242 \
      --simple-io --no-display-prompt --log-verbosity 0 \
      >"${condition_dir}/cold-output.txt" 2>&1
    python3 "${root_dir}/v2_matrix.py" --manifest "${manifest}" energy-snapshot --output "${condition_dir}/energy-after.json" >/dev/null
    python3 "${root_dir}/v2_matrix.py" --manifest "${manifest}" parse-time \
      "${condition_dir}/time.txt" --artifact "${model_path}" \
      --energy-before "${condition_dir}/energy-before.json" --energy-after "${condition_dir}/energy-after.json" \
      --output "${condition_dir}/resource.json" >/dev/null

    printf 'stage=semantic-evaluation model=%s runtime=%s\n' "${model_id}" "${runtime}"
    while IFS= read -r fixture_id; do
      prompt_path="${condition_dir}/${fixture_id}-prompt.txt"
      python3 "${root_dir}/setup_companion_eval.py" --fixtures "${root_dir}/fixtures/setup-companion-v2.json" prompt "${fixture_id}" >"${prompt_path}"
      "${build_dir}/bin/llama-completion" \
        --device none -m "${model_path}" --conversation --single-turn \
        -f "${prompt_path}" -n 220 --temp 0 --seed 424242 \
        --simple-io --no-display-prompt --log-verbosity 0 \
        >"${condition_dir}/candidates/${fixture_id}.txt" 2>&1
    done < <(python3 "${root_dir}/setup_companion_eval.py" --fixtures "${root_dir}/fixtures/setup-companion-v2.json" ids)
    if ! python3 "${root_dir}/setup_companion_eval.py" --fixtures "${root_dir}/fixtures/setup-companion-v2.json" \
      evaluate-dir "${condition_dir}/candidates" --output "${condition_dir}/semantic.json"; then
      semantic_failed=1
      printf 'semantic_status=failed model=%s runtime=%s\n' "${model_id}" "${runtime}"
    fi

    printf 'stage=throughput model=%s runtime=%s\n' "${model_id}" "${runtime}"
    while IFS=$'\t' read -r workload_id prompt_tokens generation_tokens repetitions; do
      "${build_dir}/bin/llama-bench" --device none -m "${model_path}" \
        -p "${prompt_tokens}" -n "${generation_tokens}" -r "${repetitions}" \
        -t "${threads}" -o json >"${condition_dir}/${workload_id}.json"
    done < <(python3 "${root_dir}/v2_matrix.py" --manifest "${manifest}" workloads-tsv)
  done
done < <(python3 "${root_dir}/v2_matrix.py" --manifest "${manifest}" models-tsv)

{
  date --iso-8601=seconds
  uname -a
  printf 'host_label=%s\n' "${host_label}"
  printf 'architecture=%s\n' "${arch}"
  printf 'threads=%s\n' "${threads}"
  printf 'llama_cpp_commit=%s\n' "$(git -C "${source_dir}" rev-parse HEAD)"
  cmake --version | head -n 1
  cc --version | head -n 1
  command -v lscpu >/dev/null 2>&1 && lscpu
} >"${host_root}/environment.txt"

python3 "${root_dir}/v2_matrix.py" --manifest "${manifest}" summarize "${raw_root}" \
  --host "${host_label}" --output "${result_root}/summary-${host_label}.json"

printf 'stage=complete semantic_failed=%s\n' "${semantic_failed}"
if [[ "${semantic_failed}" != "0" ]]; then
  echo "One or more registered semantic conditions failed; raw evidence and summary were preserved." >&2
  exit 4
fi
