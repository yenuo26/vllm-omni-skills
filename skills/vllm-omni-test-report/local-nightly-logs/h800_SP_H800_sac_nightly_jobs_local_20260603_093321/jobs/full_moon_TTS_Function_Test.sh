#!/usr/bin/env bash
# From Buildkite label: :full_moon: TTS · Function Test
set -euo pipefail
cd "/alicia/vllm-omni"
export VLLM_ALLOW_LONG_MAX_MODEL_LEN="1"
pytest -s -v tests/e2e/ -m "full_model and L4 and tts" --run-level "full_model" --ignore=tests/e2e/accuracy
