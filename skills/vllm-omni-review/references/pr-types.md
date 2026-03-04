# PR Type Review Checklists

## Bugfix

- [ ] Regression test to prevent recurrence?
- [ ] Root cause understood and documented?
- [ ] Similar bugs elsewhere in codebase?
- [ ] Fix addresses root cause, not just symptoms?
- [ ] Error handling improved, not just hidden?

**Common Issues:**
- Fixing symptom without understanding root cause
- Missing regression test
- Not checking for similar patterns elsewhere

---

## Feature

- [ ] Comprehensive test coverage (happy path + edge cases + errors)?
- [ ] User-facing documentation updated?
- [ ] Breaking changes documented?
- [ ] Performance impact measured?
- [ ] Backward compatibility preserved?

**Common Issues:**
- Missing tests for error paths
- Undocumented breaking changes
- No performance benchmarks

---

## Refactor

- [ ] Behavior preserved (no functional changes)?
- [ ] Existing tests still pass?
- [ ] No performance regressions?
- [ ] Clear improvement in code quality?
- [ ] No scope creep (unrelated changes)?

**Common Issues:**
- Accidental behavior changes
- Mixing refactoring with feature work
- Tests not updated to match new structure

---

## Model

- [ ] Model correctness validated (outputs match expected)?
- [ ] Memory/hardware requirements documented?
- [ ] Distributed execution support (TP/PP)?
- [ ] Works with quantization/cudagraph/streaming?
- [ ] Stage config YAML provided?

**Common Issues:**
- Missing stage configuration
- No memory requirements documented
- Untested with tensor parallelism

---

## Performance

- [ ] Benchmark results on realistic workloads?
- [ ] Quality preservation (no accuracy degradation)?
- [ ] Memory usage changes measured?
- [ ] Scalability with model/batch size?
- [ ] Before/after comparison data?

**Common Issues:**
- Claims without measurements
- Quality degradation not tested
- Only tested on small scale

---

## Distributed

- [ ] Correctness in TP/PP/EP/DP modes?
- [ ] Communication overhead measured?
- [ ] Memory distribution across devices?
- [ ] Fault tolerance and error handling?
- [ ] Connector changes (Shm/Zmq) tested?

**Common Issues:**
- Only tested single-GPU
- Memory leaks in connectors
- Race conditions in worker coordination

---

## Quantization

- [ ] Memory measurements before/after?
- [ ] Quality trade-offs documented (accuracy, perceptual)?
- [ ] Compatibility with different model types?
- [ ] Fallback when quantization not supported?
- [ ] Config validation for unsupported combinations?

**Common Issues:**
- Quality degradation not measured
- No fallback for unsupported models
- Missing config validation

---

## Platform (NPU/XPU/ROCm)

- [ ] Platform-specific correctness?
- [ ] Fallback for unsupported features?
- [ ] Performance on target platform?
- [ ] Clear documentation of requirements?
- [ ] CI coverage for platform?

**Common Issues:**
- Platform-specific code breaks CUDA
- Missing fallback implementations
- Undocumented platform requirements

---

## API

- [ ] Backward compatibility preserved?
- [ ] Breaking changes clearly marked?
- [ ] Migration path for deprecated APIs?
- [ ] OpenAI-compatible endpoints maintained?
- [ ] Input validation added for new parameters?

**Common Issues:**
- Breaking changes without deprecation
- Non-OpenAI-compatible behavior
- Missing input validation

---

## Documentation

- [ ] Technical content accurate?
- [ ] Code examples work (copy-paste test)?
- [ ] Clear explanations for target audience?
- [ ] Links to related docs?
- [ ] No orphaned/removed references?

**Common Issues:**
- Code examples don't run
- Outdated API references
- Missing context for new users

---

## CI

- [ ] Test coverage for new code paths?
- [ ] No flaky tests introduced?
- [ ] Build reproducibility maintained?
- [ ] Clear failure messages?
- [ ] Reasonable execution time?

**Common Issues:**
- Flaky async tests
- Missing timeout handling
- Unclear failure messages
