"""Produce the common final-holdout comparison without overwriting released traces."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-pipeline"))
from engine.reevaluation import build  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Candidate JSON outside the repository")
    output = parser.parse_args().output.resolve()
    if output == ROOT or output.is_relative_to(ROOT):
        parser.error("--output must be outside the repository; admitted research artifacts are immutable inputs")
    document = build(ROOT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(f"reevaluation: {len(document['cases'])} cases, {len(document['summary'])} methods -> {output.name}")
