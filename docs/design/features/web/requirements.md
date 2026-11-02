# Web product requirements

The current shell and product definitions are enforced on the actual product, its artifacts and disposable planted-defect copies. Browser measurements run locally on the served build.

| ID | Requirement | Gate |
|---|---|---|
| WB-001 | The design record SHALL name the executive data file immediately after the problem and SHALL not duplicate its narrative. | `scripts/check_sdd.py` |
| WB-002 | The committed bilingual executive brief SHALL validate against the exact installed shell schema and all content floors. | `scripts/check_sdd.py` |
| WB-003 | A missing or incompatible installed executive schema SHALL fail validation rather than skip it. | `tests/test_spec_guards.py` |
| WB-004 | Every executive illustration SHALL exist within the public site and provide a valid SVG viewBox. | `tests/test_spec_guards.py` |
| WB-005 | Every executive claim and figure SHALL cite a unique, used HTTPS source. | `scripts/check_sdd.py` |
| WB-006 | Introduction SHALL open the executive view first and retain the technical view as a separate choice. | `frontend/scripts/gate.mjs` |
| WB-007 | Executive illustrations SHALL support both languages, theme tokens and a shared pain/proposal setting. | `frontend/scripts/gate.mjs` |
| WB-008 | The root and unknown paths SHALL open the Introduction landing while /app serves the forecasting atlas. | `frontend/scripts/gate.mjs` |
| WB-009 | Executive cause weights, action owners, writing limits and capability definitions SHALL satisfy the shell content rules. | `scripts/check_sdd.py` |
| WB-010 | The header SHALL order App, Introduction, Methodology, Implementation, Experiments and Benchmark. | `frontend/scripts/gate.mjs` |
| WB-011 | Every documentation page SHALL use the full-width shell document layout with substantive measured areas. | `frontend/scripts/gate.mjs` |
| WB-012 | Executive cards SHALL retain bilingual title and description limits including the shell labels. | `scripts/check_sdd.py` |
| WB-013 | An animated illustration SHALL finish within ten seconds and stop under reduced motion. | `scripts/check_svg_animation.py` |
| WB-014 | The App SHALL provide Focus mode and no runner argument SHALL suppress or redirect its required measurement. | `frontend/scripts/gate.mjs` |
| WB-015 | The App kind and any Focus waiver SHALL agree between product metadata and the design record. | `tests/adversarial/test_app_kind.py` |
| WB-016 | The content guard SHALL inspect suffix-free UTF-8 files and report disallowed punctuation with location. | `tests/adversarial/test_guard_gaps_0_09_0.py` |
| WB-017 | Every JSON artifact SHALL validate against its normative schema; declared non-JSON files SHALL name their real contract tests. | `scripts/check_documents.py` |
| WB-018 | The technology guard SHALL validate exact npm aliases against the lock and design table. | `tests/adversarial/test_guard_gaps_0_09_0.py` |
| WB-019 | Product-neutral inherited guards SHALL carry no owner-specific prose or hardcoded machine configuration. | `scripts/check_owner_names.py` |
| WB-020 | Prebuild SHALL replace the generated public corpus from canonical inputs and reject a missing canonical corpus rather than ship cached results. | `frontend/scripts/copy-data.test.mjs` |
