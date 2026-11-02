# Web product adversarial validation

The current shell and product definitions are enforced on the actual product, its artifacts and disposable planted-defect copies. Browser measurements run locally on the served build.

| requirement | adversarial check | gate |
|---|---|---|
| WB-001 | Move, remove or duplicate the executive brief declaration and require the real design guard to reject it. | `tests/adversarial/test_guard_holes.py::test_sdd_rereview_m3b_a_brief_after_resources_when_the_headings_are_numbered` |
| WB-002 | Remove executive data or plant schema and writing-limit violations. | `tests/adversarial/test_web_content.py::test_missing_executive_data_is_rejected` |
| WB-003 | Remove the installed executive schema or replace its version. | `tests/adversarial/test_web_content.py::test_missing_installed_schema_is_rejected` |
| WB-004 | Remove an illustration, corrupt its SVG or make its path leave the site. | `tests/adversarial/test_web_content.py::test_missing_executive_illustration_is_rejected` |
| WB-005 | Plant missing and duplicate source references or an insecure source URL. | `tests/adversarial/test_web_content.py::test_unknown_executive_source_is_rejected` |
| WB-006 | Traverse the actual introductory views and require the executive-first architecture. | `frontend/src/test/navigation.test.tsx::adversarial: root and unknown links resolve to the executive introduction` |
| WB-007 | Measure the actual illustrated scenes in both languages and themes. | `tests/adversarial/test_web_content.py::test_executive_scene_without_spanish_labels_is_rejected` |
| WB-008 | Visit root, deep links and unknown paths in the served static build. | `frontend/src/test/navigation.test.tsx::adversarial: an old root app link preserves its case query and fragment` |
| WB-009 | Plant excessive cause weights and invalid action-owner and capability relations. | `frontend/src/test/executive.test.ts::adversarial: rejects cause weights that exceed the whole` |
| WB-010 | Traverse the actual header and require all standard routes and navigation. | `frontend/src/test/navigation.test.tsx::adversarial: landing choice does not change the six header destinations or their order` |
| WB-011 | Measure all documentation widths, areas, figures and equations, including enlarged fonts. | `frontend/src/test/navigation.test.tsx::adversarial: all documentation routes retain the shared full width document boundary` |
| WB-012 | Plant a card exceeding the declared bilingual writing limits. | `tests/adversarial/test_web_content.py::test_excessive_executive_card_text_is_rejected` |
| WB-013 | Remove the reduced-motion block or overrun the maximum animation duration. local-only: SVG parsing uses the installed Node runtime locally. | `tests/adversarial/test_animation_and_focus.py::test_an_animated_svg_without_its_reduced_motion_block_fails` |
| WB-014 | Pass runner overrides that remove the app route or redirect Focus measurement; require refusal. local-only: the installed Node runtime executes this actual runner test. | `tests/adversarial/test_animation_and_focus.py::test_the_gate_runner_always_passes_require_focus_to_the_shell_gate` |
| WB-015 | Plant an unknown App kind, invalid waiver, missing reason or conflicting design row. | `tests/adversarial/test_app_kind.py::test_a_waiver_on_a_workbench_fails` |
| WB-016 | Plant prohibited content in a root suffix-free file, a dotfile and a deployment file. | `tests/adversarial/test_guard_gaps_0_09_0.py::test_an_em_dash_in_a_tracked_file_with_no_suffix_fails` |
| WB-017 | Plant wrong numeric types, remove a required licensing field or omit a binary contract test. | `tests/adversarial/test_guard_gaps_0_09_0.py::test_a_declared_onnx_file_fails_when_its_row_names_no_test` |
| WB-018 | Plant ranged or mismatched npm aliases and require the actual guard to reject them. | `tests/adversarial/test_guard_gaps_0_09_0.py::test_an_alias_with_a_range_fails` |
| WB-019 | Plant the product owner in an inherited guard and require the owner-neutrality check to refuse it. | `tests/adversarial/test_product_admission.py::test_owner_specific_prose_in_an_inherited_guard_is_refused` |
| WB-020 | Plant an orphaned generated case and separately omit canonical inputs while leaving a cached corpus; the real prebuild removes the orphan and refuses the missing source. | `frontend/src/test/copy-data.test.ts::adversarial: prebuild removes orphaned public cases and copies the canonical corpus`, `frontend/src/test/copy-data.test.ts::adversarial: prebuild refuses missing canonical inputs instead of publishing a cached corpus` |
