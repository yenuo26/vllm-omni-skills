#!/usr/bin/env bash
# From Buildkite label: :full_moon: Diffusion X2V · Accuracy Test
set -euo pipefail
cd "/alicia/vllm-omni"
pytest -s -v tests/e2e/accuracy/wan22_i2v/test_wan22_i2v_video_similarity.py -m full_model --run-level full_model
pytest -s -v tests/e2e/accuracy/hunyuanvideo15_t2v/test_hunyuanvideo15_t2v_video_similarity.py -m full_model --run-level full_model
pytest -s -v tests/e2e/accuracy/hunyuanvideo15_i2v/test_hunyuanvideo15_i2v_video_similarity.py -m full_model --run-level full_model
pytest -s -v tests/e2e/accuracy/test_ltx2_3_video_similarity.py -m full_model --run-level full_model
pytest -s -v tests/e2e/accuracy/test_diffusers_backend_similarity.py -k '2v_matches_diffusers' -m full_model --run-level full_model
