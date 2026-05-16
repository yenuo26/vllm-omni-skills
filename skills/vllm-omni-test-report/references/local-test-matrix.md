# Local test scenarios (matrix)

Canonical content for the **Local testing** section of the test report: CUDA / Torch / deps / hardware / testers, plus **result counts** and **issue tracking** from local or offline runs. Update this file when local QA scope or a test round’s summary changes.

The **CI testing** section is filled from Buildkite (scheduled nightly build link, jobs, pytest logs), not from this file.

## Common stack (all rows)

Torch **2.11.0**, Python **3.12**, Diffusers **0.37.1**, transformers **5.8.0**, huggingface_hub **1.13.0**.

## Test results analysis

Per-matrix totals for **this round** (or the agreed window) of manually / offline-run cases; numbers are filled in by testers and **do not** auto-map to CI pytest counts.

### Functional testing

| CUDA | Torch | Hardware | Python | Diffusers | transformers | huggingface_hub | Tester | Total cases | Passed Job | Failed Job |
|------|-------|----------|--------|-----------|--------------|-----------------|--------|-------------|--------|--------|
| 13.0 | 2.11.0 | H200 | 3.12 | 0.37.1 | 5.8.0 | 1.13.0 | yenuo26 | 19 | 13 | 6 |

### Long-run stability

| CUDA | Torch | Hardware | Python | Diffusers | transformers | huggingface_hub | Tester | Scenario (e.g. load / duration) | Result |
|------|-------|----------|--------|-----------|--------------|-----------------|--------|--------------------------------|--------|
| 13.0 | 2.11.0 | H200 | 3.12 | 0.37.1 | 5.8.0 | 1.13.0 | zhumingjue | wan2.2 24h | Passed |
| 13.0 | 2.11.0 | H200 | 3.12 | 0.37.1 | 5.8.0 | 1.13.0 | zhumingjue | qwen-image 24h | Passed |
| 13.1 | 2.11.0 | A100 | 3.12 | 0.37.1 | 5.7.0 | 1.13.0 | zhumingjue | wan2.2 24h | Passed |
| 13.1 | 2.11.0 | A100 | 3.12 | 0.37.1 | 5.7.0 | 1.13.0 | zhumingjue | qwen-image 24h | Passed |
| 13.1 | 2.11.0 | A100 | 3.12 | 0.37.1 | 5.7.0 | 1.13.0 | zhumingjue | qwen3-omni 24h | Passed |
| 13.1 | 2.11.0 | A100 | 3.12 | 0.37.1 | 5.7.0 | 1.13.0 | zhumingjue | qwen3-tts 24h | Passed |

## Issue tracking

| Issue | Description | Status |
|-------|-------------|--------|
| https://github.com/vllm-project/vllm-omni/issues/3372 | [Bug]: stability test: stop sending requests after send 60 requests for qwen3-omni model | closed |
