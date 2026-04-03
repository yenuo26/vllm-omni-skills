# vLLM-Omni Release Note Templates

Use this template after triaging PRs and drafting the main themes.

Use the same structure for both RC and final releases. For RCs, keep the `rc` suffix in `<VERSION>` and make the opening paragraph explicitly say it is a release candidate.

Before drafting, set the comparison boundary correctly:

- Final release: `current tag = this final release tag`, `previous tag = previous final release tag`
- RC release: `current tag = this RC tag`, `previous tag = immediately previous final or RC release tag`

## Final Release Template

```md
## Highlights

This release features <N> commits from <contributors> contributors, including <new contributors> new contributors.

vLLM-Omni `<VERSION>` is a <release story>. It aligns with <upstream or platform context>, expands <model/capability scope>, and improves <production, performance, or deployment story>.

If `<VERSION>` is an RC, add one sentence such as: `This release candidate is intended to validate <focus area> before the final cut.`

### Key Improvements

* **<Major release theme 1>**, with <user-facing effect>. **(#1234, #2345)**
* **<Major release theme 2>**, with <user-facing effect>. **(#1234, #2345)**
* **<Major release theme 3>**, with <user-facing effect>. **(#1234, #2345)**

### Core Architecture & Runtime

* <Grouped summary>. **(#1234, #2345)**

### Model Support

* <Grouped summary by modality or family>. **(#1234, #2345)**

### Audio, Speech & Omni Production Optimization

* <Grouped summary>. **(#1234, #2345)**

### Diffusion, Image & Video Generation

* <Grouped summary>. **(#1234, #2345)**

### Quantization & Memory Efficiency

* <Grouped summary>. **(#1234, #2345)**

### RL, Serving & Integrations

* <Grouped summary>. **(#1234, #2345)**

### Platforms, Distributed Execution & Hardware Coverage

* <Grouped summary>. **(#1234, #2345)**

### CI, Benchmarks & Documentation

* <Grouped summary>. **(#1234, #2345)**

### Note

* <Dependency caveat / special upgrade note / compatibility reminder>
```

## Editing Rules

- Keep the opening paragraph to 2-3 sentences
- Keep `Key Improvements` to the handful of items a user should read first
- Prefer grouped summaries over long bullet dumps
- Keep PR citations representative rather than exhaustive
- Do not create a separate RC-only section layout; RCs use this same template
