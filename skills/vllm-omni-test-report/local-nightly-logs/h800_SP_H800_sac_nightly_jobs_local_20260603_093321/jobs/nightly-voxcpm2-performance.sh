#!/usr/bin/env bash
# From Buildkite label: :full_moon: VoxCPM2 · Perf Test
set -euo pipefail
cd "/alicia/vllm-omni"
export BENCHMARK_DIR=tests/dfx/perf/results
export VLLM_ALLOW_LONG_MAX_MODEL_LEN="1"
pytest -s -v tests/dfx/perf/scripts/run_benchmark.py --test-config-file tests/dfx/perf/tests/test_voxcpm2.json
