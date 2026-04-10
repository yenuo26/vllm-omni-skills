---
name: vllm-omni-review
description: Review PRs on vllm-project/vllm-omni by routing to the right domain skills, checking critical evidence, and focusing comments on blocking issues. Use when reviewing pull requests, triaging review depth, or checking tests, benchmarks, and breaking changes in vllm-omni.
---

# vLLM-Omni PR Review

## Overview

Review PRs like a real maintainer — direct, selective, and focused on high-signal issues. Prioritize 2-3 real problems per PR over exhaustive coverage. Most PRs should get 1-5 short comments; some just get an empty APPROVE.

Use this skill as a router for `vllm-project/vllm-omni` pull request reviews. Keep the default context small, load only the references that match the diff, and prioritize high-confidence findings over coverage theater.

## Which reference to load (do not load everything)

| Situation | Open |
|-----------|------|
| Every review | [references/review-execution.md](references/review-execution.md) — gates, `gh` commands, comment budget, tone, batch/CI triage, Python style flags |
| Prefix / multi-skill / hardware guess | [references/review-routing.md](references/review-routing.md) |
| Blocker scan details + merge-blocking patterns | [references/blocker-patterns.md](references/blocker-patterns.md) — Part 1 patterns; **Part 2** = former “pitfalls” (footguns, MRO, connectors, async, etc.) |
| System layout + **code-pattern review** (async, connectors, validation, …) | [references/architecture.md](references/architecture.md) — includes “Code patterns for review” at the end |
| Diffusion / image / video model PRs | [references/diffusion-checklist.md](references/diffusion-checklist.md) |
| High-risk change; need coverage matrix / docs sync | [references/tests-docs-checklist.md](references/tests-docs-checklist.md) |
| Calibrating phrasing from real maintainers | [references/maintainer-style-study.md](references/maintainer-style-study.md) |

## Priority Hierarchy Under Context Pressure

If context is limited, prioritize: blocker scan → evidence → domain routing → verdict.

Always run the blocker scan. Under context pressure, do a shallow scan of the most critical categories (Correctness, Security) and flag that the scan was incomplete.

## Core Workflow

Check whether this PR is still a draft or WIP in the PR title, if so, end the review process. 


### Step 0: Verify Review Gates First

If this is a ready-to-review PR, check the mergeability and required checks (DCO, pre-commit, mergeability). If failing, stop and ask the author to fix gates before proceeding.

For gate commands, review submission, and comment style, see [references/review-execution.md](references/review-execution.md).

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
| Draft PRs | Do not block; add a single non-blocking comment: "Ready for full review when draft status removed. Preliminary scan available on request." |

For detailed anti-patterns with code examples, see [references/blocker-patterns.md](references/blocker-patterns.md).

**If blockers found:** Track issues internally (category + file + line). Request changes on GitHub only for real blockers; do not paste structured `BLOCKING ISSUES:` templates into the review body (see Step 6).

**If no blockers:** List non-blocking suggestions and proceed to Step 3.

### Step 3: Route to the Right Skill

Use the title prefix and changed directories to decide whether a domain skill is required. Doc-only, config-only, and test-only PRs usually skip domain skills unless the diff crosses into model or API areas.

**Full prefix table, multi-skill combos, hardware detection, and delegation triggers:** [references/review-routing.md](references/review-routing.md).

### Step 4: Load Only the Relevant Review Reference

Load targeted references based on the diff:

| Diff Area                                                                                 | Load                                                       |
| ----------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `vllm_omni/engine/`, `vllm_omni/stages/`, `vllm_omni/connectors/`, `vllm_omni/diffusion/` | [blocker-patterns.md](references/blocker-patterns.md) **Part 2** (common pitfalls) |
| Async, distributed coordination, validation, connector behavior                           | [architecture.md](references/architecture.md) — section **Code patterns for review** (at end of file) |
| Scheduler, stage boundaries, execution model, critical paths                              | [Architecture](references/architecture.md) (full)          |
| High-risk changes (core logic, configs/params, error handling, concurrency/distributed, I/O) or `[Feature]` / `[Bugfix]` PRs | [references/tests-docs-checklist.md](references/tests-docs-checklist.md) |

Pick the narrowest references that match the diff; avoid loading every row by default.

### Step 5: Ask for Concrete Validation Evidence

When tests or benchmarks are missing **and PR description evidence is insufficient**, ask for specific evidence:

| Change Type | Minimum Evidence to Request |
|-------------|-----------------------------|
| API behavior | Functional tests covering success + invalid input + response contract |
| Model execution | Inference correctness tests comparing outputs against baseline |
| Performance optimization | Benchmark showing before/after latency on stated hardware |
| New feature (performance-affecting) | Performance comparison test: baseline vs. with change (latency, throughput, VRAM) |
| Memory management | Peak memory measurement showing no regression |
| Bug fixes | Regression test that reproduces the original bug |

For `[Feature]` PRs affecting performance or `[Performance]` PRs, use the checklist in [references/tests-docs-checklist.md](references/tests-docs-checklist.md) section 5.

Be explicit in review comments. Treat "manual verification only" as insufficient unless automation is genuinely impossible.

### Step 6: Final Verdict

Use the review body to summarize:
- What was validated
- What still lacks evidence

**Verdict:** Use the GitHub review event (`APPROVE` / `COMMENT` / `REQUEST_CHANGES`). Do not put structured verdict blocks in the review body.

- `APPROVE` — no blockers; body optional (empty is fine).
- `COMMENT` — suggestions only; body optional (~50% should be empty).
- `REQUEST_CHANGES` — genuine blocking issues only (crashes, data loss, security, policy gates).

For tone and inline style, see [references/review-execution.md](references/review-execution.md). For maintainer phrasing samples, see [references/maintainer-style-study.md](references/maintainer-style-study.md).

## Review Heuristics

Trust PR description and CI evidence before demanding new tests. Prefer regression tests for `[Bugfix]`, contract tests for API changes, and scan engine → connectors → stages → entrypoints before peripheral files. Skip style nits unless they mask correctness.

## When to Fetch More Context

Fetch more context when:
- The diff snippet hides lifecycle or cleanup behavior
- A config key or API field is introduced without nearby validation
- A benchmark claim references unseen measurement code
- The PR appears to rely on prior design discussion

Keep additional fetches narrow and tied to a specific uncertainty.

## Diffusion Model PR Review

**When:** Title prefix `[Model]`, `[New Model]`, `[Image]`, `[ImageGen]`, `[Video]`, `[VideoGen]`, or `[Diffusion]`, or a new diffusion model path under `vllm_omni/diffusion/`.

**Load** [references/diffusion-checklist.md](references/diffusion-checklist.md) instead of expanding the full workflow here: Dimensions 1–4 (including optional canonical PR body template + measurement guidance for Dimension 1), `gh`/`grep` detection commands, **Quick Red Flags**, combined-feature rules.

**Gate order before approve:** PR body evidence (script, samples, latency, VRAM) → offline **and** online paths → at least one acceleration **and** one memory optimization (new models) → docs tables + usage examples → required e2e online test → offline test if no e2e → combined test when 2+ accel/memory features.

Use Quick Red Flags actions for comment severity; write human-shaped GitHub comments, not giant pasted templates.

## Batch Review Session

For daily sessions (reply-first, PR selection, pacing, re-review): [references/review-execution.md](references/review-execution.md) — sections **Batch and daily review sessions** and related scripts.

## References

- [Review execution](references/review-execution.md) — Gates, `gh` fetch/submit, comments, batch workflow, CI log triage, Python style flags
- [Review routing](references/review-routing.md) — Prefix → domain skill, hardware, multi-skill
- [Blocker patterns](references/blocker-patterns.md) — Merge-blocking patterns (Part 1) + footguns / pitfalls (Part 2)
- [Architecture](references/architecture.md) — System overview, critical paths, code patterns for review
- [Diffusion checklist](references/diffusion-checklist.md) — Diffusion PR dimensions, PR body template, Quick Red Flags
- [Tests & docs checklist](references/tests-docs-checklist.md) — High-risk coverage matrix and docs sync
- [Maintainer style study](references/maintainer-style-study.md) — Example maintainer phrasing
