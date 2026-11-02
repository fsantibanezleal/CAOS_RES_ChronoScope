"""Keep product-neutral inherited checks free of owner-specific prose."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]


def findings(root):
    holder = json.loads((root / "product.json").read_text(encoding="utf-8"))["holder"]
    first = holder.split()[0]
    pattern = re.compile(r"\b" + re.escape(first) + r"\b", re.I)
    paths = [*sorted((root / "scripts").glob("check_*.py")), root / "frontend/scripts/gate.mjs"]
    return [str(p.relative_to(root)) for p in paths if pattern.search(p.read_text(encoding="utf-8"))]


if __name__ == "__main__":
    problems = findings(ROOT)
    for path in problems:
        print(f"Owner-specific prose in inherited guard: {path}")
    if not problems:
        print("Inherited guards: owner-neutral")
    raise SystemExit(bool(problems))
