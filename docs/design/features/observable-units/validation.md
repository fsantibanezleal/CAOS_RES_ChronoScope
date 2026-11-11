# Observable-range validation

| requirement | adversarial check | gate |
|---|---|---|
| OU-1 | Wrong normalized units, non-finite endpoints, crossed/mismatched paths and redacted export refuse before writing. | `tests/test_forecast_units.py::test_adversarial_export_refuses_before_creating_any_file_including_redacted_paths` |
| OU-2 | A valid flat fit is exported unchanged, with an advisory; the caller's flags remain untouched. | `tests/test_forecast_units.py::test_adversarial_flat_forecast_is_exported_and_recorded_without_altering_callers_flags` |
| OU-3 | Corrupt a forecast in an existing artifact and require the sweep to identify that exact file. | `tests/test_forecast_units.py::test_adversarial_artifact_sweep_refuses_a_tampered_existing_forecast` |
| OU-4 | Alter source bytes even after rehashing the outer ZIP, remove a member, redirect the archive or alter its experiment. | `tests/test_fresh_reevaluation.py::test_adversarial_frozen_sources_refuse_tampering` |

The standard-library boundary in `data-pipeline/chronoscopelab/io/units.py` runs
before export, including before source-license redaction. The shipped-artifact
sweep is called by `scripts/check_artifacts.py` in CI and smoke. Its detailed
receipt is `docs/validation/2026-11-05/forecast-units.json`.

The November 5 sweep covers 45 case documents and 945 method paths, with zero
blocking findings and 108 constant-path advisories. Frozen forecast bytes are
unchanged. Tests plant normalized outputs against a 433–484 observable, positive
unit conversions and origin shifts, non-finite endpoints, mismatched/empty paths,
crossed intervals, a licensed-redacted export, a valid constant fit and a corrupted
existing artifact. A poor but overlapping forecast remains admissible.

This is a unit-consistency heuristic, not a proof of dimensional correctness or
an accuracy threshold. It inspects point-path overlap, not whether every interval
endpoint lies inside the observed range. Evaluation truths can enter this
post-prediction diagnostic; they cannot influence fitting, clipping or selection.
Observed values retain their source units, including undisclosed units in M4.

The November 11 combination check reconstructed 4,429 exact source prefixes and
reserved targets from the two Zenodo collections. It checked 53,148 external
forecast paths, with zero blocking findings and 5,736 flat-path advisories.
The [receipt](../../../validation/base-adoption-2026-11-10/combination-units.json)
binds the source archives, retained forecasts and unit boundary.

The separate literal-unit review and complete browser runtime audit remain pending. Passing these 945 paths does not close the
whole product's units requirement. Redacted public paths are reported as
uncheckable and make the standalone sweep fail rather than count as inspected.
