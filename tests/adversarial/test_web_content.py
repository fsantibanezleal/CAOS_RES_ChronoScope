"""Planted content defects run against the actual product's design and executive guards."""
import json

from planting import guard


def test_missing_executive_data_is_rejected(repo):
    (repo / "content/executive.json").unlink()
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "executive.json" in r.stdout


def test_missing_installed_schema_is_rejected(repo):
    path = repo / "frontend/node_modules/@fasl-work/caos-app-shell/src/content/executive.schema.json"
    path.unlink()
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "schema" in r.stdout


def test_missing_executive_illustration_is_rejected(repo):
    doc = json.loads((repo / "content/executive.json").read_text(encoding="utf-8"))
    path = doc["illustrations"]["pain"]["file"]
    if isinstance(path, dict):
        path = path["es"]
    (repo / "frontend/public" / path.lstrip("/")).unlink()
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1


def test_excessive_executive_card_text_is_rejected(repo):
    path = repo / "content/executive.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["pain"]["bearers"][0]["who"]["en"] = "planner " * 40
    path.write_text(json.dumps(doc), encoding="utf-8")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "bearers" in r.stdout


def test_unknown_executive_source_is_rejected(repo):
    path = repo / "content/executive.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["sources"].append({"id": "unused-source", "title": {"en": "unused", "es": "sin uso"},
                           "url": "https://doi.org/10.1016/j.ijforecast.2019.02.011",
                           "note": {"en": "unused reference", "es": "referencia sin uso"}})
    path.write_text(json.dumps(doc), encoding="utf-8")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "source" in r.stdout.lower()


def test_executive_scene_without_spanish_labels_is_rejected(repo):
    clean = guard(repo, "check_executive_assets.py")
    assert clean.returncode == 0, clean.stdout
    doc = json.loads((repo / "content/executive.json").read_text(encoding="utf-8"))
    file = doc["illustrations"]["pain"]["file"]
    path = repo / "frontend/public" / (file["es"] if isinstance(file, dict) else file)
    source = path.read_text(encoding="utf-8")
    assert 'data-lang="es"' in source
    path.write_text(source.replace('data-lang="es"', 'data-lang="removed"'), encoding="utf-8")
    planted = guard(repo, "check_executive_assets.py")
    assert planted.returncode == 1 and "Spanish" in planted.stdout


def test_executive_shared_and_bilingual_files_are_both_admitted(repo):
    assert guard(repo, "check_executive_assets.py").returncode == 0
    path = repo / "content/executive.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    for scene in doc["illustrations"].values():
        if isinstance(scene["file"], dict):
            scene["file"] = scene["file"]["en"]
    path.write_text(json.dumps(doc), encoding="utf-8")
    assert guard(repo, "check_executive_assets.py").returncode == 0


def test_executive_missing_spanish_file_is_refused(repo):
    path = repo / "content/executive.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    file = doc["illustrations"]["pain"]["file"]
    english = file["en"] if isinstance(file, dict) else file
    doc["illustrations"]["pain"]["file"] = {"en": english, "es": "executive/absent-es.svg"}
    path.write_text(json.dumps(doc), encoding="utf-8")
    result = guard(repo, "check_executive_assets.py")
    assert result.returncode == 1 and "pain.es" in result.stdout


def test_executive_spanish_variant_keeps_theme_paints(repo):
    path = repo / "content/executive.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    file = doc["illustrations"]["pain"]["file"]
    source = repo / "frontend/public" / (file["es"] if isinstance(file, dict) else file)
    source.write_text(source.read_text(encoding="utf-8").replace('fill="var(', 'fill="#fff" data-original="var(', 1), encoding="utf-8")
    result = guard(repo, "check_executive_assets.py")
    assert result.returncode == 1 and "theme-token" in result.stdout
