#!/usr/bin/env bash
# From Buildkite label: :full_moon: Omni · Accuracy Test
set -euo pipefail
cd "/alicia/vllm-omni"
export SEED_TTS_WER_EVAL=1
export SEED_TTS_EVAL_DEVICE=cuda:1
pytest -s -v tests/e2e/accuracy/qwen3_omni/test_qwen3_omni.py -m "full_model" --run-level full_model
