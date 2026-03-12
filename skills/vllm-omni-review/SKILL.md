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

## References

- [Review Routing](references/review-routing.md) - prefix mapping, multi-skill routing, hardware detection, delegation
- [Review Execution](references/review-execution.md) - gate checks, commands, comment budget, review phrasing
- [Common Pitfalls](references/pitfalls.md) - MRO issues, connector state, async differences, validation gaps
- [Architecture](references/architecture.md) - system overview and critical paths
- [Code Patterns](references/code-patterns.md) - async, distributed, cache, validation, and error handling patterns
