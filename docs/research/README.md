# Research reference library

ChronoScope's persisted, cited reference library on the time-series forecasting model landscape. It is
the durable knowledge base behind the method atlas: what the methods are, how their architectures
differ, and where the field stands (2025 to 2026). Authored as the product grows (ADR-0056), in English.

## Pages

1. [Foundation-model survey (anchor: arXiv 2504.04011)](01_foundation-model-survey.md): the multi-axis
   taxonomy of time-series foundation models from Kottapalli et al. (2025), and how its axes map onto
   ChronoScope's atlas columns.
2. [Architecture landscape](02_architecture-landscape.md): the transformer lineage (Informer to
   iTransformer), the "are transformers effective for long-horizon forecasting" debate and its
   resolution, and the 2025 to 2026 foundation-model families, with an architectural comparison table
   and the axes the atlas exposes.
3. [Reference index](03_references.md): the grouped, deduplicated list of papers with arXiv ids and
   canonical GitHub/HuggingFace URLs, with honest verified/assumed tags.

## Verification convention

Each factual claim is tagged **[verified]** (a primary page, arXiv abstract or model card or repo, was
fetched) or **[assumed]** (from a secondary source, to be confirmed before it becomes load-bearing).
Model licenses and arXiv ids that gate an engine choice are verified directly.

## How this connects to the engines

The pinned foundation engines (see [../frameworks.md](../frameworks.md)) are chosen from this landscape
for permissive license and local runnability, and deliberately span distinct architecture families:
decoder (TimesFM 2.5), encoder with covariate in-context learning (Chronos-2), recurrent xLSTM with
streaming (TiRex-2), MLP-mixer (Granite TTM r2), and state-space (FlowState r1). The classical numpy
ladder and the statistical tier (statsforecast) sit below them as the transparent baselines every
foundation model is scored against.
