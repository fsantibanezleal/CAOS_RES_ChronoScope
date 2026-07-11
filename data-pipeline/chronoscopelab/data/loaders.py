"""Real-dataset loaders: read the private vault and emit license-cleared, Contract-1-shaped sample series.

Each loader reads a raw file from the local vault (``E:\\_Datos\\chronoscope``), selects a representative
single series, resamples/trims it to a compact window, and returns a long-format ``(unique_id, ds, y)`` table
ready for Contract 1. The pipeline commits only the small derived SAMPLE (a few hundred points) for a
PUBLIC-safe source; the raw bulk stays in the vault. Loaders are used offline to refresh
``data/examples/<name>.csv``; they are not called at bake time (the committed sample is).

Public-safe sources only (per provenance.py): UCI Electricity (CC-BY-4.0), UCI Beijing PM2.5 (CC-BY-4.0),
Monash M4 competition series (CC-BY-4.0, via the autogluon/chronos_datasets HF snapshot in the vault cache).
"""
from __future__ import annotations

import csv
import glob
import os
from pathlib import Path

# The private vault root (never committed; see data/README.md and the provenance policy).
VAULT = Path(r"E:\_Datos\chronoscope")
# The HF datasets cache holding the autogluon/chronos_datasets M4 snapshot (offline; never committed).
_HF_M4 = VAULT / "hf_cache" / "autogluon___chronos_datasets"


def _write_long_csv(out_path: Path, uid: str, timestamps: list[str], values: list[float]) -> int:
    """Write a long-format (unique_id, ds, y) CSV and return the row count."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["unique_id", "ds", "y"])
        for ts, v in zip(timestamps, values):
            w.writerow([uid, ts, f"{v:.4f}"])
    return len(timestamps)


def load_uci_electricity(meter: str = "MT_010", n_hours: int = 480,
                         start_row: int = 35040) -> tuple[list[str], list[float]]:
    """UCI ElectricityLoadDiagrams: one meter, resampled 15-min -> hourly, a ``n_hours`` window.

    The raw file is ``;``-separated with a first column of timestamps and MT_001..MT_370 load columns in kW
    (15-minute cadence). We sum each hour's four quarter-hour readings to hourly load. ``start_row`` skips the
    long all-zero warm-up at the start of many meters (35040 = ~one year of 15-min steps into 2012).
    """
    src = VAULT / "uci_electricity_370" / "LD2011_2014.txt"
    rows: list[list[str]] = []
    with open(src, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader)
        col = header.index(f'"{meter}"') if f'"{meter}"' in header else header.index(meter)
        for i, r in enumerate(reader):
            if i < start_row:
                continue
            rows.append([r[0].strip('"'), r[col]])
            if len(rows) >= n_hours * 4 + 4:
                break
    # aggregate the 15-min readings to hourly (sum of the four quarter-hours), keep the hour-start timestamp
    timestamps: list[str] = []
    values: list[float] = []
    for h in range(0, len(rows) - 3, 4):
        block = rows[h:h + 4]
        hourly = sum(float(b[1].replace(",", ".")) for b in block)
        timestamps.append(block[0][0])
        values.append(hourly)
        if len(values) >= n_hours:
            break
    return timestamps, values


def load_uci_beijing_pm25(n_hours: int = 480, start_row: int = 8760) -> tuple[list[str], list[float]]:
    """UCI Beijing PM2.5: the hourly pm2.5 column, a ``n_hours`` window (forward-filling the few NA gaps).

    ``start_row`` skips 2010 (the first year has the longest NA runs); the window lands in clean 2011 data.
    """
    src = VAULT / "uci_beijing_pm25" / "PRSA_data_2010.1.1-2014.12.31.csv"
    timestamps: list[str] = []
    values: list[float] = []
    last = 0.0
    with open(src, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, r in enumerate(reader):
            if i < start_row:
                continue
            raw = r.get("pm2.5", "NA")
            val = last if raw in ("NA", "", None) else float(raw)
            last = val
            ts = f"{r['year']}-{int(r['month']):02d}-{int(r['day']):02d} {int(r['hour']):02d}:00:00"
            timestamps.append(ts)
            values.append(val)
            if len(values) >= n_hours:
                break
    return timestamps, values


def _load_m4_config(config: str, n: int, m: int, min_std: float = 1e-6) -> tuple[str, list[str], list[float]]:
    """Read one representative series from the cached Monash M4 ``config`` (offline HF Arrow).

    Each Arrow row is a full series (parallel ``timestamp`` / ``target`` arrays). We pick the FIRST series
    (deterministic) whose length >= ``n`` and whose window has real seasonal structure (a positive lag-``m``
    autocorrelation and non-trivial variance), so the committed sample is a genuine seasonal case rather
    than a flat or too-short one. Returns ``(series_id, iso_timestamps, values)`` for the first ``n`` points.
    """
    import numpy as np
    from datasets import Dataset  # local, offline; the dep is already pinned for the pipeline

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
    arrows = glob.glob(str(_HF_M4 / config / "**" / "*.arrow"), recursive=True)
    if not arrows:
        raise FileNotFoundError(f"no cached Arrow for M4 config {config!r} under {_HF_M4}")
    ds = Dataset.from_file(arrows[0])
    for row in ds:
        tgt = row.get("target")
        ts = row.get("timestamp")
        if tgt is None or ts is None or len(tgt) < n:
            continue
        y = np.asarray(tgt[:n], dtype=float)
        if not np.all(np.isfinite(y)) or float(np.std(y)) < min_std:
            continue
        # require some seasonal signal at lag m (so we commit a genuinely seasonal sample)
        yc = y - y.mean()
        denom = float(np.dot(yc, yc))
        if denom <= 0:
            continue
        acf_m = float(np.dot(yc[m:], yc[:-m]) / denom) if len(yc) > m else 0.0
        if acf_m < 0.2:
            continue
        stamps = [str(t) for t in ts[:n]]
        return str(row.get("id", config)), stamps, [float(v) for v in y]
    raise ValueError(f"no suitable M4 series found in {config!r} (len>={n}, std>0, lag-{m} acf>=0.2)")


def load_m4_hourly(n_hours: int = 480) -> tuple[str, list[str], list[float]]:
    """A representative M4 hourly series (daily seasonality m=24): the real counterpart to SEAS_hourly."""
    return _load_m4_config("m4_hourly", n_hours, m=24)


def load_m4_daily(n_days: int = 400) -> tuple[str, list[str], list[float]]:
    """A representative M4 daily series (weekly seasonality m=7)."""
    return _load_m4_config("m4_daily", n_days, m=7)


def refresh_samples(examples_dir: str) -> dict[str, int]:
    """Regenerate the committed PUBLIC-safe sample CSVs from the vault. Returns {name: n_rows}.

    Run offline to refresh the committed excerpts (the bake reads the committed CSV, not the vault). Only
    public-safe sources are written here; local-only sources are never committed as raw excerpts.
    """
    out = Path(examples_dir)
    written: dict[str, int] = {}
    try:
        ts, ys = load_uci_electricity()
        written["electricity_sample.csv"] = _write_long_csv(out / "electricity_sample.csv", "MT_010", ts, ys)
    except FileNotFoundError:
        pass
    try:
        ts, ys = load_uci_beijing_pm25()
        written["beijing_pm25_sample.csv"] = _write_long_csv(out / "beijing_pm25_sample.csv", "BEIJING_PM25", ts, ys)
    except FileNotFoundError:
        pass
    # Monash M4 (CC-BY-4.0): real competition series at two seasonalities (hourly m=24, daily m=7).
    try:
        uid, ts, ys = load_m4_hourly()
        written["m4_hourly_sample.csv"] = _write_long_csv(out / "m4_hourly_sample.csv", f"M4H_{uid}", ts, ys)
    except (FileNotFoundError, ValueError):
        pass
    try:
        uid, ts, ys = load_m4_daily()
        written["m4_daily_sample.csv"] = _write_long_csv(out / "m4_daily_sample.csv", f"M4D_{uid}", ts, ys)
    except (FileNotFoundError, ValueError):
        pass
    return written
