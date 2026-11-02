# Local workflow

Run `00_install-prereqs` to check Python, Node and Git; `01_init` initializes declared
Python environments and the frontend lock; `02_generate-data` prepares an external
candidate; `03_dev` validates the shipped corpus before starting Vite. Both PowerShell
and Bash entry points call the same standard-library workflow implementation.

Set `CAOS_TEMP_ROOT` to an external scratch directory. Generation recomputes the eight
light variants from the immutable released histories and rescores fourteen frozen model
paths. It carries the already admitted fresh experiment unchanged and verifies its source, input and metric bindings. It does not train or download foundation models. The explicit
`02_generate-data --release --from-stage <candidate>` operation validates source and
payload fingerprints, then promotes the complete candidate transactionally. A partial
corpus, altered released input, stale implementation binding, source change during
execution, unavailable environment alias or occupied development port fails closed.

The product admission hook replaces the template example's readiness and engine-version
assumptions: historical engine versions are retained rather than rewritten. Fresh final-block regeneration follows [the fresh evaluation guide](../../docs/guides/fresh-reevaluation.md) in its separately recorded Linux environment. The historical full pipeline can still be regenerated with the precompute entry points; its results require separate validation before admission. Never point an unavailable
junction at an unrelated environment to bypass these checks.

Use `01_init -Notebooks` (Bash: `--notebooks`) for the isolated lesson environment.
Local validation: `python scripts/check_notebooks.py`, then
`python scripts/run_notebooks.py --check --tmp <external scratch directory>`.
Full scientific tests use `.venv` and run locally, outside CI. CI performs schema,
content, design, manuscript declaration, notebook static, frontend and guard tests.
