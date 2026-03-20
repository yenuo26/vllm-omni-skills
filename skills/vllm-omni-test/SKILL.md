---
name: vllm-omni-test
description: Generate and run tests for vllm-project/vllm-omni with CI-aligned levels and markers. Use when creating regression tests, adding L1-L4 coverage, selecting pytest markers, or validating fixes from issues/PRs.
---

# vLLM-Omni Test Generator & Runner

## Purpose

Use this skill to generate minimal, stable test cases and run them with the correct marker/level strategy for `vllm-project/vllm-omni`.

Default priorities:

1. Reproducible regression coverage for bug fixes
2. Correct test level and marker selection
3. Low flake, low dependency tests first
4. CI-compatible run commands

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

### Step 4: Generate Test Case Skeleton

Use the narrowest deterministic skeleton first:

```python
import pytest

pytestmark = [pytest.mark.core_model, pytest.mark.cpu]

def test_<scenario_name>():
    # Arrange
    # Act
    # Assert
    ...
```

For API/e2e tests:

- Reuse existing fixtures (`omni_server`, `openai_client`) when available.
- Avoid external network dependency in assertions.
- Keep one scenario = one clear intent.

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

### Step 5: Run Tests

Pick one command path:

- **Quick local regression (preferred first)**: single file/case
- **CI-like level run**: marker + `--run-level`

Command templates are in [references/test-routing.md](references/test-routing.md).

### Step 6: Validate Result Quality

Before finishing:

- Is the new assertion directly tied to the bug/feature contract?
- Is the test deterministic (no fragile timing/network coupling)?
- Is runtime appropriate for the selected level?
- Are markers and `--run-level` consistent?

## Output Format

When completing a request, return:

1. **Test plan** (level, markers, file target)
2. **Generated/updated test file(s)**
3. **Run command(s) used**
4. **Result summary** (pass/fail, key evidence, next action)

## Additional Resources

- Marker and command routing: [references/test-routing.md](references/test-routing.md)
- Bug regression coverage rubric: [../vllm-omni-review/references/bug-test-coverage.md](../vllm-omni-review/references/bug-test-coverage.md)
