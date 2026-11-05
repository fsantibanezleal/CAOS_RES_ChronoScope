"""Build review PDFs and exact local-input receipts outside the source tree."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUGS = ("context-memory", "product-report", "prequential-streaming-conformal")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh_replay(scratch: Path) -> None:
    """Run predecessor generators in an isolated input copy, preserving originals."""
    stage = scratch / "replay-generator-inputs"
    slug = "manuscripts/prequential-streaming-conformal"
    inputs = ("scripts/make_manuscript_tables.py", f"{slug}/figures/make_figs.py", f"{slug}/evidence/replay.json")
    for rel in inputs:
        target = stage / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)
    protected = {rel: digest(ROOT / rel) for rel in inputs}
    for rel in ("scripts/make_manuscript_tables.py", f"{slug}/figures/make_figs.py"):
        subprocess.run([sys.executable, str(stage / rel)], cwd=stage, check=True)
    target = ROOT / slug / "next"
    for name in ("coverage", "efficiency", "sensitivity", "seeds"):
        source = (stage / slug / "tables" / f"{name}.tex").read_text(encoding="utf-8")
        lines = source.splitlines()
        caption = next(i for i, line in enumerate(lines) if line.startswith("\\caption{"))
        lines.insert(caption + 1, f"\\label{{tab:{name}}}")
        (target / "tables" / f"{name}.tex").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    for name in ("fig-coverage-percase.pdf", "fig-coverage-summary.pdf"):
        shutil.copy2(stage / slug / "figures" / name, target / "figures" / name)
    for name in ("fig-prequential.pdf", "fig-prequential.svg"):
        shutil.copy2(ROOT / slug / "figures" / name, target / "figures" / name)
    subprocess.run([sys.executable, str(ROOT / "scripts/analyze_replay_cases.py"), "--check", "--render"],
                   cwd=ROOT, check=True)
    assert protected == {rel: digest(ROOT / rel) for rel in inputs}, "A frozen generator input changed"


def build(slug: str, scratch: Path) -> None:
    folder = ROOT / "manuscripts" / slug / "next"
    output = scratch / slug
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run(["latexmk", "-cd", "-pdf", "-recorder", "-interaction=nonstopmode", "-halt-on-error",
                    f"-outdir={output.as_posix()}", str(folder / "tex/main.tex")], cwd=ROOT, check=True)
    log = (output / "main.log").read_text(encoding="utf-8", errors="replace")
    bad = ("has been already used, duplicate ignored", "There were undefined references", "Citation `", "Overfull \\hbox")
    if any(marker in log for marker in bad):
        raise ValueError(f"Unresolved LaTeX layout/reference warning in {output / 'main.log'}")
    sources = {}
    for line in (output / "main.fls").read_text(encoding="utf-8").splitlines():
        if not line.startswith("INPUT "):
            continue
        path = Path(line[6:].strip().strip('"'))
        if not path.is_absolute():
            path = folder / "tex" / path
        path = path.resolve()
        if path.is_relative_to(ROOT.resolve()) and path.is_file() and path.suffix in (".tex", ".pdf", ".svg"):
            sources[path.relative_to(ROOT).as_posix()] = digest(path)
    assert (folder / "tex/main.tex").relative_to(ROOT).as_posix() in sources
    shutil.copy2(output / "main.pdf", folder / "main.pdf")
    pdf = folder / "main.pdf"
    engine = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    receipt = {"state": "working-revision", "published": False, "independent_reader_review": "pending",
               "scope": "Compiled PDF and local input identity only; not publication acceptance",
               "latex_engine": engine, "pdf_sha256": digest(pdf), "pdf_bytes": pdf.stat().st_size,
               "source_files": dict(sorted(sources.items()))}
    (folder / "build-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Bound {slug}: {len(sources)} local inputs, PDF {receipt['pdf_sha256']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--only", choices=SLUGS, action="append")
    parser.add_argument("--refresh-replay-inputs", action="store_true")
    args = parser.parse_args()
    scratch = args.scratch.resolve()
    if scratch.is_relative_to(ROOT.resolve()):
        raise ValueError("Use an external scratch folder; source-tree build output is prohibited")
    scratch.mkdir(parents=True, exist_ok=True)
    if args.refresh_replay_inputs:
        refresh_replay(scratch)
    for slug in args.only or SLUGS:
        build(slug, scratch)


if __name__ == "__main__":
    main()
