"""Native Linux TiRex-2 inference; weights remain in the local model cache."""
from __future__ import annotations

import os
from functools import lru_cache

import numpy as np

from ..model.forecasters import Forecaster, _clean


def decile_columns(levels):
    columns = []
    for level in levels:
        decile = round(float(level) * 10)
        if decile < 1 or decile > 9 or abs(decile / 10 - level) > 1e-8:
            raise ValueError("TiRex-2 provides the nine deciles; requested level is not a decile")
        columns.append(decile - 1)
    return columns


@lru_cache(maxsize=1)
def _model():
    from tirex2 import load_model

    from ..gpu import device

    revision = os.environ.get("CHRONOSCOPE_TIREX_REVISION")
    if not revision:
        raise ValueError("Native TiRex-2 requires an explicit checkpoint revision")
    return load_model("NX-AI/TiRex-2", device=device(), hf_kwargs={"revision": revision})


class Tirex2Forecaster(Forecaster):
    name = "TiRex-2"
    family = "foundation"
    max_windows = 2

    def quantiles(self, y, m, h, levels):
        import torch
        from tirex2 import TimeseriesType

        yy = _clean(np.asarray(y, dtype=float))
        target = torch.tensor(yy, dtype=torch.float32).unsqueeze(0)
        series = TimeseriesType(target=target, past_covariates=None, future_covariates=None)
        with torch.inference_mode():
            result = _model().forecast(timeseries=[series], prediction_length=h, output_type="numpy")
        array = np.asarray(result[0])
        if array.ndim == 3 and array.shape[0] == 1:
            array = array[0]
        if array.shape != (9, h):
            raise ValueError(f"Unexpected TiRex-2 output shape: {array.shape}")
        return np.maximum.accumulate(array[decile_columns(levels)].T.astype(float), axis=1)


def tirex2_forecasters():
    if os.environ.get("CHRONOSCOPE_ENABLE_TIREX") != "1":
        return []
    try:
        import tirex2  # noqa: F401
    except ImportError:
        return []
    return [Tirex2Forecaster()]
