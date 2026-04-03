# Historical vLLM-Omni Release Note Patterns

This reference summarizes the style that emerged across `vllm-project/vllm-omni` releases from `v0.11.0rc1` through `v0.18.0`.

## Evolution Summary

### `v0.11.0rc1`

- Mostly an initial pre-release announcement plus GitHub-generated `What's Changed`
- Useful as project history, but **not** the right template for current releases

### `v0.12.0rc1`

- First strong editorialized release note
- Introduced:
  - a real `## Highlights` section
  - themed sections such as breaking changes, diffusion engine, serving, omni pipeline, model support, and platform coverage
- Treat this as the first modern baseline

### `v0.14.0rc1`, `v0.15.0rc1`, `v0.16.0rc1`

- RCs emphasized:
  - release scale
  - upstream alignment or rebase
  - a short set of user-visible focus areas
- Sections were compact and pragmatic

### `v0.14.0`, `v0.16.0`, `v0.18.0`

- Final releases became more polished and narrative
- Common pattern:
  - `## Highlights`
  - one summary paragraph describing the release story
  - `### Key Improvements`
  - several domain sections with grouped bullets

### `v0.17.0rc1`, `v0.18.0rc1`

- RC structure stabilized around concise themed buckets:
  - `Expanded Model Support`
  - `Performance Improvements`
  - `Inference Infrastructure & Parallelism`
  - `Text-to-Speech Improvements`
  - `Quantization & Hardware Support`
  - `Frontend & Serving`
  - `Reliability, Tooling & Developer Experience`

## Default Style Rules

- Start with the release story, not raw PR enumeration
- Organize by user-facing domains, not code directories
- Merge related PRs into one sentence when they support the same claim
- Mention representative PR numbers after the claim
- Keep internal refactors only when they unlock visible capabilities
- Even for RCs, prefer the final-release narrative structure instead of maintaining a separate RC template

## Recommended Section Bank

Choose from these headings before inventing new ones:

### Frequently seen section headings

- `### Expanded Model Support`
- `### Performance Improvements`
- `### Inference Infrastructure & Parallelism`
- `### Text-to-Speech Improvements`
- `### Quantization & Hardware Support`
- `### Frontend & Serving`
- `### Reliability, Tooling & Developer Experience`

- `### Key Improvements`
- `### Core Architecture & Runtime`
- `### Model Support`
- `### Audio, Speech & Omni Production Optimization`
- `### Diffusion, Image & Video Generation`
- `### Quantization & Memory Efficiency`
- `### RL, Serving & Integrations`
- `### Platforms, Distributed Execution & Hardware Coverage`
- `### CI, Benchmarks & Documentation`
- `### Note`
- `### Breaking Changes`

## Inclusion Heuristics

Include:

- new model support or major capability expansion
- serving/API behavior changes users will notice
- meaningful latency, throughput, startup, or memory improvements
- distributed execution and backend coverage changes
- quantization support that changes deployability
- explicit upgrade notes, caveats, or compatibility warnings

Usually merge or omit:

- pure typo/docs cleanup
- lint-only or formatting-only PRs
- internal CI maintenance with no release-facing impact
- repeated follow-up fixes that are already captured by one stronger summary

## Tone and Density

- `v0.17.0rc1` and `v0.18.0rc1` are the best compact RC examples
- `v0.16.0` and `v0.18.0` are the best final-release examples
- Keep bullet density moderate; readers should be able to scan one section in under a minute

## Common Mistakes

| Mistake | Better approach |
|---------|-----------------|
| One bullet per PR | Merge PRs into a release-facing narrative |
| Listing refactors without impact | Explain what the refactor enables |
| Mixing breaking changes into generic sections | Pull them into `Breaking Changes` or `Note` |
| Letting `What's Changed` drive the whole note | Use it as source material, not final structure |
