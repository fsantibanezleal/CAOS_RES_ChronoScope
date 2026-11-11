# Reproduce the ChronoScope technical report

Check the source files listed by SHA-256 in `build-receipt.json` before
interpreting the PDF. The earlier evaluation and calibration inputs are
available at [20fa935](https://github.com/fsantibanezleal/CAOS_RES_ChronoScope/tree/20fa9357716b534c4fdd3a5aa66cacd9eb66e416).
The separate Timestral experiment is at [a9b83ea](https://github.com/fsantibanezleal/CAOS_RES_ChronoScope/tree/a9b83ea22cbedd1856ab6b5839d95f2caa7f4e4e).
Use the source tree containing this guide for the working TeX files, updated
generators and combined PDF. The original source bundle for the historical
fresh execution identifies 56 recovered files by digest.

## Numerical checks

Install the declared numerical requirements in the product's external runtime.
The report uses the immutable admitted paths for archived, fresh and
external-collection results. Run the checks from the product root:

```text
python scripts/check_fresh_reevaluation.py
python scripts/check_research_extensions.py --statistics
python scripts/check_browser_linear_evidence.py
python scripts/manuscript_replay.py --check
python scripts/check_timestral_study.py --reweight
python scripts/build_combination_review_tables.py --check
```

The combination manuscript's reconstruction instructions specify the two
original Monash TSF files and the source-prefix checker. The retained numbers
separate the original evaluation, the later paired-series reweighting, the
independently confirmed browser intervals and the Timestral comparison.
Rechecking retained forecasts requires the bound target vectors and model
paths. Fresh inference additionally requires the checkpoint revisions and
runtime in the corresponding analysis plan.

The [fresh case and method scores](tables/fresh-by-case.csv) come from
[fresh-reevaluation.json](https://github.com/fsantibanezleal/CAOS_RES_ChronoScope/blob/20fa9357716b534c4fdd3a5aa66cacd9eb66e416/data/derived/fresh-reevaluation.json).
The [archived case and method paths](https://github.com/fsantibanezleal/CAOS_RES_ChronoScope/blob/20fa9357716b534c4fdd3a5aa66cacd9eb66e416/data/derived/reevaluation.json)
include the same reserved targets and their historical metrics. The
[external per-origin audit](https://github.com/fsantibanezleal/CAOS_RES_ChronoScope/blob/20fa9357716b534c4fdd3a5aa66cacd9eb66e416/manuscripts/context-memory/evidence/external-evaluation.json.gz)
contains forecasts, targets, seasonal scales, weights, selection metadata
and scores by source series and origin.

## Tables, figures and PDF

```text
python scripts/build_report_contract_tables.py
python scripts/build_report_evidence_tables.py
python scripts/build_timestral_report.py
python scripts/build_combination_review_tables.py
python scripts/build_report_architecture.py
python scripts/plot_browser_calibration.py --output manuscripts/product-report/next/figures
python scripts/build_research_report.py --sequence-output manuscripts/product-report/next/figures/sequence-patterns.pdf
python scripts/build_working_manuscripts.py --only product-report --scratch <external-build-folder>
python scripts/check_working_draft_bindings.py
```

The sequence figure is regenerated directly from the released structural-break
analysis, with separate hatching for motif and discord windows. The remaining
original research-report tables and figures come from the earlier source
snapshot's `scripts/build_research_report.py`, `scripts/build_combination_report.py`
and `manuscripts/product-report/make_evidence.py`. Run those historical
generators in a detached source snapshot because their original destinations
are published manuscript folders. The working report uses labelled copies of
their outputs.

The procedure crosswalk names validation files and examples of retained
artifacts. A test reference identifies the check to run. The observed-field
inventory measures serialized types and prevalence across the retained cases.
The Catch24 dictionary maps the exact names emitted by `pycatch22==0.4.5` to
their scientific quantities and axes using the original paper and the
pinned feature implementation.

Use `latexmk` and pdfTeX with the packages in `tex/main.tex`. The builder
compiles outside the source tree and records every local TeX and figure input.
A different TeX installation may change PDF bytes. Check the retained
scientific data, generated tables and compiled input identities separately.
