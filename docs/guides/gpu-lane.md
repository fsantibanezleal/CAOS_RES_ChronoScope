# The GPU lane

The offline pipeline trains the deep forecasting ladder and runs the foundation models. When a CUDA GPU is
present it uses it; everywhere else (CI, a CPU-only clone) it falls back to CPU transparently. Code:
[`chronoscopelab/gpu.py`](../../data-pipeline/chronoscopelab/gpu.py) · Tests:
[`tests/test_gpu.py`](../../tests/test_gpu.py).

## The build box

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 4070 Laptop |
| VRAM | ~8.5 GB |
| Driver | 560.94 (supports CUDA 12.6) |
| torch | `2.12.1+cu126` |

The 8 GB VRAM budget shapes the ladder: the small deep models (NHITS, DLinear, NLinear, TSMixer, PatchTST)
train comfortably; the foundation models run **zero-shot** (no training); full fine-tuning of a 200M-parameter
model is out of budget (LoRA/few-shot only, where it is used at all).

## Installing the CUDA build (verified 2026-07-04)

The driver (560.94) supports CUDA 12.6, so the **cu126** wheel is the correct one. It was verified to exist
for our exact torch version (`torch==2.12.1+cu126`; the cu128 index tops out at 2.11.0):

```
pip install torch==2.12.1+cu126 --index-url https://download.pytorch.org/whl/cu126
```

`pip` treats the plain `2.12.1` and the `+cpu` local version as already-satisfied, so swapping the CPU wheel
for the CUDA one needs an explicit build tag (and `--force-reinstall` if a CPU wheel is already present).

**CPU-only environments** (CI, a clone without a GPU) install plain `pip install torch==2.12.1` (or nothing):
`chronoscopelab.gpu` reports no CUDA device and every engine falls back to CPU. Nothing in the core imports
torch at module load, so the light precompute stays importable without it.

## Using it

```python
from chronoscopelab import gpu

gpu.device()        # "cuda" when available, else "cpu"
gpu.cuda_available() # bool
gpu.gpu_info()      # GpuInfo(available, device, name, total_vram_gb, torch_version)
gpu.summary()       # "GPU: NVIDIA GeForce RTX 4070 Laptop GPU (8.59 GB VRAM), torch 2.12.1+cu126"
```

The deep engine (`engines/neural_engine.py`) and the foundation engines call `gpu.device()` and move their
tensors accordingly; the pipeline logs `gpu.summary()` at startup so the device used for a bake is on record.

## Honesty

CI cannot run a GPU or load multi-GB checkpoints, so the deep/foundation engines skip gracefully there and the
unit tests exercise only the shapes and the CPU fallback. The **full foundation-ladder bake happens offline on
this box** and is committed as artifacts (the existing deploy-pages pattern: the site builds over the committed
foundation-baked artifacts, never regenerating them in CI). The device used for each bake is recorded so the
provenance of a baked forecast is auditable.
