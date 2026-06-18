#!/usr/bin/env bash
# From Buildkite label: :full_moon: Quantization Test with L4
set -euo pipefail
cd "/alicia/vllm-omni"
pytest -sv tests/diffusion/quantization -m 'full_model and cuda and L4' --run-level "full_model"
