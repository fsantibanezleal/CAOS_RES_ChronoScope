# scripts/: environment + pipeline orchestration (cross-platform)

Local scripts so **anyone** can configure the env and run the flow. Provide every script in BOTH `*.sh`
(macOS/Linux/Git-Bash) and `*.ps1` (Windows PowerShell, since Felipe runs PS).

## How to populate

| Script | What it must do |
|---|---|
| `setup.sh` / `setup.ps1` | forward to `local/workflow.py init`: initialize the explicitly configured external environments and frontend lock; print the next commands. Notebook and GPU environments are opt-in. |
| `precompute.sh` / `precompute.ps1` | forward to `local/workflow.py generate`: prepare and admit an external candidate. Promotion requires `--release --from-stage` (PowerShell: `-Release -FromStage`). |
| `fetch-data.sh` / `fetch-data.ps1` | (optional) stage raw inputs into `data/raw/` (gitignored). Never commit raw. |
| `serve-api.sh` / `serve-api.ps1` | (optional, only if `api/` is active) `uvicorn api.main:app --reload`. |

Rules: idempotent; detect `.venv/bin/python` vs `.venv/Scripts/python.exe`; never use global Python/Node.
Pin nothing here, versions live in `requirements-*.txt`.

All legacy entrypoints call the numbered workflow rather than implementing a
second installation or generation path. See [local/README.md](local/README.md)
for role-root configuration, admission, rollback and the research reproduction
boundaries. The historical full-engine bake is a separate explicit operation
documented in the research guides; `precompute` never starts it implicitly.
