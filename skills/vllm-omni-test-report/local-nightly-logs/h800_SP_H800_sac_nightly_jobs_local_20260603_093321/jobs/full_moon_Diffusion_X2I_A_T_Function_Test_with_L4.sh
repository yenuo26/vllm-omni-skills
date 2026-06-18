#!/usr/bin/env bash
# From Buildkite label: :full_moon: Diffusion X2I(&A&T) · Function Test with L4
set -euo pipefail
cd "/alicia/vllm-omni"
pytest -sv tests/e2e/ -k "not test_wan and not test_bagel_expansion and not hunyuan" -m "full_model and diffusion and L4" --run-level "full_model" --ignore=tests/e2e/accuracy
