# Timestral on the common final blocks

Four pinned Mistral checkpoints each forecast the same 15 reserved blocks used
in the fresh ChronoScope comparison. The input is the complete contiguous
prefix for each case, converted to float32. Inference uses the official CPU
implementation with no covariates or fine-tuning. The plan was saved before
Timestral inference, with the reference outcomes already known.

| Checkpoint | Mean case MASE | Mean case MSIS | Mean case coverage |
|---|---:|---:|---:|
| Timestral-5M | 1.08491 | 4.80842 | 81.47% |
| Timestral-28M | 1.05492 | 4.67321 | 81.94% |
| Timestral-123M | 1.03585 | 4.61816 | 81.11% |
| Timestral-209M | 1.04903 | 4.67244 | 77.94% |

The planned Timestral-209M minus AutoTheta mean MASE difference was −0.44740.
Twelve cases favored Timestral and three favored AutoTheta. The exploratory
95% case-reweighting interval was [−0.79356, −0.15991]. Each draw resamples
the paired differences on the same 15 selected cases. The four authentic
excerpts and eleven generated cases do not represent a sampled population.
The 123M checkpoint had the lowest mean MASE and MSIS in this Timestral family.
The 209M checkpoint's coverage was 89.14% on the four authentic excerpts and
73.86% on the generated cases. Means are case-weighted, with nominal coverage
80%. Per-case results retain MAE, RMSE and interval width in their source units.

[The analysis plan](analysis-plan.json) pins the runner and checkpoint revisions
and fixes the evaluation protocol. [The numerical output](results.json)
retains all 21 quantile levels, checkpoint-file hashes, timings and pairwise
comparisons with all 22 reference methods. Its execution status is the raw
runner's output. [The validation record](verification.json) documents the later
independent rescoring and the exact match between the two executions.

Run the official inference implementation at the commit in the plan with the
recorded runtime versions and use external model, cache and output paths.
The model weights have their own Modified MIT licence. The code is Apache 2.0.
The repository stores the measured output and checkpoint identities.

```text
python scripts/evaluate_timestral.py --model-cache <models> --cache <scratch> --output <result.json>
python scripts/check_timestral_study.py <result.json> --reweight
```

The holdout protocol tests univariate forecasts. The results leave
multivariate and covariate effects, pretraining overlap, benchmark-wide
rankings and operational latency comparisons open.

[Official Timestral implementation](https://github.com/mistralai/timestral) ·
[Mistral release description](https://mistral.ai/news/timestral/)
