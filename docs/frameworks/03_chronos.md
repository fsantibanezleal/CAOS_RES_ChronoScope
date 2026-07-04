# Framework: Amazon Chronos (zero-shot foundation tier)

The SOTA zero-shot foundation-model tier of the ladder, run OFFLINE on local checkpoints. Used by
`data-pipeline/chronoscopelab/engines/chronos_engine.py`.

## What and why

[Chronos](https://github.com/amazon-science/chronos-forecasting) (Amazon, Apache-2.0) is a family of
pretrained time-series foundation models: they forecast a series zero-shot, with no fitting, by treating
forecasting as a sequence problem over scaled/quantized values. Chronos-Bolt is the fast T5
encoder-decoder variant with direct multi-step quantile output. This is the "beyond the classical and
statistical baselines" tier the atlas exists to compare against: a single pretrained model that, on the
seasonal cases, already beats the auto-tuned statistical models.

## The offline hard-processing lane

This is the ADR-0057 heavy lane. The model is a transformer that loads from a checkpoint and runs CPU
inference; it is not Pyodide-safe, so it runs only in the offline `.venv-pipeline` and never in the browser
live lane. Its forecasts are baked into the committed artifacts, and the web app **replays** them (the live
lane runs the classical core, and in a later slice small ONNX-exported deep models). The loaded pipeline is
cached at module level, so a checkpoint is read from disk once per process and reused across every backtest
window and case.

## Opt-in and graceful degradation

The tier is heavy, so it is OPT-IN:

- Deps live in `data-pipeline/requirements-foundation.txt` (torch CPU + chronos-forecasting), not installed
  by default.
- Checkpoints live in the model vault (`CHRONOSCOPE_MODEL_ROOT`, default `E:\_Models\chronoscope`), never
  in git.
- Set `CHRONOSCOPE_ENABLE_FOUNDATION=1` to include the tier when baking artifacts. Without it (and in CI,
  which has neither the deps nor the checkpoints), the pipeline runs the classical + statistical + ML ladder
  and the test suite stays fast.

## Install and bake

```bash
.venv-pipeline/Scripts/python.exe -m pip install --index-url https://download.pytorch.org/whl/cpu torch
.venv-pipeline/Scripts/python.exe -m pip install -r data-pipeline/requirements-foundation.txt
# then bake the canonical artifacts with the tier on:
CHRONOSCOPE_ENABLE_FOUNDATION=1 .venv-pipeline/Scripts/python.exe -m chronoscopelab.pipeline
```

## How ChronoScope uses it

```python
from chronos import BaseChronosPipeline
import torch
pipe = BaseChronosPipeline.from_pretrained(checkpoint_path, device_map="cpu")
q, mean = pipe.predict_quantiles(torch.tensor(context, dtype=torch.float32),
                                 prediction_length=h, quantile_levels=[0.1, 0.5, 0.9])
# q: (1, h, len(levels)) -> take q[0], enforce monotone across levels
```

The forecast is wrapped into the same `MethodForecast` contract as every other method and scored by the
`preqts` rolling backtest. Because the model is zero-shot, the backtest is pure inference per origin (no
refit), given a small window budget and a context cap to keep the heavy lane practical.

## Result (this slice)

On the seasonal built-in case, Chronos-Bolt reaches the lowest MASE of the whole ladder (below the
seasonal-naive baseline and below the auto-tuned AutoARIMA), which is exactly the point of the atlas: a
transparent baseline, a strong classical/statistical tier, and a foundation model that pushes past them,
all scored on the same held-out backtest.

## Follow-ups

Chronos-2, TimesFM 2.5, Granite TTM r2, FlowState r1 and TiRex-2 (all confirmed Apache-2.0, checkpoints in
the vault) are wired in later slices with their own loaders; each is added to `_CHECKPOINTS` or its own
engine module behind the same contract. See `_CAOS_MANAGE/wip/chronoscope/` and `docs/research/`.
