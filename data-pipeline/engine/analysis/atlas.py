"""Prefix-only corpus features, BY-confirmed associations and held-out selection."""
from __future__ import annotations

import hashlib

import numpy as np
from scipy import stats

from .sequence import finite_sequence, matrix_profile, multiscale_entropy, time_reversal
from ..model.forecasters import METHODS

MODEL_NAMES = ("Naive", *(name for name, _, _ in METHODS), "AutoETS", "AutoTheta")
PROTOCOL = {"horizon": 14, "origins": 3, "context_cap": 1024, "seasonality": 1,
            "duplicates": "retain lexicographically first exact whole-sequence duplicate only",
            "minimum_prefix": 32, "q": .05, "discovery_percent": 70, "seed": 42,
            "target": "log1p of per-series minimum mean MASE across the fixed roster",
            "feature_origin": "earliest forecast origin only", "correction": "Benjamini-Yekutieli",
            "selection": {"class": "RandomForestClassifier", "n_estimators": 200, "max_depth": 8,
                          "min_samples_leaf": 10, "random_state": 42}}


def partition(sequence_hash: str) -> str:
    """Exact duplicates stay together, independently of the observed labels."""
    value = int(hashlib.sha256(("chronoscope-atlas-v1:"+sequence_hash).encode()).hexdigest()[:8], 16)
    return "discovery" if value % 100 < PROTOCOL["discovery_percent"] else "confirmation"


def prefix_features(history) -> dict[str, float | None]:
    import antropy
    import pycatch22

    a = finite_sequence(history)
    if len(a) < PROTOCOL["minimum_prefix"]:
        raise ValueError("Insufficient feature prefix")
    sd = np.std(a)
    z = (a-a.mean()) / sd if sd else np.zeros_like(a)
    feature = {"history_length": float(len(a)), "log_std": float(np.log1p(sd)),
               "skewness": float(stats.skew(a)) if sd else 0.,
               "kurtosis": float(stats.kurtosis(a)) if sd else 0.,
               "linear_trend_r": float(np.corrcoef(np.arange(len(a)), a)[0, 1]) if sd else 0.,
               "acf_1": float(np.corrcoef(a[:-1], a[1:])[0, 1]) if sd else 0.,
               "acf_7": float(np.corrcoef(a[:-7], a[7:])[0, 1]) if sd else 0.,
               "weekly_phase_strength": 0.}
    if sd and len(a) >= 21:
        phase = np.array([z[np.arange(len(z)) % 7 == i].mean() for i in range(7)])
        feature["weekly_phase_strength"] = float(np.var(phase))
    catch = pycatch22.catch22_all(a.tolist(), catch24=True)
    feature.update({"catch24_"+k: float(v) for k, v in zip(catch["names"], catch["values"], strict=True)})
    entropy = multiscale_entropy(a, scales=(1, 2, 5, 10))
    feature.update({f"mse_{r['scale']}": r['entropy'] for r in entropy['scales']})
    feature["lz_binary"] = float(antropy.lziv_complexity((a > np.median(a)).astype(int), normalize=True))
    feature["reversal_1"] = time_reversal(a)["standardized"]
    profile = matrix_profile(a, window=min(32, len(a)//3))
    values = np.asarray([v for v in profile.get("profile", []) if v is not None])
    feature["profile_median"] = float(np.median(values)/np.sqrt(profile["window"])) if len(values) else None
    feature["profile_max"] = float(np.max(values)/np.sqrt(profile["window"])) if len(values) else None
    return {k: float(v) if v is not None and np.isfinite(v) else None for k, v in sorted(feature.items())}


def by_adjust(pvalues) -> np.ndarray:
    p = np.asarray(pvalues, dtype=float)
    if p.ndim != 1 or not len(p) or not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError("BY correction requires finite probabilities")
    return stats.false_discovery_control(p, method="by")


def associations(rows: list[dict]) -> list[dict]:
    if not rows:
        raise ValueError("A study partition cannot be empty")
    result = []
    target = np.log1p([min(r['mase'].values()) for r in rows])
    for name in sorted(rows[0]['features']):
        x = np.array([r['features'][name] if r['features'][name] is not None else np.nan for r in rows])
        keep = np.isfinite(x) & np.isfinite(target)
        tau, p = stats.kendalltau(x[keep], target[keep]) if keep.sum() >= 20 and np.std(x[keep]) else (0., 1.)
        result.append({"feature": name, "n": int(keep.sum()), "tau": float(tau) if np.isfinite(tau) else 0.,
                       "p": float(p) if np.isfinite(p) else 1.})
    adjusted = by_adjust([r['p'] for r in result])
    for row, q in zip(result, adjusted, strict=True):
        row.update(q=float(q), rejected=bool(q <= PROTOCOL['q']))
    return result


def study_summary(rows: list[dict]) -> tuple[dict, object]:
    from sklearn.ensemble import RandomForestClassifier

    discovery = [r for r in rows if r['partition'] == 'discovery']
    confirmation = [r for r in rows if r['partition'] == 'confirmation']
    if not discovery or not confirmation:
        raise ValueError("Both independent series partitions are required")
    d, c = associations(discovery), associations(confirmation)
    association = [{"feature": a['feature'], "discovery": a, "confirmation": b,
                    "confirmed": bool(a['rejected'] and b['rejected'] and a['tau']*b['tau'] > 0)}
                   for a, b in zip(d, c, strict=True)]
    features = sorted(rows[0]['features'])
    xd = np.array([[r['features'][f] if r['features'][f] is not None else np.nan for f in features] for r in discovery])
    xc = np.array([[r['features'][f] if r['features'][f] is not None else np.nan for f in features] for r in confirmation])
    # Missing-value imputation is fitted on discovery only, including all-missing columns.
    medians = np.array([np.median(col[np.isfinite(col)]) if np.isfinite(col).any() else 0. for col in xd.T])
    xd, xc = np.where(np.isfinite(xd), xd, medians), np.where(np.isfinite(xc), xc, medians)
    labels = np.array([min(MODEL_NAMES, key=lambda n: r['mase'][n]) for r in discovery])
    model = RandomForestClassifier(n_estimators=200, max_depth=8, min_samples_leaf=10, random_state=42, n_jobs=4)
    model.fit(xd, labels)
    predictions = model.predict(xc)
    constant = min(MODEL_NAMES, key=lambda name: np.mean([r['mase'][name] for r in discovery]))
    for row, predicted in zip(confirmation, predictions, strict=True):
        row['selected_method'] = str(predicted)
    scores = {"selected": float(np.mean([r['mase'][p] for r, p in zip(confirmation, predictions, strict=True)])),
              "discovery_constant": float(np.mean([r['mase'][constant] for r in confirmation])),
              "oracle": float(np.mean([min(r['mase'].values()) for r in confirmation]))}
    return {"discovery_n": len(discovery), "confirmation_n": len(confirmation), "associations": association,
            "constant_method": constant, "selection_mean_mase": scores,
            "model_mean_mase": {n: float(np.mean([r['mase'][n] for r in confirmation])) for n in MODEL_NAMES},
            "selector_features": features, "discovery_medians": medians.tolist(),
            "limitations": ["Confirmation is disjoint by exact sequence, not necessarily by underlying source or industry.",
                            "The target uses the best of a bounded roster and is an optimistic oracle, not inherent predictability.",
                            "Feature association does not establish causality; BY's assumptions may fail for related series.",
                            "No foundation or deep model is included in this separate corpus study."]}, model
