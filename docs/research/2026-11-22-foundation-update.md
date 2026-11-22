# Foundation-model update checked on 2026-11-22

Status: primary-source research and proposed experiment scope. No model was downloaded or executed for this note; no numerical source, dependency pin, shared WSL environment or historical result was changed. The currently executing pinned-reference study remains a separate historical configuration.

## What is current, and what the retained study actually used

Google announced TimesFM 3 on August 31, 2026: a 330M-parameter model with native joint-target and covariate forecasting. The publisher's claimed benchmark gains are its results, not ChronoScope measurements. [Google Research announcement](https://research.google/blog/timesfm-3-a-zero-shot-foundation-model-for-multivariate-forecasting/)

The current source package is `timesfm` 3.0.2; the published wheel was uploaded September 9, 2026. TiRex-2's current package is 0.5.0, with its wheel uploaded November 9. The TiRex changelog dates that version November 3, while GitHub records the later release publication. Record both dates accurately. [TimesFM package metadata](https://pypi.org/pypi/timesfm/json), [TiRex package metadata](https://pypi.org/pypi/tirex-2/json), [TiRex release](https://github.com/NX-AI/tirex-2/releases/tag/v0.5.0), [TiRex changelog](https://nx-ai.github.io/tirex-2/changelog/)

The retained data/derived/fresh-reevaluation.json instead records `timesfm` 2.0.2 with the TimesFM 2.5 checkpoint and tirex-2=0.1.1. That is a valid pinned comparison, not an evaluation of these latest releases. Current source files engine/engines/timesfm_engine.py and tirex2_engine.py must retain that identity until a separately named execution is validated. A newer release neither invalidates its old measured result nor supplies evidence that the new one improves it.

## TimesFM 3 permission boundary

The weights' separate licence permits noncommercial, nonproduction research. It excludes Outputs from Derivatives, but still prohibits commercial/production use of outputs and redistribution of the model or Derivatives. Its purpose definition excludes end-user/production interaction; free access alone is insufficient. The Derivative definition is broader than copyright terminology. Separately licensed Apache code does not license these weights. [Exact model licence](https://huggingface.co/google/timesfm-3.0-pytorch/raw/main/LICENSE)

**Interpretation for this atlas:** offline academic evaluation and static publication of its research findings fit the stated research purpose, conditional on remaining noncommercial and nonproduction. This supports a research-results publication lane, not public user-upload forecasting or operational recommendations. The output carve-out is not unrestricted permission to commercially reuse forecast arrays. Keep provenance and the source restriction with published results; do not automatically assign existing unrestricted data licences to new TimesFM 3 outputs. A distributed helper incorporating restricted model material also needs separate consideration under the broad Derivative clause. Keep such material out of the public artifact bundle. This is a reading of publisher terms for this experiment, not blanket production clearance.

Google explicitly distinguishes Apache source and weights through 2.5 from the restricted 3.0 download. Its authorized Google Cloud service route has separate commercial/production terms; that route would be a separately configured and measured service experiment. [Official licence notice](https://github.com/google-research/timesfm#license-notice-for-pretrained-weights)

## TimesFM 3 adapter requirements

The official API uses the timesfm3 namespace, TimesFM 3Evaluator/ModelConfig and predict_batch. Univariate quantiles have shape (H, 9); joint-target output is (V, H, 9), with deciles 0.1 through 0.9 and median index 4. [Official API examples](https://github.com/google-research/timesfm#code-examples-timesfm-30)

Our 2.5 adapter currently reads ten columns including a leading point column and selects 1/5/9. Reusing that mapping for 3.0 would select wrong probabilities or exceed the array bounds. A distinct TimesFM-3.0 adapter must validate the returned grid and use 0/4/8 for the canonical 10/50/90 percent outputs. Explicitly identify the selected point statistic rather than assuming a separate point return equals the median. These are adapter corrections inferred from the two interfaces, not measured forecast findings.

The new model supports historical-only and future-known covariates. Its model card describes training-source exclusions relative to fev-bench, not universal absence of overlap with every dataset used here. Carry a dataset-specific overlap status. [Official model card](https://huggingface.co/google/timesfm-3.0-pytorch)

Pin implementation, checkpoint revision, configuration, normalization/padding, target/covariate identities, probability grid, device/dtype and any test-time averaging. Start with the exact univariate input/origin protocol already used by the retained comparison; multivariate or covariate extensions are new protocols with their own information-availability checks. Preserve rejected/unsupported cases and all common-target paths. Do not describe package installation, API success or the publisher's leaderboard position as validation of our model comparison.

## TiRex-2 version 0.5.0 changes and permission

The 0.5.0 changelog removes legacy YAML/CKPT loading and requires JSON/Safetensors, replaces FlashRNN/mlstm_kernels with new recurrence implementations, changes CUDA-graph behavior and adds native quantile sorting. Its speed/unchanged-score statements are upstream claims requiring our own reproduction before reuse. Preserve the old 0.1.1 runtime/checkpoint pair for its admitted study. [Official changelog](https://nx-ai.github.io/tirex-2/changelog/)

The official model card labels TiRex-2 Apache 2.0, lists config.json/model.safetensors as the default and identifies ONNX as another format. [Official checkpoint card](https://huggingface.co/NX-AI/TiRex-2) Apache 2.0 permits use and distribution subject to its terms; redistributed code/model materials need the licence, applicable attribution/NOTICE and change notices. It supplies no trademark or validation guarantee. Noncommercial research-results publication has no additional noncommercial-only weight restriction here. [Repository licence](https://github.com/NX-AI/tirex-2/blob/main/LICENSE)

The current official FAQ documents Windows PyTorch fallbacks and Linux kernel compilation. Our older blanket statement that TiRex-2 cannot install on native Windows is therefore version-specific. This does not prove native Windows compatibility in our environment: verify the actual PyTorch/GPU/compiler path in a separate runtime. Do not modify the shared historical WSL lane during its active inference run. [Official FAQ](https://nx-ai.github.io/tirex-2/faq/)

The documented tensor contract uses (V, T) targets, past covariates aligned to T and future-known covariates spanning T + H; forecast output is (V, 9, H). Defaults for padding and test-time augmentations must be recorded, and the canonical three quantiles selected by their actual levels. Our existing decile mapping is compatible in principle, but new sorting, kernels, padding and converted checkpoint bytes can still change outputs. [Official forecasting guide](https://nx-ai.github.io/tirex-2/how-to/forecasting/)

## Bounded next implementation

1. Keep all admitted historical code/checkpoint/source bindings and the currently running reference runtime unchanged. Establish isolated candidate runtimes after that run finishes.
2. Implement the separately named TiRex 0.5 adapter/configuration path against a revision-pinned Safetensors checkpoint. Compare new and old paths on identical histories, horizons and origins, with complete numerical/units checks and explicit tolerance/precision. Timing must distinguish first compilation, steady inference and batching. This is an experiment, not an assumed equivalent replacement.
3. Create a TimesFM 3 offline-research candidate only within the permission boundary above. Do not bundle its model, converted model or restricted derivatives into browser assets. Resolve intended distribution of any new model-derived helper/material before publishing that material. Keep the existing permissive-license runtime separate.
4. For each admitted new run, retain actual forecasts, targets, scales, runtime/checkpoint/file hashes, settings, exclusions and per-origin warning/error records. Aggregate within series and compare paired differences with uncertainty appropriate to the selected dataset. Use new result/study identifiers and preserve adverse outcomes.
5. Update the method ladder, model labels, notebook execution, report and app evidence only from those measured results. Genuine multivariate/covariate/native-update evaluation requires its own protocol. These two version checks do not complete a survey or evaluation of every current forecasting method, and do not establish an advantage over the existing roster.

## Observed identities for a future acquisition receipt

These are metadata observations, not downloaded-model checks or final experiment pins. Freeze the actual acquired files separately and confirm their hashes before inference.

| Item | Observed identity |
|---|---|
| TimesFM 3 official checkpoint revision |43046b85ec22d584a13f8098c2ed39c889e129c2|
| TimesFM 3 LICENSE at that revision |7270 bytes; SHA-256 3e36db7240d23adb6ac6d7d931892dcc5706a14a7d31581f08c35d2f25736dfd|
| `timesfm` 3.0.2 wheel |SHA-256 cfa3d22ddc3f019f0d9d95f19055428c4a4713526dafd7e5d1a7769782e7613f|
| TiRex-2 official checkpoint revision |352636173653592b6dceb3fbeee9224ca97952a9|
| tirex_2-0.5.0 wheel |SHA-256 aed1de741872f33a388ee28bcf5dddc46b6cb5d12d5291187c496d7f45209f26|

Checkpoint revisions were read from the publishers' Hugging Face model API; wheel identities from the publishers' PyPI release metadata. The TimesFM licence bytes were read from its revision-specific official raw URL. [TimesFM checkpoint API](https://huggingface.co/api/models/google/timesfm-3.0-pytorch), [TiRex checkpoint API](https://huggingface.co/api/models/NX-AI/TiRex-2), [TimesFM package API](https://pypi.org/pypi/timesfm/json), [TiRex package API](https://pypi.org/pypi/tirex-2/json)
