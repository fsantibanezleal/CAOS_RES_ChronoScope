"""Accelerated loop results must retain the reference forecast equations."""
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np


def test_all_experts_match_reference_before_and_after_compilation(tmp_path):
    # A subprocess confines the module-global dispatcher replacement to this run.
    root = Path(__file__).resolve().parents[1]
    code = r'''
import sys,json
import numpy as np
sys.path[:0]=['data-pipeline','scripts']
from chronoscopelab.model.forecasters import METHODS
from accelerate_expert_loops import enable
rng=np.random.default_rng(123)
series=[(np.ones(40),1),(np.arange(65,dtype=float),12),
        (20+np.sin(np.arange(97)*2*np.pi/12)+rng.normal(0,.4,97),12),
        (rng.normal(size=120),52),(np.zeros(80),12)]
before=[[[p.tolist(),s] for _,_,f in METHODS for p,s in [f(y,m,7)]] for y,m in series]
enable()
after=[[[p.tolist(),s] for _,_,f in METHODS for p,s in [f(y,m,7)]] for y,m in series]
print(json.dumps({'before':before,'after':after}))
'''
    env = {**os.environ, "NUMBA_CACHE_DIR": str(tmp_path / "numba")}
    run = subprocess.run([sys.executable, "-c", code], cwd=root, env=env, check=True, capture_output=True, text=True)
    result = json.loads(run.stdout)
    for before, after in zip(result['before'], result['after']):
        for (bp, bs), (ap, ass) in zip(before, after):
            np.testing.assert_allclose(bp, ap, rtol=1e-11, atol=1e-10)
            np.testing.assert_allclose(bs, ass, rtol=1e-11, atol=1e-10)
