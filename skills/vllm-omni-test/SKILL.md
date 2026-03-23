---
name: vllm-omni-test
description: Generate and run tests for vllm-project/vllm-omni with CI-aligned levels and markers; wire new tests into Buildkite (test-ready.yml for L1/L2, test-merge.yml for L3, test-nightly.yml for L4). On completion, always provide copy-paste local and CI-like pytest commands plus prerequisites. Use when creating regression tests, adding L1-L4 coverage, selecting pytest markers, or validating fixes from issues/PRs.
---

# vLLM-Omni Test Generator & Runner

## Purpose

Use this skill to generate minimal, stable test cases and run them with the correct marker/level strategy for `vllm-project/vllm-omni`.

Default priorities:

1. Reproducible regression coverage for bug fixes
2. Correct test level and marker selection
3. Low flake, low dependency tests first
4. CI-compatible run commands
5. **Actionable run commands for the human**: whenever you add or change tests, always finish with **copy-paste-ready** `pytest` lines (local: single file and/or single test; CI-like: markers + `--run-level`), plus short **prerequisites** (GPU tier, HF cache, optional `model_prefix`). Do not assume the reader will infer commands from `test-routing.md` alone.

## Inputs

- Issue/PR link and summary
- Changed files or suspected code path
- Whether the user wants local quick validation or CI-equivalent validation
- Hardware constraints (CPU only / CUDA / ROCm / NPU)

## Workflow

### Step 1: Classify Test Goal

- **Bugfix regression**: start from a minimal failing scenario and add assertions that prevent recurrence.
- **Feature coverage**: verify new behavior and one negative/boundary case.
- **Perf/benchmark claim**: require benchmark-oriented tests and explicit metrics.

If the task is bug-oriented, also read [references/bug-test-coverage.md](../vllm-omni-review/references/bug-test-coverage.md) and produce an explicit conclusion (`required` / `recommended` / `not_needed`).

### Step 2: Select Test Level

- **L1**: unit/logic, deterministic, CPU-friendly, fastest feedback.
- **L2**: basic e2e/integration and platform-dependent checks.
- **L3/L4**: advanced model/integration/perf validation.

Use [references/test-routing.md](references/test-routing.md) for level-to-marker and command mapping.

### Step 3: Pick Markers

Always attach markers deliberately:

- Level: `core_model` (L1/L2) or `advanced_model` (L3/L4)
- Modality/area: `diffusion`, `omni`, `parallel`, `cache`
- Hardware: `cpu`, `gpu`, `cuda`, `rocm`, `npu`
- Optional: `slow`, `benchmark`, distributed markers when multi-card is required

For hardware-aware tests, prefer `@hardware_test(...)` or `hardware_marks(...)` in `tests/utils.py`.

### Naming: generated test module files (L2–L4, model-centric e2e)

When adding **new** pytest modules whose primary scope is a **specific model** (typical under `tests/e2e/offline_inference/` or `tests/e2e/online_serving/`), use this filename pattern:

| Level | Filename pattern | Example (model `Qwen/Qwen2.5-Omni-7B`) |
|-------|------------------|----------------------------------------|
| **L2**, **L3** | `test_{lowercase_model_slug}.py` | `test_qwen2_5_omni.py` |
| **L4** | `test_{lowercase_model_slug}_expansion.py` | `test_qwen2_5_omni_expansion.py` |

**Slug rules for `{lowercase_model_slug}`:**

1. Start from the HuggingFace-style id (e.g. `Qwen/Qwen2.5-Omni-7B`), but **do not** put the org into the filename: use the **repo segment only** (`Qwen2.5-Omni-7B`), not `Qwen_...` / `qwen_qwen2_5_...`.
2. **Lowercase**; replace `.`, `-`, and whitespace with a single `_` (e.g. `Qwen2.5-Omni-7B` → `qwen2_5_omni`). **Omit** trailing size tokens such as `7b` / `30b` in the basename when a single file covers that model line in the directory (matches `test_qwen2_5_omni.py` in-tree).
3. If two checkpoints in the same folder need separate modules, add a **minimal** disambiguator (e.g. `_7b` vs `_3b`) only then.
4. **L1** unit tests are **not** bound to this pattern; use `tests/<area>/test_<feature>.py` as today.

Existing references: `tests/e2e/offline_inference/test_qwen2_5_omni.py` (L2-style omni), `tests/e2e/offline_inference/test_qwen3_5_9b.py` (L2-style omni, single-stage VL), `tests/e2e/online_serving/test_qwen3_omni_expansion.py` (L4-style omni), `tests/e2e/online_serving/test_qwen_image_edit_expansion.py` / `test_qwen_image_expansion.py` (L4-style diffusion).

### Step 4: Generate Test Case Skeleton

**1. Pick the functional scenario** (then choose directory, fixtures, and markers):

| Scenario | Typical location | Fixtures / runner pattern | Baseline markers & level |
|----------|------------------|---------------------------|---------------------------|
| **Offline inference e2e** | `tests/e2e/offline_inference/` | `omni_runner` + `omni_runner_handler` (module-scoped multimodal runner); synthetic media from `tests.conftest` | L2: `core_model`, `omni`, plus `@hardware_test(...)` when GPU/NPU is required |
| **Online serving e2e** | `tests/e2e/online_serving/` | `omni_server`, `openai_client` (or equivalent HTTP/OpenAI-compatible client fixtures) when available | L2: `core_model` for smoke paths; L3/L4: `advanced_model` for heavier serving scenarios |
| **Documentation / runnable examples** | `tests/examples/offline_inference/`, `tests/examples/online_serving/` | **Offline docs (preferred):** extract Python/Bash blocks from the doc README (e.g. `ReadmeSnippet.extract_readme_snippets`), `pytest.mark.parametrize` each snippet, run via `example_runner.run` with a stable `output_subfolder`. **Online docs:** copy client/request scripts into dedicated tests and keep them in sync with the doc page. | Usually **L4**: `advanced_model`, often `example` plus hardware marks matching the nightly docs-example job (see `.buildkite/test-nightly.yml`). Full conventions: [docs/contributing/ci/test_examples/doc_example_tests.inc.md](../../../docs/contributing/ci/test_examples/doc_example_tests.inc.md) (introduced in [PR #1910](https://github.com/vllm-project/vllm-omni/pull/1910): naming, output directory layout, skip rules, avoid trimming `num_inference_steps` without a strong CI reason). |
| **Performance / benchmark** | `tests/perf/`, heavy `*_expansion.py` e2e | JSON or script-driven server + load config; assert explicit metrics / baselines | L3/L4: `advanced_model`, plus `benchmark` or other perf markers used in merge/nightly steps; wire commands to `test-merge.yml` / `test-nightly.yml` as appropriate |

**1b. Omni vs diffusion — domain-specific writing**

The scenario table above applies to **both** stacks (offline paths often live under the same `tests/e2e/offline_inference/` tree). After choosing offline/online/docs/perf, decide whether the **product under test** is an **Omni multimodal LLM pipeline** (thinker/talker/stages, text+audio+vision) or a **diffusion generative model** (image/video/audio from noise). Conventions diverge:

| Dimension | **Omni** | **Diffusion** |
|-----------|----------|----------------|
| **Domain marker** | `pytest.mark.omni` | `pytest.mark.diffusion` |
| **Primary API / fixture mental model** | Stage configs + `OmniRunner` / `generate_multimodal`; prompts and **modalities** (`text`, `audio`, …) | `Omni(...).generate(...)` with `OmniDiffusionSamplingParams`, or diffusion-oriented handlers; **sampling** args (`num_inference_steps`, `height`/`width`, `extra_body`, LoRA/offload flags) |
| **Typical assertions** | `assert_omni_response` / `OmniRunnerHandler`: stage outputs, text and optional audio | `assert_diffusion_response` or checks on tensors / `OmniRequestOutput` / image dimensions and `final_output_type` (e.g. `image`) |
| **Config artifact** | **Stage YAML** under `stage_configs/` (and platform variants: `npu/`, `rocm/`, …) tuned per omni model | Model + sampling params; YAML may appear for parallel/offload/Layerwise cases — follow an existing diffusion test in the same feature area |
| **L4 / CI pressure** | Add focused expansion cases per modality or model family as needed | Prefer **merging feature combos into fewer tests** per [#1832](https://github.com/vllm-project/vllm-omni/issues/1832) to save GPU jobs |
| **Doc-example nuance** | Online/offline omni snippets (serving, multimodal requests) | T2I/T2V READMEs: do not lower `num_inference_steps` (or similar) **only** to speed tests unless CI reliability requires it (see [doc_example_tests.inc.md](../../../docs/contributing/ci/test_examples/doc_example_tests.inc.md)) |

Do **not** copy an omni `omni_runner` + stage-config layout for a pure diffusion model without mirroring an existing diffusion test: the runner, params object, and response shape differ.

**2. Use the narrowest deterministic skeleton for the scenario**

*L1 unit / logic (CPU-first):*

```python
import pytest

pytestmark = [pytest.mark.core_model, pytest.mark.cpu]

def test_<scenario_name>():
    # Arrange
    # Act
    # Assert
    ...
```

*Offline multimodal e2e — **Omni** (representative):*

```python
@pytest.mark.core_model
@pytest.mark.omni
@hardware_test(...)
@pytest.mark.parametrize("omni_runner", test_params, indirect=True)
def test_<scenario>(omni_runner, omni_runner_handler) -> None:
    request_config = {"prompts": ..., "modalities": [...]}  # optional: images, videos, audios
    omni_runner_handler.send_request(request_config)
```

*Offline generative e2e — **Diffusion** (representative; adjust markers to match CI — often `diffusion` + `advanced_model` for heavier cases):*

```python
@pytest.mark.core_model  # or advanced_model — match existing tests in the same directory
@pytest.mark.diffusion
@hardware_test(...)
def test_<scenario>(run_level):
    m = Omni(model=...)
    outputs = m.generate(
        "<prompt>",
        OmniDiffusionSamplingParams(
            height=..., width=..., num_inference_steps=..., generator=...,
        ),
    )
    # Assert final_output_type, image/video fields, or use assert_diffusion_response via a diffusion handler pattern
```

*Online serving e2e (representative):*

```python
def test_<scenario>(omni_server, openai_client):
    # Drive the running server; avoid flaky timing; assert response shape / contract
    ...
```

*Documentation example tests:* follow the **Preferred Test Strategy** in [doc_example_tests.inc.md](../../../docs/contributing/ci/test_examples/doc_example_tests.inc.md): dynamic extraction for offline READMEs; explicit copied client code for online pages until extraction is justified; use the documented **naming**, **output directory** (page folder + case id), and **skipping** rules (e.g. Gradio-only scripts).

*Performance tests:* add or extend entries under `tests/perf/` (and JSON configs where the project uses them), with **explicit baselines** and the same marker/run-level pairing as the CI step that will execute them.

**3. Cross-cutting rules**

- Reuse existing fixtures for the chosen scenario; do not mix “online client” assumptions into offline `OmniRunner` tests without a clear reason.
- Avoid external network dependency in assertions unless the scenario is explicitly “online serving” or doc examples that require a model hub (then align with CI secrets/cache).
- Keep **one test function = one intent** (one modality combo or one doc snippet id).

#### Omni Test Writing Guidance (L1-L4 Layering)

When the goal is a general Omni/multimodal test case, prioritize mapping the test to the correct purpose, directory, and resource assumptions aligned with the layers (see [`CI_5levels.md`](https://raw.githubusercontent.com/vllm-project/vllm-omni/main/docs/contributing/ci/CI_5levels.md)):

- **L1**: Unit/logic validation. Prefer CPU-friendly tests that cover input validation, branches, and exception paths (typically `tests/<component>/test_*.py`).
- **L2**: Basic e2e (online/offline basic scenarios). Prefer dummy/lightweight models to validate the end-to-end request-to-output-structure/streaming chain (typically `tests/e2e/online_serving/` and `tests/e2e/offline_inference/`).
- **L3/L4**: Important integration, performance, and accuracy validation. L4 emphasizes “full functional scenarios + performance/stress + runnable doc examples” (typically `*_expansion.py` plus related expansion cases).

Also keep markers consistent with the run level: use `core_model` for L1/L2 and `advanced_model` for L3/L4, and pair with `--run-level` to select the intended CI strategy.

#### Diffusion Test Writing Guidance (L4 Coverage Combinations)

When the task involves diffusion models/features, organize L4 test cases following [`#1832`](https://github.com/vllm-project/vllm-omni/issues/1832): combine multiple diffusion features into as few test cases as possible to fit limited CI GPU resources.

Implementation strategy:

1. If “full L4 is too heavy”: first provide a **reduced local validation case in L1/L2** (so the key assertion and the contract fix point are covered deterministically).
2. Then provide **CI/nightly-ready L3/L4 high-marked cases** (e.g. `advanced_model`) to broaden coverage under resource constraints.

### Step 5: Wire Buildkite (when CI must run the new test)

If the test is not already collected by an existing pipeline command (for example, L1 tests marked `core_model and cpu` are already covered by the **Simple Unit Test** step in ready/merge), update the appropriate pipeline under `.buildkite/`:

| Test level | Edit this file | Typical trigger / intent |
|------------|----------------|---------------------------|
| **L1** and **L2** | [`.buildkite/test-ready.yml`](../../../.buildkite/test-ready.yml) | PR **ready** label; L1 CPU + L2 GPU/basic e2e |
| **L3** | [`.buildkite/test-merge.yml`](../../../.buildkite/test-merge.yml) | Post-merge; deeper `advanced_model` integration |
| **L4** | [`.buildkite/test-nightly.yml`](../../../.buildkite/test-nightly.yml) | Nightly / heavy / expansion-style jobs |

Guidelines when editing YAML:

- **Match markers and `--run-level`** to the test: L1/L2 steps in `test-ready.yml` usually use `core_model` (and `cpu` vs `not cpu` / file paths as in existing steps); L3/L4 in `test-merge.yml` / `test-nightly.yml` typically use `advanced_model` and `--run-level advanced_model` where applicable.
- **Reuse or extend an existing step** when the new test shares the same marker expression, queue, and timeout; otherwise add a new `steps:` entry with the correct `agents.queue`, `timeout_in_minutes`, and docker/kubernetes plugin blocks consistent with neighboring jobs.
- **Platform forks** (e.g. AMD-ready / AMD-merge) live alongside these files; apply the same level → file mapping for those pipelines when the test is platform-specific.

#### L3 / L4: validating Buildkite from a feature branch (root `pipeline.yml`)

Production behavior is driven by [`.buildkite/pipeline.yml`](../../../.buildkite/pipeline.yml): it builds the CI image, then uploads **L2** (`test-ready.yml` on non-`main`), **L3** (`test-merge.yml` when `build.branch == "main"`), and **L4** (`test-nightly.yml` when `build.env("NIGHTLY") == "1"`).

When you add or debug **L3** or **L4** tests and need those child pipelines to run **off `main`** or **without** `NIGHTLY=1`, apply **temporary** edits (revert before merge):

1. **Point the upload at the right file (optional shortcut)**  
   In the **Upload Ready Pipeline** step, the command is `buildkite-agent pipeline upload .buildkite/test-ready.yml`. For a one-off run you may change that path to `.buildkite/test-merge.yml` (L3) or `.buildkite/test-nightly.yml` (L4), and adjust the step’s `if:` so it does not conflict with the other upload steps (avoid double-uploading unless intentional).

2. **L3 — merge pipeline**  
   The gate `if: build.branch == "main"` lives on the **Upload Merge Pipeline** step in `pipeline.yml` (not inside `test-merge.yml`). **Comment out that `if` line** so `test-merge.yml` is uploaded on your feature branch. Alternatively rely on step (1) instead of the dedicated merge upload step.

3. **L4 — nightly pipeline**  
   **Comment out** `if: build.env("NIGHTLY") == "1"` on the **Upload Nightly Pipeline** step in `pipeline.yml` so the nightly definition is uploaded without setting the env var.  
   Child steps in [`test-nightly.yml`](../../../.buildkite/test-nightly.yml) often repeat `if: build.env("NIGHTLY") == "1"`; **comment out those lines on the steps you need to run**, otherwise they will still be skipped after upload.

### Step 6: Run Tests

Pick one command path:

- **Quick local regression (preferred first)**: single file or `file.py::test_name`
- **CI-like level run**: marker expression + `--run-level`

Full templates live in [references/test-routing.md](references/test-routing.md). **After authoring tests, always emit concrete commands** (see **Output Format**).

**Typical copy-paste examples** (run from repo `tests/` directory; requires matching vLLM/vllm-omni install and hardware):

| Area | Example |
|------|---------|
| **Omni offline L2** (GPU, `core_model`) | `pytest -s -v e2e/offline_inference/test_qwen2_5_omni.py -m "core_model and not cpu" --run-level=core_model` |
| **Omni offline — single test** | `pytest -s -v e2e/offline_inference/test_qwen2_5_omni.py::test_text_to_text -m "core_model and not cpu" --run-level=core_model` |
| **Omni online / diffusion L4 expansion** (nightly-style, H100) | `pytest -s -v e2e/online_serving/test_qwen_image_expansion.py -m "advanced_model and diffusion and H100" --run-level=advanced_model` |
| **L1 CPU** | `pytest -s -v -m "core_model and cpu"` |

**Prerequisites to mention when relevant**: GPU model (e.g. L4 vs H100), `HF_HOME` / token for hub weights, module-level `skipif` (NPU/XPU-only gaps), and whether CI already collects the path (e.g. `test_*_expansion.py` glob in `test-nightly.yml`).

### Step 7: Validate Result Quality

Before finishing:

- Is the new assertion directly tied to the bug/feature contract?
- Is the test deterministic (no fragile timing/network coupling)?
- Is runtime appropriate for the selected level?
- Are markers and `--run-level` consistent?

## Output Format

When completing a request, return:

1. **Test plan** (level, markers, file target, and **module basename** `test_{slug}.py` / `test_{slug}_expansion.py` for L2–L4 model e2e)
2. **Generated/updated test file(s)**
3. **Buildkite change** (if any: which `.buildkite/*.yml` and what was added or why existing steps already cover the test — e.g. nightly `test_*_expansion.py` may need **no** YAML edit)
4. **Run commands (required)** — always include, in fenced `bash` blocks:
   - **Local — whole file**: `cd tests` then `pytest -s -v <path> …`
   - **Local — single test** (optional but preferred when the change is one function): `pytest -s -v path::test_func …`
   - **CI-like** (when not L1 CPU): the same **marker + `--run-level`** pairing the level uses (see [references/test-routing.md](references/test-routing.md) and **Step 6** table above)
   - **Prerequisites** (one line): e.g. “需要 CUDA L4 + 已拉取权重”“需要 H100 + `HF_TOKEN`”“本机未装 vllm 时仅校验语法”
5. **Result summary** (pass/fail if you executed tests; if not executed, state that explicitly and what the user should run)

## Additional Resources

- Marker and command routing: [references/test-routing.md](references/test-routing.md)
- CI pipelines: `.buildkite/test-ready.yml` (L1/L2), `test-merge.yml` (L3), `test-nightly.yml` (L4)
- L4 documentation example tests (naming, extraction vs copied scripts, output dirs, skips): [docs/contributing/ci/test_examples/doc_example_tests.inc.md](../../../docs/contributing/ci/test_examples/doc_example_tests.inc.md) — see also [PR #1910](https://github.com/vllm-project/vllm-omni/pull/1910)
- Bug regression coverage rubric: [../vllm-omni-review/references/bug-test-coverage.md](../vllm-omni-review/references/bug-test-coverage.md)
