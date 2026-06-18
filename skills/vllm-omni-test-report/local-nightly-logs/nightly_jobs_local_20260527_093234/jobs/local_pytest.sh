#!/usr/bin/env bash
# Local marker tests — MODEL_TYPE=all
set -euo pipefail
cd "/workspace/zmj/podzcg/vllm-omni-main"
pytest -sv -m "(omni or tts or diffusion) and local_model"
