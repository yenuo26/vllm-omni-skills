#!/usr/bin/env bash
# From Buildkite label: :full_moon: Omni · Function Test with H100
set -euo pipefail
cd "/alicia/vllm-omni"
pytest -sv tests/e2e --run-level "full_model" -m "full_model and H100 and omni" --ignore=tests/e2e/accuracy --ignore=tests/e2e/online_serving/test_qwen3_omni_multi_replicas.py
