"""Published-source identity survives checkout and rejects altered PDF/source bytes."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("publication_bindings", ROOT / "scripts/check_publication_bindings.py")
bindings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bindings)


@pytest.mark.parametrize("defect", ["pdf", "source", "line-endings", "reviewed-hash"])
def test_adversarial_publication_rejects_changed_or_noncanonical_source(tmp_path, defect):
    folder = tmp_path / "report"
    shutil.copytree(ROOT / "manuscripts/product-report", folder,
                    ignore=shutil.ignore_patterns("*.aux", "*.log", "*.out", "*.toc"))
    candidate = next(c for c in json.loads((ROOT / "manuscripts/publication-candidates.json").read_text(encoding="utf-8"))["candidates"]
                     if c["pdf"] == "manuscripts/product-report/main.pdf")
    assert bindings.verify(folder, candidate) == "10.5281/zenodo.23884372"
    if defect == "pdf":
        path = folder / "main.pdf"
        path.write_bytes(path.read_bytes() + b"altered")
    elif defect == "reviewed-hash":
        candidate = copy.deepcopy(candidate)
        candidate["reviewed_source_sha256"] = "0"*64
    else:
        path = folder / "tex/main.tex"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n") if defect == "line-endings"
                         else path.read_bytes() + b"\nChanged scientific source\n")
    with pytest.raises(AssertionError):
        bindings.verify(folder, candidate)
