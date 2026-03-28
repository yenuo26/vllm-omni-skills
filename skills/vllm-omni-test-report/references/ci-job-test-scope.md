# CI job test scope (Scheduled nightly)

This reference describes the intended test coverage of common **Buildkite job names** for **vllm-omni** (Scheduled nightly–oriented; exact pytest nodes follow each build’s logs). Steps that only upload artifacts—such as `Upload * Pipeline`—are not listed here.

## Diffusion / video generation

| Typical job name | Scope / intent |
|------------------|----------------|
| **Diffusion Model Test with H100** | Diffusion pytest on **H100** (multimodal diffusion inference, configuration, and regressions; see `tests/` paths in the log). |
| **Diffusion Model Test with L4** | Diffusion pytest on **L4** (different hardware / VRAM tier vs the H100 row). |
| **Diffusion Model Wan22 completed Test with H100** | **Wan 2.2** diffusion / video flows (completed path on **H100**). |
| **Qwen-Image Diffusion Perf Test with H100** | **Qwen-Image** diffusion **performance** and related regressions on **H100**. |

## Omni multimodal

| Typical job name | Scope / intent |
|------------------|----------------|
| **Omni Model Test** | **Qwen-Omni** end-to-end capability (multimodal inference, API/engine integration). |
| **Omni Model Test with H100** | Same as above, pinned to **H100**. |
| **Omni Model Perf Test & Test Case Statistics** | Omni **performance**, test-case statistics, and related regressions (perf / stats–oriented). |

## Speech / TTS

| Typical job name | Scope / intent |
|------------------|----------------|
| **Qwen3-TTS Non-Async-Chunk E2E Test** | **Qwen3-TTS** **end-to-end** non–async chunk scenarios (service/inference path and audio output regressions). |

## Benchmarks & docs

| Typical job name | Scope / intent |
|------------------|----------------|
| **GEBench Accuracy Test with H100** | **GEBench** image-generation **accuracy/quality** benchmark (**H100**). |
| **GEdit-Bench Accuracy Test with H100** | **GEdit-Bench** editing **accuracy** benchmark (**H100**). |
| **Documentation Example Code Test with H100** | Runnable **documentation examples** (examples tied to docs, executed on **H100**). |

## Unit tests & coverage (Metrics **ut**)

| Source | Scope / intent |
|--------|----------------|
| **Simple Unit Test** (step on the **latest non–Scheduled nightly** build on [`main`](https://buildkite.com/vllm/vllm-omni/builds?branch=main)) | Repo **unit / fast pytest** and **coverage** (e.g. **TOTAL** row). **Metrics overview** rows **ut** / **ut (exclude models)** come from `buildkite_build_stats.py` parsing that step’s log (independent of the Metrics date window; see `references/buildkite-api.md`). |

## Maintenance

- Job names change with `.buildkite` / pipeline YAML; keep this file in sync when Buildkite labels change.
- For failure details, rely on each step’s **raw log** and the **Per-job test execution (pytest)** table.
