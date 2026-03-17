---
name: vllm-omni-review
description: Review PRs on vllm-project/vllm-omni by routing to the right domain skills, checking critical evidence, and focusing comments on blocking issues. Use when reviewing pull requests, triaging review depth, or checking tests, benchmarks, and breaking changes in vllm-omni.
---

# vLLM-Omni PR Review

## Overview

Use this skill as a router for `vllm-project/vllm-omni` pull request reviews. Keep the default context small, load only the references that match the diff, and prioritize high-confidence findings over coverage theater.

Default review priorities:

1. Missing regression or integration tests
2. Claims without evidence
3. Security or reliability regressions
4. Breaking API or behavior changes
5. Architecture flaws in critical paths

## Core Workflow

### Step 0: Verify Review Gates First

Check mergeability and required checks before reading the diff in depth. If DCO, pre-commit, or mergeability is failing, stop and ask the author to fix the gate before doing a full review.

For concrete gate commands, review submission commands, and comment style, see [references/review-execution.md](references/review-execution.md).

### Step 1: Gather Minimal Context

Fetch:

- PR metadata and changed files
- The diff
- Linked issues for `[Bugfix]` and `[Feature]` PRs
- Related PRs only when conventions or prior decisions are unclear

Do not fetch broad extra context unless the diff or linked issue leaves real ambiguity.

### Step 2: Route to the Right Skill

Use the title prefix and changed directories to decide whether a domain skill is required.

| Signal | Action |
|--------|--------|
| `[Model]`, `[New Model]`, `[Image]`, `[ImageGen]`, `[Video]`, `[VideoGen]`, `[Diffusion]` | → [Diffusion Model PR Review](#diffusion-model-pr-review) |
| `[Audio]`, `[TTS]` | Use `vllm-omni-audio-tts` |
| `[Multimodal]` | Use `vllm-omni-multimodal` |
| `[Distributed]` | Use `vllm-omni-distributed` |
| `[Quantization]` | Use `vllm-omni-quantization` |
| `[Performance]` | Use `vllm-omni-perf` |
| `[Hardware]` or backend-specific code | Use `vllm-omni-hardware` |
| `[API]` or `vllm_omni/entrypoints/` changes | Use `vllm-omni-api` |
| `[CI]` | Use `vllm-omni-cicd` |

If the PR spans multiple specialized areas, choose the primary skill first and load a secondary skill only when the diff crosses a real subsystem boundary.

For multi-skill routing, hardware detection, and delegation rules, see [references/review-routing.md](references/review-routing.md).

### Step 3: Load Only the Relevant Review Reference

Load targeted references based on the diff:

| Diff Area | Load |
|-----------|------|
| `vllm_omni/engine/`, `vllm_omni/stages/`, `vllm_omni/connectors/`, `vllm_omni/diffusion/` | [references/pitfalls.md](references/pitfalls.md) |
| Async, distributed coordination, validation, connector behavior | [references/code-patterns.md](references/code-patterns.md) |
| Scheduler, stage boundaries, execution model, critical paths | [references/architecture.md](references/architecture.md) |

Avoid loading all three by default. Start with the one that matches the changed files or the most likely failure mode.

### Step 4: Run the Critical Checks

Apply these checks to every substantive PR:

- Is there a regression test for bug fixes?
- Do new features include tests and docs where needed?
- Are performance claims backed by benchmark data?
- Are API or config changes validated early and documented?
- Does the change preserve cleanup, state transitions, and distributed invariants?

If a finding is speculative, do not comment. Fetch a bit more code context first or drop it.

### Step 5: Keep the Output Tight

Comment only on blocking or high-value issues. Combine related problems into a single comment when possible, and avoid praise-only or low-signal remarks. Small documentation-only PRs often need no inline comments.

Use the review body to summarize:

- what you validated
- what still lacks evidence
- what must change before approval

For comment budget, phrasing, examples, and posting mechanics, see [references/review-execution.md](references/review-execution.md).

## Review Heuristics

- Treat missing tests as the default highest-priority issue.
- Demand measurements for performance, memory, or quality claims.
- Be suspicious of silent fallbacks, swallowed exceptions, and device-specific assumptions.
- Review critical paths first: engine, model executor, connectors, stages, and API entrypoints.
- Skip nits, style comments, and linter-covered feedback unless they hide a correctness issue.

## When to Fetch More Context

Fetch more code or issue context when:

- the diff snippet hides lifecycle or cleanup behavior
- a config key or API field is introduced without nearby validation
- a benchmark or quality claim references unseen measurement code
- the PR appears to rely on prior design discussion

Keep additional fetches narrow and tied to a specific uncertainty.

## Diffusion Model PR Review

> **Invoked when PR prefix is `[Model]`, `[New Model]`, `[Image]`, `[ImageGen]`, `[Video]`, `[VideoGen]`, or `[Diffusion]`.**

All four dimensions below must pass before approving. Work through them in priority order.

### Priority Order

1. **PR body evidence** — missing samples/metrics block the entire review
2. **Missing inference mode** — model must work offline and online
3. **Missing acceleration feature** — required for all new diffusion models
4. **Missing memory optimization** — required for all new diffusion models
5. **Missing documentation** — tables and examples must be updated
6. **Missing e2e test** — required for merge gate
7. **Missing offline inference test** — recommended; required only when no e2e test is present
8. **Combined feature test** — required when two or more acceleration/memory features are implemented

---

### Dimension 1: PR Body Completeness

#### Table A — Required (block merge if missing)

| Item | What to Check | Missing → Action |
|------|---------------|------------------|
| **vLLM-Omni generation script** | Runnable Python or bash snippet using `Omni` / `vllm serve` that produces output | Request script |
| **Generated sample outputs** | At least 1 image / video / audio sample attached or linked | Request sample |
| **vLLM-Omni e2e latency** | Wall-clock time from request to output, with GPU model, count, resolution, steps | Request measurement |
| **vLLM-Omni VRAM usage** | Peak VRAM in GB during generation, with resolution / steps | Request measurement |

#### Table B — Strongly Recommended (comment if absent, do not block)

| Item | Why It Matters |
|------|---------------|
| **diffusers generation script** | Reproducible baseline for quality and speed comparison |
| **diffusers sample outputs** | Side-by-side quality comparison demonstrates parity |
| **diffusers e2e latency** | Quantifies vLLM-Omni speedup relative to reference |
| **diffusers VRAM usage** | Quantifies memory reduction or overhead |

**Comment when Table A items are missing:**

```
🔴 **PR Body Incomplete — Required Evidence Missing**

The following items are required before this PR can be reviewed:

- [ ] vLLM-Omni generation script (offline `Omni` or online `vllm serve`)
- [ ] Generated sample output (image / video / audio)
- [ ] vLLM-Omni e2e latency (hardware: GPU model, count; resolution; steps)
- [ ] vLLM-Omni peak VRAM usage (GB)

Please update the PR description with this information.
```

**Comment when Table B items are absent:**

```
💡 **Recommended: diffusers Baseline Comparison**

Adding a diffusers comparison would strengthen this PR:

- diffusers generation script (same prompt, same resolution/steps)
- diffusers sample output
- diffusers e2e latency vs vLLM-Omni latency
- diffusers peak VRAM vs vLLM-Omni VRAM
```

---

### Dimension 2: Code Review

```bash
# Detect leftover diffusers mixins
gh pr diff <pr_number> --repo vllm-project/vllm-omni \
  | grep -E '^\+.*DiffusionPipelineMixin|SchedulerMixin|ConfigMixin'

# Check acceleration features
gh pr diff <pr_number> --repo vllm-project/vllm-omni \
  | grep -iE 'sequence_parallel|cfg_parallel|vae_patch_parallel|tensor_parallel|teacache|cache_dit'

# Check memory optimizations
gh pr diff <pr_number> --repo vllm-project/vllm-omni \
  | grep -iE 'cpu_offload|offload_to_cpu|quantization|int8|fp8|bitsandbytes|vae_tiling'
```

#### 2.1 Inference Mode Coverage (both required)

| Check | Pass Condition | Flag |
|-------|---------------|------|
| **Offline inference** | `Omni` / `OmniLLM` integration exists; model can be instantiated and called | Missing offline path |
| **Online serving** | `vllm serve` or `AsyncOmni` handles the model; API routes return correct responses | Missing online path |

```
🔴 Missing <offline inference / online serving> support. The model must work in both
Omni (offline) and vllm serve / AsyncOmni (online) modes before merging.
```

#### 2.2 Diffusers Mixin Cleanup (required)

Flag if any diffusers mixin is still present in `+` lines:

```
🔴 Leftover diffusers mixin detected: `<MixinName>` in `<file>:<line>`.
Remove diffusers mixins and use vLLM-Omni's native abstractions instead.
```

#### 2.3 Acceleration Features (at least one required)

| Feature | Patterns to Detect |
|---------|-------------------|
| Sequence Parallel | `sequence_parallel`, `sp_group`, `ring_attn` |
| CFG Parallel | `cfg_parallel`, `cfg_group`, `ClassifierFreeGuidance` with parallel context |
| VAE Patch Parallel | `vae_patch_parallel`, `patch_parallel` |
| Tensor Parallel | `tensor_parallel`, `tp_group`, `ColumnParallelLinear` |
| TeaCache / Step Cache | `teacache`, `cache_dit`, `cache_interval` |

```
🔴 No acceleration feature detected. The model must support at least one of:
sequence parallel, CFG parallel, VAE patch parallel, tensor parallel, or step caching (TeaCache).
```

#### 2.4 Memory Optimization Features (at least one required)

| Feature | Patterns to Detect |
|---------|-------------------|
| CPU Offload | `cpu_offload`, `offload_to_cpu`, `--cpu-offload-gb` |
| Quantization | `quantization`, `int8`, `fp8`, `bnb`, `bitsandbytes`, `load_in_8bit` |
| VAE Tiling | `vae_tiling`, `tile_size` |

```
🔴 No memory optimization feature detected. The model must support at least one of:
CPU offload (`--cpu-offload-gb`), quantization (int8/fp8/bnb), or VAE tiling.
```

---

### Dimension 3: Documentation

```bash
gh pr view <pr_number> --repo vllm-project/vllm-omni \
  --json files --jq '.files[].path' | grep -E 'docs/|\.md$'
```

| Doc Artifact | Required | Check |
|-------------|----------|-------|
| **Model support table** | Yes | Row added: model name, architecture, HF model ID, modality, min VRAM |
| **Feature support table** | Yes | Row showing which acceleration and memory features are supported |
| **Usage example doc** | Yes | Runnable offline + online example for the new model |
| **Feature compatibility table** | Optional | If multiple features: matrix showing validated combinations |

```
🔴 Documentation incomplete:
- [ ] Model support table not updated (docs/models/supported_models.md or equivalent)
- [ ] Feature support table not updated
- [ ] Usage example doc missing or not updated for <ModelName>
```

---

### Dimension 4: Test Coverage

```bash
gh pr view <pr_number> --repo vllm-project/vllm-omni \
  --json files --jq '.files[].path' | grep -E '^tests/'
```

| Test Type | Location | Required | What to Verify |
|-----------|----------|----------|----------------|
| **e2e online serving test** | `tests/e2e/online_serving/` | Yes | Start server, send request, assert output shape / non-null |
| **Offline inference test** | `tests/` or `tests/models/` | No (if e2e test exists) | Instantiate `Omni`, call `.generate()`, assert output |
| **Acceleration / memory feature test** | Alongside above | Recommended | Enable each supported feature, verify output and speed |
| **Combined feature test** | Alongside above | Required if 2+ features | Enable multiple features together, assert output + VRAM + latency |

Flag if e2e online serving test is missing:

```
🔴 Missing e2e online serving test in `tests/e2e/online_serving/`.
Please add a test that:
1. Starts `vllm serve <model> --omni`
2. Sends a generation request via the API
3. Asserts the response contains a valid image / video / audio output
```

Flag if combined feature test is missing when 2+ features are implemented:

```
⚠️ Multiple features are implemented (e.g., <feature A> + <feature B>) but no combined
feature test is present. Please add a test (or extend the e2e test) that enables both
features together and asserts output validity + reports latency + VRAM.
```

### Quick Red Flags (post blocking comment immediately)

| Red Flag | Severity |
|----------|----------|
| No generation script / sample / latency / VRAM in PR body | 🔴 Blocking |
| Online or offline inference not implemented | 🔴 Blocking |
| Diffusers mixin still in production code | 🔴 Blocking |
| No acceleration feature | 🔴 Blocking |
| No memory optimization | 🔴 Blocking |
| No e2e online serving test | 🔴 Blocking |
| Model or feature support table not updated | 🔴 Blocking |
| No usage example doc | 🔴 Blocking |
| No diffusers baseline comparison | 💡 Recommended |
| No combined feature test (2+ features) | ⚠️ Conditional |

> See [Diffusion Checklist](references/diffusion-checklist.md) and [Diffusion PR Requirements](references/diffusion-pr-requirements.md) for full per-item details.

---

## References

- [Review Routing](references/review-routing.md) - prefix mapping, multi-skill routing, hardware detection, delegation
- [Review Execution](references/review-execution.md) - gate checks, commands, comment budget, review phrasing
- [Common Pitfalls](references/pitfalls.md) - MRO issues, connector state, async differences, validation gaps
- [Architecture](references/architecture.md) - system overview and critical paths
- [Code Patterns](references/code-patterns.md) - async, distributed, cache, validation, and error handling patterns
