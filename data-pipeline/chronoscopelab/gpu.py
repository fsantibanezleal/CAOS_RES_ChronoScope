"""GPU device selection with a safe CPU fallback (the offline lane runs on any box, GPU-accelerated or not).

The offline pipeline trains the deep ladder and runs the foundation models. On a machine with a CUDA GPU
(the build box: RTX 4070 Laptop, 8 GB, CUDA 12.6, torch cu126 wheel) these use the GPU; anywhere else
(CI, a CPU-only clone) they fall back to CPU transparently. Nothing here imports torch at module load, so
the core precompute stays importable without the heavy dep.

The 8 GB VRAM budget shapes the engines (small deep models train comfortably; foundation models run
zero-shot; full fine-tuning of a 200M model is out of budget). See docs/guides/gpu-lane.md.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GpuInfo:
    """A snapshot of the compute device the offline lane will use."""

    available: bool
    device: str                  # "cuda" or "cpu"
    name: str                    # GPU name, or "CPU"
    total_vram_gb: float | None  # total VRAM in GB, or None on CPU
    torch_version: str | None    # the installed torch build string, or None if torch is absent


def _torch():
    """Import torch lazily; return the module or None if it is not installed."""
    try:
        import torch
        return torch
    except Exception:
        return None


def cuda_available() -> bool:
    """True iff torch is installed AND a CUDA device is visible."""
    t = _torch()
    return bool(t is not None and t.cuda.is_available())


def device(prefer_gpu: bool = True) -> str:
    """The device string to use: 'cuda' when available and preferred, else 'cpu'."""
    if prefer_gpu and cuda_available():
        return "cuda"
    return "cpu"


def gpu_info() -> GpuInfo:
    """Describe the selected compute device (safe to call without torch or a GPU)."""
    t = _torch()
    if t is None:
        return GpuInfo(available=False, device="cpu", name="CPU", total_vram_gb=None, torch_version=None)
    if t.cuda.is_available():
        props = t.cuda.get_device_properties(0)
        return GpuInfo(
            available=True, device="cuda", name=props.name,
            total_vram_gb=round(props.total_memory / 1e9, 2), torch_version=t.__version__,
        )
    return GpuInfo(available=False, device="cpu", name="CPU", total_vram_gb=None, torch_version=t.__version__)


def summary() -> str:
    """A one-line human-readable device summary (for the pipeline log)."""
    info = gpu_info()
    if info.available:
        return f"GPU: {info.name} ({info.total_vram_gb} GB VRAM), torch {info.torch_version}"
    tv = f", torch {info.torch_version}" if info.torch_version else " (torch not installed)"
    return f"CPU (no CUDA device){tv}"
