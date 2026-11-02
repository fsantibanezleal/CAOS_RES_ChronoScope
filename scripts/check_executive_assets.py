"""The three executive scenes keep theme paints and bilingual labels."""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]


def findings(root):
    doc = json.loads((root / "content/executive.json").read_text(encoding="utf-8"))
    out = []
    for name, scene in doc["illustrations"].items():
        path = root / "frontend/public" / scene["file"]
        source = path.read_text(encoding="utf-8")
        svg = ET.fromstring(source)
        langs = {e.get("data-lang") for e in svg.iter() if e.get("data-lang")}
        if not {"en", "es"}.issubset(langs):
            out.append(f"{name}: labels must include English and Spanish")
        if not svg.get("viewBox") or re.search(r"#[0-9a-fA-F]{3,8}\b", source):
            out.append(f"{name}: requires a viewBox and theme-token paints")
        for e in svg.iter():
            for attr in ("fill", "stroke"):
                value = e.get(attr, "none")
                if value not in ("none", "currentColor", "transparent") and not value.startswith(("var(", "url(")):
                    out.append(f"{name}: literal {attr} paint {value}")
    return out


if __name__ == "__main__":
    problems = findings(ROOT)
    for problem in problems:
        print(problem)
    if not problems:
        print("Executive assets: bilingual labels and theme paints")
    raise SystemExit(bool(problems))
