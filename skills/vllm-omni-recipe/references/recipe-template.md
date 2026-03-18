# Recipe Template Reference

This document provides detailed templates and code examples for creating vLLM-Omni recipes.

## Recipe Structure

Every recipe follows this structure. Sections marked ⚪ are optional.

```markdown
# ModelName Usage Guide

[Introduction with HuggingFace link, architecture description, key capabilities]

## Supported Models
[Model variants and sizes]

## Installing vLLM-Omni
[Pip install instructions with version variable]

## [Modality] Generation
[Text-to-Image/Video/Audio/Any-to-Any examples - Python + CLI]

## Recommended Deployment Strategy
[Hardware recommendations by model size and workload]

## Key Parameters
[Parameter table for generation config]

## Expected Performance ⚪
[Generation time, throughput metrics - only if verified measurements available]

## Accuracy Comparison ⚪
[vs Diffusers/HF metrics - only if verified measurements available]

## Online Serving ⚪
[vllm serve --omni and OpenAI client examples]

## Cache-DiT Acceleration ⚪
[Optional: caching configuration for speedup]

## Additional Resources
[Model card, examples, related links]
```

## Section Templates

### Introduction

```markdown
[ModelName](https://huggingface.co/org/model-name) is a [architecture type] model for [modality] generation.

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

### Installing vLLM-Omni

```bash
# Set version variables (check vllm-omni quickstart for current versions)
export VLLM_VERSION="0.16.0"

uv venv
source .venv/bin/activate
uv pip install vllm==$VLLM_VERSION
uv pip install git+https://github.com/vllm-project/vllm-omni.git
```

Modality-specific dependencies:
| Modality | Additional Dependencies |
|----------|------------------------|
| Image | `pillow`, `diffusers` (for CLI scripts) |
| Video | `diffusers` (for `export_to_video`) |
| Audio | `soundfile` or `scipy` |

## Code Examples

### Text-to-Image

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

### Text-to-Video

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

### Text-to-Audio

```python
audio = omni.generate(
    "The sound of a dog barking",
    negative_prompt="Low quality.",
    guidance_scale=7.0,
    num_inference_steps=100,
    extra={"audio_start_in_s": 0.0, "audio_end_in_s": 10.0},
)
```

### Image-to-Video/Image-to-Image

```python
import PIL.Image
image = PIL.Image.open("input.jpg").convert("RGB")
frames = omni.generate(
    "A cat playing with yarn",
    pil_image=image,
    # ... other params
)
```

### Any-to-Any

```python
# Models that support cross-modal generation (e.g., text+image -> audio+video)
omni = Omni(model="org/any-to-any-model")

# Generate multiple output modalities from mixed input
# Assumes 'image' is loaded as shown in the Image-to-Video/Image-to-Image example above
outputs = omni.generate(
    prompt="Describe this scene and generate matching audio",
    pil_image=image,  # Optional: image input
    # Model handles cross-modal generation
)
```

## Deployment Strategy Template

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

## Key Parameters

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

## Performance & Accuracy (Optional)

**Only include if you have verified measurements from actual testing.**

### Expected Performance

```markdown
## Expected Performance

Performance measured on [GPU type]:

| Configuration | Generation Time | Memory | Notes |
|---------------|-----------------|--------|-------|
| [res/frames/duration], [N] steps | [X.Xs] | [XGB] | [variant] |

**Notes:**
- Generation time scales with resolution/frame count
- Turbo variants achieve similar quality with fewer steps
```

### Accuracy Comparison

```markdown
## Accuracy Comparison

### vs Diffusers

| Metric | Diffusers | vLLM-Omni | Notes |
|--------|-----------|-----------|-------|
| FID Score | [value] | [value] | [identical / delta] |
| CLIP Score | [value] | [value] | [identical / delta] |
| Generation Time | [Xs] | [Xs] | [Nx faster/slower] |

### Known Differences
- [List any numerical differences]
- [Note any vLLM-Omni specific optimizations]
```

**Important:** Do not fabricate benchmark numbers. Only include metrics you have personally verified or can cite from published sources.

## Optional Sections

### Cache-DiT Acceleration

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

````markdown
The CLI examples below are from the vLLM-Omni repo. Clone the repo and run:

```bash
python examples/offline_inference/text_to_image/text_to_image.py \
  --model org/model-name \
  --prompt "your prompt" \
  --output output.png
```
````

> **Note:** When writing a recipe, use proper markdown code blocks without escaping.
