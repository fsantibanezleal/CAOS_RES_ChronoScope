# Architecture landscape (transformers and foundation models, 2025 to 2026)

The layer the anchor survey ([01_foundation-model-survey.md](01_foundation-model-survey.md)) cannot
provide: the supervised transformer lineage, the linear-baseline debate, and the current
foundation-model families. Reference ids are in [03_references.md](03_references.md).

## 1. The supervised long-horizon transformer lineage

- **Informer** (arXiv 2012.07436, AAAI-21 best paper): ProbSparse attention plus a distillation encoder
  to cut the quadratic cost of long-sequence forecasting. The first serious long-horizon transformer.
- **Autoformer** (arXiv 2106.13008, NeurIPS-21): series decomposition (trend/seasonal) as an inner block
  plus an Auto-Correlation mechanism replacing dot-product attention.
- **FEDformer** (arXiv 2201.12740, ICML-22): frequency-domain attention via Fourier/wavelet with
  seasonal-trend decomposition; roughly 22% univariate improvement over Autoformer.
- **TFT, Temporal Fusion Transformer** (arXiv 1912.09363): interpretable multi-horizon with
  variable-selection networks, gated residuals, LSTM local processing plus interpretable attention, and
  native static / known-future / observed covariates with quantile output. Still the reference for
  covariate-rich interpretable forecasting.

## 2. The 2023 turn: patching and axis inversion

- **PatchTST** (arXiv 2211.14730, ICLR-23), "A Time Series is Worth 64 Words": patch the series into
  subseries-level tokens (retains local semantics, cuts attention cost, allows longer history) plus
  channel-independence (each channel a univariate series sharing weights). The standard supervised
  transformer baseline and the seed of many foundation models.
- **iTransformer** (arXiv 2310.06625, ICLR-24 Spotlight): invert the axes, embed each variate's whole
  series as one token and attend across variates rather than across time; clean multivariate correlation.
- **Crossformer** (ICLR-23): two-dimensional patch embedding to model cross-time and cross-dimension
  dependencies explicitly.

## 3. The "are transformers effective for long-horizon forecasting" debate

- **DLinear / NLinear** (arXiv 2205.13504, AAAI-23 Oral, "Are Transformers Effective for Time Series
  Forecasting?"): a one-layer linear model (NLinear normalizes by the last value; DLinear adds
  Autoformer-style decomposition) beat Informer/Autoformer/FEDformer across nine datasets, often widely.
  The diagnosis: permutation-invariant self-attention loses temporal ordering.
- **Resolution (2024 to 2026)**: the debate reframed rather than closed. PatchTST and iTransformer
  answered the specific critique (patching and axis-inversion restore attention's usefulness), and
  pretrained foundation models now dominate zero-shot benchmarks. But linear and MLP-mixer baselines
  (DLinear, TSMixer) remain strong, cheap, and hard to beat on many in-domain supervised tasks. The
  practical rule for an atlas: keep a linear/MLP baseline as a mandatory control; transformers win when
  you need scale, transfer, covariates, or probabilistic heads, not automatically on every dataset.

## 4. Foundation-model families (zero-shot pretrained)

- **Amazon Chronos** (arXiv 2403.07815): scale-and-quantize values into a fixed vocabulary, train a
  T5-family LM with cross-entropy, sample token sequences for a probabilistic forecast. **Chronos-Bolt**
  is the T5 encoder-decoder direct-multi-step variant (much faster). **Chronos-2** (arXiv 2510.15821,
  120M, encoder, quantile output, group-attention in-context learning across related series and
  covariates) reports SOTA zero-shot on fev-bench, GIFT-Eval and Chronos Benchmark II, strongest on
  covariate tasks. **License Apache-2.0** (verified on the model card 2026-07-04).
- **Google TimesFM** (arXiv 2310.10688): decoder-only, patched, MSE point head. **TimesFM 2.5** (200M,
  Apache-2.0, context up to 16,384) was GIFT-Eval zero-shot #1 at release; the safest permissive,
  CPU-runnable pick.
- **Salesforce Moirai** (arXiv 2402.02592): masked-encoder, multi-size patches, probabilistic mixture
  head, trained on LOTSA. **Moirai-MoE** (arXiv 2410.10469) adds sparse experts. **Moirai 2.0** (arXiv
  2511.11698) switches to decoder-only with quantile plus multi-token prediction; top-tier on GIFT-Eval.
- **Datadog Toto** (arXiv 2505.14766): patch-based, Student-t mixture, observability-tuned; ships the
  BOOM benchmark. **Toto 2.0** (arXiv 2605.20119) scales u-muP transformers up to 2.5B on one recipe;
  Pareto-frontier on BOOM, GIFT-Eval and a contamination-resistant TIME benchmark.
- **NX-AI TiRex** (arXiv 2505.23719): 35M, **xLSTM** recurrent backbone (not attention), point plus
  quantile output; top scores on GIFT-Eval at tiny scale. **TiRex-2** (arXiv 2607.01204, submitted
  2026-07-01, Podest et al.): generalizes TiRex to **multivariate** with **past and future-known
  covariates** and **constant-cost streaming**; 38.4M univariate plus 44.1M multivariate (about 82.5M);
  **Apache-2.0** (verified 2026-07-04). This is ChronoScope's flagship streaming engine: its constant-cost
  update is exactly what the `preqts` streaming lane exists to demonstrate.
- **IBM Granite time-series** (GPU-free, ultra-light): **Tiny Time Mixers / TTM** (arXiv 2401.03955),
  TSMixer-based non-transformer, few-million params, r2 is the current release; **FlowState** (arXiv
  2508.05287), an SSM (state-space) encoder plus functional-basis decoder giving sampling-rate
  invariance, held GIFT-Eval #3 in October 2025. Both Apache-2.0.
- **THU Sundial** (arXiv 2502.00816, ICML-25 Oral): continuous-value transformer with a flow-matching
  TimeFlow loss for generative multi-sample forecasts.
- **THU Timer / Timer-XL** (arXiv 2402.02368, 2410.04803): decoder-only unified generative pretraining,
  long-context TimeAttention with RoPE.
- **Time-MoE** (arXiv 2409.16040, ICLR-25 Spotlight): decoder plus sparse mixture-of-experts scaled to
  2.4B, pretrained on Time-300B.
- **Kairos** (arXiv 2509.25826): encoder-decoder with mixture-of-size dynamic patching and
  instance-adaptive RoPE; parameter-efficient, strong zero-shot on GIFT-Eval.
- **TabPFN-TS** (arXiv 2501.02945): recasts forecasting as tabular regression over temporal features fed
  to a pretrained TabPFN-v2 (11M, no time-series pretraining); a genuinely different, very light paradigm.
- **TempoPFN** (arXiv 2510.25502): a univariate foundation model on **linear RNNs**, pretrained purely on
  synthetic data; top-tier among synthetic-only approaches.

## 5. Architectural comparison table

Columns follow the anchor paper's axes plus covariate and streaming support. "Prob head" is the
probabilistic output mechanism; params are the headline/largest public size. Verification is per row in
[03_references.md](03_references.md).

| Model | Org | Backbone | Tokenization | Prob head | Multivariate | Covariates | Params (max) | License | Local-runnable |
|---|---|---|---|---|---|---|---|---|---|
| Informer | THU/Beihang | enc-dec | point | point | via channels | limited | tens of M | permissive | yes |
| Autoformer | THU | enc-dec | point | point | via channels | limited | tens of M | permissive | yes |
| FEDformer | Alibaba/THU | enc-dec | point | point | via channels | limited | tens of M | permissive | yes |
| TFT | Google | enc-dec (LSTM+attn) | point | quantile | yes | full | ~M | permissive | yes |
| PatchTST | Princeton/IBM | encoder | patch | point | channel-indep | no | ~M | permissive | yes |
| iTransformer | THU | encoder | series-as-token | point | native | via variate tokens | ~M | permissive | yes |
| DLinear/NLinear | CUHK | linear | point | point | channel-indep | no | K to M | permissive | yes |
| Chronos | Amazon | enc-dec (T5) | quantized token | sampling | no | no | 710M | Apache-2.0 | yes |
| Chronos-2 | Amazon | encoder | patch-ish | quantile | native | full | 120M | Apache-2.0 | yes |
| TimesFM 2.5 | Google | decoder | patch | point (+quantile) | via channels | limited | 200M | Apache-2.0 | yes (CPU ok) |
| Moirai 2.0 | Salesforce | decoder | patch | quantile | native | yes | small/base | permissive | yes |
| Toto 2.0 | Datadog | decoder | patch | Student-t mixture | native | yes | 2.5B | open weights | GPU (large) |
| TimeGPT | Nixtla | enc-dec | internal | dist | yes | yes (exog) | closed | closed/API | no (API only) |
| Lag-Llama | Morgan/Mila | decoder | lag features | Student-t | no | limited | ~M | Apache-2.0 | yes |
| Timer-XL | THU | decoder | segment/patch | point | yes | limited | ~M | permissive | yes |
| Time-MoE | multi | decoder + MoE | point | point | both | limited | 2.4B | Apache-2.0 | GPU (large) |
| Sundial | THU | decoder | patch | flow-matching | via channels | limited | 128M+ | permissive | yes |
| Granite TTM r2 | IBM | MLP-mixer | patch | point | channel-mix | yes | few M | Apache-2.0 | yes (GPU-free) |
| FlowState r1 | IBM | SSM enc + basis dec | continuous | point | yes | limited | few M | Apache-2.0 | yes (GPU-free) |
| TiRex | NX-AI | recurrent (xLSTM) | patch | quantile | via channels | limited | 35M | Apache-2.0 | yes (CPU/GPU light) |
| TiRex-2 | NX-AI | recurrent (xLSTM) | patch | quantile | native | past + future | 82.5M | Apache-2.0 | yes (streaming) |
| Kairos | academic | enc-dec | dynamic patch | quantile | via channels | limited | small | open | yes |
| TabPFN-TS | Prior Labs | tabular PFN | tabular rows | PFN posterior | via features | full | 11M | open | yes |
| TempoPFN | AutoML | linear RNN | point | PFN posterior | no | no | small | open | yes |

Axes the atlas UI exposes: tokenization, backbone family, probabilistic head, covariate support, and
streaming/constant-cost inference (the axis the `preqts` lane measures).

## 6. Benchmarks

- **GIFT-Eval** (arXiv 2410.10393, Salesforce): 23 datasets, 144k series, 7 domains, MASE and CRPS, with
  a non-leaking pretraining corpus and a live HuggingFace leaderboard. The de-facto general zero-shot
  leaderboard.
- **fev-bench** (arXiv 2509.26468, AutoGluon/Amazon): 100 tasks from 96 datasets, explicitly
  covariate-heavy (30 known-dynamic, 24 past-dynamic, 19 static), bootstrap confidence intervals; the
  covariate-focused complement to GIFT-Eval and the spine ChronoScope's Benchmark reproduces a subset of.
- **BOOM** (Datadog, with Toto): observability metrics. **Chronos Benchmark II** (Amazon). Newer
  leakage-aware suites (Toto 2.0's TIME, TempoPFN's Chronos-ZS) are worth tracking.

Leaderboards move monthly; the atlas links the live GIFT-Eval and fev-bench leaderboards rather than
hard-coding ranks.
