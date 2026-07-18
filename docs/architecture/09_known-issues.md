# Known issues

## Deep-tier baking on Windows: numba + CUDA + the D: drive (WinError 6714)

**Symptom.** Running the FULL offline pipeline with the deep tier enabled (`CHRONOSCOPE_ENABLE_NEURAL=1`) on
the Windows build box raises `OSError: [WinError 6714]` ("the transaction context associated with the thread
is not valid") when the pipeline tries to write a baked artifact to the `D:` working drive.

**Root cause (diagnosed 2026-07-04).** When **numba** (pulled in by statsforecast) and **CUDA** (torch) both
initialize in the **same process** on this machine, the `D:` drive enters a transactional-NTFS state that
breaks subsequent `pathlib`/`os` file operations on it (the error appears even on the `D:\` root). Verified:

- torch CUDA init alone -> D: writes fine.
- statsforecast (numba) alone -> D: writes fine.
- deep training alone -> D: writes fine.
- **numba in the main process AND torch CUDA in the main process -> D: writes fail.**
- numba in the main process AND torch CUDA in a **separate subprocess** -> D: writes fine.

So it is an OS-level interaction on this specific Windows + D:-drive setup, not a defect in the pipeline code
or the deep engine.

**What works today.** The deep engine (`engines/neural_engine.py`) is real and verified: NLinear / DLinear /
NHITS train on the GPU and produce monotone quantile forecasts (8 GPU-gated tests green, and a standalone bake
of any single case succeeds). The engine already trains in a **subprocess** on Windows
(`_run_in_subprocess`), which keeps a standalone deep bake healthy.

**What is blocked.** Baking the deep tier as part of the same full-pipeline process as the statsforecast
(numba) tier: the parent process is already tainted before the deep subprocess returns, so the parent's
artifact write to D: fails.

**Workarounds / next step (tracked).**
1. Bake the deep tier in its own dedicated pipeline pass (torch only, no statsforecast in the process),
   merging its forecasts into the trace - the subprocess groundwork is in place.
2. Or move the derived-artifact output to a non-transactional path.
3. Or pin the offline bake to a Linux/WSL2 runner (no transactional-NTFS), where the interaction does not occur.

Set `CHRONOSCOPE_NEURAL_INPROC=1` to force in-process training (useful on non-Windows / CI, where the
interaction does not happen and the subprocess overhead is unnecessary).


## RESOLUTION (2026-07-10): Python 3.12 base + neuralforecast

Two updates resolved the deep-tier situation:

1. **The Python base moved to 3.12** (`.venv-pipeline312`, the canonical offline venv). The precise blocker
   was re-verified against PyPI metadata: ray ships cp310-cp314 wheels but its **Windows** wheels stop at
   cp312 - so "no py3.13 wheel" was really "no py3.13 wheel on Windows". On 3.12/win, ray 2.56.0 installs,
   `neuralforecast==3.1.9` installs, and the REAL framework is now the canonical deep tier
   (`engines/neuralforecast_engine.py`); the direct-torch implementations remain the parity reference.
2. **The WinError 6714 interaction did not reproduce on the 3.12 interpreter** for the full-ladder bake
   invoked via direct `precompute()` calls (the `-m` runpy path remains deprecated in favour of
   `scripts/bake.py`). The full 15-method ladder (classical + statistical + ML + both deep tiers) baked all
   cases successfully on the GPU.

The py3.13 venv (`.venv-pipeline`) is kept for compatibility testing; the deep tier skips gracefully there.
