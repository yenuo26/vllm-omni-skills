#!/usr/bin/env bash
# From Buildkite label: :full_moon: Diffusion X2I(&A&T) · Function Test with H100 · Multi-GPU Layered/LongCat/FLUX
set -euo pipefail
cd "/alicia/vllm-omni"
pytest -sv tests/e2e/online_serving/test_qwen_image_layered_expansion.py tests/e2e/online_serving/test_longcat_image_expansion.py tests/e2e/online_serving/test_longcat_image_edit_expansion.py tests/e2e/online_serving/test_flux_2_dev_expansion.py tests/e2e/offline_inference/test_glm_image_autoround_w4a16_expansion.py -m "full_model and diffusion and H100 and distributed_cuda" --run-level "full_model"
