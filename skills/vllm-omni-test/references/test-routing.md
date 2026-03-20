# Test Routing Reference

Use this reference to map testing goals to levels, markers, and runnable commands.

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

## Diffusion RFC (#1832) Alignment Tips

For diffusion model coverage planning:

- Prioritize high-value feature combinations with minimal case count.
- Split into:
  - lightweight validation case(s) for quick checks
  - advanced/nightly case(s) for broader feature combinations
- If hardware is insufficient, provide an executable reduced case plus a deferred full CI/nightly plan.
