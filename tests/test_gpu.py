"""GPU helper tests: the device selector works with or without a GPU (CI has none), never raising."""
from chronoscopelab import gpu


def test_device_is_cuda_or_cpu():
    d = gpu.device()
    assert d in ("cuda", "cpu")


def test_prefer_gpu_false_is_always_cpu():
    assert gpu.device(prefer_gpu=False) == "cpu"


def test_gpu_info_is_consistent():
    info = gpu.gpu_info()
    if info.available:
        assert info.device == "cuda"
        assert info.name and info.name != "CPU"
        assert info.total_vram_gb and info.total_vram_gb > 0
    else:
        assert info.device == "cpu"
        assert info.total_vram_gb is None


def test_cuda_available_matches_device():
    # if CUDA is reported available, device() must pick it; if not, it must be cpu
    assert (gpu.device() == "cuda") == gpu.cuda_available()


def test_summary_is_a_nonempty_string():
    s = gpu.summary()
    assert isinstance(s, str) and len(s) > 0
    assert "GPU:" in s or "CPU" in s
