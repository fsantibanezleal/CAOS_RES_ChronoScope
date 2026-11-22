# Worked forecasting lessons

The English and Spanish notebooks progress from an inspectable seasonal
reference through partial-season diagnosis, executed statistical/tree comparisons, and
a fixed context-memory proposal with matching ablations, followed by temporally validated
combinations and complete weekly/monthly external results.
A second mirrored topic covers original-axis motifs and segmentation, multiscale complexity,
and corrected feature associations with a discovery-trained corpus selector.
The forecast workflow lesson runs all eight pipeline stages on an authentic
electricity excerpt and two distinct generated training histories.
Start with the [English index](en/README.md) or [Spanish index](es/README.md).

Initialize the isolated environment with `scripts/local/01_init.ps1 -Notebooks` or
`bash scripts/local/01_init.sh --notebooks`. Run `python scripts/run_notebooks.py` to
execute every lesson in a fresh kernel. For a release, run
`python scripts/run_notebooks.py --check --tmp <external scratch directory>`; it executes
copies and rejects stale committed outputs. Static validation is
`python scripts/check_notebooks.py` and runs in CI without executing scientific work.

The lessons import the product's methods, use exact direct package pins and the committed
history/holdout split, and identify which models execute versus which frozen paths are
rescored. They do not claim fresh neural training or pretrained-checkpoint inference.
Narrative sources are in `docs/lessons/`. The four notebook builders in `scripts/` author the notebook
cells and deliberately clear outputs. Always execute again after authoring, then commit
the clean resulting notebooks. Never hand-edit execution counts or numerical outputs.
