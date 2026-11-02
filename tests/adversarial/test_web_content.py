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
    doc = json.loads((repo / "content/executive.json").read_text())
    path = doc["illustrations"]["pain"]["file"]
    (repo / "frontend/public" / path.lstrip("/")).unlink()
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1


def test_excessive_executive_card_text_is_rejected(repo):
    path = repo / "content/executive.json"
    doc = json.loads(path.read_text())
    doc["pain"]["bearers"][0]["who"]["en"] = "planner " * 40
    path.write_text(json.dumps(doc))
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "bearers" in r.stdout


def test_unknown_executive_source_is_rejected(repo):
    path = repo / "content/executive.json"
    doc = json.loads(path.read_text())
    doc["sources"].append({"id": "unused-source", "title": {"en": "unused", "es": "sin uso"},
                           "url": "https://doi.org/10.1016/j.ijforecast.2019.02.011",
                           "note": {"en": "unused reference", "es": "referencia sin uso"}})
    path.write_text(json.dumps(doc))
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "source" in r.stdout.lower()


def test_executive_scene_without_spanish_labels_is_rejected(repo):
    clean = guard(repo, "check_executive_assets.py")
    assert clean.returncode == 0, clean.stdout
    path = repo / "frontend/public/executive/pain.svg"
    source = path.read_text()
    assert 'data-lang="es"' in source
    path.write_text(source.replace('data-lang="es"', 'data-lang="removed"'))
    planted = guard(repo, "check_executive_assets.py")
    assert planted.returncode == 1 and "Spanish" in planted.stdout
