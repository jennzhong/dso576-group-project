"""DSO 576 Phase 2 — Member 4: KPI backend for the Emerging Artist Discovery dashboard.

Run: python kpi_analysis.py --input listenbrainz_final_cleaned.csv --outdir outputs_kpi
     python kpi_analysis.py --start 2019-07-15 --end 2019-08-31     # KPIs for one period
Input: Member 3's canonical event table (9 source columns + listened_at_utc + artist_mbids_parsed).
Writes: artist_kpis.csv, listener_artist_kpis.csv, kpi_summary.json.
Dependencies: pandas. Definitions and decisions: kpi_analysis_log.md.

Every function below is pure (DataFrame in, new DataFrame/dict out) except load_listens()
and main(), so the Phase 3 dashboard can import and cache them.
"""
import argparse
import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

DEFAULT_INPUT = Path(__file__).resolve().parent / 'listenbrainz_final_cleaned.csv'
RAW_COLUMNS = ['username', 'listened_at', 'track_name', 'artist_name', 'release_name',
               'recording_msid', 'artist_mbids', 'recording_mbid', 'release_mbid']
REQUIRED_COLUMNS = RAW_COLUMNS + ['listened_at_utc', 'artist_mbids_parsed']

# Same values as clean_listens.py (cleaning_rules.md R6, R9); copied so this script runs on any branch.
DOUBLE_SCROBBLE_SECONDS = 60
PLACEHOLDER_NAMES = {'unknown', '[unknown]', 'unknown artist', 'n/a', 'none', 'null', '-'}
TOPIC_SUFFIX = ' - topic'
ARTIST_ALIASES = {'takanashi yasuharu / -yaiba-': 'yasuharu takanashi / -yaiba-'}

PAIR_KEY = ['artist_id', 'username']
PAIR_COLUMNS = ['artist_id', 'username', 'display_name', 'countable_listens', 'distinct_tracks',
                'active_days', 'first_listen_utc', 'last_listen_utc', 'returned', 'multi_track',
                'days_to_return', 'return_listens', 'late_return_listens', 'expected_late_share',
                'return_momentum']
ARTIST_COLUMNS = ['rank', 'artist_id', 'display_name', 'artist_mbid', 'countable_listens',
                  'unique_listeners', 'returning_listeners', 'return_rate', 'avg_active_days',
                  'distinct_tracks', 'listens_per_listener', 'multi_track_rate',
                  'median_days_to_return', 'return_momentum', 'momentum_pairs',
                  'first_listen_utc', 'last_listen_utc']
ONE_DAY = pd.Timedelta(1, unit='D')


# ---------------------------------------------------------------- load + derive

def load_listens(path=DEFAULT_INPUT):
    """Read the canonical CSV as text (empty cell = missing) and add the analysis columns."""
    source = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[''])
    missing = [col for col in REQUIRED_COLUMNS if col not in source]
    if missing:
        raise ValueError('Required columns missing: ' + ', '.join(missing))
    return derive_columns(source)


def nfc_strip(value):
    return pd.NA if pd.isna(value) else unicodedata.normalize('NFC', value).strip()


def make_artist_key(name):
    if pd.isna(name):
        return pd.NA
    key = name.casefold()
    if key.endswith(TOPIC_SUFFIX):
        key = key[:-len(TOPIC_SUFFIX)].strip()
    if key in PLACEHOLDER_NAMES:
        return pd.NA
    return ARTIST_ALIASES.get(key, key)


def derive_columns(source):
    """One row per listen, sorted by user and time, with identity and countability columns."""
    df = source.copy()
    df['listened_at_utc'] = pd.to_datetime(df['listened_at_utc'], utc=True, format='ISO8601')
    df['listen_id'] = df['username'] + '|' + (df['listened_at_utc'].astype('int64') // 10**9).astype(str)
    df['listen_day'] = df['listened_at_utc'].dt.floor('D')
    df['track_name_clean'] = df['track_name'].map(nfc_strip).astype('string')
    df['artist_name_clean'] = df['artist_name'].map(nfc_strip).astype('string')
    df['artist_key'] = df['artist_name_clean'].map(make_artist_key).astype('string')

    mbids = df['artist_mbids_parsed'].map(lambda v: json.loads(v) if isinstance(v, str) else [])
    df['n_credited_artists'] = mbids.map(len).astype('int64')
    df['has_artist_mbid'] = df['n_credited_artists'] > 0
    first_mbid = mbids.map(lambda v: v[0] if v else pd.NA)

    # R7: first credited MBID, else the name key.  R7b: a key seen with exactly one MBID
    # lends that MBID to its rows without one (e.g. Arthrn: 125 MBID rows + 57 name-only rows).
    key_mbids = (pd.DataFrame({'key': df['artist_key'], 'mbid': first_mbid})
                 .dropna().groupby('key')['mbid'].unique())
    single_mbid = key_mbids[key_mbids.map(len) == 1].map(lambda a: a[0])
    borrowed = ~df['has_artist_mbid'] & df['artist_key'].isin(single_mbid.index)
    df['artist_id'] = first_mbid.where(df['has_artist_mbid'], 'name:' + df['artist_key'].astype(object))
    df.loc[borrowed, 'artist_id'] = df.loc[borrowed, 'artist_key'].map(single_mbid)
    df['artist_id'] = df['artist_id'].astype('string')
    df['artist_id_source'] = np.select([df['has_artist_mbid'], borrowed, df['artist_key'].notna()],
                                       ['mbid', 'key_mbid', 'name'], 'missing')

    # R9: same user + recording within 60 s of the previous play = suspected double-scrobble.
    # Computed on the full table, before any period filter.
    df = df.sort_values(['username', 'listened_at_utc'], kind='stable')
    gap = df.groupby(['username', 'recording_msid'])['listened_at_utc'].diff().dt.total_seconds()
    df['is_countable'] = ~(gap < DOUBLE_SCROBBLE_SECONDS)
    return df.reset_index(drop=True)


# ---------------------------------------------------------------- filters

def filter_period(listens, start=None, end=None, users=None):
    """Keep listens from start to end (inclusive UTC days) and, optionally, only some users."""
    keep = pd.Series(True, index=listens.index)
    if start is not None:
        keep &= listens['listened_at_utc'] >= _utc_day(start)
    if end is not None:
        keep &= listens['listened_at_utc'] < _utc_day(end) + ONE_DAY
    if users is not None:
        keep &= listens['username'].isin(list(users))
    return listens.loc[keep].copy()


def _utc_day(value):
    ts = pd.Timestamp(value)
    return (ts.tz_localize('UTC') if ts.tzinfo is None else ts.tz_convert('UTC')).normalize()


def countable_artist_listens(listens):
    """Rows the artist metrics use: countable and with an artist (placeholders excluded)."""
    return listens.loc[listens['is_countable'] & listens['artist_key'].notna()]


def user_windows(listens):
    """Each user's observed window: first/last countable listen in the frame passed in."""
    countable = listens.loc[listens['is_countable']]
    return (countable.groupby('username')['listened_at_utc']
            .agg(first_listen_utc='min', last_listen_utc='max', countable_listens='size')
            .reset_index())


# ---------------------------------------------------------------- KPIs

def pair_kpis(listens, min_return_listens=3, min_return_window_days=2):
    """One row per listener x artist: depth of engagement and return momentum."""
    rows = countable_artist_listens(listens)
    if rows.empty:
        return pd.DataFrame(columns=PAIR_COLUMNS)
    g = rows.groupby(PAIR_KEY)
    pairs = g.agg(countable_listens=('listen_id', 'size'),
                  distinct_tracks=('recording_msid', 'nunique'),
                  active_days=('listen_day', 'nunique'),
                  first_listen_utc=('listened_at_utc', 'min'),
                  last_listen_utc=('listened_at_utc', 'max'),
                  first_day=('listen_day', 'min')).reset_index()
    pairs['returned'] = pairs['active_days'] >= 2
    pairs['multi_track'] = pairs['distinct_tracks'] >= 2

    later = rows.merge(pairs[PAIR_KEY + ['first_day']], on=PAIR_KEY)
    later = later.loc[later['listen_day'] > later['first_day']]
    second_day = later.groupby(PAIR_KEY)['listen_day'].min().rename('second_day').reset_index()
    pairs = pairs.merge(second_day, on=PAIR_KEY, how='left')
    pairs['days_to_return'] = (pairs['second_day'] - pairs['first_day']).dt.days

    pairs = _return_momentum(pairs, rows, listens, min_return_listens, min_return_window_days)
    pairs['display_name'] = pairs['artist_id'].map(_display_names(rows))
    return pairs[PAIR_COLUMNS].sort_values(PAIR_KEY, kind='stable').reset_index(drop=True)


def _return_momentum(pairs, rows, listens, min_return_listens, min_return_window_days):
    """Share of the pair's return listens in the late half of its return window, minus the
    listener's own late-half share over the same window (0 = kept pace with the listener).
    Return window: midnight after the first listen -> listener's last countable listen."""
    windows = user_windows(listens).set_index('username')['last_listen_utc']
    pairs['return_start'] = pairs['first_day'] + ONE_DAY
    pairs['return_end'] = pairs['username'].map(windows)
    pairs['return_mid'] = pairs['return_start'] + (pairs['return_end'] - pairs['return_start']) / 2

    marks = rows.merge(pairs[PAIR_KEY + ['return_start', 'return_mid']], on=PAIR_KEY)
    marks['in_return'] = marks['listened_at_utc'] >= marks['return_start']
    marks['late'] = marks['in_return'] & (marks['listened_at_utc'] >= marks['return_mid'])
    counts = marks.groupby(PAIR_KEY)[['in_return', 'late']].sum()
    pairs = pairs.join(counts.rename(columns={'in_return': 'return_listens',
                                              'late': 'late_return_listens'}), on=PAIR_KEY)

    # Listener baseline: all of the user's countable listens (any artist) inside the window.
    activity = listens.loc[listens['is_countable']]
    pairs['expected_late_share'] = np.nan
    for user, idx in pairs.groupby('username').groups.items():
        times = np.sort(activity.loc[activity['username'] == user, 'listened_at_utc'].to_numpy())
        start = pairs.loc[idx, 'return_start'].to_numpy()
        mid = pairs.loc[idx, 'return_mid'].to_numpy()
        in_window = len(times) - np.searchsorted(times, start)
        late = len(times) - np.searchsorted(times, mid)
        with np.errstate(invalid='ignore', divide='ignore'):
            pairs.loc[idx, 'expected_late_share'] = np.where(in_window > 0, late / in_window, np.nan)

    valid = ((pairs['return_listens'] >= min_return_listens)
             & (pairs['return_end'] - pairs['return_start'] >= pd.Timedelta(min_return_window_days, unit='D')))
    momentum = pairs['late_return_listens'] / pairs['return_listens'] - pairs['expected_late_share']
    pairs['return_momentum'] = momentum.where(valid)
    return pairs


def _display_names(rows):
    """Most common spelling, preferring single-credit rows; ties -> alphabetically first."""
    single = rows.loc[rows['n_credited_artists'] == 1]
    pick = pd.concat([single, rows.loc[~rows['artist_id'].isin(single['artist_id'])]])
    return pick.groupby('artist_id')['artist_name_clean'].agg(lambda s: s.mode().iloc[0])


def artist_kpis(listens, **pair_params):
    """One row per artist (UC1 ranking table). pair_params go to pair_kpis()."""
    pairs = pair_kpis(listens, **pair_params)
    rows = countable_artist_listens(listens)
    if rows.empty:
        return pd.DataFrame(columns=ARTIST_COLUMNS)
    artists = rows.groupby('artist_id').agg(
        countable_listens=('listen_id', 'size'),
        distinct_tracks=('recording_msid', 'nunique'),
        first_listen_utc=('listened_at_utc', 'min'),
        last_listen_utc=('listened_at_utc', 'max'))
    by_pair = pairs.groupby('artist_id').agg(
        unique_listeners=('username', 'size'),
        returning_listeners=('returned', 'sum'),
        avg_active_days=('active_days', 'mean'),
        multi_track_rate=('multi_track', 'mean'),
        median_days_to_return=('days_to_return', 'median'))
    artists = artists.join(by_pair)
    artists['return_rate'] = artists['returning_listeners'] / artists['unique_listeners']
    artists['listens_per_listener'] = artists['countable_listens'] / artists['unique_listeners']

    artists = artists.join(pooled_momentum(pairs))
    artists['momentum_pairs'] = artists['momentum_pairs'].fillna(0).astype('int64')
    artists['display_name'] = _display_names(rows)
    ids = artists.index.to_series()
    artists['artist_mbid'] = ids.where(~ids.str.startswith('name:'))
    artists = rank_artists(artists.reset_index())
    return artists[ARTIST_COLUMNS].sort_values('rank').reset_index(drop=True)


def pooled_momentum(pairs):
    """Artist momentum pooled over valid pairs, (sum L - sum exp*R) / sum R, so a pair with
    more return listens weighs more. Returns return_momentum and momentum_pairs per artist."""
    valid = pairs.loc[pairs['return_momentum'].notna()].copy()
    valid['expected_late'] = valid['expected_late_share'] * valid['return_listens']
    sums = valid.groupby('artist_id')[['late_return_listens', 'expected_late', 'return_listens']].sum()
    return pd.DataFrame({
        'return_momentum': (sums['late_return_listens'] - sums['expected_late']) / sums['return_listens'],
        'momentum_pairs': valid.groupby('artist_id').size()})


def rank_artists(artists):
    """Default order of the UC1 table: rank 1 = strongest repeat-engagement evidence.
    Most artists have 1 listener, so depth (days, returns, listens) carries the ranking."""
    order = artists.sort_values(
        ['return_rate', 'avg_active_days', 'countable_listens', 'return_momentum', 'artist_id'],
        ascending=[False, False, False, False, True], kind='stable')
    artists = artists.copy()
    artists.loc[order.index, 'rank'] = np.arange(1, len(order) + 1)
    artists['rank'] = artists['rank'].astype('int64')
    return artists


def headline_kpis(listens, pairs, artists):
    """Dataset-level numbers for the KPI cards, as plain Python values (JSON-ready)."""
    countable = listens['is_countable']
    times = listens['listened_at_utc']
    kpis = {
        'period_start': times.min().date().isoformat() if len(times) else None,
        'period_end': times.max().date().isoformat() if len(times) else None,
        'listeners': listens['username'].nunique(),
        'artists': len(artists),
        'total_listens': len(listens),
        'countable_listens': int(countable.sum()),
        'excluded_double_scrobbles': int((~countable).sum()),
        'excluded_missing_artist': int((countable & listens['artist_key'].isna()).sum()),
        'artist_listens': len(countable_artist_listens(listens)),
        'listener_artist_pairs': len(pairs),
        'pair_return_rate': pairs['returned'].mean(),
        'pair_multi_track_rate': pairs['multi_track'].mean(),
        'pct_artists_with_return': (artists['returning_listeners'] > 0).mean(),
        'artists_with_2plus_listeners': int((artists['unique_listeners'] >= 2).sum()),
        'artists_with_momentum': int(artists['return_momentum'].notna().sum()),
        'median_return_momentum': artists['return_momentum'].median(),
    }
    return {k: _plain(v) for k, v in kpis.items()}


def _plain(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return None if np.isnan(value) else round(float(value), 4)
    return value


# ---------------------------------------------------------------- shortlist + detail

@dataclass(frozen=True)
class EmergingFilter:
    """Artist-level shortlist filter applied after KPIs are computed (UC1)."""
    min_listens: int = 1
    min_avg_active_days: float = 1.0
    max_listeners: int | None = None
    mbid_status: str = 'any'                  # 'any' | 'mbid' | 'no_mbid'
    exclude_artist_ids: tuple = ()            # editor's list of established artists


def apply_emerging_filter(artists, f=EmergingFilter()):
    if f.mbid_status not in {'any', 'mbid', 'no_mbid'}:
        raise ValueError(f'mbid_status must be any, mbid or no_mbid, got {f.mbid_status!r}')
    keep = (artists['countable_listens'] >= f.min_listens) & (artists['avg_active_days'] >= f.min_avg_active_days)
    if f.max_listeners is not None:
        keep &= artists['unique_listeners'] <= f.max_listeners
    if f.mbid_status != 'any':
        keep &= artists['artist_mbid'].notna() == (f.mbid_status == 'mbid')
    keep &= ~artists['artist_id'].isin(list(f.exclude_artist_ids))
    return artists.loc[keep].reset_index(drop=True)


class ArtistDetail(NamedTuple):
    summary: pd.Series        # this artist's artist_kpis row
    listeners: pd.DataFrame   # this artist's pair_kpis rows
    tracks: pd.DataFrame      # one row per recording


def artist_detail(listens, artist_id, **pair_params):
    """Everything UC2/UC3 show for one artist. Raises KeyError if the artist has no listens."""
    artists = artist_kpis(listens, **pair_params)
    match = artists.loc[artists['artist_id'] == artist_id]
    if match.empty:
        raise KeyError(artist_id)
    pairs = pair_kpis(listens, **pair_params)
    rows = countable_artist_listens(listens)
    rows = rows.loc[rows['artist_id'] == artist_id]
    tracks = (rows.groupby('recording_msid')
              .agg(track_name=('track_name_clean', lambda s: s.mode().iloc[0]),
                   countable_listens=('listen_id', 'size'),
                   listeners=('username', 'nunique'),
                   first_listen_utc=('listened_at_utc', 'min'),
                   last_listen_utc=('listened_at_utc', 'max'))
              .reset_index()
              .sort_values(['countable_listens', 'track_name'], ascending=[False, True], kind='stable')
              .reset_index(drop=True))
    return ArtistDetail(match.iloc[0], pairs.loc[pairs['artist_id'] == artist_id].reset_index(drop=True), tracks)


# ---------------------------------------------------------------- pipeline

def compute_kpis(listens, **pair_params):
    """Artist table, listener x artist table and summary (KPI cards + reconciliation checks)."""
    pairs = pair_kpis(listens, **pair_params)
    artists = artist_kpis(listens, **pair_params)
    kpis = headline_kpis(listens, pairs, artists)
    checks = {
        'pair_listens_equal_artist_listens': int(pairs['countable_listens'].sum()) == kpis['artist_listens'],
        'artist_listens_equal_artist_listens': int(artists['countable_listens'].sum()) == kpis['artist_listens'],
        'listeners_sum_equals_pairs': int(artists['unique_listeners'].sum()) == len(pairs),
        'countable_plus_excluded_equals_total':
            kpis['countable_listens'] + kpis['excluded_double_scrobbles'] == kpis['total_listens'],
        'return_rate_in_0_1': bool(artists['return_rate'].between(0, 1).all()),
        'momentum_in_minus1_1': bool(artists['return_momentum'].dropna().between(-1, 1).all()),
        'ranks_unique_1_to_n': sorted(artists['rank']) == list(range(1, len(artists) + 1)),
    }
    assert all(checks.values()), {k: v for k, v in checks.items() if not v}
    identity = listens['artist_id_source'].value_counts().to_dict()
    return artists, pairs, {'kpis': kpis, 'artist_id_source_rows': identity, 'checks': checks}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', default=DEFAULT_INPUT, help="Member 3's listenbrainz_final_cleaned.csv")
    p.add_argument('--outdir', default='outputs_kpi')
    p.add_argument('--start', help='first UTC day to include, YYYY-MM-DD')
    p.add_argument('--end', help='last UTC day to include, YYYY-MM-DD')
    a = p.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    listens = filter_period(load_listens(a.input), a.start, a.end)
    artists, pairs, summary = compute_kpis(listens)
    artists.round(4).to_csv(out / 'artist_kpis.csv', index=False)
    pairs.round(4).to_csv(out / 'listener_artist_kpis.csv', index=False)
    (out / 'kpi_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))
    print(f'artists: {len(artists)}  listener x artist pairs: {len(pairs)}  -> {out}/')


if __name__ == '__main__':
    main()
