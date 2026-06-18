#!/usr/bin/env bash
# From Buildkite label: :full_moon: Diffusion X2V · Perf Test
set -euo pipefail
cd "/alicia/vllm-omni"
export DIFFUSION_BENCHMARK_DIR=tests/dfx/perf/results
export DIFFUSION_ATTENTION_BACKEND=FLASH_ATTN
pytest -s -v tests/dfx/perf/scripts/run_diffusion_benchmark.py --test-config-file tests/dfx/perf/tests/test_wan22_i2v_vllm_omni.json
