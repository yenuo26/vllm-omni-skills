---
name: vllm-omni-review
description: Review pull requests on vllm-project/vllm-omni repository. Use when reviewing PRs, checking code quality, validating tests, or ensuring adherence to project conventions.
---

# vLLM-Omni PR Review

## Overview

This skill guides PR reviews for [vLLM-Omni](https://github.com/vllm-project/vllm-omni), an omni-modal inference framework. Reviews focus on critical issues: missing tests, unvalidated claims, security concerns, design flaws, and breaking changes.

## Review Constraints

| Constraint | Value |
|------------|-------|
| Max inline comments | 5 per PR |
| Comment length | 2-4 sentences each |
| Small doc fix | 0 comments expected |
| Large feature | 3-5 comments on critical gaps |

### Banned Phrases (Generic Praise)
- "solid", "generally", "looks good", "well done", "nice work", "great job"
- "comprehensive", "well structured", "good implementation"
- Any phrase without specific code location reference

## Review Workflow

### Step 1: Fetch PR Data
```bash
gh pr view <pr_number> --repo vllm-project/vllm-omni --json title,body,author,state
gh pr diff <pr_number> --repo vllm-project/vllm-omni
```

### Step 2: Identify PR Type
Check PR title/description for prefixes:
- `[Bugfix]` → Bugfix review checklist
- `[Feature]` → Feature review checklist
- `[Refactor]` → Refactor review checklist
- `[Model]` → Model review checklist
- `[Performance]` → Performance review checklist
- `[Distributed]` → Distributed review checklist
- `[Quantization]` → Quantization review checklist
- `[API]` → API review checklist
- `[CI]` → CI review checklist

### Step 3: Run Red Flag Checks

**Must check for ALL PRs:**
- [ ] New API without tests?
- [ ] New model without tests?
- [ ] Performance claims without benchmarks?
- [ ] Mixin after `nn.Module` with `__init__` setting attributes?
- [ ] API changes without documentation?

### Step 4: Apply Type-Specific Checklist
See [references/pr-types.md](references/pr-types.md) for detailed checklists by PR type.

### Step 5: Check Common Pitfalls
See [references/pitfalls.md](references/pitfalls.md) for known issues:
- MRO issues with mixins
- Connector state management
- Async vs Sync path differences
- Stage configuration validation

### Step 6: Post Review
```bash
gh api repos/vllm-project/vllm-omni/pulls/<pr_number>/reviews --input - <<EOF
{
  "event": "REQUEST_CHANGES" | "APPROVE" | "COMMENT",
  "body": "<summary>",
  "comments": [
    {"path": "<file>", "line": <num>, "body": "<comment>"}
  ]
}
EOF
```

## Priority Order

1. **Missing tests** - highest priority
2. **Unvalidated claims** - demand measurements/evidence
3. **Security concerns** - input validation, resource exhaustion
4. **Design flaws** - architectural issues, race conditions
5. **Breaking changes** - undocumented API changes

**Skip:** Minor style issues, nitpicks, nice-to-haves, linter-covered issues

## Critical Directories

| Directory | Impact | Review Focus |
|-----------|--------|--------------|
| `vllm_omni/engine/` | **Critical** | Scheduler, pipeline coordination |
| `vllm_omni/model_executor/` | **Critical** | Model loading, weight management |
| `vllm_omni/connectors/` | High | Shared memory, IPC |
| `vllm_omni/entrypoints/` | High | API validation, error handling |
| `vllm_omni/stages/` | High | Stage lifecycle, state management |
| `vllm_omni/diffusion/` | High | Generation quality, memory |

## Example Comments

**Good (Demands Evidence):**
```
Where are the memory measurements? The PR claims "50% reduction" but provides no before/after data. Run benchmarks with realistic workloads and report peak VRAM usage.
```

**Good (Missing Tests):**
```
Missing regression test for this bug fix. Add a test that reproduces the original issue and verifies this fix prevents it.
```

**Good (MRO Issue):**
```
This mixin is listed after nn.Module but has an __init__ that sets attributes. When nn.Module.__init__ is called, the mixin's __init__ won't run. Use lazy initialization with @property instead.
```

**Bad (Generic):**
```
The implementation looks good. Consider adding tests.
```

## Context Fetching

**When to fetch more context:**
- New imports with performance/compatibility implications
- 3-line diff context isn't enough
- Code changes might require config updates

**Tools:**
```bash
# Get surrounding code
gh api repos/vllm-project/vllm-omni/contents/<path>?ref=<branch>

# Find symbol definition
gh search code --repo vllm-project/vllm-omni "class <SymbolName>"

# Check related configs
gh search code --repo vllm-project/vllm-omni "<config_key>" --extension yaml
```

**Limits:** 3-5 context fetches per review, 20-50 lines each

## Known Dependencies

Do NOT flag these as missing:
- `einops` - inherited from vLLM
- `diffusers` - already in requirements

## References

- [PR Type Checklists](references/pr-types.md) - Detailed checklists by PR type
- [Common Pitfalls](references/pitfalls.md) - MRO issues, connector state, async patterns
- [Architecture](references/architecture.md) - System overview and critical paths
- [Code Patterns](references/code-patterns.md) - Async, distributed, KV cache patterns
