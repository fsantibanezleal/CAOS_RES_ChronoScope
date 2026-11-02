"""Robust estimator reproducibility must not depend on the caller's RNG."""
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

from chronoscopelab.analysis.nonlinear import chaos_measures


def test_seeded_fit_preserves_global_rng_and_repeats_after_unrelated_random_draws():
    x = np.random.default_rng(3).normal(size=180)
    np.random.seed(2)
    before = np.random.get_state()
    first = chaos_measures(x, seed=42)
    after = np.random.get_state()
    assert before[0] == after[0] and np.array_equal(before[1], after[1]) and before[2:] == after[2:]
    np.random.normal(size=100)
    assert chaos_measures(x, seed=42) == first


def test_adversarial_independent_processes_reproduce_identical_robust_estimates():
    code = """import json,numpy as np
from dataclasses import asdict
from chronoscopelab.analysis.nonlinear import chaos_measures
x=np.random.default_rng(19).normal(size=180)
print(json.dumps(asdict(chaos_measures(x,seed=42)),sort_keys=True))
"""
    environment = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1]/'data-pipeline')}
    results = [subprocess.check_output([sys.executable, '-c', code], env=environment) for _ in range(2)]
    assert results[0] == results[1]
    assert np.isfinite(json.loads(results[0])['corr_dim'])
