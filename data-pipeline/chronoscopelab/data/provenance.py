"""Data provenance + license registry: the source of truth for what may ship in the PUBLIC repo.

ChronoScope is a public Apache-2.0 repo. The offline pipeline reads raw data from a private local vault and
bakes compact derived artifacts (series excerpts + forecasts + metrics + analysis) into the public repo. The
LEGAL question per dataset is: may those small derived excerpts be redistributed publicly, with attribution?

This module answers it. Every source has a verified ``DataSource`` record carrying its license and a
``public_artifact_ok`` verdict; the export stage enforces that a raw excerpt of a local-only source never
lands in the public repo (only its aggregate metrics do). Verdicts are transcribed from the verified license
dossier (wip/chronoscope/deep-research-datasets-licenses-2026-07-04.md); do NOT invent a permissive verdict.

NOTE ON HONESTY: where the dossier flagged a source UNVERIFIED (e.g. Kaggle mining-flotation's uploader
license, Stooq redistribution terms), it is registered as ``public_artifact_ok=False`` (the safe default):
the pipeline may run on it locally, but nothing derived from it ships publicly until the license is confirmed.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataSource:
    """One data source and its public-redistribution verdict."""

    id: str
    name: str
    url: str
    license: str                 # the license NAME (e.g. "CC-BY-4.0", "Kaggle competition rules")
    citation: str
    public_artifact_ok: bool     # may DERIVED excerpts ship in the public repo (with attribution)?
    license_url: str = ""
    note: str = ""


# The registry. Verdicts verified 2026-07-04 against each source's stated terms (license dossier).
SOURCES: dict[str, DataSource] = {
    "synthetic": DataSource(
        id="synthetic", name="Synthetic generators (ChronoScope)",
        url="", license="ChronoScope-own (Apache-2.0)",
        citation="ChronoScope seeded synthetic generators (deterministic).",
        public_artifact_ok=True, note="fully owned; no third-party rights.",
    ),
    # --- PUBLIC-safe: CC-BY-4.0, derived excerpts ship with attribution ---
    "uci_electricity": DataSource(
        id="uci_electricity", name="UCI ElectricityLoadDiagrams20112014",
        url="https://archive.ics.uci.edu/dataset/321/electricityloaddiagrams20112014",
        license="CC-BY-4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        citation="Trindade, A. (2015). ElectricityLoadDiagrams20112014. UCI ML Repository. DOI 10.24432/C58C86.",
        public_artifact_ok=True,
    ),
    "uci_beijing_pm25": DataSource(
        id="uci_beijing_pm25", name="UCI Beijing PM2.5 / Multi-Site Air Quality",
        url="https://archive.ics.uci.edu/dataset/381/beijing+pm2+5+data",
        license="CC-BY-4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        citation="Liang, X. et al. (2015). Beijing PM2.5 Data. UCI ML Repository.",
        public_artifact_ok=True,
    ),
    "opsd": DataSource(
        id="opsd", name="Open Power System Data - time_series",
        url="https://open-power-system-data.org/",
        license="CC-BY-4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        citation="Open Power System Data (2020). Data Package time_series.",
        public_artifact_ok=True,
    ),
    "monash": DataSource(
        id="monash", name="Monash Time Series Forecasting Repository (incl. M3/M4)",
        url="https://forecastingdata.org/",
        license="CC-BY-4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        citation="Godahewa, R. et al. (2021). Monash Time Series Forecasting Archive. arXiv:2105.06643.",
        public_artifact_ok=True,
    ),
    # --- LOCAL-only: pipeline may run, but NO raw excerpt ships (only aggregate metrics) ---
    "m5": DataSource(
        id="m5", name="M5 competition (Walmart, Kaggle)",
        url="https://www.kaggle.com/competitions/m5-forecasting-accuracy",
        license="Kaggle competition rules (no redistribution)",
        citation="Makridakis, S. et al. (2022). The M5 competition. IJF 38(4). DOI 10.1016/j.ijforecast.2021.07.007.",
        public_artifact_ok=False, note="competition rules forbid redistributing the data; aggregate metrics only.",
    ),
    "favorita": DataSource(
        id="favorita", name="Corporacion Favorita Grocery Sales (Kaggle)",
        url="https://www.kaggle.com/competitions/favorita-grocery-sales-forecasting",
        license="Kaggle competition rules (no redistribution)",
        citation="Corporacion Favorita Grocery Sales Forecasting (Kaggle, 2017-18).",
        public_artifact_ok=False, note="competition rules forbid redistribution; aggregate metrics only.",
    ),
    "ett_ltsf": DataSource(
        id="ett_ltsf", name="ETT / LTSF bundle (Electricity/Traffic/Weather/Exchange/ILI)",
        url="https://github.com/zhouhaoyi/ETDataset",
        license="CC-BY-NC-ND-4.0 (ETT) / murky provenance (LTSF bundle)",
        citation="Zhou, H. et al. (2021). Informer (ETT). AAAI-21.",
        public_artifact_ok=False, note="ND clause blocks derived excerpts; the bundle's provenance is murky.",
    ),
    "mining_flotation": DataSource(
        id="mining_flotation", name="Quality Prediction in a Mining Process (Kaggle)",
        url="https://www.kaggle.com/datasets/edumagalhaes/quality-prediction-in-a-mining-process",
        license="uploader-stated (UNVERIFIED)",
        citation="Quality Prediction in a Mining Process (Kaggle, edumagalhaes).",
        public_artifact_ok=False, note="uploader license unverified; safe default = local-only until confirmed.",
    ),
    "stooq": DataSource(
        id="stooq", name="Stooq finance series",
        url="https://stooq.com/",
        license="Stooq terms (UNVERIFIED for redistribution)",
        citation="Stooq historical price data.",
        public_artifact_ok=False, note="redistribution terms unverified; local-only.",
    ),
}


def get_source(source_id: str) -> DataSource:
    """Return the registered DataSource, or raise if the id is unknown (fail loud, never guess a license)."""
    if source_id not in SOURCES:
        raise KeyError(f"unknown data source: {source_id!r}. registered: {sorted(SOURCES)}")
    return SOURCES[source_id]


def public_artifact_ok(source_id: str) -> bool:
    """May DERIVED excerpts of this source ship in the public repo? Unknown sources are False (safe default)."""
    return SOURCES[source_id].public_artifact_ok if source_id in SOURCES else False


def public_safe_ids() -> list[str]:
    """The source ids whose derived excerpts may ship publicly (with attribution)."""
    return sorted(s.id for s in SOURCES.values() if s.public_artifact_ok)


def local_only_ids() -> list[str]:
    """The source ids that stay local (only aggregate metrics ship publicly)."""
    return sorted(s.id for s in SOURCES.values() if not s.public_artifact_ok)
