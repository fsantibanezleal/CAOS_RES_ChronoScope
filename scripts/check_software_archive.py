"""Verify a public Zenodo software ZIP against git archive of an exact release commit."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
from urllib.request import Request, urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
CONCEPT = "10.5281/zenodo.23875114"
REPO = "https://github.com/fsantibanezleal/CAOS_RES_ChronoScope"


def fetch(url):
    with urlopen(
        Request(url, headers={"User-Agent": "ChronoScope-release-verification"}), timeout=120
    ) as response:
        return response.read()


def members(payload, strip_root=False):
    result = {}
    with ZipFile(BytesIO(payload)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = info.filename.split("/", 1)[1] if strip_root else info.filename
            if name in result:
                raise ValueError("Duplicate ZIP member")
            result[name] = archive.read(info)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=int, required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sha = subprocess.check_output(["git", "rev-parse", f"{args.sha}^{{commit}}"], cwd=ROOT).decode().strip()
    version = subprocess.check_output(["git", "show", f"{sha}:VERSION"], cwd=ROOT).decode().strip()
    report = {
        "ok": False,
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha": sha,
        "record_id": args.record,
        "version": "v" + version,
    }
    try:
        record = json.loads(fetch(f"https://zenodo.org/api/records/{args.record}"))
        assert record["conceptdoi"] == CONCEPT and record["metadata"]["version"] == "v" + version
        assert record["metadata"]["resource_type"]["type"] == "software"
        assert any(
            r["identifier"] == REPO + "/tree/v" + version for r in record["metadata"]["related_identifiers"]
        )
        assert len(record["files"]) == 1 and record["files"][0]["key"].endswith(".zip")
        file = record["files"][0]
        payload = fetch(file["links"]["self"])
        md5 = hashlib.md5(payload).hexdigest()
        assert file["checksum"] == "md5:" + md5 and file["size"] == len(payload)
        remote = members(payload, strip_root=True)
        local_zip = subprocess.check_output(["git", "archive", "--format=zip", sha], cwd=ROOT)
        local = members(local_zip)
        assert remote.keys() == local.keys(), "Archive inventory differs"
        assert all(remote[k] == value for k, value in local.items()), "Archive member differs"
        report.update(
            ok=True,
            doi=record["doi"],
            concept_doi=CONCEPT,
            archive_bytes=len(payload),
            archive_md5=md5,
            archive_sha256=hashlib.sha256(payload).hexdigest(),
            verified_archive_members=len(remote),
            related_identifiers=record["metadata"]["related_identifiers"],
            comparison="Every member matches git archive of the exact source commit, including .gitattributes eol conversion.",
        )
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Software archive: {len(remote)} members match {sha}")


if __name__ == "__main__":
    main()
