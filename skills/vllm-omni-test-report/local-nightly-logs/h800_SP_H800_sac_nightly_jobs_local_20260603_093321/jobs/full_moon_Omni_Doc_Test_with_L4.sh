#!/usr/bin/env bash
# From Buildkite label: :full_moon: Omni · Doc Test with L4
set -euo pipefail
cd "/alicia/vllm-omni"
export VLLM_ALLOW_LONG_MAX_MODEL_LEN="1"
pytest -s -v tests/examples/ -m "full_model and omni and L4" --run-level "full_model"
