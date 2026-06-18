#!/usr/bin/env bash
# From Buildkite label: :full_moon: Omni · Doc Test with H100
set -euo pipefail
cd "/alicia/vllm-omni"
pytest -s -v tests/examples/ -m "full_model and omni and H100" --run-level "full_model"
