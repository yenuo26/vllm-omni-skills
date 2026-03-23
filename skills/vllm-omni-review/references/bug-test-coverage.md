# Bug Review and Missing Test Case Supplement

When a new bug issue is added or an associated bugfix PR is reviewed, determine whether regression coverage is missing for the bug, and provide minimal test case recommendations to be added alongside the fix.

## Inputs

| Input | Description |
|-------|-------------|
| **Bug issue description** | Title, body, and reproduction steps of the GitHub issue |
| **Issue link** | `https://github.com/vllm-project/vllm-omni/issues/<number>` |
| **Associated PR** | PR link referenced in the issue |
| **Affected code path** | Files and functions modified by the fix |
| **Existing test coverage** | Unit/e2e/perf tests under `tests/` that cover the path |

## Procedure

### Step 1: Classify the Bug

| Type | Definition | Examples |
|------|------------|----------|
| **Code issue** | Logic errors, contract violations, implementation defects | Division by zero, null pointer, wrong branch |
| **Uncovered edge case** | Main path tested, boundary/exception paths untested | Empty input, oversized input, invalid combinations |
| **Environment-specific** | Depends on hardware/OS/driver/library version | CUDA version, NPU compatibility, OOM |
| **Flake** | Intermittent failures, hard to reproduce consistently | Race conditions, timing-sensitive, resource contention |
| **Non-code/config** | One-off environment drift, external services, human error | Misconfiguration, network outage, data corruption |

### Step 2: Map to Existing Coverage

Check whether the following locations already have coverage:

- **Unit tests**: Directories under `tests/` except `tests/e2e/` and `tests/perf/`
- **Integration/E2E**: `tests/e2e/`
- **Performance**: `tests/perf/`, benchmark scripts
- **Model/path**: Tests related to the affected model or pipeline

**Output**: List any relevant existing test files and coverage scope.

### Step 3: Decide Whether New Tests Are Needed

| Conclusion | Applicable scenarios |
|------------|----------------------|
| **required** | Bug affects user-visible behavior; fix addresses logic/contract errors; bug is stably reproducible and should theoretically have been caught by tests |
| **recommended** | Low risk or heavily environment-dependent, but adding a lightweight regression case reduces likelihood of recurrence |
| **not_needed** | One-off environment drift, anomalous data, external service failure; or coverage exists with no product/code path gap |

### Step 4: Design Minimal Test Plan (when conclusion is required or recommended)

Prefer the **narrowest, most stable, and deterministically reproducible** regression test; add broader integration coverage only when necessary.

- **Level**: L1, L2, L3, L4
- **Scenario name**: Brief description of test intent
- **Preconditions**: Required fixtures, mocks, environment
- **Core assertions**: Input, trigger action, expected output/state

### Step 5: Specify Missing Assertions

Elements required to demonstrate that the bug is fixed and will not recur:

- **Input**: Minimal input that triggers the bug
- **Pre-state**: Necessary context or configuration
- **Trigger action**: Call or execution step
- **Expected output/state**: Success indicator or error that must not occur

### Step 6: Assess CI Impact

| Dimension | Description |
|-----------|-------------|
| **Runtime cost** | Estimated execution time, suitability for main CI |
| **Flake risk** | Dependence on timing, external services, non-deterministic behavior |
| **Fixture size** | Need for large models/files, mockability |
| **External dependencies** | Need for GPU, specific hardware, network |
| **Test level** | Recommended placement in L1/L2/L3/L4 |

## Output Template

```markdown
## Coverage Conclusion

**required** / **recommended** / **not_needed** (select one)

## Rationale

[Explain why the current test suite missed this bug and identify the missing or insufficient coverage point]

## Minimal Test Plan (only when required/recommended)

### Suggested Test Level
L1 / L2 / L3 / L4 (select one)

### Scenario Name and Intent
[Brief description]

### Key Preconditions and Core Assertions
- **Preconditions**: [...]
- **Input**: [...]
- **Trigger**: [...]
- **Expected**: [...]

### CI Impact
- Runtime: [...]
- Flake risk: [...]
- Fixture/dependencies: [...]
- Suggested level: [...]

---

(If conclusion is not_needed, explain which existing safeguard is sufficient, or why the issue is outside normal regression coverage scope)
```

## Output Constraints

1. **Conclusion must be explicit**: Output must state `required`, `recommended`, or `not_needed`.
2. **At least one candidate case**: If conclusion is `required` or `recommended`, provide at least one minimal candidate test case.
3. **Prefer narrow and stable**: Prioritize the narrowest, most stable, and deterministically reproducible regression test before considering broader test sets.
4. **Avoid flaky solutions**: Do not recommend tests that depend on flaky timing, manual verification, or external services unless no smaller, more reliable alternative exists.

## vLLM-Omni Test Level Reference

| Level | Description | Typical location |
|-------|-------------|------------------|
| **L1** | Unit tests, no external dependencies, millisecond runtime | Directories under `tests/` except `tests/e2e/` and `tests/perf/` |
| **L2, L3** | Integration tests | `tests/e2e` |
| **L4** | Performance/full validation | `tests/perf/`, `tests/e2e` |

## Examples

### Example 1: required

**Bug**: When layer-wise offload and cache-dit are both enabled, `inspect.signature` fails because `_WrappedForward` has no signature.

**Conclusion**: **required**

**Rationale**: `HookRegistry` in `vllm_omni/diffusion/hooks/base.py` does not preserve `__signature__` when wrapping forward; cache-dit's block adapter depends on `inspect.signature()`. This combination path was previously untested.

**Minimal test plan**:
- **Level**: L1
- **Scenario**: `test_wrapped_forward_preserves_signature`
- **Preconditions**: Create mock with `nn.Module`, register hook
- **Assertion**: `inspect.signature(module.forward)` matches original forward signature
- **CI impact**: Lightweight, no GPU, suitable for L1

### Example 2: recommended

**Bug**: A model OOMs at a specific batch size.

**Conclusion**: **recommended**

**Rationale**: Heavily dependent on GPU memory and model size, hard to reproduce stably, but a lightweight regression can reduce the chance of similar regressions from future changes.

**Minimal test plan**:
- **Level**: L2 or L3
- **Scenario**: Verify batch logic with mock or small model, or optional OOM regression on a small GPU
- **CI impact**: May require GPU, can run at L3 or conditionally

### Example 3: not_needed

**Bug**: A CI run failed due to transient network failure when downloading a model.

**Conclusion**: **not_needed**

**Rationale**: One-off external failure, not a product/code path gap. Existing retry or error handling, if adequate, is sufficient; no new regression test is needed.
