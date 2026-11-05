# Held-out linear controls

| requirement | adversarial check | gate |
|---|---|---|
| BR-1 | Change units and translate the complete window; supply constant, nonfinite and malformed windows and require refusal. | `tests/test_browser_linear.py::test_adversarial_positive_affine_units_preserve_normalized_window_and_raw_forecast` |
| BR-2 | Solve a rank-deficient least-squares problem, compare ridge against a closed-form coefficient, and require selection to follow validation loss and ties. | `tests/test_browser_linear.py::test_adversarial_rank_deficient_fit_and_regularized_closed_form` |
| BR-3 | Use a calibration sample whose correct order statistic differs from interpolation; independently calculate both tail penalties and constant paired bootstrap results. | `tests/test_browser_linear.py::test_adversarial_calibration_uses_finite_sample_rank_and_each_lead_separately` |
