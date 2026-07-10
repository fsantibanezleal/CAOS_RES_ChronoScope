"""Data lane: provenance/license registry + real-dataset loaders.

The provenance registry is the source of truth for what may ship in the PUBLIC repo (per the verified license
dossier); the loaders read the private vault and produce Contract-1 series. The export stage enforces the
``public_artifact_ok`` verdict so a raw excerpt of a local-only source never lands in the public repo.
"""
from __future__ import annotations

from . import provenance
from .provenance import (
    DataSource,
    SOURCES,
    get_source,
    local_only_ids,
    public_artifact_ok,
    public_safe_ids,
)

__all__ = [
    "provenance",
    "DataSource",
    "SOURCES",
    "get_source",
    "public_artifact_ok",
    "public_safe_ids",
    "local_only_ids",
]
