# TiRex-2 WSL2 lane — setup + how it works

TiRex-2 (NX-AI, streaming-native xLSTM) is the atlas's 19th method. It cannot run on native Windows: its
`flashrnn` dependency needs `triton` and fused sLSTM CUDA kernels compiled by `nvcc`, and none ship Windows
wheels. So TiRex-2 runs in a WSL2 (Linux) venv with CUDA-in-WSL, and the Windows pipeline invokes it per
case and merges the result as a foundation method. The lane is **opt-in** and degrades gracefully, so CI and
the default bake never depend on WSL.

## One-time setup (the build box)

```powershell
# 1. WSL2 Ubuntu (reversible: wsl --unregister Ubuntu-24.04). GPU passthrough comes from the Windows
#    NVIDIA driver automatically (/dev/dxg); no CUDA driver install inside WSL.
wsl --install -d Ubuntu-24.04 --no-launch
```
```bash
# 2. In the distro, as root:
apt-get update && apt-get install -y python3-venv python3-pip build-essential nvidia-cuda-toolkit
python3 -m venv /root/tirex-venv
/root/tirex-venv/bin/pip install --upgrade pip
/root/tirex-venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cu124
/root/tirex-venv/bin/pip install numpy preqts git+https://github.com/NX-AI/tirex-2.git
# 3. The gated checkpoint: TiRex-2 is a gated HF repo. Put a token with access at /root/.hf_token
printf '%s' 'hf_xxx' > /root/.hf_token   # from credentials/providers/huggingface (the vault)
```

Verify:
```bash
env CUDA_HOME=/usr PATH=/usr/bin:/bin:/root/tirex-venv/bin /root/tirex-venv/bin/python - <<'PY'
import os, torch; os.environ["HF_TOKEN"]=open("/root/.hf_token").read().strip()
from tirex2 import load_model, TimeseriesType
m = load_model("NX-AI/TiRex-2", device="cuda")
import numpy as np
ts = TimeseriesType(torch.tensor(np.arange(256, dtype="float32")), None, None)
print(m.forecast(timeseries=[ts], prediction_length=24, output_type="numpy")[0].shape)  # (9, 24)
PY
```
The first run compiles the sLSTM kernels (~25 s, cached under `/root/.cache/torch_extensions`); later runs
are a few seconds.

## Baking with TiRex-2

```powershell
# from the repo, with the pipeline venv:
$env:CHRONOSCOPE_ENABLE_TIREX_WSL = "1"
# (plus the usual GPU/foundation gates for the full ladder)
python -m chronoscopelab.pipeline           # all cases gain TiRex-2 as the 19th method
```

Env knobs: `CHRONOSCOPE_ENABLE_TIREX_WSL` (on/off), `CHRONOSCOPE_TIREX_WSL_DISTRO` (default `Ubuntu-24.04`),
`CHRONOSCOPE_TIREX_WSL_PYTHON` (default `/root/tirex-venv/bin/python`).

## How it works

- `engines/tirex2_wsl_engine.py` (Windows): for each case it writes the `SeriesSpec` (y, m, horizon,
  quantile levels, the foundation `max_windows=2` budget) to a temp JSON, invokes
  `env CUDA_HOME=/usr PATH=... TORCH_EXTENSIONS_DIR=... python tools/tirex2_wsl/tirex2_bake.py in out` in
  WSL, and reads back the method + backtest. One WSL call per case (the model loads once inside that call).
- `tools/tirex2_wsl/tirex2_bake.py` (WSL): loads TiRex-2 once, wraps its forecast in a `preqts.ReplayAdapter`,
  and runs `preqts.run_prequential` with the SAME warmup/step formula as `stages/evaluate.py`, so
  MASE/WQL/coverage/MSIS/per-horizon are identical to the rest of the ladder; it also emits the display
  forecast (point + 10/90 interval) on the full history.
- `pipeline.precompute` calls `tirex2_wsl_engine.merge_into(...)` after `evaluate`, appending TiRex-2 to the
  trace + metrics and re-picking `best_method` honestly.

## Honesty + reversibility

- Opt-in: the flag off (or WSL absent) is a no-op; the committed artifact stays valid and the ladder-
  completeness drift gate (`>= 15` methods) passes either way (18 native, 19 with TiRex-2).
- The committed canonical bake is produced WITH the lane (19 methods), exactly like the other GPU/foundation
  tiers that CI cannot reproduce; CI verifies consistency + completeness, not re-execution.
- Reversible: `wsl --unregister Ubuntu-24.04` removes the distro; nothing on the Windows side changes
  behaviour unless the flag is set.
