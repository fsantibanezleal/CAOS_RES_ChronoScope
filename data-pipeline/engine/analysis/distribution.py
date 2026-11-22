"""Compatibility import for the published numerical provider; no local numerical implementation."""
import importlib
import sys

_provider = importlib.import_module('forecastscope.diagnostics.distribution')
sys.modules[__name__] = _provider
