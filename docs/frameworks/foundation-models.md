# The foundation tier: zero-shot pretrained forecasters

Engines: [`chronos_engine.py`](../../data-pipeline/chronoscopelab/engines/chronos_engine.py) ·
[`timesfm_engine.py`](../../data-pipeline/chronoscopelab/engines/timesfm_engine.py) · Tests:
[`tests/test_engine_foundation.py`](../../tests/test_engine_foundation.py)

The SOTA tier of the ladder: pretrained time-series foundation models forecasting each case **zero-shot**
(no fitting), from local checkpoints in the model vault (`E:\_Models\chronoscope`, override with
`CHRONOSCOPE_MODEL_ROOT`). Opt-in via `CHRONOSCOPE_ENABLE_FOUNDATION=1`; every engine degrades gracefully
when its package or checkpoint is absent (CI has neither). All weights below are **Apache-2.0**.

## The native-Windows roster (baked)

| Engine | Checkpoint | Params | Architecture | Notes |
|---|---|---|---|---|
| Chronos-Bolt | `chronos-bolt-small` | 48M class | T5 patch-based | CPU-fast; the in-browser ONNX candidate |
| Chronos-2 | `chronos-2` | 120M | T5-encoder, group attention | native multivariate + past/future covariates (arXiv:2510.15821); 3-d input API |
| TimesFM 2.5 | `timesfm-2.5` | 200M | decoder-only | 16k context; continuous quantile head -> deciles (arXiv:2310.10688) |

Quantile handling: Chronos pipelines emit the requested levels directly; TimesFM's continuous quantile head
returns `[mean, q0.1..q0.9]`, mapped to the nearest decile (the canonical 0.1/0.5/0.9 levels map exactly).
All outputs are made monotone across levels.

## Honest roster limits (verified 2026-07-10)

- **TiRex-2** (35M-class xLSTM, streaming-native, arXiv:2607.01204): NOT installable on native Windows - its
  `flashrnn` dependency requires `triton`, which ships no Windows wheels. It remains the WSL2/Linux-lane
  engine and the streaming bench's future headline subject; the paper + checkpoint are verified real
  (see the research dossiers).
- **Granite TTM r2** (`granite-tsfm` 0.3.6): pins `torch<2.11`, conflicting with the pipeline's cu126
  `torch 2.12.1`. Deferred to a dedicated venv rather than downgrading the shared torch.
- **Moirai / Moirai-2**: real and strong on GIFT-Eval, but the WEIGHTS are CC-BY-NC (non-commercial) - guide
  material only, never baked into the public product.

## References

- Ansari, A.F. et al. (2024). Chronos: Learning the Language of Time Series. arXiv:[2403.07815](https://arxiv.org/abs/2403.07815).
- Amazon (2025). Chronos-2: universal, covariate-aware zero-shot forecasting. arXiv:[2510.15821](https://arxiv.org/abs/2510.15821).
- Das, A. et al. (2024). A decoder-only foundation model for time-series forecasting. *ICML*. arXiv:[2310.10688](https://arxiv.org/abs/2310.10688).
- Podest, P. et al. (2026). TiRex-2: Generalizing TiRex to Multivariate Data and Streaming. arXiv:[2607.01204](https://arxiv.org/abs/2607.01204) (WSL2 lane).
