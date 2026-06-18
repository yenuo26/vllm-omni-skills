#!/usr/bin/env bash
# From Buildkite label: :full_moon: Diffusion X2I(&A&T) · Perf Test · Qwen-Image-Edit-2511
set -euo pipefail
cd "/alicia/vllm-omni"
export DIFFUSION_BENCHMARK_DIR=tests/dfx/perf/results
export DIFFUSION_ATTENTION_BACKEND=FLASH_ATTN
export CACHE_DIT_VERSION=1.3.0
pytest -s -v tests/dfx/perf/scripts/run_diffusion_benchmark.py --test-config-file tests/dfx/perf/tests/test_qwen_image_edit_2511_vllm_omni.json
