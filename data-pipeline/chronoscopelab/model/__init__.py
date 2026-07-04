"""The pure-numpy analytic core, Pyodide-safe, shared by the offline stages AND the live lane.

Classical time-series forecasters (seasonal-naive, SES, Holt, Holt-Winters, Theta) live here as the
same code path the browser live lane uses. Heavier engines (Nixtla, LightGBM, zero-shot foundation
models) run only in the offline stages and are never imported by the live lane.
"""
