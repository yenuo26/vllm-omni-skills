#!/usr/bin/env bash
# From Buildkite label: :full_moon: Omni · Multi-Replica Startup Test with 4x H100
set -euo pipefail
cd "/alicia/vllm-omni"
pytest -s -v tests/e2e/online_serving/test_qwen3_omni_multi_replicas.py -m "full_model" --run-level "core_model"
