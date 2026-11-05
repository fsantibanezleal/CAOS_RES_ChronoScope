"""Model-interface adversaries without checkpoint downloads or mocked accuracy claims."""
import copy
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("timestral_study", ROOT / "scripts/evaluate_timestral.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)
SETTINGS = {"probabilities": [.1, .5, .9], "symmetric_averaging": True, "clip_nonnegative": True}
LEVELS = (.01, .05, .1, .15, .2, .25, .3, .35, .4, .45, .5, .55, .6, .65, .7, .75, .8, .85, .9, .95, .99)


class Recorder:
    def __init__(self, defect=None):
        self.calls = []
        self.defect = defect

    def forecast(self, history, **kwargs):
        self.calls.append((history.copy(), kwargs))
        q = np.broadcast_to(np.arange(21) + 430., (1, 1, kwargs["prediction_length"], 21)).copy()
        if self.defect == "nonfinite":
            q[..., 0] = np.nan
        elif self.defect == "crossing":
            q[..., 2] = 500
        elif self.defect == "shape":
            q = q[0]
        return SimpleNamespace(quantiles=q, quantile_levels=LEVELS)


def case():
    return {"case_id": "probe", "history": [433., 450., 484., 460.], "actual": [441., 443.],
            "horizon": 2, "seasonality": 1}


def test_adversarial_only_prefix_and_declared_configuration_reach_the_model():
    model = Recorder()
    original = case()
    row = study.forecast_case(model, original, SETTINGS)
    changed = copy.deepcopy(original)
    changed["actual"] = [480., 481.]
    later = study.forecast_case(model, changed, SETTINGS)
    assert np.array_equal(model.calls[0][0], np.array(original["history"], dtype=np.float32))
    assert np.array_equal(model.calls[0][0], model.calls[1][0])
    assert model.calls[0][1] == {"prediction_length": 2, "symmetric_averaging": True, "clip_nonnegative": True}
    assert row["lower"] == [432., 432.] and row["point"] == [440., 440.] and row["upper"] == [448., 448.]
    assert row["point"] == later["point"] and row["metrics"] != later["metrics"]
    assert row["metrics"]["mae"] == 2


@pytest.mark.parametrize("defect", ["nonfinite", "crossing", "shape"])
def test_adversarial_malformed_public_model_output_refuses(defect):
    with pytest.raises(ValueError):
        study.forecast_case(Recorder(defect), case(), SETTINGS)


def test_unavailable_quantile_is_not_silently_rounded_to_a_nearby_level():
    with pytest.raises(ValueError):
        study.forecast_case(Recorder(), case(), {**SETTINGS, "probabilities": [.11, .5, .9]})
