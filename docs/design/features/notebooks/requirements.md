# Requirements for executable sequence lessons

The two language trees teach the same experiments and apply the structural and content checks installed from the product template. Their metadata identifies the method packages, real or generated inputs and source references. The requirements below name the execution and measured-depth gates.

| ID | Requirement | Gate |
|---|---|---|
| NB-041 | WHEN the notebook runner is asked to check the committed set, it SHALL require an external scratch root. | `tests/test_run_notebooks.py::test_adversarial_check_without_a_temp_root_stops_with_exit_2` |
| NB-042 | WHEN a check runs, scratch output SHALL stay in its declared external root. | `tests/test_run_notebooks.py::test_adversarial_check_writes_only_under_the_temp_root_and_removes_it` |
| NB-092 | Every bilingual lesson SHALL contain the explanatory prose, figures, equations and sources required by its level. | `tests/adversarial/test_check_notebook_depth.py::test_adversarial_depth_floors_and_duplicate_images` |
| NB-093 | Levels two through four SHALL explain sensitivity and demonstrate how to use the method on new input. | `tests/adversarial/test_check_notebook_depth.py::test_adversarial_sensitivity_own_data_and_generic_questions` |
| NB-094 | The bilingual curriculum SHALL cover the current method, contract, stage and package inventories. | `tests/adversarial/test_check_notebook_depth.py::test_adversarial_complete_tool_coverage` |
