#!/usr/bin/env bash
# From Buildkite label: :full_moon: Diffusion X2V · Function Test
set -euo pipefail
cd "/alicia/vllm-omni"
pytest -s -v tests/e2e/online_serving/test_wan22_expansion.py tests/e2e/online_serving/test_wan_2_1_vace_expansion.py tests/e2e/online_serving/test_hunyuan_video_15_expansion.py tests/e2e/offline_inference/test_wan22_autoround_w4a16_expansion.py -m "full_model and cuda" --run-level "full_model"
