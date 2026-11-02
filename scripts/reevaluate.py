"""Produce the common final-holdout comparison without overwriting released traces."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-pipeline"))
from chronoscopelab.reevaluation import build  # noqa: E402

if __name__ == "__main__":
    document = build(ROOT)
    output = ROOT / "data/derived/reevaluation.json"
    output.write_text(json.dumps(document, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(f"reevaluation: {len(document['cases'])} cases, {len(document['summary'])} methods -> {output.name}")
