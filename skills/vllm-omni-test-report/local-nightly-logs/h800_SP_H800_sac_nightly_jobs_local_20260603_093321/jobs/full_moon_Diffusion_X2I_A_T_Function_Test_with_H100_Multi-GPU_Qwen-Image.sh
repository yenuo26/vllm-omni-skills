#!/usr/bin/env bash
# From Buildkite label: :full_moon: Diffusion X2I(&A&T) · Function Test with H100 · Multi-GPU Qwen-Image
set -euo pipefail
cd "/alicia/vllm-omni"
pytest -sv tests/e2e/online_serving/test_qwen_image_expansion.py tests/e2e/online_serving/test_qwen_image_edit_expansion.py -m "full_model and diffusion and H100 and distributed_cuda" --run-level "full_model"
