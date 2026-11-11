# Validation for executable sequence lessons

| requirement | adversarial check | gate |
|---|---|---|
| NB-041 | Run without either external scratch argument or environment variable and require an explicit refusal. | `tests/test_run_notebooks.py::test_adversarial_check_without_a_temp_root_stops_with_exit_2` |
| NB-042 | Run a controlled notebook execution and check the locations and cleanup of all generated files. | `tests/test_run_notebooks.py::test_adversarial_check_writes_only_under_the_temp_root_and_removes_it` |
| NB-092 | Plant short prose and duplicate image outputs. Confirm they cannot satisfy the measured floors. | `tests/adversarial/test_check_notebook_depth.py::test_adversarial_depth_floors_and_duplicate_images` |
| NB-093 | Remove or hide the two required sections or give the lesson a generic validation question. | `tests/adversarial/test_check_notebook_depth.py::test_adversarial_sensitivity_own_data_and_generic_questions` |
| NB-094 | Remove a covered item or point to a notebook missing from one language tree. | `tests/adversarial/test_check_notebook_depth.py::test_adversarial_complete_tool_coverage` |
