# Test Routing Reference

Use this reference to map testing goals to levels, markers, and runnable commands.

## Model-centric e2e filename convention (L2–L4)

When generating a **new** test module tied to a **specific model** under `tests/e2e/`:

| Level | Pattern |
|-------|---------|
| **L2**, **L3** | `test_{lowercase_model_slug}.py` |
| **L4** | `test_{lowercase_model_slug}_expansion.py` |

Normalize the slug from the **repo segment only** (after `Org/`), lowercase, replace `.`, `-`, and spaces with `_`; **do not** prefix the org (avoid `qwen_qwen2_5_omni_7b`). Drop trailing size tokens like `7b` when one file per model line is enough — e.g. `Qwen/Qwen2.5-Omni-7B` → `test_qwen2_5_omni.py` / `test_qwen2_5_omni_expansion.py`. L1 modules elsewhere are not required to follow this.

## Level and Marker Mapping

| Goal | Suggested Level | Marker baseline | Typical location |
|------|------------------|-----------------|------------------|
| Unit logic, regression on pure code path | L1 | `core_model and cpu` | `tests/<component>/test_*.py` |
| Basic integration/e2e | L2 | `core_model` (+ hardware marker if needed) | `tests/e2e/...` |
| Advanced integration/perf/accuracy | L3 | `advanced_model` | `tests/e2e/...` |
| Full function/perf/nightly | L4 | `advanced_model` (+ perf markers) | `tests/e2e/...`, perf scripts |

## Marker Selection Rules

1. Start with one level marker:
   - `core_model` for L1/L2
   - `advanced_model` for L3/L4
2. Add domain marker when relevant:
   - `diffusion`, `omni`, `cache`, `parallel`
3. Add hardware marker explicitly:
   - `cpu`, `cuda`, `rocm`, `npu`, etc.
4. For multi-card tests, use `@hardware_test(...)` to auto-apply distributed markers.

## Command Templates

### Quick local checks

```bash
cd tests
pytest -s -v test_xxxx.py
```

### L1

```bash
cd tests
pytest -s -v -m "core_model and cpu"
```

### L2

```bash
cd tests
pytest -s -v -m "core_model and not cpu" --run-level=core_model
```

### L3/L4 baseline

```bash
cd tests
pytest -s -v -m "advanced_model" --run-level=advanced_model
```

### Platform-targeted examples

```bash
cd tests
pytest -s -v -m "core_model and distributed_cuda and L4" --run-level=core_model
```

### Concrete e2e paths (common in-tree)

Paths are relative to `tests/` after `cd tests`.

| Scenario | Example command |
|----------|------------------|
| Omni offline L2 (Qwen2.5-Omni, GPU) | `pytest -s -v e2e/offline_inference/test_qwen2_5_omni.py -m "core_model and not cpu" --run-level=core_model` |
| Omni offline L2 — one test | `pytest -s -v e2e/offline_inference/test_qwen2_5_omni.py::test_text_to_text -m "core_model and not cpu" --run-level=core_model` |
| Omni offline L2 (Qwen3.5-9B, CUDA/ROCm) | `pytest -s -v e2e/offline_inference/test_qwen3_5_9b.py -m "core_model and not cpu" --run-level=core_model` |
| Diffusion offline (incl. qwen-image random / Z-Image) | `pytest -s -v e2e/offline_inference/test_t2i_model.py -m "core_model and not cpu" --run-level=core_model` (see file for `run_level` skips) |
| Diffusion L4 online expansion (Qwen-Image T2I, H100) | `pytest -s -v e2e/online_serving/test_qwen_image_expansion.py -m "advanced_model and diffusion and H100" --run-level=advanced_model` |
| Diffusion L4 online expansion (Qwen-Image-Edit) | `pytest -s -v e2e/online_serving/test_qwen_image_edit_expansion.py -m "advanced_model and diffusion and H100" --run-level=advanced_model` |

### Agent / author completion checklist

When adding or modifying tests, do not stop at “where the file lives” — also deliver:

1. **Local**: `cd tests` + `pytest -s -v <path>` (and `path::test_func` when a single case is enough).
2. **CI-like**: marker string + `--run-level` matching the test’s level (`core_model` vs `advanced_model`).
3. **Prerequisites**: GPU tier, HF cache/token, and any module `skipif` / platform-only YAML.

## Buildkite pipeline mapping

After adding or changing tests, update the pipeline that actually executes them (unless an existing step already collects them via `-m` / file path):

| Level | Repo file |
|-------|-----------|
| L1, L2 | `.buildkite/test-ready.yml` |
| L3 | `.buildkite/test-merge.yml` |
| L4 | `.buildkite/test-nightly.yml` |

The root [`.buildkite/pipeline.yml`](../../../.buildkite/pipeline.yml) decides **which** child file is uploaded (`test-ready.yml` vs `test-merge.yml` vs `test-nightly.yml`) and under which `if` conditions. To run **L3** on a feature branch, comment out `if: build.branch == "main"` on the merge upload step (or temporarily point the ready-step `pipeline upload` at `test-merge.yml`). To run **L4** without `NIGHTLY=1`, comment out the nightly upload step’s `if: build.env("NIGHTLY") == "1"` and the same `if` on relevant steps inside `test-nightly.yml`. Revert such edits before merging. See comments at the top of `pipeline.yml` and **Step 5** in the vllm-omni-test skill.

Platform-specific pipelines (e.g. AMD) follow the same level → file pairing under `.buildkite/`.

## Diffusion RFC (#1832) Alignment Tips

For diffusion model coverage planning:

- Prioritize high-value feature combinations with minimal case count.
- Split into:
  - lightweight validation case(s) for quick checks
  - advanced/nightly case(s) for broader feature combinations
- If hardware is insufficient, provide an executable reduced case plus a deferred full CI/nightly plan.
