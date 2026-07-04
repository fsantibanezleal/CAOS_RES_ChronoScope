# Foundation-model survey (anchor: arXiv 2504.04011)

The taxonomy backbone for ChronoScope's atlas. Felipe flagged this paper as the SOTA anchor to build on.

## The paper

"Foundation Models for Time Series: A Survey", Siva Rama Krishna Kottapalli, Karthik Hubli, Sandeep
Chandrashekhara, Garima Jain, Sunayana Hubli, Gayathri Botla, Ramesh Doddaiah (Dell Technologies and
University of Massachusetts Lowell), submitted 2025-04-05, cs.LG, CC BY 4.0.
**[verified]** (https://arxiv.org/abs/2504.04011, https://arxiv.org/html/2504.04011v1)

It is a survey, not a new model, and it runs no leaderboard of its own. Its value is a clean, multi-axis
vocabulary for classifying transformer-based time-series foundation models, which is exactly the set of
columns a method atlas should expose. Its limitation is recency: it is an April-2025 snapshot and
predates the entire late-2025 to 2026 wave (Chronos-2, TimesFM 2.5, Moirai 2.0, Toto 2.0, TiRex-2,
Sundial, Kairos, TabPFN-TS, FlowState, TempoPFN). ChronoScope uses it as the taxonomy backbone and layers
the newer families on top (see [02_architecture-landscape.md](02_architecture-landscape.md)).

## The multi-axis taxonomy

The survey classifies models along five axes. Its distinctive angle is including the **training
objective / loss family** alongside the more common architectural axes. **[verified]**

1. **Architecture representation**: patch-based (segment the series into patches used as tokens) versus
   raw-sequence (raw points, quantized tokens, digit strings, or lagged features).
2. **Prediction nature**: probabilistic (distribution, quantiles, or sampled) versus deterministic (point).
3. **Variate support**: univariate-only versus native multivariate.
4. **Scale**: lightweight versus large-scale.
5. **Training objective**: MSE/Huber regression, cross-entropy over a token vocabulary, negative
   log-likelihood over a parametric mixture, or masked reconstruction.

## Model catalog, as the survey groups it

Grouped by backbone shape, then classified by the axes above. **[verified from the paper HTML]**

- **Encoder-decoder**: TimeGPT (deterministic, univariate, large; LLM techniques with CNNs and residuals).
- **Encoder-only**: MOMENT (patch-based, deterministic, masked pretraining); Moirai (patch-based,
  probabilistic mixture of Student-t / negative-binomial / log-normal, multivariate).
- **Decoder-only**: TimesFM (non-overlapping patches, deterministic, MSE); Timer and Timer-XL
  (segment/patch, autoregressive, MSE, TimeAttention with RoPE); Time-MoE (raw, Huber plus
  expert-balancing); Toto (patch-based, Student-t mixture, multivariate); Lag-Llama (lagged-feature
  tokenization, probabilistic, univariate).
- **Adapted-LLM**: Chronos (quantization tokenization, cross-entropy, T5/GPT-2 based); AutoTimes;
  LLMTime (digit-string encoding); Time-LLM (patches plus text reprogramming); Frozen Pretrained
  Transformer / FPT (over GPT/BERT/BEiT).
- **Non-transformer**: Tiny Time Mixers / TTM (adaptive patching, MLP-mixer, lightweight).

Datasets it names: Time Series Pile, UTSD (Unified Time Series Dataset), LOTSA. **[verified]**

## How the axes map onto ChronoScope's atlas

The survey's axes are, almost one to one, the columns the atlas should show per method:

| Survey axis | ChronoScope atlas column |
|---|---|
| Architecture representation | tokenization: point, patch, quantized-vocab, lag-feature, digit-string, tabular-row, dynamic-patch |
| (backbone shape, from the grouping) | backbone: encoder, decoder, encoder-decoder, MLP-mixer, SSM, recurrent-xLSTM, linear-RNN, linear |
| Prediction nature | probabilistic head: none/point, quantile, parametric-mixture, sampling, flow-matching, PFN-posterior |
| Variate support | covariate support: none, past-only, known-future, static, full |
| Scale | parameter footprint and local-runnability |
| Training objective | loss family (documented per method in the Methodology page) |

To these ChronoScope adds one axis the 2025 survey does not emphasize but that its own differentiator
needs: **streaming / constant-cost inference** (yes for state-space and recurrent backbones such as
FlowState and TiRex-2, no for full-attention models without a cache). This is the axis the `preqts`
prequential evaluation lane is built to measure.

## What the anchor changes versus reinforces

- **Reinforces**: the atlas axes (patch vs raw, probabilistic vs deterministic head, univariate vs
  multivariate, scale, objective), and the inclusion of a non-transformer entry (it lists TTM, which
  validates pinning Granite TTM r2).
- **Changes none of the engine picks**: it predates all five pinned models except the lineage they
  descend from. Its contribution is taxonomy vocabulary and historical framing, not a fresh leaderboard.
- **Gap it exposes**: no recency and no live benchmark. ChronoScope therefore links the live GIFT-Eval
  and fev-bench leaderboards rather than freezing ranks, and adds the post-April-2025 families the
  survey could not include.
