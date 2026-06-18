#!/usr/bin/env bash
# From Buildkite label: :full_moon: Diffusion X2I(&A&T) · Function Test with H100 · Single-GPU
set -euo pipefail
cd "/alicia/vllm-omni"
pytest -sv tests/e2e/online_serving/test_qwen_image_expansion.py tests/e2e/online_serving/test_qwen_image_edit_expansion.py tests/e2e/online_serving/test_qwen_image_layered_expansion.py tests/e2e/online_serving/test_longcat_image_expansion.py tests/e2e/online_serving/test_longcat_image_edit_expansion.py tests/e2e/online_serving/test_flux_2_dev_expansion.py tests/e2e/online_serving/test_bagel_expansion.py -m "full_model and diffusion and H100 and not distributed_cuda" --run-level "full_model"
