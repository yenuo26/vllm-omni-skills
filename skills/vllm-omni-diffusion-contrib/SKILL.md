---
name: vllm-omni-diffusion-contrib
description: Review PRs that add new diffusion models (image/video) to vLLM-Omni. Triggered by [Model], [New Model], [Image], [Video], or [Diffusion] PR prefixes. Checks PR body completeness, code correctness, acceleration/memory features, documentation updates, and e2e test coverage.
---

# vLLM-Omni Diffusion Model Contribution Review

## Overview

This skill reviews PRs that **integrate a new diffusion model** into vLLM-Omni. The review focuses on four dimensions: PR body evidence, code correctness, documentation, and test coverage. All four must pass before approving.

## When to Use This Skill

Invoke when a PR:
- Has prefix `[Model]`, `[New Model]`, `[Image]`, `[Video]`, `[Diffusion]`, or combination thereof
- Adds files under `vllm_omni/models/`, `vllm_omni/diffusion/`, or introduces a new model config YAML
- Claims to integrate a new DiT, text-to-image, text-to-video, or multi-stage AR+DiT model

---

## Review Workflow

### Step 0: Fetch PR Data

```bash
gh pr view <pr_number> --repo vllm-project/vllm-omni \
  --json title,body,author,state,files,closingIssuesReferences

gh pr diff <pr_number> --repo vllm-project/vllm-omni
```

Parse the PR body for the four required sections (see Dimension 1 below). Scan the diff for changed files to drive Dimensions 2–4.

---

### Dimension 1: PR Body Completeness

**Every diffusion model addition PR must include all items in Table A. Items in Table B are strongly recommended.**

#### Table A — Required (block merge if missing)

| Item | What to Check | Missing → Action |
|------|---------------|-----------------|
| **vLLM-Omni generation script** | Runnable Python or bash snippet using `Omni` / `vllm serve` that produces output | Request script |
| **Generated sample outputs** | At least 1 image / video / audio sample attached or linked | Request sample |
| **vLLM-Omni e2e latency** | Measured wall-clock time from request to output, with hardware spec (GPU model, count) | Request measurement |
| **vLLM-Omni VRAM usage** | Peak VRAM in GB during generation, with resolution / steps | Request measurement |

#### Table B — Strongly Recommended (comment if absent, do not block)

| Item | Why It Matters |
|------|---------------|
| **diffusers generation script** | Establishes a reproducible baseline for quality and speed comparison |
| **diffusers sample outputs** | Side-by-side quality comparison demonstrates parity |
| **diffusers e2e latency** | Quantifies vLLM-Omni speedup relative to reference implementation |
| **diffusers VRAM usage** | Quantifies memory reduction or overhead introduced by vLLM-Omni |

**Comment template when Table A items are missing:**

```
🔴 **PR Body Incomplete — Required Evidence Missing**

The following items are required before this PR can be reviewed:

- [ ] vLLM-Omni generation script (offline `Omni` or online `vllm serve`)
- [ ] Generated sample output (image / video / audio)
- [ ] vLLM-Omni e2e latency (hardware: GPU model, count; resolution; steps)
- [ ] vLLM-Omni peak VRAM usage (GB)

Please update the PR description with this information.
```

**Comment template when Table B items are absent:**

```
💡 **Recommended: diffusers Baseline Comparison**

Adding a diffusers comparison would strengthen this PR:

- diffusers generation script (same prompt, same resolution/steps)
- diffusers sample output
- diffusers e2e latency vs vLLM-Omni latency
- diffusers peak VRAM vs vLLM-Omni VRAM

This helps reviewers assess quality parity and performance gains.
```

---

### Dimension 2: Code Review

Scan the diff for the following. Use `gh pr diff` output; fetch additional file context when needed.

```bash
# Fetch surrounding context for a file
gh api repos/vllm-project/vllm-omni/contents/<path>?ref=<branch>
```

#### 2.1 Inference Mode Coverage

| Check | Pass Condition | Flag |
|-------|---------------|------|
| **Offline inference** | `Omni` / `OmniLLM` integration exists; model can be instantiated and called | Missing offline path |
| **Online serving** | `vllm serve` or `AsyncOmni` entrypoint handles the model; API routes return correct responses | Missing online path |

Flag if either mode lacks implementation:
```
🔴 Missing <offline inference / online serving> support. The model must work in both
`Omni` (offline) and `vllm serve` / `AsyncOmni` (online) modes before merging.
```

#### 2.2 Diffusers Mixin Cleanup

Diffusers mixins (`DiffusionPipelineMixin`, `SchedulerMixin`, etc.) are only needed during initial porting. Merged models must use vLLM-Omni's native abstractions.

```bash
# Detect leftover diffusers mixins
gh pr diff <pr_number> --repo vllm-project/vllm-omni \
  | grep -E '^\+.*DiffusionPipelineMixin|SchedulerMixin|ConfigMixin'
```

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
| TeaCache / Step Cache | `teacache`, `step_cache`, `cache_interval` |

```bash
gh pr diff <pr_number> --repo vllm-project/vllm-omni \
  | grep -iE 'sequence_parallel|cfg_parallel|vae_patch_parallel|tensor_parallel|teacache|step_cache'
```

Flag if none found:
```
🔴 No acceleration feature detected. The model must support at least one of:
sequence parallel, CFG parallel, VAE patch parallel, tensor parallel, or step caching (TeaCache).
Please implement and document which feature is supported.
```

#### 2.4 Memory Optimization Features (at least one required)

| Feature | Patterns to Detect |
|---------|-------------------|
| CPU Offload | `cpu_offload`, `offload_to_cpu`, `--enable-cpu-offload` |
| Quantization | `quantization`, `int8`, `fp8`, `bnb`, `bitsandbytes`, `load_in_8bit` |
| VAE Tiling | `vae_tiling`, `tile_size` |

```bash
gh pr diff <pr_number> --repo vllm-project/vllm-omni \
  | grep -iE 'cpu_offload|offload_to_cpu|quantization|int8|fp8|bitsandbytes|vae_tiling'
```

Flag if none found:
```
🔴 No memory optimization feature detected. The model must support at least one of:
CPU offload (`--cpu-offload-gb`), quantization (int8/fp8/bnb), or VAE tiling.
Please implement and document which option is supported.
```

---

### Dimension 3: Documentation

Identify documentation files changed in the PR:

```bash
gh pr view <pr_number> --repo vllm-project/vllm-omni \
  --json files --jq '.files[].path' | grep -E 'docs/|\.md$'
```

#### Documentation Checklist

| Doc Artifact | Required | Check |
|-------------|----------|-------|
| **Model support table** | Yes | Row added with: model name, architecture, HF model ID, modality, min VRAM |
| **Feature support table** | Yes | Row added showing which acceleration and memory features are supported |
| **Feature compatibility table** | Optional | If multiple features: matrix showing which combinations are validated |
| **Usage example doc** | Yes | Runnable offline + online example for the new model |

**Model support table** — expected columns:

| Model | Architecture | HF ID | Modality | Min VRAM |
|-------|-------------|-------|----------|----------|
| NewModel | DiT / AR+DiT | org/model-id | text-to-image | XX GB |

**Feature support table** — expected columns:

| Model | Seq Parallel | CFG Parallel | VAE Patch | Tensor Parallel | CPU Offload | Quantization |
|-------|-------------|-------------|-----------|----------------|------------|-------------|
| NewModel | ✅ / ❌ | ✅ / ❌ | ✅ / ❌ | ✅ / ❌ | ✅ / ❌ | ✅ / ❌ |

Flag missing docs:
```
🔴 Documentation incomplete:
- [ ] Model support table not updated (docs/models/supported_models.md or equivalent)
- [ ] Feature support table not updated
- [ ] Usage example doc missing or not updated for <ModelName>
```

---

### Dimension 4: Test Coverage

Check for new test files:

```bash
gh pr view <pr_number> --repo vllm-project/vllm-omni \
  --json files --jq '.files[].path' | grep -E '^tests/'
```

#### Test Requirements

| Test Type | Location | Required | What to Verify |
|-----------|----------|----------|----------------|
| **e2e online serving test** | `tests/e2e/online_serving/` | Yes | Start server, send request, assert output shape / non-null |
| **Offline inference test** | `tests/` or `tests/models/` | No (if e2e test exists) | Instantiate `Omni`, call `.generate()`, assert output |
| **Acceleration / memory feature test** | Alongside above | Recommended | Enable each supported feature, verify output quality and speed |
| **Combined feature test** | Alongside above | Required if 2+ features implemented | Enable multiple features together, assert output valid + VRAM + latency reported |

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
features together and asserts output validity + reports latency + VRAM under the
combined configuration.
```

---

### Step 5: Synthesize and Post Review

After completing all four dimensions, determine the overall verdict:

| Condition | Verdict |
|-----------|---------|
| Any **Required** item from Dimensions 1–4 missing | `REQUEST_CHANGES` |
| All required items present, only recommended items absent | `COMMENT` (with suggestions) |
| All required and recommended items present | `APPROVE` (or `COMMENT` for minor nits) |

Post the review:

```bash
gh api repos/vllm-project/vllm-omni/pulls/<pr_number>/reviews --input - <<EOF
{
  "event": "REQUEST_CHANGES",
  "body": "<summary of blocking issues>",
  "comments": [
    {"path": "<file>", "line": <num>, "body": "<comment>"}
  ]
}
EOF
```

---

## Priority Order

1. **PR body evidence** — missing samples/metrics block the entire review; nothing else matters if we cannot assess quality
2. **Missing inference mode** — model must work offline and online
3. **Missing acceleration feature** — required for all new diffusion models
4. **Missing memory optimization** — required for all new diffusion models
5. **Missing documentation** — tables and examples must be updated
6. **Missing e2e test** — required for merge gate
7. **Missing offline inference test** — recommended; required only when no e2e test is present
8. **Combined feature test** — required when two or more acceleration/memory features are implemented

## Comment Constraints

| Constraint | Value |
|------------|-------|
| Max inline comments | 6 per PR |
| Comment length | 2–4 sentences + checklist |
| Banned phrases | "looks good", "well done", "great job", "comprehensive", "solid" |
| Every comment | Must reference specific file/section or PR body section |

---

## References

- [Review Checklist](references/checklist.md) — per-dimension detailed checks
- [PR Body Requirements](references/pr-requirements.md) — complete PR template with examples
