---
name: vllm-omni-release-note-writer
description: Use when drafting or editing release notes for vllm-project/vllm-omni, especially when summarizing changes between tags, organizing highlights, and matching the style of recent vLLM-Omni releases
---

# vLLM-Omni Release Note Writer

## Overview

This skill writes release notes for `vllm-project/vllm-omni` by following the editorial style that emerged in the project's historical releases.

Always read [references/past-release-note-patterns.md](references/past-release-note-patterns.md) first, then use [references/release-note-template.md](references/release-note-template.md) as the drafting template.

## When to Use

- Drafting a new `vLLM-Omni` release note from merged PRs or a GitHub compare view
- Rewriting an auto-generated `What's Changed` dump into a user-facing summary
- Editing an RC or final release note so it matches recent `v0.12.0rc1` to `v0.18.0` structure
- Cross-checking whether a change belongs in Highlights, a themed section, or should be omitted

Do not use this skill for changelog generation in unrelated repos.

## Output Workspace

Save working files under `vllm-omni-release-note/output/$VERSION/`.

Recommended files:

- `0-raw-input.md`: compare output, PR list, and rough notes
- `1-commit-triage.csv`: per-PR inclusion and category decisions
- `2-highlights-draft.md`: short editorial summary
- `3-release-note-draft.md`: full release note draft
- `4-release-note-review.md`: questions, uncertainties, and follow-up checks

## Core Workflow

### 1. Gather the release boundary

Identify:

- current tag, for example `v0.18.0`
- previous tag
- whether the target is an RC or final release

Tag selection rules:

- For a final release, `current tag` is the tag of the release being written, and `previous tag` is the previous final release tag.
- For an RC release, `current tag` is the tag of the RC being written, and `previous tag` is the immediately previous final or RC release tag.

Examples:

- Final release: writing `v0.18.0` means `current tag = v0.18.0`, `previous tag = v0.16.0`
- RC release: writing `v0.18.0rc1` means `current tag = v0.18.0rc1`, `previous tag = v0.17.0rc1` or `v0.17.0`, whichever is the most recent prior final/RC tag in the release chain

Use one or more of:

- `https://github.com/vllm-project/vllm-omni/releases`
- `https://api.github.com/repos/vllm-project/vllm-omni/releases`
- `https://api.github.com/repos/vllm-project/vllm-omni/compare/<base>...<head>`

If the release body already exists, treat it as one source, not ground truth. Re-check important claims against PRs when wording matters.

### 2. Build a triage sheet

Review each PR or commit and record:

- title
- PR number
- area or model family
- user-facing summary
- category
- decision: `include`, `merge-into-summary`, `ignore`
- reason

Ignore or merge away low-signal items such as:

- typo-only docs
- trivial CI maintenance with no release impact
- internal cleanup with no user-visible outcome
- duplicate fixes already covered by a stronger umbrella PR

### 3. Convert engineering changes into release language

Write for users, not for the merge log.

Prefer:

- "Added support for FLUX.2-dev and FLUX.1-Kontext-dev"
- "Improved Qwen3-TTS latency and streaming stability"
- "Expanded TP/SP/HSDP support for diffusion serving"

Avoid:

- PR-title fragments
- implementation-only detail with no user impact
- one bullet per PR when several PRs clearly belong to one theme

### 4. Write the Highlights block first

The opening should do three things:

1. state release scale or context when useful
2. summarize the main story of the release in 1 paragraph
3. list 4-8 key improvements that a user should scan first

Recent `vLLM-Omni` releases consistently lead with:

- upstream rebase or alignment
- major model support expansion
- serving/runtime architecture changes
- performance or production-readiness gains
- quantization / distributed / platform coverage

RC releases should also use the same final-release narrative template. Keep the `rc` version identifier in the title and opening copy, but do not switch to a separate RC-only structure.

### 5. Expand into themed sections

Choose section headings from the historical section bank in [references/past-release-note-patterns.md](references/past-release-note-patterns.md). Do not invent a brand-new taxonomy unless the release genuinely needs it.

Rules:

- keep section order stable
- group related PRs into one paragraph or bullet cluster
- mention representative PR numbers, not every PR
- preserve important caveats, flags, and compatibility notes

### 6. Add notes and breaking changes explicitly

If a release includes:

- upgrade caveats
- manual dependency bumps
- hardware/backend limitations
- experimental support
- incompatible default changes

surface them in `### Breaking Changes`, `### Note`, or a short dedicated paragraph. Do not bury them in a generic feature section.

## Section Selection Rules

Use this mapping as the default:

| Change type | Preferred section |
|-------------|-------------------|
| New model family, new checkpoints, new modality coverage | `Expanded Model Support` or `Model Support` |
| Throughput, latency, startup, cache, memory, scheduler gains | `Performance Improvements` or the relevant domain section |
| Refactors that change serving/runtime capability | `Core Architecture & Runtime` or `Inference Infrastructure & Parallelism` |
| Qwen3-TTS, MiMo-Audio, Fish Speech, omni speech serving | `Text-to-Speech Improvements` or `Audio, Speech & Omni...` |
| Diffusion runtime, image/video serving, TeaCache, DiT execution | `Diffusion, Image & Video Generation` |
| INT8, FP8, GGUF, unified quantization, CPU offload compatibility | `Quantization & Memory Efficiency` |
| Frontend, OpenAI API behavior, Helm, integrations, RL pipelines | `Serving & Integrations` or `Frontend & Serving` |
| ROCm, NPU, XPU, CI coverage, distributed platform support | `Platforms...` or `Hardware Support` |
| Docs refresh, benchmark infra, release pipeline, nightly coverage | `CI, Benchmarks & Documentation` |

## Writing Rules

- Prefer one paragraph plus grouped bullets over a long flat bullet list
- Mention PR numbers in `(#1234)` form after the claim
- Keep claims specific and user-facing
- If several fixes land for one model, merge them into one sentence
- Do not overstate internal refactors; explain what they unlock
- Keep `What's Changed` and `New Contributors` as GitHub-generated appendices if they already exist

## Validation Checklist

- [ ] RC and final releases both use the Final Release Template structure
- [ ] `current tag` is the tag of the release being written
- [ ] `previous tag` follows the release-boundary rule: previous final for finals, previous final or RC for RCs
- [ ] Opening paragraph states the release story clearly
- [ ] Highlights contain only the most important user-facing items
- [ ] Section headings match historical vLLM-Omni patterns
- [ ] Pure maintenance noise is omitted or merged away
- [ ] Important caveats, flags, and breakages are explicit
- [ ] PR numbers and model names are accurate
- [ ] Any uncertain claim is marked in `4-release-note-review.md`

## Research Tips

- For ambiguous PRs, inspect the PR body via `https://api.github.com/repos/vllm-project/vllm-omni/pulls/<number>`
- Use the compare API to avoid missing merged work between tags
- If a release reuses content from an RC, make the delta versus the prior RC explicit
- When a refactor is large, summarize the user-visible consequence instead of enumerating files

## References

- [past-release-note-patterns.md](references/past-release-note-patterns.md) - Historical release-note structure, style evolution, and section bank
- [release-note-template.md](references/release-note-template.md) - Copyable Final Release Template used for both RC and final releases
