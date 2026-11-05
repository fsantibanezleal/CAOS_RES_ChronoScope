# Held-out linear controls

| requirement | adversarial check | gate |
|---|---|---|
| BR-1 | Change units and translate the complete window; supply constant, nonfinite and malformed windows and require refusal. | `tests/test_browser_linear.py::test_adversarial_positive_affine_units_preserve_normalized_window_and_raw_forecast` |
| BR-2 | Solve a rank-deficient least-squares problem, compare ridge against a closed-form coefficient, and require selection to follow validation loss and ties. | `tests/test_browser_linear.py::test_adversarial_rank_deficient_fit_and_regularized_closed_form` |
| BR-3 | Use a calibration sample whose correct order statistic differs from interpolation; independently calculate both tail penalties and constant paired bootstrap results. | `tests/test_browser_linear.py::test_adversarial_calibration_uses_finite_sample_rank_and_each_lead_separately` |
| BR-4 | Permute complete calibration pairs, change units, undersize one group and plant each failed acceptance condition; require explicit refusal. | `tests/test_browser_calibration.py::test_adversarial_every_prerecorded_admission_condition_can_refuse` |
| BR-5 | Modify a forecast and reseal its receipt; require independent rescoring to reject it. Also plant overlapping series, removed sources, changed points and false acceptance. | `tests/test_browser_linear_evidence.py::test_adversarial_resealed_forecast_does_not_reproduce_reported_score` |
| BR-6 | Compare all 800 admitted paths, change units, corrupt scales and metadata, and supply a graph with another digest; require refusal before model execution. | `frontend/src/test/onnx-runner.test.ts::adversarial: an ONNX graph with the wrong digest cannot use this calibration` |
