"""Tests for kpi_analysis.py.  Run: uv run pytest

Part 1 uses a 12-row hand-built table whose expected values were worked out by hand.
Part 2 checks the real canonical file against the Module 6 cleaning outputs.
"""
import json
from pathlib import Path

import pandas as pd
import pytest

import kpi_analysis as k

ROOT = Path(__file__).resolve().parents[1]
A_MBID = 'aaaaaaaa-0000-0000-0000-000000000001'

# user, UTC time, artist_name, recording, has MBID (artist A only)
FIXTURE = [
    ('u1', '2024-01-01 10:00:00', 'Alpha', 'r1', True),    # 1
    ('u1', '2024-01-01 10:00:30', 'Alpha', 'r1', True),    # 2  double-scrobble (30 s after 1)
    ('u1', '2024-01-01 12:00:00', 'alpha', 'r2', True),    # 3
    ('u1', '2024-01-04 09:00:00', 'Alpha', 'r1', True),    # 4
    ('u1', '2024-01-08 09:00:00', 'Alpha', 'r3', True),    # 5
    ('u1', '2024-01-10 20:00:00', 'Alpha', 'r3', True),    # 6
    ('u1', '2024-01-11 00:00:00', 'Beta', 'r4', False),    # 7  u1's last listen
    ('u1', '2024-01-02 08:00:00', 'Unknown', 'r5', False), # 8  placeholder artist
    ('u2', '2024-01-01 00:00:00', 'ALPHA', 'r1', False),   # 9  no MBID -> R7b borrows A_MBID
    ('u2', '2024-01-03 00:00:00', 'Beta', 'r4', False),    # 10
    ('u2', '2024-01-03 01:00:00', 'Gamma', 'r6', False),   # 11
    ('u2', '2024-01-03 02:00:00', 'gamma', 'r6', False),   # 12 tie Gamma/gamma
]


def raw_rows(rows):
    """Build rows in the canonical file's 11-column text format."""
    out = []
    for user, ts, artist, rec, has_mbid in rows:
        out.append({
            'username': user, 'listened_at': ts, 'track_name': f'track {rec}',
            'artist_name': artist, 'release_name': pd.NA, 'recording_msid': rec,
            'artist_mbids': f"['{A_MBID}']" if has_mbid else pd.NA,
            'recording_mbid': pd.NA, 'release_mbid': pd.NA,
            'listened_at_utc': ts.replace(' ', 'T') + '+00:00',
            'artist_mbids_parsed': json.dumps([A_MBID]) if has_mbid else pd.NA,
        })
    return pd.DataFrame(out, columns=k.REQUIRED_COLUMNS)


@pytest.fixture
def listens():
    return k.derive_columns(raw_rows(FIXTURE))


def pair(pairs, artist_id, user):
    return pairs.set_index(k.PAIR_KEY).loc[(artist_id, user)]


def artist(artists, artist_id):
    return artists.set_index('artist_id').loc[artist_id]


# ---------------------------------------------------------------- part 1: hand-built table

def test_derived_identity_and_countability(listens):
    by_time = listens.set_index('listened_at_utc')
    assert not by_time.loc[pd.Timestamp('2024-01-01 10:00:30', tz='UTC'), 'is_countable']
    assert listens['is_countable'].sum() == 11
    assert listens.loc[listens['artist_name'] == 'Unknown', 'artist_key'].isna().all()
    row9 = listens.loc[listens['artist_name'] == 'ALPHA'].iloc[0]
    assert row9['artist_id'] == A_MBID and row9['artist_id_source'] == 'key_mbid'
    assert set(listens['artist_id'].dropna()) == {A_MBID, 'name:beta', 'name:gamma'}
    assert str(listens['listened_at_utc'].dt.tz) == 'UTC'


def test_pair_kpis_hand_values(listens):
    pairs = k.pair_kpis(listens)
    assert list(pairs.columns) == k.PAIR_COLUMNS
    assert len(pairs) == 5
    a1 = pair(pairs, A_MBID, 'u1')
    assert (a1.countable_listens, a1.distinct_tracks, a1.active_days, a1.days_to_return) == (5, 3, 4, 3)
    assert a1.returned and a1.multi_track
    # Return window 01-02 00:00 -> 01-11 00:00, midpoint 01-06 12:00.
    # A: 3 return listens, 2 late.  u1 overall in window: rows 4-8 = 5 listens, 3 late.
    assert (a1.return_listens, a1.late_return_listens) == (3, 2)
    assert a1.expected_late_share == pytest.approx(0.6)
    assert a1.return_momentum == pytest.approx(2 / 3 - 3 / 5)          # 1/15
    for aid, user in [(A_MBID, 'u2'), ('name:beta', 'u1'), ('name:beta', 'u2')]:
        p = pair(pairs, aid, user)
        assert p.countable_listens == 1 and not p.returned
        assert pd.isna(p.days_to_return) and pd.isna(p.return_momentum)


def test_artist_kpis_hand_values(listens):
    artists = k.artist_kpis(listens)
    assert list(artists.columns) == k.ARTIST_COLUMNS
    a = artist(artists, A_MBID)
    assert a.display_name == 'Alpha' and a.artist_mbid == A_MBID
    assert (a.countable_listens, a.unique_listeners, a.returning_listeners, a.distinct_tracks) == (6, 2, 1, 3)
    assert a.return_rate == 0.5 and a.avg_active_days == 2.5 and a.listens_per_listener == 3.0
    assert a.multi_track_rate == 0.5 and a.median_days_to_return == 3
    assert a.return_momentum == pytest.approx(1 / 15) and a.momentum_pairs == 1
    assert a.first_listen_utc == pd.Timestamp('2024-01-01 00:00', tz='UTC')
    assert a.last_listen_utc == pd.Timestamp('2024-01-10 20:00', tz='UTC')
    assert artist(artists, 'name:beta').return_rate == 0
    assert artist(artists, 'name:gamma').display_name == 'Gamma'       # tie -> alphabetical
    assert pd.isna(artist(artists, 'name:beta').artist_mbid)
    assert sorted(artists['rank']) == [1, 2, 3]


def test_headline_kpis_hand_values(listens):
    artists, pairs, summary = k.compute_kpis(listens)
    kpis = summary['kpis']
    assert kpis['total_listens'] == 12 and kpis['countable_listens'] == 11
    assert kpis['excluded_double_scrobbles'] == 1 and kpis['excluded_missing_artist'] == 1
    assert kpis['artist_listens'] == 10 and kpis['listeners'] == 2 and kpis['artists'] == 3
    assert kpis['listener_artist_pairs'] == 5
    assert kpis['pair_return_rate'] == 0.2
    assert kpis['pct_artists_with_return'] == pytest.approx(1 / 3, abs=1e-4)
    assert kpis['period_start'] == '2024-01-01' and kpis['period_end'] == '2024-01-11'
    assert all(summary['checks'].values())
    json.dumps(summary)                                                 # JSON-ready


def test_period_filter_recomputes_within_period(listens):
    early = k.artist_kpis(k.filter_period(listens, '2024-01-01', '2024-01-03'))
    assert artist(early, A_MBID).return_rate == 0                       # u1's later days dropped
    assert artist(early, 'name:beta').unique_listeners == 1             # row 7 (01-11) dropped
    late = k.filter_period(listens, '2024-01-09', '2024-01-11')
    assert late['username'].unique().tolist() == ['u1']                 # end day is inclusive
    assert 'name:gamma' not in set(k.artist_kpis(late)['artist_id'])
    only_u2 = k.filter_period(listens, users=['u2'])
    assert set(only_u2['username']) == {'u2'}


def test_empty_period_returns_empty_tables(listens):
    empty = k.filter_period(listens, '2025-01-01', '2025-12-31')
    artists, pairs, summary = k.compute_kpis(empty)
    assert artists.empty and list(artists.columns) == k.ARTIST_COLUMNS
    assert pairs.empty and list(pairs.columns) == k.PAIR_COLUMNS
    assert summary['kpis']['total_listens'] == 0
    assert summary['kpis']['pair_return_rate'] is None
    assert summary['kpis']['period_start'] is None


def test_late_discovery_gets_no_momentum():
    # Discovered on the listener's last day with several plays: no return window -> NaN, not +1.
    rows = [('u1', '2024-01-01 00:00:00', 'Other', 'r1', False),
            ('u1', '2024-01-05 00:00:00', 'Other', 'r1', False),
            ('u1', '2024-01-10 01:00:00', 'Late', 'r2', False),
            ('u1', '2024-01-10 02:00:00', 'Late', 'r2', False),
            ('u1', '2024-01-10 03:00:00', 'Late', 'r3', False)]
    pairs = k.pair_kpis(k.derive_columns(raw_rows(rows)))
    assert pd.isna(pair(pairs, 'name:late', 'u1').return_momentum)


def test_listener_with_one_artist_has_zero_momentum():
    # Every listen is the same artist, so the artist exactly keeps pace with the listener.
    rows = [('u3', f'2024-01-0{d} 12:00:00', 'Delta', 'r1', False) for d in (1, 3, 5, 7)]
    p = pair(k.pair_kpis(k.derive_columns(raw_rows(rows))), 'name:delta', 'u3')
    assert p.return_listens == 3 and p.return_momentum == pytest.approx(0)


def test_momentum_guards():
    # Only 2 return listens -> below min_return_listens=3 -> NaN; allowed when the guard is 2.
    rows = [('u1', '2024-01-01 12:00:00', 'Echo', 'r1', False),
            ('u1', '2024-01-03 12:00:00', 'Echo', 'r1', False),
            ('u1', '2024-01-06 12:00:00', 'Echo', 'r1', False)]
    listens = k.derive_columns(raw_rows(rows))
    assert pd.isna(pair(k.pair_kpis(listens), 'name:echo', 'u1').return_momentum)
    assert pair(k.pair_kpis(listens, min_return_listens=2), 'name:echo', 'u1').return_momentum == pytest.approx(0)


def test_pooled_momentum_weights_by_return_listens():
    pairs = pd.DataFrame({'artist_id': ['E', 'E'], 'return_listens': [3, 9],
                          'late_return_listens': [3, 3], 'expected_late_share': [0.5, 0.5],
                          'return_momentum': [0.5, 3 / 9 - 0.5]})
    pooled = k.pooled_momentum(pairs).loc['E']
    assert pooled.return_momentum == pytest.approx(0)                   # simple mean would be 1/6
    assert pooled.momentum_pairs == 2


def test_emerging_filter(listens):
    artists = k.artist_kpis(listens)
    ids = lambda f: set(k.apply_emerging_filter(artists, f)['artist_id'])
    assert ids(k.EmergingFilter()) == {A_MBID, 'name:beta', 'name:gamma'}
    assert ids(k.EmergingFilter(min_listens=3)) == {A_MBID}
    assert ids(k.EmergingFilter(min_avg_active_days=2)) == {A_MBID}
    assert ids(k.EmergingFilter(max_listeners=1)) == {'name:gamma'}
    assert ids(k.EmergingFilter(mbid_status='mbid')) == {A_MBID}
    assert ids(k.EmergingFilter(mbid_status='no_mbid')) == {'name:beta', 'name:gamma'}
    assert ids(k.EmergingFilter(exclude_artist_ids=(A_MBID,))) == {'name:beta', 'name:gamma'}
    with pytest.raises(ValueError):
        k.apply_emerging_filter(artists, k.EmergingFilter(mbid_status='unknown'))


def test_artist_detail(listens):
    detail = k.artist_detail(listens, A_MBID)
    assert detail.summary['countable_listens'] == 6
    assert set(detail.listeners['username']) == {'u1', 'u2'}
    assert detail.tracks['recording_msid'].tolist() == ['r1', 'r3', 'r2']   # 3, 2, 1 listens
    with pytest.raises(KeyError):
        k.artist_detail(listens, 'name:nobody')


def test_functions_do_not_mutate_input(listens):
    before = listens.copy()
    k.compute_kpis(listens)
    k.artist_detail(listens, A_MBID)
    k.filter_period(listens, '2024-01-01', '2024-01-02')
    pd.testing.assert_frame_equal(listens, before)


def test_loader_keeps_text_and_checks_columns(tmp_path):
    df = raw_rows([('u1', '2024-01-01 00:00:00', 'NaN', 'r1', False)])
    df['track_name'] = 'None'
    df.to_csv(tmp_path / 'ok.csv', index=False)
    listens = k.load_listens(tmp_path / 'ok.csv')
    assert listens.loc[0, 'track_name'] == 'None' and listens.loc[0, 'artist_name'] == 'NaN'
    df.drop(columns='artist_mbids_parsed').to_csv(tmp_path / 'bad.csv', index=False)
    with pytest.raises(ValueError, match='artist_mbids_parsed'):
        k.load_listens(tmp_path / 'bad.csv')


# ---------------------------------------------------------------- part 2: real data

CANONICAL = ROOT / 'listenbrainz_final_cleaned.csv'
MODULE6 = ROOT / 'outputs' / 'cleaned_listens.csv'
needs_data = pytest.mark.skipif(not (CANONICAL.exists() and MODULE6.exists()),
                                reason='canonical CSV or Module 6 outputs not present')


@pytest.fixture(scope='module')
def real():
    return k.load_listens(CANONICAL)


@needs_data
def test_parity_with_module6_cleaning(real):
    m6 = pd.read_csv(MODULE6, dtype=str, keep_default_na=False, na_values=[''])
    both = real.merge(m6, on='listen_id', suffixes=('', '_m6'), validate='one_to_one')
    assert len(both) == len(real) == 1940
    assert both['artist_key'].fillna('').eq(both['artist_key_m6'].fillna('')).all()
    assert both['is_countable'].eq(both['is_countable_m6'] == 'True').all()
    changed = (both['artist_id'].fillna('') != both['artist_id_m6'].fillna('')).astype(bool)
    r7b = both['artist_id_source'] == 'key_mbid'
    assert (changed == r7b).all()                                     # only R7b rows differ
    assert r7b.sum() == 116 and (r7b & both['is_countable']).sum() == 113


@needs_data
def test_real_data_snapshot(real):
    artists, pairs, summary = k.compute_kpis(real)
    kpis = summary['kpis']
    assert (kpis['total_listens'], kpis['countable_listens'], kpis['artist_listens']) == (1940, 1882, 1880)
    assert (kpis['excluded_double_scrobbles'], kpis['excluded_missing_artist']) == (58, 2)
    assert (kpis['listeners'], kpis['artists'], kpis['listener_artist_pairs']) == (5, 669, 677)
    assert kpis['artists_with_2plus_listeners'] == 8
    assert kpis['artists_with_momentum'] == 48
    assert kpis['pair_return_rate'] == pytest.approx(0.2496, abs=1e-4)
    arthrn = artists.loc[artists['display_name'] == 'Arthrn']
    assert len(arthrn) == 1
    assert (arthrn.iloc[0]['countable_listens'], arthrn.iloc[0]['avg_active_days']) == (182, 19)


@needs_data
def test_listen_counts_match_module6_artist_summary(real):
    # Grouped by name key (as in Module 6), countable listens per artist are unchanged.
    summary = pd.read_csv(ROOT / 'outputs' / 'artist_summary.csv').set_index('artist_key')
    ours = k.countable_artist_listens(real).groupby('artist_key').size()
    assert ours.to_dict() == summary['countable_listens'].to_dict()
