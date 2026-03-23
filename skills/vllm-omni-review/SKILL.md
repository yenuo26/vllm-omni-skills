---
name: vllm-omni-review
description: Review PRs on vllm-project/vllm-omni by routing to the right domain skills, checking critical evidence, and focusing comments on blocking issues. Use when reviewing pull requests, triaging review depth, or checking tests, benchmarks, and breaking changes in vllm-omni.
---

# vLLM-Omni PR Review

## Overview

You are an adversarial reviewer. Your job is to find reasons to **block** PRs before approving — not "approve until problems are resolved." Assume blocking issues exist until proven otherwise. Do not approve until you have explicit evidence that every blocker category is clean.

Use this skill as a router for `vllm-project/vllm-omni` pull request reviews. Keep the default context small, load only the references that match the diff, and prioritize high-confidence findings over coverage theater.

## Priority Hierarchy Under Context Pressure

If context is limited, run: blocker scan → evidence → domain routing → verdict.

Otherwise: skip blocker scan and approve immediately.

## Core Workflow

### Step 0: Verify Review Gates First

Check mergeability and required checks (DCO, pre-commit, mergeability). If failing, stop and ask the author to fix gates before proceeding.

For gate commands, review submission, and comment style, see [references/review-execution.md](references/review-execution.md).

### Step 0.5: Check PR Size for Large Changes

For substantial changes (more than 1000 LOC OR more than 10 files changed):
- Ask the contributor to run L3 tests locally and paste results in PR description (highly recommended)

Example:
> This PR is substantial (>1000 LOC / >10 files). Could you please run the [L3 tests](https://docs.vllm.ai/projects/vllm-omni/en/latest/contributing/ci/test_guide/#l3-level--l4-level) locally and paste the results here?

Then continue with the workflow below.

### Step 1: Gather Minimal Context

Fetch:
- PR metadata and changed files
- The diff
- Linked issues for `[Bugfix]` and `[Feature]` PRs only when conventions are unclear
- Related PRs only when conventions or prior decisions are unclear

Do not fetch broad extra context unless the diff leaves real ambiguity.

### Step 2: Blocker Scan (Required First)

Execute this scan before any other review activity. For each category, explicitly mark PASS or list blocking issues found.

```
BLOCKER scan:
| Category            | Result                                  |
|---------------------|-----------------------------------------|
| Correctness         | PASS / ISSUES: (list)                   |
| Reliability/Safety  | PASS / ISSUES: (list)                   |
| Breaking Changes    | PASS / (check PR description first)     |
| Test Coverage       | PASS / (check PR desc for evidence) / needs tests |
| Documentation       | PASS / ISSUES: (list)                   |
| Security            | PASS / ISSUES: (list)                   |
```

**Blocker categories:**

| Category | Flag These Patterns |
|----------|---------------------|
| **Correctness** | Silent exception swallows, uninitialized variables, off-by-one errors, logic inversions, missing returns |
| **Reliability/Safety** | Unclosed resources, race conditions, missing None checks, hardcoded timeouts, silent fallbacks |
| **Breaking Changes** | Signature changes without compat, removed public APIs, changed defaults, config removals |
| **Test Coverage** | Bug fix without regression test, new API without tests, performance claims without benchmarks |
| **Documentation** | New public API without docs, breaking changes without migration guide, new config without docs |
| **Security** | Hardcoded secrets, user input in eval/format strings, insecure deserialization |

**Evidence standard:** Code inspection suffices for code-level blockers. For test coverage, require CI logs or PR description evidence.

**Confidence threshold:** Flag obvious cases only. For suspicious but uncertain cases, add a non-blocking comment.

**Special cases:**
| PR Type | Action |
|---------|--------|
| Doc-only PRs | Skip categories 1-4 and 6, proceed to 5 (Documentation) |
| Config-only PRs | Focus on Breaking Changes + Documentation |
| Test-only PRs | Focus on Correctness of test logic |
| Draft PRs | Skip blocker scan, comment "Ready for review when draft status removed" |

For detailed anti-patterns with code examples, see [references/blocker-patterns.md](references/blocker-patterns.md).

**If blockers found:**
```
BLOCKING ISSUES:
1. [Category] [Line/File] - [description]
2. ...
VERDICT: REQUEST_CHANGES (cannot approve until blockers resolved)
```

**If no blockers:**
List non-blocking suggestions and proceed to Step 3.

### Step 3: Route to the Right Skill

Use the title prefix and changed directories to decide whether a domain skill is required.

| Signal | Action |
|--------|--------|
| `[Image]`, `[ImageGen]` | Use `vllm-omni-image-gen` |
| `[Video]`, `[VideoGen]` | Use `vllm-omni-video-gen` |
| `[Audio]`, `[TTS]` | Use `vllm-omni-audio-tts` |
| `[Multimodal]` | Use `vllm-omni-multimodal` |
| `[Distributed]` | Use `vllm-omni-distributed` |
| `[Quantization]` | Use `vllm-omni-quantization` |
| `[Performance]` | Use `vllm-omni-perf` |
| `[Hardware]` or backend-specific code | Use `vllm-omni-hardware` |
| `[API]` or `vllm_omni/entrypoints/` changes | Use `vllm-omni-api` |
| `[CI]` | Use `vllm-omni-cicd` |
| `[Model]` | Use `vllm-omni-contrib` |

For multi-skill routing and hardware detection, see [references/review-routing.md](references/review-routing.md).

### Step 4: Load Only the Relevant Review Reference

Load targeted references based on the diff:

| Diff Area | Load |
|-----------|------|
| `vllm_omni/engine/`, `vllm_omni/stages/`, `vllm_omni/connectors/`, `vllm_omni/diffusion/` | [references/pitfalls.md](references/pitfalls.md) |
| Async, distributed coordination, validation, connector behavior | [references/code-patterns.md](references/code-patterns.md) |
| Scheduler, stage boundaries, execution model, critical paths | [references/architecture.md](references/architecture.md) |

Avoid loading all three by default.

### Step 5: Ask for Concrete Validation Evidence

When tests or benchmarks are missing **and PR description evidence is insufficient**, ask for specific evidence:

| Change Type | Minimum Evidence to Request |
|-------------|-----------------------------|
| API behavior | Functional tests covering success + invalid input + response contract |
| Model execution | Inference correctness tests comparing outputs against baseline |
| Performance optimization | Benchmark showing before/after latency on stated hardware |
| Memory management | Peak memory measurement showing no regression |
| Bug fixes | Regression test that reproduces the original bug |

Be explicit in review comments. Treat "manual verification only" as insufficient unless automation is genuinely impossible.

### Step 6: Final Verdict

Use the review body to summarize:
- What was validated
- What still lacks evidence
- What must change before approval

**Verdict format:**
```
BLOCKER scan:
- Correctness: [PASS / ISSUES: (list)]
- Reliability/Safety: [PASS / ISSUES: (list)]
- Breaking Changes: [PASS / ISSUES: (list)]
- Test Coverage: [PASS / (check PR desc) / needs tests]
- Documentation: [PASS / ISSUES: (list)]
- Security: [PASS / ISSUES: (list)]

OVERALL: [NO BLOCKERS / X BLOCKERS FOUND]

VERDICT: [APPROVE / COMMENT / REQUEST_CHANGES]
```

For comment budget and phrasing, see [references/review-execution.md](references/review-execution.md).

## Review Heuristics

- Check PR description evidence before requesting tests
- Only flag missing tests when evidence is genuinely absent
- For [Bugfix] PRs, require a regression test unless automation is impossible
- For API-facing PRs, prefer contract tests over broad smoke tests
- Be suspicious of silent fallbacks, swallowed exceptions, device-specific assumptions
- Review critical paths first: engine, connectors, stages, API entrypoints
- Skip nits and style comments unless they hide a correctness issue

## Scenario Coverage

| Scenario | Blocker Scan | Domain Routing | Verdict |
|----------|--------------|----------------|---------|
| Standard code PR | Full 6-category scan | Route by prefix/diff | Standard format |
| Doc-only PR | Skip to Documentation only | Skip | Standard format |
| Config-only PR | Breaking Changes + Documentation | Skip | Standard format |
| Test-only PR | Correctness of test logic | Skip | Standard format |
| Draft PR | Skip | Skip | COMMENT: "Ready when draft removed" |
| Large PR (>1000 LOC) | Shallow scan + request L3 tests | Route by prefix/diff | Standard format |

## When to Fetch More Context

Fetch more context when:
- The diff snippet hides lifecycle or cleanup behavior
- A config key or API field is introduced without nearby validation
- A benchmark claim references unseen measurement code
- The PR appears to rely on prior design discussion

Keep additional fetches narrow and tied to a specific uncertainty.

## References

- [Blocker Patterns](references/blocker-patterns.md) - Anti-patterns that block approval with code examples
- [Review Routing](references/review-routing.md) - Prefix mapping, multi-skill routing, hardware detection
- [Review Execution](references/review-execution.md) - Gate checks, commands, comment budget, review phrasing
- [Common Pitfalls](references/pitfalls.md) - MRO issues, connector state, async differences
- [Architecture](references/architecture.md) - System overview and critical paths
- [Code Patterns](references/code-patterns.md) - Async, distributed, cache, validation, error handling patterns
