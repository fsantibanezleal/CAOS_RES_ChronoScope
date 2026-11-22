"""Verify a canonical HTTPS deployment against an exact committed artifact tree."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import ssl
import subprocess
import time
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ("/", "/app/", "/methodology/", "/implementation/", "/experiments/", "/benchmark/")


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def fetch(url: str, retry_log: list | None = None) -> tuple[bytes, str, int]:
    request = Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "ChronoScope-deployment-check"})
    for attempt in range(1, 4):
        try:
            with urlopen(request, timeout=60) as response:
                return response.read(), response.url, response.status
        except HTTPError as error:
            retryable = error.code in {429, 500, 502, 503, 504} and attempt < 3
            delay = .5 * 2 ** (attempt - 1)
            retry_after = error.headers.get("Retry-After") if error.headers else None
            if retry_after:
                try:
                    requested = float(retry_after)
                    # Refuse instead of retrying sooner than a long server-requested wait.
                    retryable = retryable and 0 <= requested <= 10
                    delay = max(delay, requested)
                except ValueError:
                    retryable = False
            error.close()
            if not retryable:
                raise
            if retry_log is not None:
                retry_log.append({"url": url, "attempt": attempt, "status": error.code, "delay_seconds": delay})
            time.sleep(delay)
    raise AssertionError("Unreachable retry state")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    origin = args.url.rstrip("/")
    parsed = urlsplit(origin)
    if parsed.scheme != "https" or parsed.path or not parsed.hostname:
        parser.error("--url must be the canonical HTTPS origin")
    sha = git("rev-parse", f"{args.sha}^{{commit}}").decode().strip()
    version = git("show", f"{sha}:VERSION").decode().strip()
    nonce = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    report: dict = {"ok": False, "checked_utc": datetime.now(timezone.utc).isoformat(),
                    "origin": origin, "source_sha": sha, "version": version}
    retries: list = []
    report["http_retries"] = retries
    try:
        report["dns_addresses"] = sorted({item[4][0] for item in socket.getaddrinfo(parsed.hostname, 443)})
        context = ssl.create_default_context()
        with socket.create_connection((parsed.hostname, 443), timeout=30) as connection:
            with context.wrap_socket(connection, server_hostname=parsed.hostname) as secured:
                certificate = secured.getpeercert()
                report["tls"] = {"verified": True, "protocol": secured.version(),
                                 "subject_alt_names": certificate.get("subjectAltName"),
                                 "not_after": certificate.get("notAfter")}
        body, final, status = fetch(f"{origin}/build.json?verify={nonce}", retries)
        build = json.loads(body)
        assert build["sha"] == sha and build["version"] == version, build
        assert urlsplit(final).netloc == parsed.netloc and status == 200
        report["build"] = build
        report["routes"] = []
        for route in ROUTES:
            body, final, status = fetch(f"{origin}{route}?verify={nonce}", retries)
            assert status == 200 and urlsplit(final).netloc == parsed.netloc
            assert b"<html" in body and b"ChronoScope" in body and b"data-theme" in body, route
            report["routes"].append({"route": route, "status": status, "final_url": final})

        entries = git("ls-tree", "-rz", sha, "--", "data/derived").split(b"\0")

        def artifact(entry: bytes) -> dict:
            metadata, raw_path = entry.split(b"\t", 1)
            object_id = metadata.decode().split()[2]
            path = raw_path.decode()
            expected = git("cat-file", "blob", object_id)
            remote_path = "/data/" + path.removeprefix("data/derived/")
            actual, final, status = fetch(f"{origin}{quote(remote_path)}?verify={nonce}", retries)
            assert status == 200 and urlsplit(final).netloc == parsed.netloc
            expected_hash = hashlib.sha256(expected).hexdigest()
            actual_hash = hashlib.sha256(actual).hexdigest()
            assert actual_hash == expected_hash, f"Artifact mismatch: {remote_path}"
            return {"path": remote_path, "bytes": len(actual), "sha256": actual_hash}

        with ThreadPoolExecutor(max_workers=6) as pool:
            report["artifacts"] = list(pool.map(artifact, filter(None, entries)))
        report["ok"] = True
    except Exception as error:
        report["error"] = str(error)
        if isinstance(error, HTTPError):
            report["failed_url"] = error.url
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Canonical deployment: {len(report['routes'])} routes and {len(report['artifacts'])} exact artifacts passed ({sha})")


if __name__ == "__main__":
    main()
