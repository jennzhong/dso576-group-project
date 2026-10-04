"""
Recreate the DSO 576 ListenBrainz sample documented in the team's Project Starting Point.

This script:
- uses the five documented ListenBrainz users
- only requests listens before 2026-09-22 00:00:00 UTC
  (so the historical cutoff includes September 21, 2026)
- targets the documented per-user row counts
- uses the server-resolved track_metadata.mbid_mapping fields when present
- writes the raw extract to listenbrainz_sample.csv

The raw CSV is an input artifact. Do not edit it by hand.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests


API_ROOT = "https://api.listenbrainz.org"
OUTPUT_FILE = Path("listenbrainz_sample.csv")
VALIDATION_FILE = Path("pull_validation.json")

# Documented in the team's Project Starting Point.
TARGET_COUNTS = {
    "iliekcomputers": 500,
    "H-music": 500,
    "s_john_s": 500,
    "John V": 226,
    "music_af": 214,
}

# max_ts is exclusive in the ListenBrainz API.
CUTOFF_UTC = datetime(2026, 9, 22, 0, 0, 0, tzinfo=timezone.utc)
PAGE_SIZE = 100

# Reference values from the team's September 2026 project exploration.
REFERENCE = {
    "rows": 1940,
    "unique_listeners": 5,
    "unique_artist_names": 756,
    "missing": {
        "username": 0,
        "listened_at": 0,
        "track_name": 0,
        "artist_name": 0,
        "recording_msid": 0,
        "recording_mbid": 728,
        "release_name": 754,
        "artist_mbids": 759,
        "release_mbid": 759,
    },
    "date_ranges": {
        "music_af": ("2025-09-17", "2026-03-25"),
        "H-music": ("2019-07-15", "2019-11-15"),
        "iliekcomputers": ("2024-11-16", "2024-12-16"),
        "s_john_s": ("2019-03-07", "2019-03-20"),
        "John V": ("2026-09-17", "2026-09-21"),
    },
}


def iso_utc(unix_ts: int | float | None) -> str | None:
    if unix_ts is None:
        return None
    return datetime.fromtimestamp(int(unix_ts), tz=timezone.utc).isoformat()


def fetch_user_listens(session: requests.Session, username: str, target_count: int) -> list[dict]:
    """Fetch up to target_count historical listens, paging backward with max_ts."""
    collected: list[dict] = []
    max_ts = int(CUTOFF_UTC.timestamp())

    while len(collected) < target_count:
        remaining = target_count - len(collected)
        count = min(PAGE_SIZE, remaining)

        url = f"{API_ROOT}/1/user/{quote(username, safe='')}/listens"
        response = session.get(
            url,
            params={"max_ts": max_ts, "count": count},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json().get("payload", {})
        page = payload.get("listens", [])

        if not page:
            break

        collected.extend(page)

        oldest_ts = min(item["listened_at"] for item in page if item.get("listened_at") is not None)
        # max_ts is exclusive, so using the oldest timestamp prevents re-fetching that timestamp.
        max_ts = int(oldest_ts)

        # Be gentle to the public API.
        time.sleep(0.25)

    return collected[:target_count]


def flatten_listen(requested_username: str, listen: dict) -> dict:
    track = listen.get("track_metadata") or {}
    mapping = track.get("mbid_mapping") or {}

    artist_mbids = mapping.get("artist_mbids")
    if artist_mbids:
        artist_mbids = json.dumps(artist_mbids, ensure_ascii=False)
    else:
        artist_mbids = None

    return {
        "username": listen.get("user_name") or requested_username,
        "listened_at": iso_utc(listen.get("listened_at")),
        "track_name": track.get("track_name"),
        "artist_name": track.get("artist_name"),
        "release_name": track.get("release_name"),
        "recording_msid": listen.get("recording_msid"),
        "artist_mbids": artist_mbids,
        "recording_mbid": mapping.get("recording_mbid"),
        "release_mbid": mapping.get("release_mbid"),
    }


def build_validation(df: pd.DataFrame) -> dict:
    parsed = df.copy()
    parsed["listened_at"] = pd.to_datetime(parsed["listened_at"], errors="coerce", utc=True)

    missing = {col: int(parsed[col].isna().sum()) for col in parsed.columns}
    per_user = parsed["username"].value_counts(dropna=False).to_dict()

    date_ranges = {}
    for username, group in parsed.groupby("username", dropna=False):
        date_ranges[str(username)] = {
            "min": group["listened_at"].min().date().isoformat() if group["listened_at"].notna().any() else None,
            "max": group["listened_at"].max().date().isoformat() if group["listened_at"].notna().any() else None,
            "count": int(len(group)),
        }

    actual = {
        "rows": int(len(parsed)),
        "unique_listeners": int(parsed["username"].nunique(dropna=True)),
        "unique_artist_names": int(parsed["artist_name"].nunique(dropna=True)),
        "missing": missing,
        "per_user": {str(k): int(v) for k, v in per_user.items()},
        "date_ranges": date_ranges,
    }

    warnings = []
    if actual["rows"] != REFERENCE["rows"]:
        warnings.append(f"Row count differs from 2026 project reference: {actual['rows']} vs {REFERENCE['rows']}.")
    if actual["unique_artist_names"] != REFERENCE["unique_artist_names"]:
        warnings.append(
            "Unique artist-name count differs from the 2026 project reference. "
            "ListenBrainz mappings/history can change over time."
        )

    for col, expected in REFERENCE["missing"].items():
        if actual["missing"].get(col) != expected:
            warnings.append(
                f"Missing count for {col} differs from project reference: "
                f"{actual['missing'].get(col)} vs {expected}."
            )

    for username, expected_count in TARGET_COUNTS.items():
        if actual["per_user"].get(username, 0) != expected_count:
            warnings.append(
                f"{username}: expected target {expected_count}, received {actual['per_user'].get(username, 0)}."
            )

    return {
        "source": "ListenBrainz public API",
        "endpoint": "GET /1/user/{username}/listens",
        "historical_cutoff_utc": CUTOFF_UTC.isoformat(),
        "recreated_at_utc": datetime.now(timezone.utc).isoformat(),
        "reference_from_team_project": REFERENCE,
        "actual": actual,
        "warnings": warnings,
    }


def main() -> None:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "USC-DSO576-Student-Project/1.0 (educational data cleaning assignment)",
            "Accept": "application/json",
        }
    )

    rows = []
    for username, target in TARGET_COUNTS.items():
        print(f"Fetching {username}: target {target} listens...")
        listens = fetch_user_listens(session, username, target)
        print(f"  received {len(listens)}")
        rows.extend(flatten_listen(username, item) for item in listens)

    columns = [
        "username",
        "listened_at",
        "track_name",
        "artist_name",
        "release_name",
        "recording_msid",
        "artist_mbids",
        "recording_mbid",
        "release_mbid",
    ]
    df = pd.DataFrame(rows, columns=columns)
    df.to_csv(OUTPUT_FILE, index=False)

    validation = build_validation(df)
    VALIDATION_FILE.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nWrote {OUTPUT_FILE} with {len(df):,} rows.")
    print(f"Wrote {VALIDATION_FILE}.")
    print("\nReference check:")
    print(f"  Rows: {len(df):,} (team reference: {REFERENCE['rows']:,})")
    print(f"  Unique listeners: {df['username'].nunique()} (team reference: 5)")
    print(f"  Unique artist names: {df['artist_name'].nunique()} (team reference: 756)")
    if validation["warnings"]:
        print("\nIMPORTANT: recreation warnings")
        for warning in validation["warnings"]:
            print(f"  - {warning}")
        print(
            "\nA warning does not automatically mean the pull failed. "
            "ListenBrainz data/resolution can change after the original September 2026 extract. "
            "Keep pull_validation.json as evidence of what changed."
        )
    else:
        print("\nThe recreated extract matches all stored reference checks.")


if __name__ == "__main__":
    main()
