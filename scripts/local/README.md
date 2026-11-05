# Local workflow

Run `00_install-prereqs` to check Python, Node and Git; `01_init` initializes declared
Python environments and the frontend lock; `02_generate-data` prepares an external
candidate; `03_dev` validates the shipped corpus before starting Vite. Both PowerShell
and Bash entry points call the same standard-library workflow implementation.

Set absolute external `CAOS_VENVS_ROOT`, `CAOS_DATA_ROOT`, `CAOS_MODELS_ROOT`
and `CAOS_TEMP_ROOT` in the process environment or `.env`. Initialization allocates
environments under `<CAOS_VENVS_ROOT>/chronoscope/<runtime>`. An existing runtime
alias must resolve to that directory; initialization refuses a different local
directory or redirected namespace before installing anything. It never moves,
deletes or redirects an existing environment. The interpreter can be overridden
with `PYTHON`; PowerShell entrypoints preserve native exit status.

Generation recomputes the eight
light variants from the immutable released histories and rescores fourteen frozen model
paths. It carries the already admitted fresh experiment unchanged and verifies its source, input and metric bindings. The complete admitted sequence diagnostics and M4 corpus study are carried unchanged and checked independently. It does not rerun the corpus forecasts, train or download foundation models. The explicit
`02_generate-data --release --from-stage <candidate>` operation validates source and
payload fingerprints, then promotes the complete candidate transactionally. A partial
corpus, altered released input, stale implementation binding, source change during
execution, unavailable environment alias or occupied development port fails closed.

The product admission hook replaces the template example's readiness and engine-version
assumptions: historical engine versions are retained rather than rewritten. Fresh final-block regeneration follows [the fresh evaluation guide](../../docs/guides/fresh-reevaluation.md) in its separately recorded Linux environment. The historical full pipeline is a separate explicit research operation, not the legacy `precompute` shortcut. Its results require separate validation before admission. Never point an unavailable
junction at an unrelated environment to bypass these checks.

The complete weekly/monthly combination index, all 1,802 series documents and
the compressed full audit are frozen authored inputs. Admission checks exact
inventory, bytes, implementation/export bindings and the selected-case source.
A missing study is an error even when the earlier fifteen-case comparison still
passes. Source, payload and receipt hashes stay bound through validation,
copying and installation; a late mutation triggers transactional rollback.

Use `01_init -Notebooks` (Bash: `--notebooks`) for the isolated lesson environment.
Local validation: `python scripts/check_notebooks.py`, then
`python scripts/run_notebooks.py --check --tmp <external scratch directory>`.
Full scientific tests use `.venv` and run locally, outside CI. CI performs schema,
content, design, manuscript declaration, notebook static, frontend and guard tests.

For complete sequence/corpus reproduction and the distinction between full forecast execution and
compact-table lesson checks, see the [research extension guide](../../docs/guides/research-extensions.md).
