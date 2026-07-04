# Reference index

The deduplicated reference library for the forecasting-model landscape. Tags: **[verified]** a primary
page was fetched; **[assumed]** from a secondary source, confirm before it becomes load-bearing. Engine
licenses and ids that gate a pinned engine are verified directly.

## Surveys

- Foundation Models for Time Series: A Survey (the anchor): arXiv 2504.04011. **[verified]**
  (https://arxiv.org/abs/2504.04011)
- Empowering Time Series Analysis with Synthetic Data (survey): arXiv 2503.11411. **[assumed]**

## Transformer architectures (supervised long-horizon lineage)

- Informer: arXiv 2012.07436. **[assumed]** (https://github.com/zhouhaoyi/Informer2020)
- Autoformer: arXiv 2106.13008. **[assumed]** (https://github.com/thuml/Autoformer)
- FEDformer: arXiv 2201.12740. **[assumed]** (https://github.com/MAZiqing/FEDformer)
- TFT (Temporal Fusion Transformer): arXiv 1912.09363. **[verified]**
- PatchTST: arXiv 2211.14730. **[verified]** (https://github.com/yuqinie98/PatchTST)
- iTransformer: arXiv 2310.06625. **[verified]** (https://github.com/thuml/iTransformer)
- Crossformer: ICLR-23 (OpenReview id b9tGWYaPP7). **[assumed]**
- DLinear/NLinear ("Are Transformers Effective for TSF?"): arXiv 2205.13504. **[verified]**
  (https://github.com/cure-lab/LTSF-Linear)

## Foundation models (zero-shot pretrained)

- Chronos: arXiv 2403.07815. **[verified]** (https://github.com/amazon-science/chronos-forecasting)
- Chronos-Bolt: no standalone paper; model cards. **[verified]** (https://huggingface.co/amazon/chronos-bolt-base)
- Chronos-2: arXiv 2510.15821; **license Apache-2.0 (verified on the HF card 2026-07-04)**. **[verified]**
  (https://huggingface.co/amazon/chronos-2)
- TimesFM 1.0: arXiv 2310.10688. **[verified]** (https://github.com/google-research/timesfm)
- TimesFM 2.5: no separate paper id found; GitHub/HF release 2025-09-16, Apache-2.0. **[verified via repo]**
  (https://huggingface.co/google/timesfm-2.5-200m , confirm the exact slug)
- Moirai 1.0: arXiv 2402.02592. **[assumed]** (https://github.com/SalesforceAIResearch/uni2ts)
- Moirai-MoE: arXiv 2410.10469. **[verified]**
- Moirai 2.0: arXiv 2511.11698. **[verified]** (https://huggingface.co/Salesforce/moirai-2.0-R-small)
- Toto (observability): arXiv 2505.14766. **[verified]** (https://github.com/DataDog/toto)
- Toto 2.0: arXiv 2605.20119. **[verified]** (https://huggingface.co/Datadog/Toto-2.0-2.5B)
- TimeGPT: arXiv 2310.03589. **[assumed]** (Nixtla, closed weights / API)
- Lag-Llama: arXiv 2310.08278. **[assumed]** (https://github.com/time-series-foundation-models/lag-llama)
- Timer: arXiv 2402.02368. **[verified]** (https://github.com/thuml/Large-Time-Series-Model)
- Timer-XL: arXiv 2410.04803. **[assumed]**
- Time-MoE: arXiv 2409.16040. **[verified]** (https://github.com/Time-MoE/Time-MoE)
- Sundial: arXiv 2502.00816. **[verified]** (https://github.com/thuml/Sundial)
- MOMENT: arXiv 2402.03885. **[verified]** (https://github.com/moment-timeseries-foundation-model/moment)
- Tiny Time Mixers (Granite TTM): arXiv 2401.03955. **[assumed]** (https://github.com/ibm-granite/granite-tsfm)
- FlowState (Granite): arXiv 2508.05287; Apache-2.0. **[verified]**
  (https://huggingface.co/ibm-granite/granite-timeseries-flowstate-r1)
- TiRex: arXiv 2505.23719; Apache-2.0; 35M xLSTM. **[verified]**
  (https://github.com/NX-AI/tirex , https://huggingface.co/NX-AI/TiRex)
- **TiRex-2: arXiv 2607.01204 (submitted 2026-07-01), "TiRex-2: Generalizing TiRex to Multivariate Data
  and Streaming" (Podest, Pichler, Burger, Zolyomi, Voggenberger, Berghammer, Klotz, Bock, Klambauer,
  Hochreiter, NX-AI); Apache-2.0; 82.5M; xLSTM streaming with past + future covariates. [verified 2026-07-04]**
  (https://arxiv.org/abs/2607.01204 , https://huggingface.co/NX-AI/TiRex-2)
- Kairos: arXiv 2509.25826. **[verified]** (https://github.com/foundation-model-research/Kairos)
- TabPFN-TS: arXiv 2501.02945. **[verified]** (https://github.com/PriorLabs/tabpfn-time-series)
- TempoPFN: arXiv 2510.25502. **[verified]** (https://github.com/automl/TempoPFN)
- Chronicle (multimodal language + time series): arXiv 2605.20268. **[assumed]**

## Benchmarks

- GIFT-Eval: arXiv 2410.10393. **[verified]** (https://github.com/SalesforceAIResearch/gift-eval ,
  https://huggingface.co/spaces/Salesforce/GIFT-Eval)
- fev-bench: arXiv 2509.26468. **[verified]** (https://github.com/autogluon/fev ,
  https://huggingface.co/spaces/autogluon/fev-bench)
- BOOM (Datadog): shipped with Toto (see arXiv 2505.14766). **[verified]**
- Chronos Benchmark II: Amazon (referenced in the Chronos-2 paper 2510.15821). **[verified concept]**

## Open verification items

- Confirm the exact HuggingFace slug for TimesFM 2.5 and the Granite TTM r2 / FlowState r1 repo ids and
  CPU-only inference path before wiring each as a runnable engine.
- Clear the remaining **[assumed]** arXiv ids by fetching each abstract directly (Informer, Autoformer,
  FEDformer, Moirai 1.0, Lag-Llama, Timer-XL, TimeGPT, TTM) before they become load-bearing citations.
- Resolved 2026-07-04: TiRex-2 (real, arXiv 2607.01204, Apache-2.0) and Chronos-2 (Apache-2.0) are both
  pinnable.
