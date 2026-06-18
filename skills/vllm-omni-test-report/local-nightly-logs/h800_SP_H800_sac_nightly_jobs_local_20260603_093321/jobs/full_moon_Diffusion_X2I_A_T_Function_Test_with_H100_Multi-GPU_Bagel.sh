#!/usr/bin/env bash
# From Buildkite label: :full_moon: Diffusion X2I(&A&T) · Function Test with H100 · Multi-GPU Bagel
set -euo pipefail
cd "/alicia/vllm-omni"
pytest -sv tests/e2e/online_serving/test_bagel_expansion.py -m "full_model and diffusion and H100 and distributed_cuda" --run-level "full_model"
