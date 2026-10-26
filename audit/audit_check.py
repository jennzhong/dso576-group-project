"""Independently verify the artist-performance total-listens metric."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "listenbrainz_final_cleaned.csv"
OUTPUT_PATH = ROOT / "member5-aggregations" / "outputs" / "artist_performance.csv"


def main():
    raw = pd.read_csv(DATA_PATH)
    # Match build_artist_performance: require username, artist_name, and a
    # parseable listened_at_utc value; then count every remaining listen row.
    filtered = raw.copy()
    filtered["listened_at_utc"] = pd.to_datetime(
        filtered["listened_at_utc"], utc=True, errors="coerce"
    )
    valid = filtered.dropna(subset=["username", "artist_name", "listened_at_utc"])

    independently_grouped = valid.groupby("artist_name").size()
    expected_total = int(independently_grouped.sum())
    output = pd.read_csv(OUTPUT_PATH)
    actual_total = int(output["total_listens"].sum())

    print(f"Input file: {DATA_PATH.relative_to(ROOT)}")
    print(f"Raw records: {len(raw)}")
    print("Filter: non-missing username, artist_name, and valid listened_at_utc")
    print(f"Records retained: {len(valid)}")
    print(f"Records excluded by filter: {len(raw) - len(valid)}")
    print(f"Missing artist_name in raw data: {int(raw['artist_name'].isna().sum())}")
    print(f"Valid timestamp min: {valid['listened_at_utc'].min().isoformat()}")
    print(f"Valid timestamp max: {valid['listened_at_utc'].max().isoformat()}")
    print(f"Artists in independent grouping: {len(independently_grouped)}")
    print(f"Listens per artist min: {int(independently_grouped.min())}")
    print(f"Listens per artist max: {int(independently_grouped.max())}")
    print(f"Independent artist-performance total_listens sum: {expected_total}")
    print(f"Generated output total_listens sum: {actual_total}")
    print(f"Match: {expected_total == actual_total}")


if __name__ == "__main__":
    main()
