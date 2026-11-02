# Worked forecasting lessons

Eight mirrored English and Spanish notebooks progress from an inspectable seasonal
reference through partial-season diagnosis, executed statistical/tree comparisons, and
a fixed context-memory proposal with matching ablations and a negative aggregate result.
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
Narrative sources are in `docs/lessons/`; `scripts/build_lessons.py` authors the notebook
cells and deliberately clears outputs. Always execute again after authoring, then commit
the clean resulting notebooks. Never hand-edit execution counts or numerical outputs.
