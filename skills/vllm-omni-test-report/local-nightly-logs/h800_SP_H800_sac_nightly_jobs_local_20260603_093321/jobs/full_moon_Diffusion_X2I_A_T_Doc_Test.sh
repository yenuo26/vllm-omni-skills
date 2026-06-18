#!/usr/bin/env bash
# From Buildkite label: :full_moon: Diffusion X2I(&A&T) · Doc Test
set -euo pipefail
cd "/alicia/vllm-omni"
pytest -s -v tests/examples/*/test_text_to_image.py -m "full_model and example and H100" --run-level "full_model"
