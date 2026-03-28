# Local test scenarios (matrix)

Canonical content for the **Local testing** section of the test report: CUDA / Torch / deps / hardware / testers, plus **result counts** and **issue tracking** from local or offline runs. Update this file when local QA scope or a test round’s summary changes.

The **CI testing** section is filled from Buildkite (scheduled nightly build link, jobs, pytest logs), not from this file.

## Common stack (all rows)

Torch **2.10.0**, Python **3.12**, Diffusers **0.37.0**, transformers **4.57.6**, huggingface_hub **0.36.2**.

## Test results analysis

Per-matrix totals for **this round** (or the agreed window) of manually / offline-run cases; numbers are filled in by testers and **do not** auto-map to CI pytest counts.

| CUDA | Torch | Hardware | Python | Diffusers | transformers | huggingface_hub | Tester | Total cases | Passed | Failed |
|------|-------|----------|--------|-----------|--------------|-----------------|--------|-------------|--------|--------|
| 12.8 | 2.10.0 | A100 | 3.12 | 0.37.0 | 4.57.6 | 0.36.2 | zhumingjue138 | 141 | 140 | 1 |
| 12.8 | 2.10.0 | H800 | 3.12 | 0.37.0 | 4.57.6 | 0.36.2 | yenuo26 | 141 | 141 | 0 |
| 12.8 | 2.10.0 | H20 | 3.12 | 0.37.0 | 4.57.6 | 0.36.2 | ZJY0516 | 141 | 141 | 0 |
| 12.9 | 2.10.0 | A100 | 3.12 | 0.37.0 | 4.57.6 | 0.36.2 | zhumingjue138 | 141 | 141 | 0 |
| 12.9 | 2.10.0 | H800 | 3.12 | 0.37.0 | 4.57.6 | 0.36.2 | yenuo26 | 141 | 141 | 0 |
| 12.9 | 2.10.0 | H20 | 3.12 | 0.37.0 | 4.57.6 | 0.36.2 | ZJY0516 | 141 | 141 | 0 |
| 13.0 | 2.10.0 | H800 | 3.12 | 0.37.0 | 4.57.6 | 0.36.2 | yenuo26 | 141 | 141 | 0 |
| 13.0 | 2.10.0 | H20 | 3.12 | 0.37.0 | 4.57.6 | 0.36.2 | ZJY0516 | 141 | 141 | 0 |

## Issue tracking

| Issue | Description | Status |
|-------|-------------|--------|
| https://github.com/vllm-project/vllm-omni/issues/2255 | AssertionError: Pixel mismatch at (150, 400): expected (195, 34, 60), got (182, 25, 47) for tests/e2e/offline_inference/test_bagel_img2img.py | open |
| https://github.com/vllm-project/vllm-omni/pull/2239 | incorrect answers for single words | closed |
| https://github.com/vllm-project/vllm-omni/issues/2168 | torch.AcceleratorError: CUDA error: device-side assert triggered for Qwen2.5 model | closed |
