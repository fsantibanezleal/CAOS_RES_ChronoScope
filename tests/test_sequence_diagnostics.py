"""Numerical oracles and adversarial cases for the sequence diagnostics."""
import itertools

import numpy as np
import pytest

from chronoscopelab.analysis.sequence import multiscale_entropy, sequence_report, matrix_profile, time_reversal


def test_profile_matches_exhaustive_z_normalized_distance_oracle():
    x = np.random.default_rng(3).normal(size=64)
    m = 8
    got = matrix_profile(x, window=m)
    windows = np.lib.stride_tricks.sliding_window_view(x, m)
    z = (windows - windows.mean(axis=1)[:, None]) / windows.std(axis=1)[:, None]
    distances = np.linalg.norm(z[:, None] - z[None, :], axis=2)
    exclusion = int(np.ceil(m / 4))
    distances[np.abs(np.arange(len(z))[:, None] - np.arange(len(z))) <= exclusion] = np.inf
    np.testing.assert_allclose(got['profile'], distances.min(axis=1), atol=1e-6)
    assert all(abs(i-j) > exclusion for i, j in enumerate(got['nearest_neighbor']))


def test_repeated_motif_and_planted_discord_are_identified():
    rng = np.random.default_rng(19)
    x = rng.normal(scale=.15, size=240)
    pattern = np.sin(np.arange(24) * .4) + np.arange(24) * .03
    x[20:44] = pattern
    x[120:144] = pattern
    x[190:214] = rng.choice([-8., 8.], size=24)
    report = matrix_profile(x, window=24)
    assert report['motifs'][0]['distance'] < 1e-5
    assert {report['motifs'][0]['start'], report['motifs'][0]['match']} == {20, 120}
    assert all(0 < b < len(x) for b in report['regime_boundaries'])
    # Amplitude alone is not anomalous under z normalization: use a distinct shape.
    periodic = np.sin(np.arange(360)*2*np.pi/24)
    periodic[200:224] = np.linspace(-2, 2, 24)
    discord_report = matrix_profile(periodic, window=24)
    assert any(abs(d['start'] - 200) < 24 for d in discord_report['discords'])


def test_fluss_detects_a_planted_shape_transition_without_its_location_as_input():
    x = np.r_[np.sin(np.arange(300)*.2), np.sin(np.arange(300)*1.2)]
    report = matrix_profile(x, window=32, regimes=2)
    assert len(report['regime_boundaries']) == 1
    assert abs(report['regime_boundaries'][0]-300) <= 32


def test_lempel_ziv_binary_mapping_and_known_periodic_sequence():
    report = sequence_report(np.tile([0., 1.], 16))
    assert report['lempel_ziv']['raw'] == 3
    assert report['lempel_ziv']['normalized'] == pytest.approx(3*np.log2(32)/32)


def test_multiscale_entropy_uses_original_tolerance_and_independent_pair_counts():
    x = np.array([0, 1, 0, 1, 0, 1, 1, 0] * 20, dtype=float)
    report = multiscale_entropy(x, scales=(1, 2, 4), tolerance_ratio=.3)
    tolerance = .3 * np.std(x)
    for row in report['scales']:
        scale = row['scale']
        coarse = x[:len(x)//scale*scale].reshape(-1, scale).mean(axis=1)
        count = len(coarse) - 2
        b = sum(max(abs(coarse[i:i+2]-coarse[j:j+2])) <= tolerance
                for i, j in itertools.combinations(range(count), 2))
        a = sum(max(abs(coarse[i:i+3]-coarse[j:j+3])) <= tolerance
                for i, j in itertools.combinations(range(count), 2))
        assert row['matching_m'] == b and row['matching_m_plus_one'] == a
        assert row['tolerance'] == tolerance
        if a:
            assert row['entropy'] == pytest.approx(-np.log(a / b))


def test_reversal_flips_asymmetry_and_constant_entropy_is_zero():
    x = np.random.default_rng(7).exponential(size=100)
    assert time_reversal(x, 2)['standardized'] == pytest.approx(-time_reversal(x[::-1], 2)['standardized'])
    constant = multiscale_entropy(np.ones(100))
    assert all(s['entropy'] == 0 for s in constant['scales'] if s['n'] >= 20)
    assert sequence_report(np.ones(100))['matrix_profile']['reason']


@pytest.mark.parametrize('x', [[1, np.nan, 2], [1, np.inf, 2], [1]])
def test_invalid_sequences_are_rejected_instead_of_compacted(x):
    with pytest.raises(ValueError):
        sequence_report(x)
