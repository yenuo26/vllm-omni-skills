#!/usr/bin/env bash
# From Buildkite label: :full_moon: Quantization Test with H100
set -euo pipefail
cd "/alicia/vllm-omni"
timeout 60m pytest -sv tests/diffusion/quantization -m 'full_model and cuda and H100' --run-level "full_model"
