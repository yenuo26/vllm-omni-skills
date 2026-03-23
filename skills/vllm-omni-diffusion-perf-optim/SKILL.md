---
name: vllm-omni-diffusion-perf-optim
description: Guide for achieving optimal inference performance with vLLM-Omni diffusion models. Covers all lossless and lossy optimization methods (parallelism, torch.compile, CPU offload, quantization, cache acceleration), per-model support tables, and ready-to-use recipes. Use when asked to speed up diffusion inference, reduce latency, lower VRAM usage, or tune a diffusion pipeline.
---

# vLLM-Omni Diffusion: Optimal Performance Guide

Use this guide when a user asks how to speed up diffusion inference, reduce latency, lower VRAM, or tune a diffusion pipeline in vLLM-Omni.

> **This skill is designed to stay up to date.** Instead of hardcoding model support
> tables, it tells you *where to look* in the codebase to discover current capabilities.
> See [Discovering Current Capabilities](#discovering-current-capabilities) and
> [Extending This Skill](#extending-this-skill) at the end.

## Step 0: Understand the Baseline

Before optimizing, establish a baseline:

1. **Identify the model** and its pipeline class (check `model_index.json` → `_class_name`)
2. **Run a baseline** with `--enforce-eager` (disables torch.compile) and no parallelism
3. **Record**: server inference time, e2e latency, VRAM usage, output quality

**Online serving** (preferred — measures real deployment latency):

```bash
# Start server
vllm serve <MODEL> --omni --port 8098 --enforce-eager

# Send request and measure e2e time
time curl -sS -X POST http://localhost:8098/v1/videos \
  -F "prompt=..." -F "width=768" -F "height=480" \
  -F "num_frames=41" -F "num_inference_steps=20" -F "seed=42"

# Poll until completed, record inference_time_s from status response
curl -sS http://localhost:8098/v1/videos/<VIDEO_ID> | jq '.inference_time_s'
```

**Offline inference** (useful for quick iteration):

```bash
python examples/offline_inference/text_to_video/text_to_video.py \
  --model <MODEL> --enforce-eager --prompt "..." --output baseline.mp4
```

> **Important**: Always report online serving numbers for deployment decisions.
> Offline benchmarks may differ due to process startup, torch.compile warmup,
> and measurement methodology.

## Step 1: Apply Lossless Optimizations

These do **not** affect output quality. Apply in order of impact.

### 1.1 torch.compile (Regional Compilation)

**What**: Compiles repeated DiT transformer blocks via `torch.compile(dynamic=True)`. Fuses ops, reduces kernel launch overhead.

**How**: Enabled by **default**. Use `--enforce-eager` to disable.

**Speedup**: Model- and GPU-dependent. May provide 1.1–1.5× on the denoising loop, but on some GPU architectures (e.g., H800) and models, warm-request latency may match eager.

**Requirements**: Model transformer must define `_repeated_blocks` attribute. First request pays compilation overhead (~5–15s extra).

**Online serving note**: The first request after server start incurs compilation warmup. Subsequent requests run at compiled speed. For latency-sensitive deployments, consider `--enforce-eager` to avoid first-request penalty, especially if compile does not measurably improve warm latency for your model/GPU.

**Config**: `OmniDiffusionConfig.enforce_eager` (default `False` = compile enabled).

**Source**: `vllm_omni/diffusion/compile.py`, `vllm_omni/diffusion/worker/diffusion_model_runner.py`

### 1.2 Multi-GPU Parallelism

All configured via `DiffusionParallelConfig`. Check `docs/user_guide/diffusion/parallelism_acceleration.md` for the per-model support table before enabling.

#### Sequence Parallelism (Ulysses-SP)

**What**: Splits sequence tokens across GPUs using all-to-all communication (DeepSpeed Ulysses).

**How**: `--ulysses-degree N` (offline) or `--usp N` (online serving)

**Speedup**: Near-linear scaling. Best for long-sequence models (video, high-res image).

```python
from vllm_omni.diffusion.data import DiffusionParallelConfig
parallel_config = DiffusionParallelConfig(ulysses_degree=2)
omni = Omni(model="...", parallel_config=parallel_config)
```

#### Ring Attention

**What**: Ring-based P2P communication for attention across GPUs.

**How**: `--ring-degree N` (offline) or `--ring N` (online serving)

**Note**: Can combine with Ulysses: `ulysses_degree × ring_degree = total SP GPUs`.

#### CFG Parallel

**What**: Runs positive/negative CFG branches on separate GPUs. Only rank 0 computes scheduler step.

**How**: `--cfg-parallel-size 2`

**Speedup**: ~2× on models using classifier-free guidance.

**Constraint**: Requires exactly 2 GPUs. Only for models that use CFG.

```bash
# 4-GPU: CFG parallel (2) × Ulysses (2)
python text_to_image.py --model Qwen/Qwen-Image \
  --cfg-parallel-size 2 --ulysses-degree 2
```

#### Tensor Parallelism (TP)

**What**: Shards DiT linear layers across GPUs using `ColumnParallelLinear`, `RowParallelLinear`, `QKVParallelLinear`.

**How**: `--tensor-parallel-size N`

**Note**: Only DiT blocks are sharded — text encoder is replicated on all ranks (extra VRAM per GPU). See [Issue #771](https://github.com/vllm-project/vllm-omni/issues/771).

#### VAE Patch Parallelism

**What**: Shards VAE decode spatially across ranks using tiling.

**How**: `--vae-patch-parallel-size N`

**Constraint**: Auto-enables `--vae-use-tiling`.

#### HSDP (Hybrid Sharded Data Parallel)

**What**: Shards model weights across GPUs using PyTorch FSDP2. Reduces per-GPU VRAM.

**How**: Via `DiffusionParallelConfig(use_hsdp=True)`. Requires multi-GPU.

#### Expert Parallel

**What**: Shards MoE experts across devices with all-to-all token routing.

**How**: `--enable-expert-parallel`

**Constraint**: Only for MoE models (e.g., HunyuanImage3.0).

### 1.3 CPU Offload

Two mutually exclusive strategies. Both single-GPU only.

#### Model-level (Sequential) Offload

**What**: Swaps DiT ↔ encoders on GPU. Only one group is on GPU at a time.

**How**: `--enable-cpu-offload` or `Omni(enable_cpu_offload=True)`

**Tradeoff**: Adds H2D transfer latency between encoder and denoising phases.

#### Layerwise (Blockwise) Offload

**What**: Keeps only 1 transformer block on GPU at a time. Async prefetch via separate CUDA stream.

**How**: `--enable-layerwise-offload` or `Omni(enable_layerwise_offload=True)`

**Best for**: Large video models (Wan A14B) where per-block compute >> H2D transfer → nearly zero-cost offload.

**Requirement**: Model DiT must define `_layerwise_offload_blocks_attr`.

**VRAM savings**: Dramatic (e.g., 40+ GB → ~11 GB for Wan A14B).

### 1.4 VAE Memory Optimizations

- `--vae-use-slicing`: Process VAE in slices (saves VRAM).
- `--vae-use-tiling`: Process VAE in tiles (saves VRAM, enables patch parallel).

Both are boolean flags. Use when OOM during VAE decode.

### 1.5 Quantization

#### FP8 (W8A8)

**What**: Online quantization of DiT linear layers to FP8.

**How**: `--quantization fp8`

**Requirements**: Ada/Hopper GPU (SM89+). Native hardware FP8.

**VRAM**: ~50% reduction on DiT weights. **Speedup**: 1.3–1.5×.

```bash
python text_to_image.py --model Qwen/Qwen-Image --quantization fp8
```

**Layer skipping**: `--ignored-layers 'add_kv_proj,to_add_out'` to exclude specific layers from quantization.

#### GGUF (Pre-quantized)

**What**: Loads pre-quantized GGUF weights for transformer.

**How**: `--quantization gguf --gguf-model <path-or-hf-id>`

**Source**: `docs/user_guide/diffusion/quantization/gguf.md`

## Step 2: Apply Lossy Optimizations (Optional)

These trade quality for speed. Always compare output quality against baseline.

### 2.1 TeaCache

**What**: Caches transformer computations when consecutive timesteps are similar. Skips redundant forward passes.

**Speedup**: 1.5–2.0× depending on `rel_l1_thresh`.

**How**:
```python
omni = Omni(
    model="Qwen/Qwen-Image",
    cache_backend="tea_cache",
    cache_config={"rel_l1_thresh": 0.2},
)
```

**CLI**: `--cache-backend tea_cache`

**Online**: `vllm serve <MODEL> --omni --cache-backend tea_cache --cache-config '{"rel_l1_thresh": 0.2}'`

**Quality tuning**:
- `0.1–0.2`: minimal quality loss (~1.5× speedup)
- `0.4`: slight quality loss (~1.8× speedup)
- `0.6–0.8`: noticeable quality loss (~2.0–2.25× speedup)

**Supported models**: Qwen-Image family, BAGEL. See `docs/user_guide/diffusion/teacache.md`.

### 2.2 Cache-DiT (DBCache + TaylorSeer + SCM)

**What**: Hybrid caching with three sub-methods:
- **DBCache**: Caches intermediate block outputs when residuals are small
- **TaylorSeer**: Taylor expansion to forecast future hidden states
- **SCM**: Step Computation Masking — selectively skip entire denoising steps

**Speedup**: 1.5–2.5× depending on configuration.

**How**:
```python
omni = Omni(
    model="Qwen/Qwen-Image",
    cache_backend="cache_dit",
    cache_config={
        # DBCache
        "Fn_compute_blocks": 1,
        "Bn_compute_blocks": 0,
        "max_warmup_steps": 4,
        "residual_diff_threshold": 0.24,
        "max_continuous_cached_steps": 3,
        # TaylorSeer (optional)
        "enable_taylorseer": False,
        "taylorseer_order": 1,
        # SCM (optional)
        "scm_steps_mask_policy": None,  # "slow"/"medium"/"fast"/"ultra"
        "scm_steps_policy": "dynamic",
    },
)
```

**CLI**: `--cache-backend cache_dit`

**Excluded models**: `NextStep11Pipeline`, `StableDiffusionPipeline` (see `_NO_CACHE_ACCELERATION` in `registry.py`).

**Source**: `docs/user_guide/diffusion/cache_dit_acceleration.md`

### 2.3 Fewer Inference Steps

Reducing `--num-inference-steps` gives linear speedup but affects quality. Typical ranges:
- Image models: 20–50 steps
- Video models: 20–40 steps
- Distilled models: 4–8 steps

## Discovering Current Capabilities

The tables below may become stale as new models and methods are added.
**Always verify against the live codebase** using these source-of-truth files:

### Parallelism support per model

Read the canonical table in `docs/user_guide/diffusion/parallelism_acceleration.md`.
It lists every model with ✅/❌ for each parallelism method (Ulysses-SP, Ring, CFG, TP, VAE-Patch, Expert, HSDP).

To check programmatically whether a specific model supports a method:

| Check | How |
|-------|-----|
| **Ulysses / Ring SP** | Transformer class defines `_sp_plan`. Search: `grep -r '_sp_plan' vllm_omni/diffusion/models/` |
| **CFG Parallel** | Pipeline or transformer inherits `CFGParallelMixin`. Search: `grep -r 'CFGParallelMixin' vllm_omni/diffusion/models/` |
| **TP** | Transformer uses `ColumnParallelLinear` / `RowParallelLinear` / `QKVParallelLinear`. Search: `grep -r 'ParallelLinear\|QKVParallel' vllm_omni/diffusion/models/<model>/` |
| **Layerwise offload** | Pipeline defines `_layerwise_offload_blocks_attr`. Search: `grep -r '_layerwise_offload_blocks_attr' vllm_omni/diffusion/models/` |
| **torch.compile** | Transformer defines `_repeated_blocks`. Search: `grep -r '_repeated_blocks' vllm_omni/diffusion/models/` |
| **HSDP** | Check `DiffusionParallelConfig` usage in docs and tests. |

### Cache acceleration support

- **Excluded models**: listed in `_NO_CACHE_ACCELERATION` in `vllm_omni/diffusion/registry.py`. Any pipeline class in that set does **not** support `tea_cache` or `cache_dit`.
- **TeaCache supported models**: check `docs/user_guide/diffusion/teacache.md` for the current list.
- **Cache-DiT**: all DiT-based models not in `_NO_CACHE_ACCELERATION`. See `docs/user_guide/diffusion/cache_dit_acceleration.md`.

### Quantization support

- **Available methods**: listed in `vllm_omni/diffusion/quantization/`. Each `.py` file is a method (e.g., `fp8.py`, `gguf.py`).
- **Config**: `OmniDiffusionConfig.quantization` field in `vllm_omni/diffusion/data.py`.
- **Docs**: `docs/user_guide/diffusion/quantization/`

### Available CLI flags (online serving)

Run `vllm serve --help` and look for `--omni`-related flags. Key flags:
`--usp`, `--ring`, `--cfg-parallel-size`, `--tensor-parallel-size`, `--vae-patch-parallel-size`,
`--cache-backend`, `--quantization`, `--enforce-eager`, `--enable-cpu-offload`,
`--enable-layerwise-offload`, `--vae-use-slicing`, `--vae-use-tiling`, `--use-hsdp`,
`--enable-expert-parallel`, `--flow-shift`, `--boundary-ratio`.

## Quick Recipes

Recipes show both **online serving** (preferred for deployment) and **offline** variants.

### Recipe A: Single GPU, lossless (Image model — online)

```bash
# Server
vllm serve Qwen/Qwen-Image --omni --port 8098 --quantization fp8

# Client
curl -X POST http://localhost:8098/v1/images/generations \
  -F "prompt=A futuristic city at sunset" -F "seed=42"
```

### Recipe B: Multi-GPU, lossless (Image model, 4 GPUs — online)

```bash
vllm serve Qwen/Qwen-Image --omni --port 8098 \
  --cfg-parallel-size 2 --usp 2 --quantization fp8
```

### Recipe C: Low VRAM, single GPU (Video model — online)

```bash
vllm serve Wan-AI/Wan2.2-T2V-A14B-Diffusers --omni --port 8098 \
  --enable-layerwise-offload --vae-use-slicing --vae-use-tiling
```

### Recipe D: Multi-GPU, lossless (Video model, 8 GPUs — online)

```bash
vllm serve Wan-AI/Wan2.2-T2V-A14B-Diffusers --omni --port 8098 \
  --usp 4 --ring 2 --vae-patch-parallel-size 8 --quantization fp8
```

### Recipe E: Lossy speedup with Cache-DiT (Image model — online)

```bash
vllm serve Qwen/Qwen-Image --omni --port 8098 \
  --enforce-eager --cache-backend cache_dit
```

### Recipe F: LTX-2 video baseline (online)

```bash
vllm serve Lightricks/LTX-2 --omni --port 8098 \
  --enforce-eager --flow-shift 1.0 --boundary-ratio 1.0
```

### Recipe G: LTX-2 video with Cache-DiT (~1.4× speedup, online)

```bash
vllm serve Lightricks/LTX-2 --omni --port 8098 \
  --enforce-eager --flow-shift 1.0 --boundary-ratio 1.0 \
  --cache-backend cache_dit
```

### Offline equivalents

For quick local testing, replace `vllm serve ... --omni` with the offline scripts:

```bash
# Image
python examples/offline_inference/text_to_image/text_to_image.py \
  --model Qwen/Qwen-Image --prompt "..." --quantization fp8

# Video
python examples/offline_inference/text_to_video/text_to_video.py \
  --model Lightricks/LTX-2 --prompt "..." --enforce-eager
```

## Decision Flowchart

```
Is output quality paramount?
├── YES → Use only Step 1 (lossless)
│   ├── Single GPU? → torch.compile (default) + FP8 quantization
│   ├── Multi-GPU? → Add SP/TP/CFG parallel (check support table)
│   └── OOM? → Enable CPU offload or VAE slicing/tiling
└── NO → Also apply Step 2 (lossy)
    ├── TeaCache supported? → Use tea_cache with rel_l1_thresh=0.2
    └── DiT model? → Use cache_dit with defaults
```

## Tips

- **Benchmark in online serving mode** for deployment decisions. Offline numbers may differ due to process startup and measurement methodology.
- **Use `--enforce-eager`** unless torch.compile measurably improves warm-request latency for your model/GPU. This avoids first-request compilation overhead.
- **CFG parallel + Ulysses is usually better** than pure Ulysses at the same GPU count for CFG models.
- **Layerwise offload is nearly free for video models** where per-block compute dwarfs H2D transfer time.
- **Combine lossless + lossy**: e.g., FP8 + Cache-DiT for maximum throughput.
- **Check `_NO_CACHE_ACCELERATION`** in `registry.py` before enabling cache backends — UNet-based and some specialized models don't support them.
- **Send multiple requests** when benchmarking online serving to measure warm (steady-state) latency rather than first-request startup.

## Key Source Files

| File | What |
|------|------|
| `vllm_omni/diffusion/data.py` | `OmniDiffusionConfig`, `DiffusionParallelConfig`, `DiffusionCacheConfig` |
| `vllm_omni/diffusion/compile.py` | Regional torch.compile logic |
| `vllm_omni/diffusion/registry.py` | `_NO_CACHE_ACCELERATION`, model registry |
| `vllm_omni/diffusion/distributed/cfg_parallel.py` | CFGParallelMixin |
| `vllm_omni/diffusion/cache/` | TeaCache and CacheDiT backends |
| `vllm_omni/diffusion/offloader/` | CPU offload backends |
| `vllm_omni/diffusion/quantization/` | Quantization backends (fp8, gguf, ...) |
| `docs/user_guide/diffusion/` | All user-facing docs |
| `docs/user_guide/diffusion/parallelism_acceleration.md` | Canonical parallelism support table |

## Extending This Skill

When a **new optimization method** is added to vLLM-Omni, update this skill as follows:

### Adding a new lossless method

1. Add a subsection under **Step 1** with: What / How / Speedup / Requirements / Source.
2. Update the **Discovering Current Capabilities** section with a "How to check" row
   (e.g., what attribute or class to grep for to confirm model support).
3. Add a recipe under **Quick Recipes** if the method is broadly useful.
4. Update the **Decision Flowchart** if the method creates a new decision branch.
5. Add the key source file to the **Key Source Files** table.

### Adding a new lossy method

1. Add a subsection under **Step 2** with: What / How / Speedup / Quality impact / Config.
2. Note which models are excluded (if any) and where exclusion is tracked in code
   (e.g., a set in `registry.py`).
3. Update the **Decision Flowchart**.

### Adding a new quantization method

1. Add under **Step 1 → 1.5 Quantization** with: What / How / Requirements / VRAM savings.
2. Note the source file in `vllm_omni/diffusion/quantization/`.

### Adding a new parallelism method

1. Add under **Step 1 → 1.2 Multi-GPU Parallelism** with: What / How / Constraint / CLI flag.
2. Add a grep instruction to the **Discovering Current Capabilities** table
   (e.g., "Transformer defines `_new_attr`").
3. Update `docs/user_guide/diffusion/parallelism_acceleration.md` with the
   new column in the support table.

### General guidelines

- Prefer **"check the code" instructions** over static tables. Tables go stale;
  grep commands don't.
- Always include the **CLI flag** for both offline (`--flag-name`) and online
  serving (`--flag-name` via `vllm serve`). Online serving flags sometimes differ
  (e.g., `--ulysses-degree` offline vs `--usp` online).
- Include a **Source** pointer so developers can find the implementation.
- After updating the skill, test it by asking the agent to optimize a model
  and verify it discovers the new method correctly.
