#!/usr/bin/env bash
# From Buildkite label: :full_moon: Omni · Function Test with L4
set -euo pipefail
cd "/alicia/vllm-omni"
export VLLM_ALLOW_LONG_MAX_MODEL_LEN="1"
pytest -s -v tests/e2e/*/test_qwen2_5_omni_expansion.py --run-level "core_model"
