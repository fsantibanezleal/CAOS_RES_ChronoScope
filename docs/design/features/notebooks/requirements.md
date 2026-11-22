# Requirements for executable sequence lessons

The two language trees teach the same experiments and apply the structural and content checks installed from the product template. Their metadata identifies the method packages, real or generated inputs and source references. The requirements below name the execution and measured-depth gates.

| ID | Requirement | Gate |
|---|---|---|
| NB-041 | WHEN the notebook runner is asked to check the committed set, it SHALL require an external scratch root. | `tests/test_run_notebooks.py::test_adversarial_check_without_a_temp_root_stops_with_exit_2` |
| NB-042 | WHEN a check runs, scratch output SHALL stay in its declared external root. | `tests/test_run_notebooks.py::test_adversarial_check_writes_only_under_the_temp_root_and_removes_it` |
| ND-001 | Every bilingual lesson SHALL contain the explanatory prose, figures, equations and sources required by its level. | `tests/adversarial/test_check_notebook_depth.py::test_adversarial_depth_floors_and_duplicate_images` |
| ND-003 | Levels two through four SHALL explain sensitivity and demonstrate how to use the method on new input. | `tests/adversarial/test_check_notebook_depth.py::test_adversarial_sensitivity_own_data_and_generic_questions` |
| ND-004 | The bilingual curriculum SHALL cover the current method, contract, stage and package inventories. | `tests/adversarial/test_check_notebook_depth.py::test_adversarial_complete_tool_coverage` |
| ND-005 | A copied notebook SHALL receive the published browser inference graph, its metadata and the scientific producer modules it teaches. | `tests/test_run_notebooks.py::test_adversarial_check_copies_published_browser_inputs` |
| ND-006 | Reference inference SHALL accept only the observed prefix and forecast settings, and SHALL refuse outputs bound to another prefix. | `tests/test_notebook_reference.py::test_adversarial_future_values_cannot_cross_reference_cli`, `tests/test_notebook_reference.py::test_adversarial_result_from_another_prefix_is_refused` |
| NB-091 | WHERE the repository has a `models/` folder, `run_notebooks.py` SHALL copy it into its work tree under the temp root, so a notebook that loads a released model from `models/` runs under `--check`; IF there is none, THEN it SHALL be skipped without a message. | `tests/test_run_notebooks.py::test_adversarial_check_copies_models_so_a_notebook_can_run_a_released_model` |
| NB-092 | WHERE the repository has a `manuscripts/` folder, `run_notebooks.py` SHALL copy it into its work tree under the temp root, without its `__pycache__` and `.ipynb_checkpoints`, so a notebook that imports a manuscript's analysis code or reads its committed summaries runs under `--check`; IF there is none, THEN it SHALL be skipped without a message. | `tests/test_run_notebooks.py::test_adversarial_check_copies_manuscripts_so_a_notebook_can_import_its_analysis_code`, `tests/test_run_notebooks.py::test_adversarial_check_without_a_manuscripts_folder_runs_as_before` |
