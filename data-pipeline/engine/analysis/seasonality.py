"""Compatibility import for the published numerical provider; no local numerical implementation."""
import importlib
import sys

_provider = importlib.import_module('forecastscope.diagnostics.seasonality')
sys.modules[__name__] = _provider
