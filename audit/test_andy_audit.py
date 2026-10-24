"""Module 9 audit checks (Andy Chen).

Run: uv run pytest -q audit
Kept outside tests/ so the team suite (uv run pytest -q tests) is unchanged.
These checks are expected to FAIL on the audited commit; each failure is the evidence
for a change request in change-requests.md.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'member5-aggregations'))

import aggregation_functions as m5  # noqa: E402
import kpi_analysis as kpi  # noqa: E402

ARTIST = '00000000-0000-0000-0000-00000000000a'


def _listen(user, ts, track):
    return {'username': user, 'listened_at_utc': ts, 'track_name': track,
            'artist_name': 'Test Artist', 'recording_mbid': f'rec-{track}',
            'artist_mbids_parsed': json.dumps([ARTIST])}


def small_case():
    """Three listeners, one artist.
    u_session: two different tracks 3 minutes apart on ONE day (no return).
    u_return:  day 1, then again 9 days later (a real return within 30 days).
    u_once:    a single listen.
    """
    return pd.DataFrame([
        _listen('u_session', '2024-03-01T20:00:00Z', 'a'),
        _listen('u_session', '2024-03-01T20:03:00Z', 'b'),
        _listen('u_return', '2024-03-01T10:00:00Z', 'a'),
        _listen('u_return', '2024-03-10T10:00:00Z', 'a'),
        _listen('u_once', '2024-03-05T12:00:00Z', 'c'),
    ])


def test_30_day_return_small_case():
    """M5 return_rate_pct on a case small enough to compute by hand."""
    events = m5.build_artist_listen_events(small_case())
    row = m5.build_artist_engagement(events).set_index('artist_mbid').loc[ARTIST]
    assert row.return_rate_pct == 33.33


def test_30_day_return_never_exceeds_all_time_return():
    """On directly matched primary-artist rows, a 30-day return is a subset of
    M4's all-time (2+ distinct UTC days) return for the same listener population."""
    listens = kpi.load_listens()
    direct = listens.loc[listens['artist_id_source'].eq('mbid')]
    artists = kpi.artist_kpis(direct)
    events = m5.build_artist_listen_events(direct)
    primary_artist_by_event = direct['artist_id'].to_dict()
    events = events.loc[events['artist_mbid'].eq(
        events['listen_event_id'].map(primary_artist_by_event))]
    engagement = m5.build_artist_engagement(events)
    both = artists.merge(engagement, left_on='artist_id', right_on='artist_mbid')
    above = both.loc[both['return_rate_pct'] > both['return_rate'] * 100 + 1e-9]
    assert above.empty, (f'{len(above)} artists have 30-day return > all-time return, e.g. '
                         + ', '.join(above['display_name'].head(5)))


def test_row_click_changes_artist_detail():
    """UC1 -> UC2: a Tab 1 row click sets st.session_state.selected_artist_id
    (app.py line 151); Tab 2's picker should then show that artist."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
    first = at.selectbox(key='artist_picker').value
    target = kpi.artist_kpis(kpi.load_listens()).iloc[4]['artist_id']   # rank 5
    assert target != first
    at.session_state['selected_artist_id'] = target                     # what the click does
    at.run()
    assert at.selectbox(key='artist_picker').value == target
