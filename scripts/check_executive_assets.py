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
        files = scene.get("file")
        if isinstance(files, str):
            variants = [("shared", files, {"en", "es"})]
        elif isinstance(files, dict) and set(files) == {"en", "es"}:
            variants = [(lang, files[lang], {lang}) for lang in ("en", "es")]
        else:
            out.append(f"{name}: file must name a shared SVG or both English and Spanish SVGs")
            continue
        for lang, relative, expected_langs in variants:
            where = f"{name}.{lang}"
            if not isinstance(relative, str) or not relative.strip():
                out.append(f"{where}: missing illustration path")
                continue
            public = (root / "frontend/public").resolve()
            path = (public / relative.lstrip("/")).resolve()
            if not path.is_relative_to(public) or not path.is_file():
                out.append(f"{where}: illustration must exist inside frontend/public")
                continue
            try:
                source = path.read_text(encoding="utf-8")
                svg = ET.fromstring(source)
            except (OSError, UnicodeError, ET.ParseError):
                out.append(f"{where}: illustration must be readable SVG XML")
                continue
            langs = {e.get("data-lang") for e in svg.iter() if e.get("data-lang")}
            if not expected_langs.issubset(langs):
                out.append(f"{where}: labels must include the selected English or Spanish language")
            if not svg.get("viewBox") or re.search(r"#[0-9a-fA-F]{3,8}\b", source):
                out.append(f"{where}: requires a viewBox and theme-token paints")
            for e in svg.iter():
                for attr in ("fill", "stroke"):
                    value = e.get(attr, "none")
                    if value not in ("none", "currentColor", "transparent") and not value.startswith(("var(", "url(")):
                        out.append(f"{where}: literal {attr} paint {value}")
    return out


if __name__ == "__main__":
    problems = findings(ROOT)
    for problem in problems:
        print(problem)
    if not problems:
        print("Executive assets: bilingual labels and theme paints")
    raise SystemExit(bool(problems))
