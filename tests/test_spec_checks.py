
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "member5-aggregations"))
import kpi_analysis as kpi
import aggregation_functions as m5
listens = kpi.load_listens()
def test_data_matches_spec():
    assert len(listens) == 1940
    assert listens["username"].nunique() == 5
    assert listens.duplicated(["username", "listened_at", "recording_msid"]).sum() == 0
    assert listens["listened_at_utc"].isna().sum() == 0
def test_kpi_totals():
    summary = kpi.compute_kpis(listens)[2]["kpis"]
    assert summary["countable_listens"] == 1882
    assert summary["artists"] == 669
    assert summary["listener_artist_pairs"] == 677
def test_capped_listeners():
    users = m5.build_listener_engagement(listens)
    capped = users[users["total_listens"] == 500]["username"]
    assert set(capped) == {"H-music", "iliekcomputers", "s_john_s"}
def test_functions_do_not_change_input():
    before = listens.copy()
    kpi.compute_kpis(listens)
    m5.build_listener_engagement(listens)
    assert listens.equals(before)
def test_empty_period_gives_empty_tables():
    empty = kpi.filter_period(listens, start="2030-01-01")
    assert len(kpi.artist_kpis(empty)) == 0
def test_m4_and_m5_use_the_same_artist_id():
    top_artist = kpi.artist_kpis(listens).iloc[0]["artist_id"]
    events = m5.build_artist_listen_events(listens)
    engagement = m5.build_artist_engagement(events)
    assert top_artist in set(engagement["artist_mbid"])