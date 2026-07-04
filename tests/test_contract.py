"""CONTRACT 1 (ingestion) tests: good series validate; bad series are rejected with a reason; missing values
and outliers are flagged but accepted."""
from chronoscopelab.io.contract import MIN_OBS, validate_rows


def _rows(uid, ys):
    return [{"unique_id": uid, "ds": f"2020-01-{i + 1:02d}", "y": v} for i, v in enumerate(ys)]


def test_good_series_accepted():
    rep = validate_rows(_rows("a", [float(v) for v in range(20)]))
    assert rep.ok and len(rep.accepted) == 1 and not rep.rejected


def test_missing_required_column_rejected():
    rep = validate_rows([{"unique_id": "a", "y": 1.0}])  # no ds
    assert not rep.ok and rep.rejected


def test_too_short_rejected():
    rep = validate_rows(_rows("short", [1.0, 2.0, 3.0]))  # < MIN_OBS
    assert len(rep.accepted) == 0 and any(str(MIN_OBS) in r["reason"] for r in rep.rejected)


def test_non_numeric_rejected_not_coerced():
    rep = validate_rows(_rows("txt", ["fast"] * 10))
    assert len(rep.accepted) == 0 and "non-numeric" in rep.rejected[0]["reason"]


def test_outlier_flagged_but_accepted():
    ys = [10.0] * 20 + [10_000.0]  # one gross outlier
    rep = validate_rows(_rows("hot", ys))
    assert rep.ok and rep.flagged and "z" in rep.flagged[0]["flag"]


def test_unsorted_timestamps_flagged_and_sorted():
    rows = [{"unique_id": "u", "ds": f"2020-01-{d:02d}", "y": float(d)} for d in [3, 1, 2, 4, 5, 6, 7, 8, 9, 10]]
    rep = validate_rows(rows)
    assert rep.ok
    assert rep.accepted[0].ds == sorted(rep.accepted[0].ds)  # sorted on ingest
    assert any("increasing" in f["flag"] for f in rep.flagged)
