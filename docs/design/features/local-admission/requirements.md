# Local initialization and immutable release admission

The product consumes the released bootstrap implementation. Scientific inputs,
previous publications and model paths remain frozen during a tooling upgrade.

| ID | Requirement | Verification |
|---|---|---|
| LA-1 | Initialization SHALL allocate environments only under an explicitly configured external role root and product namespace. When an existing alias resolves elsewhere, initialization SHALL refuse before installation. | `tests/test_bootstrap_admission.py`, `tests/test_local_bootstrap.py` |
| LA-2 | Legacy setup, precompute and dev entrypoints in PowerShell and Bash SHALL forward arguments and the exact native exit status to the same numbered workflow. | `tests/test_bootstrap_admission.py` |
| LA-3 | Promotion SHALL bind one immutable source, receipt and payload snapshot through validation, copy and installation; a late mutation SHALL trigger rollback, including the product-specific admission branch. | `tests/test_bootstrap_admission.py`, `tests/test_bootstrap_regressions.py`, `tests/test_product_bootstrap_admission.py` |
| LA-4 | Admission SHALL retain the complete published combination inventory, every indexed series document, its selected-case binding and the full audit archive without alteration. Missing, added, redirected or changed payloads SHALL be refused before promotion. | `tests/test_combination_release_admission.py` |
| LA-5 | A tooling-only adoption SHALL leave all scientific forecasts and published PDF/source bindings unchanged. | `scripts/check_publication_bindings.py`, `tests/test_product_bootstrap_admission.py` |

The local workflow does not train models during startup or deployment. Generated
candidates remain outside the checkout until explicitly promoted. A copied
artifact is historical evidence, not newly executed model inference. Existing
environments are never moved, deleted or redirected by initialization.

The 0.14.006 template patch supplies non-method contribution declarations and external notebook runtime resolution. The product retains its existing checked temporary-directory cleanup. The custom product admission bridge remains authoritative; the template's example readiness writer is not substituted for that bridge.

| ID | Requirement | Verification |
|---|---|---|
| LA-6 | Notebook execution SHALL resolve the declared external notebook role, refuse a missing root or ambiguous role and reject an inner invocation using an unrelated interpreter. | `tests/test_notebook_environment.py` |
| LA-7 | A paper about a reusable empirical protocol SHALL use an explicitly declared non-method contribution; unknown, fenced or misplaced identifiers SHALL be refused. | `tests/test_novel_contribution_manuscripts.py` |
