---
name: vllm-omni-recipe
description: Use when adding a recipe for omnimodal models (text-to-image, text-to-video, text-to-audio, image-to-video, any-to-any, diffusion transformers) to the vLLM recipes repository, or documenting vLLM-Omni deployment
---

# vLLM-Omni Recipe Creation

## Overview

vLLM-Omni extends vLLM to support **non-autoregressive models** like Diffusion Transformers (DiT) for omnimodal generation: text-to-image, text-to-video, text-to-audio, image-to-video, and any-to-any generation.

This skill guides creating deployment guides for omnimodal models in the vLLM recipes repository.

## When to Use

- Adding text-to-image, text-to-video, text-to-audio, any-to-any model recipes
- Documenting Diffusion Transformer (DiT) deployments
- Creating recipes for hybrid AR + diffusion architectures

## Recipe Structure

Every recipe follows this structure. Sections marked ⚪ are optional.

```markdown
# ModelName Usage Guide

[Introduction with HuggingFace link, architecture description]

## Installing vLLM-Omni
[Version-variable based installation]

## [Modality] Generation
[Python API and CLI examples]

## Recommended Deployment Strategy
[Hardware recommendations by model size]

## Key Parameters
[Generation config table]

## Expected Performance ⚪
[Only if verified measurements available]

## Accuracy Comparison ⚪
[Only if verified measurements available]

## Online Serving ⚪
[If supported]

## Additional Resources
[Model card, examples, related links]
```

For detailed section templates and code examples, see [references/recipe-template.md](references/recipe-template.md).

## Required Sections

### 1. Introduction

Include:
- HuggingFace model link
- Architecture type (DiT, AR+Diffusion, MoE)
- Key capabilities and parameters

### 2. Installing vLLM-Omni

Use version variables:

```bash
export VLLM_VERSION="0.16.0"

uv venv
source .venv/bin/activate
uv pip install vllm==$VLLM_VERSION
uv pip install git+https://github.com/vllm-project/vllm-omni.git
```

Add modality-specific dependencies: `pillow`/`diffusers` for image/video, `soundfile` for audio.

### 3. Generation Examples

Provide Python API examples for all supported modalities. See [references/recipe-template.md](references/recipe-template.md) for code examples.

### 4. Recommended Deployment Strategy

Include hardware recommendations table with:
- Model sizes and variants
- Recommended GPU configurations
- Memory requirements
- Notes on MoE, batching, etc.

### 5. Key Parameters Table

Document generation parameters: `height`, `width`, `num_inference_steps`, `guidance_scale`, `negative_prompt`, `num_frames` (video), `audio_end_in_s` (audio).

## Optional Sections

### Performance & Accuracy ⚪

**Only include if you have verified measurements.** Do not fabricate benchmark numbers.

- Expected Performance: generation time, memory usage on specific hardware
- Accuracy Comparison: FID/CLIP scores vs Diffusers baseline

### Online Serving ⚪

If model supports OpenAI-compatible serving:

```bash
vllm serve org/model-name --omni
```

### Cache-DiT Acceleration ⚪

For DiT models that support caching:

```python
omni = Omni(model="org/model-name", cache_backend="cache_dit")
```

## File Naming

- Directory: `{OrgName}/` (e.g., `Qwen/`, `DeepSeek/`)
- File: `{ModelName}.md` (e.g., `Qwen-Image.md`)
- Use underscores for versions: `Wan2_2.md` or `Wan2.2.md`

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Placeholder version (0.XX.0) | Use `$VLLM_VERSION` variable |
| Missing modality dependencies | Add `soundfile` for audio, `diffusers` for video |
| Wrong Omni import | Use `from vllm_omni.entrypoints.omni import Omni` |
| Fabricated benchmarks | Only include verified measurements |
| Missing from README | Add to skills index |

## Checklist

- [ ] Title follows `# ModelName Usage Guide` format
- [ ] HuggingFace link in introduction
- [ ] Architecture description (DiT, AR+Diffusion, MoE)
- [ ] Installing vLLM-Omni with `$VLLM_VERSION`
- [ ] Modality-specific dependencies
- [ ] Python API examples for supported modalities
- [ ] Recommended deployment strategy by hardware
- [ ] Key parameters table
- [ ] Performance/accuracy sections (optional, only if verified)
- [ ] Online serving section (if supported)
- [ ] File named correctly
- [ ] README.md updated with new entry

## References

- [recipe-template.md](references/recipe-template.md) - Detailed section templates and code examples

## Related Skills

- **vllm-omni-contrib**: Contributing new models and development workflow to vLLM-Omni
- For standard LLM/vLLM recipes (autoregressive models), refer to the [vLLM recipes repository](https://github.com/vllm-project/recipes) for examples
