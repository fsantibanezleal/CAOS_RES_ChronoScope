#!/usr/bin/env bash
# Deprecated compatibility entrypoint; use scripts/bake.py.
set -euo pipefail
cd "$(dirname "$0")/.."
VP=".venv-pipeline/bin/python"; [ -x "$VP" ] || VP=".venv-pipeline/Scripts/python.exe"
"$VP" -m chronoscopelab.pipeline "$@"
