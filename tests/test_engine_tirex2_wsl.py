"""TiRex-2 WSL2-lane engine: the opt-in, graceful-skip contract (CI-safe: no WSL required).

The heavy path (actually invoking TiRex-2 in WSL) is exercised offline on the build box; here we assert the
gate behaves: disabled by default, and merge_into is a no-op that leaves the ForecastResult + metrics
untouched when the lane is unavailable, so CI and the default bake never depend on WSL."""

from chronoscopelab.engines import tirex2_wsl_engine as tx
from chronoscopelab.io.schema import ForecastResult, MethodForecast, SeriesSpec


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("CHRONOSCOPE_ENABLE_TIREX_WSL", raising=False)
    assert tx.tirex2_enabled() is False
    assert tx.tirex2_available() is False


def test_merge_is_noop_when_unavailable(monkeypatch):
    monkeypatch.delenv("CHRONOSCOPE_ENABLE_TIREX_WSL", raising=False)
    spec = SeriesSpec(case_id="X", y=tuple(range(60)), seasonality=12, horizon=6)
    result = ForecastResult(
        case_id="X", horizon=6, seasonality=12, quantile_levels=(0.1, 0.5, 0.9), history=tuple(range(54)),
        methods=(MethodForecast("A", "classical", (1,) * 6, (0,) * 6, (2,) * 6),),
    )
    metrics = {"methods": {"A": {"mase": 1.0}}, "best_method": "A", "best_mase": 1.0}
    r2, m2 = tx.merge_into(result, metrics, spec, (0.1, 0.5, 0.9))
    assert len(r2.methods) == 1                 # unchanged: TiRex-2 not added
    assert set(m2["methods"]) == {"A"}
    assert "TiRex-2" not in m2["methods"]


def test_wsl_path_translation():
    assert tx._to_wsl_path(r"C:\Users\x\in.json") == "/mnt/c/Users/x/in.json"
    assert tx._to_wsl_path("D:/a/b.py") == "/mnt/d/a/b.py"
