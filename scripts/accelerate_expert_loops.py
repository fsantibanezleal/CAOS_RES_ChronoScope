"""Compile unchanged recursive expert loops for the external evaluation worker.

Only loop execution changes. The finite grids, SSE objectives, recurrences,
initializations and forecast equations remain the reference implementation.
"""
from __future__ import annotations

_ENABLED = False


def enable():
    global _ENABLED
    if _ENABLED:
        return
    from numba import njit
    from chronoscopelab.model import forecasters as reference
    for name in ("_ses_run", "_opt_alpha", "_holt_run", "_hw_run"):
        setattr(reference, name, njit(cache=True, fastmath=False)(getattr(reference, name)))
    _ENABLED = True
