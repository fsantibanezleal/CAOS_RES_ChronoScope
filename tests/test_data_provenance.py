"""Provenance/license registry tests: every source has a verdict; public-safe set matches the dossier."""
import pytest

from chronoscopelab.data import provenance as pv


def test_every_source_has_a_license_and_citation():
    for sid, src in pv.SOURCES.items():
        assert src.id == sid
        assert src.license, f"{sid} missing license"
        assert src.citation, f"{sid} missing citation"
        assert isinstance(src.public_artifact_ok, bool)


def test_public_safe_set_matches_the_license_dossier():
    # The dossier's PUBLIC-safe core: synthetic + UCI Electricity + UCI Beijing PM2.5 + OPSD + Monash.
    assert set(pv.public_safe_ids()) == {
        "synthetic", "uci_electricity", "uci_beijing_pm25", "opsd", "monash",
    }


def test_local_only_set_matches_the_license_dossier():
    # LOCAL-only: Kaggle competitions + ETT/LTSF + unverified uploader licenses.
    assert set(pv.local_only_ids()) == {"m5", "favorita", "ett_ltsf", "mining_flotation", "stooq"}


def test_public_safe_sources_are_cc_by_or_owned():
    for sid in pv.public_safe_ids():
        lic = pv.get_source(sid).license.lower()
        assert "cc-by" in lic or "apache" in lic or "own" in lic, f"{sid} public but license={lic!r}"


def test_kaggle_competition_data_is_local_only():
    # competition rules forbid redistribution -> must be local-only
    assert pv.public_artifact_ok("m5") is False
    assert pv.public_artifact_ok("favorita") is False


def test_unverified_licenses_default_to_local_only():
    # the safe default: an unverified uploader/redistribution license does NOT ship publicly
    assert pv.public_artifact_ok("mining_flotation") is False
    assert pv.public_artifact_ok("stooq") is False


def test_ett_nd_clause_blocks_public_derivatives():
    assert pv.public_artifact_ok("ett_ltsf") is False


def test_unknown_source_is_not_public_and_raises_on_get():
    assert pv.public_artifact_ok("does_not_exist") is False   # safe default
    with pytest.raises(KeyError):
        pv.get_source("does_not_exist")                        # but fail loud on an explicit lookup
