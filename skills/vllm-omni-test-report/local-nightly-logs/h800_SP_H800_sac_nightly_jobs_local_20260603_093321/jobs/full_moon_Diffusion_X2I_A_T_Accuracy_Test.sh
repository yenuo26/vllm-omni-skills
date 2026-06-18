#!/usr/bin/env bash
# From Buildkite label: :full_moon: Diffusion X2I(&A&T) · Accuracy Test
set -euo pipefail
cd "/alicia/vllm-omni"
pytest -s -v tests/e2e/accuracy/test_qwen_image*.py --run-level full_model
pytest -s -v tests/e2e/accuracy/test_diffusers_backend_similarity.py -k '2i_matches_diffusers' -m full_model --run-level full_model
