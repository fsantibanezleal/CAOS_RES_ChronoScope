"""Train a small LTSF-linear (NLinear) model by least squares and export it to a tiny ONNX (a single MatMul),
so the browser can run a LEARNED method LIVE via onnxruntime-web.

NLinear (Zeng et al., "Are Transformers Effective for Time Series Forecasting?", AAAI-23) is a one-layer
linear map from a normalised lookback window to the horizon. We instance-normalise each window (subtract the
last value, divide by its std) so one weight matrix generalises across levels and scales; the normalisation
is done in JS around the ONNX MatMul, so the exported graph is just W (L x H).

Run: .venv-pipeline/Scripts/python.exe scripts/train_nlinear_onnx.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper

ROOT = Path(__file__).resolve().parents[1]
OUT_ONNX = ROOT / "frontend" / "public" / "models" / "nlinear.onnx"
OUT_META = ROOT / "frontend" / "public" / "models" / "nlinear.json"

L = 48   # lookback
H = 12   # horizon
SEED = 20260704


def _series(rng: np.random.Generator, kind: str, n: int) -> np.ndarray:
    t = np.arange(n, dtype=float)
    m = rng.choice([6, 12, 24])
    if kind == "seasonal":
        return 50 + rng.uniform(4, 20) * np.sin(2 * np.pi * t / m) + rng.normal(0, rng.uniform(0.5, 4), n)
    if kind == "trend_seasonal":
        return (50 + rng.uniform(-0.4, 0.4) * t + rng.uniform(4, 16) * np.sin(2 * np.pi * t / m)
                + rng.normal(0, rng.uniform(0.5, 4), n))
    if kind == "trend":
        return 50 + rng.uniform(-0.5, 0.5) * t + rng.normal(0, rng.uniform(0.5, 5), n)
    return 50 + rng.normal(0, rng.uniform(1, 6), n)  # noise


def _windows(y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    xs, ys = [], []
    for i in range(0, len(y) - L - H + 1):
        x = y[i:i + L]
        target = y[i + L:i + L + H]
        last = x[-1]
        s = np.std(x) or 1.0
        xs.append((x - last) / s)
        ys.append((target - last) / s)
    return np.asarray(xs), np.asarray(ys)


def main() -> int:
    rng = np.random.default_rng(SEED)
    X, Y = [], []
    for _ in range(400):
        kind = rng.choice(["seasonal", "trend_seasonal", "trend", "noise"])
        y = _series(rng, kind, n=rng.integers(120, 260))
        xw, yw = _windows(y)
        if xw.size:
            X.append(xw)
            Y.append(yw)
    Xn = np.vstack(X)
    Yn = np.vstack(Y)
    # least-squares weight matrix W (L x H): Yn ~ Xn @ W
    W, _res, _rank, _sv = np.linalg.lstsq(Xn, Yn, rcond=None)
    W = W.astype(np.float32)

    # residual sigma on the normalised scale (for prediction intervals in the browser)
    resid = Yn - Xn @ W
    sigma_norm = float(np.std(resid))

    # ONNX: input x [1, L] -> MatMul(x, W) -> y [1, H]
    x_in = helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, L])
    y_out = helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, H])
    w_init = numpy_helper.from_array(W, name="W")
    node = helper.make_node("MatMul", ["x", "W"], ["y"])
    graph = helper.make_graph([node], "nlinear", [x_in], [y_out], [w_init])
    model = helper.make_model(graph, opset_imports=[helper.make_operatorsetid("", 13)],
                              producer_name="chronoscope")
    model.ir_version = 9
    onnx.checker.check_model(model)
    OUT_ONNX.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, OUT_ONNX)
    OUT_META.write_text(json.dumps({
        "name": "NLinear",
        "lookback": L, "horizon": H,
        "normalization": "subtract_last_then_divide_std",
        "sigma_norm": round(sigma_norm, 6),
        "trained_windows": int(Xn.shape[0]),
    }, indent=2), encoding="utf-8")

    # verify with onnxruntime
    import onnxruntime as ort

    sess = ort.InferenceSession(str(OUT_ONNX), providers=["CPUExecutionProvider"])
    test = Xn[:1].astype(np.float32)
    out = sess.run(["y"], {"x": test})[0]
    print(f"exported {OUT_ONNX.name} ({OUT_ONNX.stat().st_size} bytes); L={L} H={H}; "
          f"windows={Xn.shape[0]}; sigma_norm={sigma_norm:.4f}; ort out shape {out.shape}")
    print(f"self-forecast MASE-ish on train residual: {np.mean(np.abs(resid)):.4f} (normalised)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
