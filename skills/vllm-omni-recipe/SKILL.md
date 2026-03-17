---
name: vllm-omni-recipe
description: Use when adding a recipe for omnimodal models (text-to-image, text-to-video, text-to-audio, image-to-video, any-to-any, diffusion transformers) to the vLLM recipes repository, or documenting vLLM-Omni deployment
---

# vLLM-Omni Recipe Creation

## Overview

vLLM-Omni extends vLLM to support **non-autoregressive models** like Diffusion Transformers (DiT) for omnimodal generation: text-to-image, text-to-video, text-to-audio, image-to-video, and any-to-any generation.

This skill guides creating deployment guides for omnimodal models using the vLLM-Omni framework.

## When to Use

- Adding text-to-image, text-to-video, text-to-audio, any-to-any model recipes
- Documenting Diffusion Transformer (DiT) deployments
- Creating recipes for hybrid AR + diffusion architectures

## Recipe Structure

```markdown
# ModelName Usage Guide

[Introduction with HuggingFace link, architecture description, key capabilities]

## Supported Models
[Model variants and sizes]

## Installing vLLM-Omni
[Pip install instructions with vllm-omni]

## [Modality] Generation
[Text-to-Image/Video/Audio/Any-to-Any examples - Python + CLI]

## Recommended Deployment Strategy
[Hardware recommendations by model size and workload]

## Key Parameters
[Parameter table for generation config]

## Expected Performance ⚪
[Generation time, throughput metrics on different hardware - include only if you have verified measurements]

## Accuracy Comparison ⚪
[vs Diffusers/HF performance and quality metrics - include only if you have verified measurements]

## Online Serving ⚪
[vllm serve --omni and OpenAI client examples]

## Cache-DiT Acceleration ⚪
[Optional: caching configuration for speedup]

## Additional Resources
[Model card, examples, related links]
```

## Required Sections

### 1. Introduction

Describe the architecture and capabilities:

```markdown
ModelName is a [architecture type] model for [modality] generation.

### Architecture
- **Type**: Diffusion Transformer / AR + Diffusion hybrid / MoE DiT
- **Parameters**: X billion total / Y billion active (for MoE)
- **Key Features**: [text rendering, long video, high-fidelity audio, etc.]

### Key Capabilities
- **Text-to-X**: [description]
- **Image-to-X**: [if applicable]
```

Architecture types:
| Type | Examples | Notes |
|------|----------|-------|
| DiT | SD3.5, Wan2.2 | Pure diffusion transformer |
| AR + Diffusion | GLM-Image | Autoregressive encoder + diffusion decoder |
| MoE DiT | Wan2.2-A14B | Mixture of experts diffusion |

### 2. Installing vLLM-Omni

```bash
# Set version variables (check vllm-omni quickstart for current versions)
export VLLM_VERSION="0.16.0"

uv venv
source .venv/bin/activate
uv pip install vllm==$VLLM_VERSION
uv pip install git+https://github.com/vllm-project/vllm-omni.git
```

Include modality-specific dependencies:

| Modality | Additional Dependencies |
|----------|------------------------|
| Image | `pillow`, `diffusers` (for CLI scripts) |
| Video | `diffusers` (for `export_to_video`) |
| Audio | `soundfile` or `scipy` |

### 3. Generation Examples

Provide both Python API and CLI examples:

**Text-to-Image:**
```python
from vllm_omni.entrypoints.omni import Omni

omni = Omni(model="org/model-name")

images = omni.generate(
    prompt="a cat wearing sunglasses, cyberpunk style",
    negative_prompt="blurry, low quality",
    height=1024,
    width=1024,
    num_inference_steps=28,
    guidance_scale=7.5,
)
```

**Text-to-Video:**
```python
frames = omni.generate(
    "A serene lakeside sunrise with mist over the water.",
    height=720,
    width=1280,
    num_frames=81,
    num_inference_steps=40,
    guidance_scale=4.0,
)
```

**Text-to-Audio:**
```python
audio = omni.generate(
    "The sound of a dog barking",
    negative_prompt="Low quality.",
    guidance_scale=7.0,
    num_inference_steps=100,
    extra={"audio_start_in_s": 0.0, "audio_end_in_s": 10.0},
)
```

**Image-to-Video/Image-to-Image:**
```python
import PIL.Image
image = PIL.Image.open("input.jpg").convert("RGB")
frames = omni.generate(
    "A cat playing with yarn",
    pil_image=image,
    # ... other params
)
```

**Any-to-Any:**
```python
# Models that support cross-modal generation (e.g., text+image -> audio+video)
# Models that support cross-modal generation (e.g., text+image -> audio+video)
omni = Omni(model="org/any-to-any-model")

# Generate multiple output modalities from mixed input
# Assumes 'image' is loaded as in the previous example.
outputs = omni.generate(
    prompt="Describe this scene and generate matching audio",
    pil_image=image,  # Optional: image input
    # Model handles cross-modal generation
)
```

### 4. Recommended Deployment Strategy

Provide guidance on choosing the right configuration based on model size and workload:

```markdown
## Recommended Deployment Strategy

| Model Size | Recommended Hardware | Memory | Notes |
|------------|---------------------|--------|-------|
| 2.5B (SD3.5-medium) | 1x A100 | 16GB | Single GPU |
| 8B (SD3.5-large) | 1x H100 | 40GB | Single GPU |
| 14B MoE (Wan2.2) | 1x H100/H200 | 80GB | Single GPU, MoE sparse |

### Workload-Specific Recommendations

**Batch Generation:**
- Increase `num_outputs_per_prompt` for parallel generation
- Consider batching multiple prompts

**Quality vs Speed:**
- Higher `num_inference_steps` = better quality, slower
- Turbo/distilled variants for few-step inference

**Memory Optimization:**
- Use FP8/FP16 variants when available
- Enable memory-efficient attention if supported

**Any-to-Any Models:**
- May require more memory for multi-modal processing
- Consider disaggregated serving for different modalities
```

### 5. Expected Performance ⚪

**Optional: Include only if you have verified measurements from actual deployments.**

When including performance metrics, cite your measurement methodology and hardware:

```markdown
## Expected Performance

Performance measured on H100 GPU:

| Configuration | Generation Time | Memory | Notes |
|---------------|-----------------|--------|-------|
| 1024x1024, 28 steps | 2.1s | 24GB | SD3.5-medium |
| 720p, 81 frames, 40 steps | 45s | 68GB | Wan2.2-T2V |
| 10s audio, 100 steps | 3.2s | 8GB | Stable Audio |

**Notes:**
- Generation time scales with resolution/frame count
- Turbo variants achieve similar quality with fewer steps
```

**Important:** Do not fabricate benchmark numbers. Only include metrics you have personally verified or can cite from published sources.

### 6. Key Parameters Table

| Parameter | Default | Description |
|-----------|---------|-------------|
| `height` | Model-specific | Output height (multiples of 16/32) |
| `width` | Model-specific | Output width (multiples of 16/32) |
| `num_inference_steps` | 28-100 | Denoising/diffusion steps |
| `guidance_scale` | 1.0-7.5 | Classifier-free guidance scale |
| `negative_prompt` | None | Text describing unwanted features |
| `num_outputs_per_prompt` | 1 | Number of outputs per prompt |
| `num_frames` | 81 | Video: number of frames |
| `audio_end_in_s` | 10.0 | Audio: duration in seconds |

### 7. Accuracy Comparison ⚪

**Optional: Include only if you have verified measurements from actual testing.**

Compare against Diffusers baseline:

```markdown
## Accuracy Comparison

### vs Diffusers

| Metric | Diffusers | vLLM-Omni | Notes |
|--------|-----------|-----------|-------|
| FID Score | 12.5 | 12.5 | Identical |
| CLIP Score | 0.82 | 0.82 | Identical |
| Generation Time | 4.2s | 1.1s | 3.8x faster |

### Known Differences
- [List any numerical differences]
- [Note any vLLM-Omni specific optimizations]
```

**Important:** Do not fabricate accuracy metrics. Only include metrics you have personally verified or can cite from published sources.

## Optional Sections

### Cache-DiT Acceleration

Include when model supports caching (most DiT models):

```python
omni = Omni(
    model="org/model-name",
    cache_backend="cache_dit",
)

# Or with custom config
omni = Omni(
    model="org/model-name",
    cache_backend="cache_dit",
    cache_config={
        "Fn_compute_blocks": 8,
        "Bn_compute_blocks": 0,
        "max_warmup_steps": 4,
        "residual_diff_threshold": 0.12,
    },
)
```

### Online Serving

Some models support OpenAI-compatible serving:

```bash
vllm serve org/model-name --omni
```

**Client usage:**
```python
import base64
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")

response = client.chat.completions.create(
    model="org/model-name",
    messages=[{"role": "user", "content": "A beautiful landscape"}],
)

# Extract base64 image from response
image_url = response.choices[0].message.content[0].image_url.url
image_data = base64.b64decode(image_url.split(",")[1])
```

### Limitations

Include when model has known constraints:
- Maximum output duration/resolution
- Language limitations
- Quality trade-offs
- License restrictions

## CLI Script Pattern

vLLM-Omni recipes often reference CLI scripts from the repo:

```markdown
The CLI examples below are from the vLLM-Omni repo. Clone the repo and run:

```bash
python examples/offline_inference/text_to_image/text_to_image.py \
  --model org/model-name \
  --prompt "your prompt" \
  --output output.png
```
```

> **Note:** When writing a recipe, use proper markdown code blocks without escaping.

## File Naming

Same convention as vLLM recipes:
- Directory: `{OrgName}/`
- File: `{ModelName}.md`
- Use underscores for versions: `Wan2_2.md` or `Wan2.2.md` (both seen in repo)

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Missing vllm-omni install | Add `uv pip install git+https://github.com/vllm-project/vllm-omni.git` |
| Forgetting modality dependencies | Add `soundfile` for audio, `diffusers` for video |
| Wrong Omni import | Use `from vllm_omni.entrypoints.omni import Omni` |
| No deployment strategy | Include hardware recommendations and workload guidance |
| No accuracy comparison | Compare FID/CLIP scores vs Diffusers |
| Missing any-to-any support | Document cross-modal capabilities if applicable |

## Checklist

- [ ] Title follows `# ModelName Usage Guide` format
- [ ] HuggingFace link in introduction
- [ ] Architecture description (DiT, AR+Diffusion, MoE)
- [ ] Supported models list
- [ ] Installing vLLM-Omni with version variable (`$VLLM_VERSION`)
- [ ] Modality-specific dependencies
- [ ] Python API example for supported modalities
- [ ] CLI example (if scripts exist in vllm-omni repo)
- [ ] **Recommended deployment strategy by hardware/workload**
- [ ] Key parameters table
- [ ] Expected performance metrics (optional - only if verified measurements available)
- [ ] Accuracy comparison vs Diffusers (optional - only if verified measurements available)
- [ ] Online serving section (if supported)
- [ ] Cache-DiT acceleration section (if applicable)
- [ ] File named correctly
- [ ] README.md updated with new entry

## Related Skills

- **vllm-omni-contrib**: Contributing new models and development workflow to vLLM-Omni
- For standard LLM/vLLM recipes (autoregressive models), refer to the [vLLM recipes repository](https://github.com/vllm-project/recipes) for examples
