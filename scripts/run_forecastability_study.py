"""Execute the fixed M4 Daily study; raw input and resumable audits stay external."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time
import warnings

os.environ.setdefault("NUMBA_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-pipeline"))

import numpy as np  # noqa: E402
from chronoscopelab.analysis.atlas import MODEL_NAMES, PROTOCOL, partition, prefix_features, study_summary  # noqa: E402
from chronoscopelab.model.forecasters import METHODS  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, allow_nan=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def series_from_tsf(path: Path):
    """Read this corpus's explicitly checked series_name:start_timestamp:values schema."""
    in_data = False
    seen = set()
    with path.open(encoding="cp1252") as source:
        for raw in source:
            line = raw.strip()
            if line.lower() == "@data":
                in_data = True
                continue
            if not in_data or not line or line.startswith("#"):
                continue
            name, timestamp, values = line.split(":", 2)
            if name in seen or not name.isalnum():
                raise ValueError(f"Duplicate/unsafe series identity {name}")
            seen.add(name)
            yield name, timestamp, np.array([float(v) if v != "?" else np.nan for v in values.split(",")])


def evaluate(job):
    name, timestamp, y, cache = job
    destination = Path(cache) / f"{name}.json"
    if destination.exists():
        return json.loads(destination.read_text(encoding="utf-8"))
    sequence_hash = hashlib.sha256(np.asarray(y, dtype="<f8").tobytes()).hexdigest()
    row = {"id": name, "start_timestamp": timestamp, "source_n": len(y), "sequence_sha256": sequence_hash,
           "partition": partition(sequence_hash)}
    h, origins = PROTOCOL["horizon"], PROTOCOL["origins"]
    earliest = len(y) - h*origins
    if not np.isfinite(y).all() or earliest < PROTOCOL["minimum_prefix"]:
        row["excluded"] = "nonfinite source or insufficient earliest prefix"
        write(destination, row)
        return row
    started = time.perf_counter()
    row['features'] = prefix_features(y[max(0, earliest-PROTOCOL['context_cap']):earliest])
    row['origin_audit'] = []
    from statsforecast.models import AutoETS, AutoTheta
    for end in range(earliest, len(y), h):
        start = max(0, end-PROTOCOL['context_cap'])
        history, actual = y[start:end], y[end:end+h]
        scale = float(np.mean(np.abs(np.diff(history))))
        if not np.isfinite(scale) or scale <= 0:
            row['excluded'] = "zero or unavailable MASE scale"
            break
        predictions = {"Naive": np.repeat(history[-1], h)}
        with warnings.catch_warnings(record=True) as notices:
            warnings.simplefilter("always")
            predictions.update({n: fn(history, 1, h)[0] for n, _, fn in METHODS})
            for name_, factory in (("AutoETS", AutoETS), ("AutoTheta", AutoTheta)):
                model = factory(season_length=1)
                model.fit(history)
                predictions[name_] = np.asarray(model.predict(h)['mean'])
        if set(predictions) != set(MODEL_NAMES) or any(p.shape != (h,) or not np.isfinite(p).all() for p in predictions.values()):
            raise ValueError(f"Invalid forecast for {name} at {end}")
        row['origin_audit'].append({"start": start, "end": end, "scale": scale,
                                    "history_sha256": hashlib.sha256(np.asarray(history, dtype='<f8').tobytes()).hexdigest(),
                                    "actual": actual.tolist(), "predictions": {n: p.tolist() for n, p in predictions.items()},
                                    "mase": {n: float(np.mean(np.abs(actual-p))/scale) for n, p in predictions.items()},
                                    "warnings": sorted({w.category.__name__ for w in notices})})
    if 'excluded' not in row:
        row['mase'] = {n: float(np.mean([a['mase'][n] for a in row['origin_audit']])) for n in MODEL_NAMES}
        row['origins'] = [a['end'] for a in row['origin_audit']]
    row['seconds'] = time.perf_counter()-started
    write(destination, row)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-receipt', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--limit', type=int, help='Trial only; a limited result cannot pass admission')
    args = parser.parse_args()
    if any(p.resolve().is_relative_to(ROOT) for p in (args.source, args.cache, args.output)):
        parser.error('Source, cache and candidate output must stay outside Git')
    packages = {p: importlib.metadata.version(p) for p in ('numpy','scipy','stumpy','antropy','pycatch22','statsforecast','scikit-learn','joblib')}
    sources = [Path(__file__), ROOT/'data-pipeline/chronoscopelab/analysis/atlas.py',
               ROOT/'data-pipeline/chronoscopelab/analysis/sequence.py', ROOT/'data-pipeline/chronoscopelab/model/forecasters.py']
    code = {p.relative_to(ROOT).as_posix(): digest(p) for p in sources}
    identity = {"protocol": PROTOCOL, "packages": packages, "code_sha256": code, "source_sha256": digest(args.source)}
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    cache = args.cache/fingerprint
    records = list(series_from_tsf(args.source))
    if len(records) != 4227:
        raise ValueError(f"Expected the complete 4227-series source, found {len(records)}")
    selected = records[:args.limit] if args.limit else records
    all_rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(evaluate, ((n,t,y,str(cache)) for n,t,y in selected), chunksize=4):
            all_rows.append(row)
            if len(all_rows) % 50 == 0:
                print(f"M4 study: {len(all_rows)}/{len(selected)} series", flush=True)
    seen = {}
    for row in sorted(all_rows, key=lambda r: r['id']):
        if 'excluded' not in row:
            if row['sequence_sha256'] in seen:
                row['excluded'] = 'exact duplicate of '+seen[row['sequence_sha256']]
            else:
                seen[row['sequence_sha256']] = row['id']
    included = [r for r in all_rows if 'excluded' not in r]
    # Independently recalculate every score from retained paths before exporting compact data.
    for row in included:
        assert len(row['origin_audit']) == PROTOCOL['origins']
        for audit in row['origin_audit']:
            for n, values in audit['predictions'].items():
                independently_scored = sum(abs(a-p) for a,p in zip(audit['actual'], values, strict=True))/len(values)/audit['scale']
                if not np.isclose(independently_scored, audit['mase'][n], rtol=1e-12, atol=1e-12):
                    raise ValueError('Independent score mismatch')
    summary, model = study_summary(included)
    import joblib
    checkpoint = cache/'selector.joblib'
    joblib.dump(model, checkpoint)
    if code != {p.relative_to(ROOT).as_posix(): digest(p) for p in sources}:
        raise ValueError('Implementation changed during execution; candidate refused')
    compact = [{k:v for k,v in r.items() if k not in ('origin_audit','seconds')} for r in included]
    result = {"schema": "chronoscope.forecastability/v1", "complete": not bool(args.limit),
              **identity, "source": json.loads(args.source_receipt.read_text()), "source_n": len(records),
              "included_n": len(included), "excluded": [{k:v for k,v in r.items() if k in ('id','excluded','sequence_sha256')} for r in all_rows if 'excluded' in r],
              "model_names": list(MODEL_NAMES), "summary": summary, "series": compact,
              "audit": {"verified_origin_scores": len(included)*PROTOCOL['origins']*len(MODEL_NAMES),
                        "selector_sha256": digest(checkpoint), "cache_identity": fingerprint}}
    write(args.output, result)
    print(f"Study exported: {len(included)} admitted, {len(result['excluded'])} excluded; {summary['discovery_n']}/{summary['confirmation_n']} series partitions", flush=True)


if __name__ == '__main__':
    main()
