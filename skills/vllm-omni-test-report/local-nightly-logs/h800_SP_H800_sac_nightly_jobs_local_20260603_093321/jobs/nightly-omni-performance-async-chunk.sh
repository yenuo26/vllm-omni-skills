#!/usr/bin/env bash
# From Buildkite label: :full_moon: Omni · Perf Test · Async Chunk
set -euo pipefail
cd "/alicia/vllm-omni"
export BENCHMARK_DIR=tests/dfx/perf/results
pytest -s -v tests/dfx/perf/scripts/run_benchmark.py --test-config-file tests/dfx/perf/tests/test_qwen3_omni_async_chunk.json
