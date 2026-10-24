"""Lewis's Module 9 evidence. Run from the repository root:

python lewis_audit_check.py > lewis-audit-evidence.json
python -m pytest -q lewis_audit_check.py

Three strict xfails document CR-L1/CR-L2; xfails are unresolved defects, not fixes.
No application, data, or teammate audit files are modified.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "member5-aggregations"))
import aggregation_functions as m5
import kpi_analysis as kpi

AUDITED_COMMIT = "b67101fbc3d068b5ba42c31992236bdd6bf5ee59"


def reference(rows):
    """Independent stdlib calculation: one initial play per recording MSID.

    MSID is a reproducible identity convention, not guaranteed musical truth.
    The real three-row counterexample also has three distinct recording MBIDs.
    """
    counts = Counter(r["recording_msid"] for r in rows)
    assert all(counts), "Missing identities require an agreed fallback."
    n = len(rows)
    return {
        "total_listens": n,
        "distinct_recording_msids": len(counts),
        "repeat_listens": sum(count - 1 for count in counts.values()),
        "repeat_pct": round(100 * sum(count - 1 for count in counts.values()) / n, 2)
        if n else None,
        "active_days": len({datetime.fromisoformat(r["listened_at_utc"])
                           .astimezone(timezone.utc).date() for r in rows}),
    }


def synthetic_rows():
    # Alpha/Echo and Beta/Echo are explicitly different recordings.
    return [
        {"username": "test_listener", "listened_at_utc": "2026-01-01T10:00:00+00:00",
         "artist_name": "Alpha", "track_name": "Echo", "release_name": "A",
         "recording_msid": "recording-a"},
        {"username": "test_listener", "listened_at_utc": "2026-01-01T10:05:00+00:00",
         "artist_name": "Beta", "track_name": "Echo", "release_name": "B",
         "recording_msid": "recording-b"},
        {"username": "test_listener", "listened_at_utc": "2026-01-02T10:00:00+00:00",
         "artist_name": "Alpha", "track_name": "Echo", "release_name": "A",
         "recording_msid": "recording-a"},
    ]


def app_listener_table(at):
    assert not list(at.exception), [v.value for v in at.exception]
    return next(df.value for df in at.dataframe
                if "repeat_listen_pct" in df.value.columns).copy()


@lru_cache(maxsize=1)
def evidence():
    with (ROOT / "listenbrainz_final_cleaned.csv").open(newline="") as f:
        raw = list(csv.DictReader(f))
    real = [r for r in raw if r["username"] == "music_af"
            and datetime.fromisoformat(r["listened_at_utc"])
            .astimezone(timezone.utc).date() == date(2026, 3, 14)]
    synthetic = synthetic_rows()
    synthetic_actual = m5.build_listener_engagement(pd.DataFrame(synthetic)).iloc[0]
    loaded = kpi.load_listens()
    filtered = kpi.filter_period(loaded, "2026-03-14", "2026-03-14", ["music_af"])
    real_actual = m5.build_listener_engagement(filtered).iloc[0]

    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "app.py")).run(timeout=60)
    default = app_listener_table(at)
    default_rows = default[["username", "total_listens", "active_days"]].to_dict("records")
    at.multiselect[0].set_value(["music_af"]).run(timeout=60)
    single = app_listener_table(at).to_dict("records")
    at.date_input[0].set_value((date(2026, 3, 14), date(2026, 3, 14))).run(timeout=60)
    one_day = app_listener_table(at).to_dict("records")
    at.number_input[0].set_value(10000).run(timeout=60)
    shortlist_scope = app_listener_table(at).to_dict("records")
    shortlist_messages = [v.value for v in at.info]
    at.multiselect[0].set_value([]).run(timeout=60)
    assert not list(at.exception)
    empty_users = {"messages": [v.value for v in at.info], "tables": len(at.dataframe)}
    at.multiselect[0].set_value(["music_af"])
    at.date_input[0].set_value((date(2019, 3, 7), date(2019, 3, 7))).run(timeout=60)
    assert not list(at.exception)
    empty_period = {"messages": [v.value for v in at.info], "tables": len(at.dataframe)}
    at.date_input[0].set_value((date(2026, 3, 14),)).run(timeout=60)
    partial_range = {"input": ["2026-03-14"],
                     "exceptions": [v.value for v in at.exception]}

    full_actual = m5.build_listener_engagement(loaded).set_index("username")
    sensitivity = []
    for user in sorted({r["username"] for r in raw}):
        rows = [r for r in raw if r["username"] == user]
        sensitivity.append({"username": user,
                            "title_based_actual_pct": float(full_actual.loc[user, "repeat_listen_pct"]),
                            "msid_based_reference": reference(rows)})
    return {
        "audited_commit": AUDITED_COMMIT,
        "versions": {"python": sys.version.split()[0], "pandas": pd.__version__,
                     "streamlit": __import__("streamlit").__version__,
                     "plotly": __import__("plotly").__version__, "pytest": pytest.__version__},
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                          for name in ["app.py", "listenbrainz_final_cleaned.csv",
                                       "member5-aggregations/aggregation_functions.py"]},
        "synthetic": {"inputs": synthetic, "reference": reference(synthetic),
                      "actual_pct": float(synthetic_actual.repeat_listen_pct)},
        "real_single_day": {"inputs": [
            {key: r[key] for key in ["username", "listened_at_utc", "artist_name", "track_name",
                                     "recording_msid", "recording_mbid"]} for r in real],
            "reference": reference(real), "actual_pct": float(real_actual.repeat_listen_pct)},
        "feature": {"default": default_rows, "single_user": single,
                    "single_day": one_day, "shortlist_scope": shortlist_scope,
                    "shortlist_messages": shortlist_messages,
                    "empty_users": empty_users, "empty_period": empty_period,
                    "partial_range": partial_range},
        "full_sample_identity_sensitivity": sensitivity,
    }


def test_hand_calculable_reference():
    result = reference(synthetic_rows())
    assert result["total_listens"] == 3
    assert result["repeat_listens"] == 1
    assert result["repeat_pct"] == 33.33


@pytest.mark.xfail(strict=True, reason="CR-L1: title-only identity merges distinct recordings")
def test_same_title_different_recordings():
    e = evidence()["synthetic"]
    assert e["actual_pct"] == e["reference"]["repeat_pct"]


def test_real_counterexample_has_distinct_recordings():
    e = evidence()["real_single_day"]
    assert e["reference"] == {"total_listens": 3, "distinct_recording_msids": 3,
                              "repeat_listens": 0, "repeat_pct": 0.0, "active_days": 1}
    assert len({r["recording_mbid"] for r in e["inputs"]}) == 3


@pytest.mark.xfail(strict=True, reason="CR-L1: real single-day app value is 33.33%, expected 0%")
def test_real_day_repeat_percentage():
    e = evidence()["real_single_day"]
    assert e["actual_pct"] == e["reference"]["repeat_pct"]


def test_default_listener_coverage_and_capped_labels():
    rows = evidence()["feature"]["default"]
    assert len(rows) == 5
    assert sum(r["total_listens"] for r in rows) == 1940
    assert {r["username"] for r in rows if "capped" in r["username"]} == {
        "H-music · capped", "iliekcomputers · capped", "s_john_s · capped"}


def test_listener_and_inclusive_day_filter():
    e = evidence()["feature"]
    assert len(e["single_user"]) == 1
    assert e["single_user"][0]["username"] == "music_af"
    assert e["single_user"][0]["total_listens"] == 214
    assert e["single_day"][0]["total_listens"] == 3
    assert e["single_day"][0]["active_days"] == 1
    assert e["single_day"][0]["first_observed_listen"] == "2026-03-14"
    assert e["single_day"][0]["last_observed_listen"] == "2026-03-14"


def test_shortlist_filters_do_not_change_listener_table():
    e = evidence()["feature"]
    assert e["shortlist_scope"] == e["single_day"]
    assert "No artists match these filters" in e["shortlist_messages"]


def test_empty_selection_and_period_are_safe():
    e = evidence()["feature"]
    for case in ("empty_users", "empty_period"):
        assert e[case] == {"messages": ["No listens in this period"], "tables": 0}


@pytest.mark.xfail(strict=True, reason="CR-L2: selecting only a range start raises TypeError")
def test_partial_date_range_waits_for_end_date():
    assert evidence()["feature"]["partial_range"]["exceptions"] == []


if __name__ == "__main__":
    print(json.dumps(evidence(), indent=2))
