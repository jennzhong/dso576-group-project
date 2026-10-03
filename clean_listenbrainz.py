"""Prepare a reproducible, one-row-per-listen ListenBrainz analysis dataset.

The source CSV is opened read-only and its raw columns are kept as text.
Only exact duplicate rows across all raw source columns are removed. Derived
timestamp and artist-MBID representations are added without replacing source
values or expanding the listen-event table.
"""

import json
import re
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_PATH = PROJECT_DIR / "listenbrainz_sample.csv"
CLEANED_PATH = PROJECT_DIR / "cleaned_listenbrainz.csv"
USER_SUMMARY_PATH = PROJECT_DIR / "user_observation_summary.csv"
REPORT_PATH = PROJECT_DIR / "validation_report.md"

# Keep this list in the source CSV's original order. These nine values are
# copied unchanged into the cleaned event table.
RAW_COLUMNS = [
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
EVENT_KEY_COLUMNS = ["username", "listened_at", "recording_msid"]
LISTEN_SAMPLE_CAP = 500
EXPECTED_SOURCE_ROWS = 2214

# MusicBrainz IDs are UUID-shaped strings. This check validates their visible
# format without coercing or rewriting the identifier values.
UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$"
)


def is_blank(value):
    """Treat only an empty CSV cell as missing; preserve other text literally."""
    return value == ""


def missing_counts(frame):
    """Count blank source cells and missing derived values by column."""
    counts = {}
    for column in frame.columns:
        series = frame[column]
        if column == "listened_at_utc":
            counts[column] = int(series.isna().sum())
        else:
            counts[column] = int(series.map(is_blank).sum())
    return counts


def parse_artist_mbids(value):
    """Safely parse one MBID cell, returning its list and validation details.

    This function never edits the source cell. A nonblank JSON array is
    returned as a Python list for checks, then re-serialized as JSON in the
    separate ``artist_mbids_parsed`` output column.
    """
    if is_blank(value):
        return None, "missing", 0

    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None, "invalid_json", 0

    if not isinstance(parsed, list):
        return None, "not_array", 0

    invalid_ids = sum(
        not isinstance(mbid, str) or not UUID_PATTERN.fullmatch(mbid)
        for mbid in parsed
    )
    return parsed, "valid_array", int(invalid_ids)


def key_diagnostics(frame):
    """Return uniqueness statistics for the candidate listen-event key."""
    duplicate_mask = frame.duplicated(subset=EVENT_KEY_COLUMNS, keep=False)
    duplicated_rows = int(duplicate_mask.sum())
    duplicate_groups = int(
        frame.loc[duplicate_mask, EVENT_KEY_COLUMNS]
        .drop_duplicates()
        .shape[0]
    )
    return {
        "unique": duplicated_rows == 0,
        "duplicate_rows": duplicated_rows,
        "duplicate_key_groups": duplicate_groups,
    }


def repeated_identifier_diagnostics(frame, column):
    """Report repeats of an entity identifier, separately from duplicate rows."""
    values = frame.loc[frame[column] != "", column]
    frequencies = values.value_counts()
    repeated = frequencies[frequencies > 1]
    return {
        "nonmissing_rows": int(len(values)),
        "distinct_ids": int(frequencies.size),
        "repeated_distinct_ids": int(len(repeated)),
        "rows_with_repeated_id": int(repeated.sum()),
        "extra_occurrences": int((repeated - 1).sum()),
    }


def timestamp_range(series):
    """Return ISO UTC range strings for a parsed datetime series."""
    valid = series.dropna()
    if valid.empty:
        return None, None
    return valid.min().isoformat(), valid.max().isoformat()


def make_user_observation_summary(source, cleaned):
    """Summarize cleaned time coverage and source cap status for each user."""
    source_counts = source.groupby("username", dropna=False).size().to_dict()
    user_names = sorted(set(source["username"].tolist()))
    rows = []

    for username in user_names:
        user_rows = cleaned.loc[cleaned["username"] == username]
        valid_timestamps = user_rows["listened_at_utc"].dropna()
        first_listen = valid_timestamps.min() if not valid_timestamps.empty else pd.NaT
        last_listen = valid_timestamps.max() if not valid_timestamps.empty else pd.NaT
        duration = (
            last_listen - first_listen
            if pd.notna(first_listen) and pd.notna(last_listen)
            else pd.NaT
        )
        source_row_count = int(source_counts.get(username, 0))

        rows.append(
            {
                "username": username,
                "row_count": int(len(user_rows)),
                "first_listen_utc": first_listen,
                "last_listen_utc": last_listen,
                "observed_duration": duration,
                # The sample cap applies to retrieved source events. Use the
                # pre-dedup source count so duplicate handling cannot conceal it.
                "source_row_count": source_row_count,
                "sampling_cap_reached": source_row_count >= LISTEN_SAMPLE_CAP,
            }
        )

    return pd.DataFrame(rows)


def format_missing_table(source_counts, final_counts, source_rows, final_rows):
    lines = [
        "| Column | Source missing | Source % | Cleaned missing | Cleaned % |",
        "|---|---:|---:|---:|---:|",
    ]
    columns = list(source_counts) + [
        column for column in final_counts if column not in source_counts
    ]
    for column in columns:
        before = source_counts.get(column, 0)
        after = final_counts.get(column, 0)
        before_pct = before * 100 / source_rows if source_rows else 0
        after_pct = after * 100 / final_rows if final_rows else 0
        lines.append(
            f"| `{column}` | {before:,} | {before_pct:.2f}% | "
            f"{after:,} | {after_pct:.2f}% |"
        )
    return "\n".join(lines)


def create_validation_report(
    source,
    cleaned,
    user_summary,
    source_duplicate_rows,
    source_key_check,
    final_key_check,
    source_missing,
    final_missing,
    source_timestamps,
    final_timestamps,
    source_timestamp_failures,
    final_timestamp_failures,
    mbid_validation,
    artist_mbid_coverage,
    repeated_ids,
):
    """Build a Markdown report with counts, comparisons, and validation results."""
    source_rows, source_columns = source.shape
    final_rows, final_columns = cleaned.shape
    rows_removed = source_rows - final_rows
    source_timestamp_min, source_timestamp_max = source_timestamps
    final_timestamp_min, final_timestamp_max = final_timestamps
    final_artist_names = int(cleaned["artist_name"].nunique())
    source_artist_names = int(source["artist_name"].nunique())
    source_users = int(source["username"].nunique())
    final_users = int(cleaned["username"].nunique())
    final_user_counts = cleaned["username"].value_counts().sort_index()

    if rows_removed == 0:
        row_account = (
            f"Source rows: {source_rows:,}\n"
            f"Cleaned rows: {final_rows:,}\n"
            "Rows removed: 0"
        )
    else:
        row_account = (
            f"Source rows: {source_rows:,}\n"
            f"Cleaned rows: {final_rows:,}\n"
            f"Rows removed: {rows_removed:,} (exact duplicate rows only)"
        )

    user_count_lines = [
        f"| `{username}` | {count:,} |"
        for username, count in final_user_counts.items()
    ]
    repeated_id_lines = []
    for column, values in repeated_ids.items():
        repeated_id_lines.append(
            f"| `{column}` | {values['distinct_ids']:,} | "
            f"{values['repeated_distinct_ids']:,} | "
            f"{values['rows_with_repeated_id']:,} | "
            f"{values['extra_occurrences']:,} |"
        )

    report = f"""# ListenBrainz Cleaning Validation Report

## Run summary

The source `listenbrainz_sample.csv` was read without modification. Raw source columns were loaded as text, and the cleaned event table retains all raw columns and values. The only permitted row removal is an exact duplicate across all nine raw source fields.

{row_account}

The cleaned table has **{final_columns} columns**: the {source_columns} preserved raw columns plus `listened_at_utc` and `artist_mbids_parsed`. The latter is JSON-serialized parsed-array text for portability in CSV; the original `artist_mbids` text is retained unchanged. The main table remains one row per listen. No artist rows were exploded, no MusicBrainz metadata was merged, and no emerging-artist or final continued-engagement labels were created.

## Shape and event checks

| Check | Source | Cleaned | Result |
|---|---:|---:|---|
| Rows | {source_rows:,} (expected {EXPECTED_SOURCE_ROWS:,}) | {final_rows:,} | {'PASS' if source_rows == EXPECTED_SOURCE_ROWS and final_rows == source_rows - source_duplicate_rows else 'CHECK'} |
| Columns | {source.shape[1]:,} | {cleaned.shape[1]:,} | {'PASS' if source.shape[1] == len(RAW_COLUMNS) and cleaned.shape[1] == len(RAW_COLUMNS) + 2 else 'CHECK'}: raw source columns preserved; two derived columns added |
| Exact duplicate rows across raw columns | {source_duplicate_rows:,} | 0 | Removed only from cleaned output |
| Candidate event key duplicate rows (`username`, `listened_at`, `recording_msid`) | {source_key_check['duplicate_rows']:,} | {final_key_check['duplicate_rows']:,} | {'Unique' if final_key_check['unique'] else 'Review key collisions'} |

Repeated recording, release, or artist identifiers are entity repeats and are not counted as duplicate listen events. No row was removed merely because an identifier repeats.

## Missing values

Blank CSV cells are preserved as blank in the raw columns. No optional metadata was filled or inferred.

{format_missing_table(source_missing, final_missing, source_rows, final_rows)}

## Timestamps

`listened_at` remains unchanged in the raw column. `listened_at_utc` is a derived, UTC-aware datetime. Timestamp conversion failures: **{source_timestamp_failures:,} source rows** and **{final_timestamp_failures:,} cleaned rows**. Failed conversions remain as missing derived datetimes; their source events are retained.

| Range | Earliest UTC | Latest UTC |
|---|---|---|
| Source | {source_timestamp_min or 'Unavailable'} | {source_timestamp_max or 'Unavailable'} |
| Cleaned | {final_timestamp_min or 'Unavailable'} | {final_timestamp_max or 'Unavailable'} |

## Users and artists

- Unique users: **{source_users:,} source**, **{final_users:,} cleaned**.
- Distinct submitted `artist_name` values: **{source_artist_names:,} source**, **{final_artist_names:,} cleaned**.
- Populated artist MBID arrays: **{artist_mbid_coverage['populated_rows']:,} rows**; blank: **{artist_mbid_coverage['missing_rows']:,} rows**; coverage: **{artist_mbid_coverage['coverage_percent']:.2f}%**.
- Distinct individual artist MBIDs: **{artist_mbid_coverage['unique_ids']:,}** across **{artist_mbid_coverage['id_occurrences']:,} occurrences**.
- Parsed-array validity: **{mbid_validation['valid_arrays']:,} valid arrays**, **{mbid_validation['invalid_json']:,} invalid JSON values**, **{mbid_validation['not_arrays']:,} non-array values**, **{mbid_validation['invalid_ids']:,} invalid UUID-shaped elements**.

| User | Cleaned listen rows |
|---|---:|
{chr(10).join(user_count_lines)}

## Repeated identifiers (not duplicate-event removal)

| Identifier column | Distinct populated IDs | IDs appearing more than once | Rows with a repeated ID | Occurrences beyond first |
|---|---:|---:|---:|---:|
{chr(10).join(repeated_id_lines)}

## Per-user observation windows

See `user_observation_summary.csv` for row counts, first and last valid UTC listen, observed duration, source row count, and whether the 500-listen sampling cap was reached. The cap status uses source counts before any exact-duplicate removal.

## Project limitations

The dataset has five users with different, non-overlapping windows; four histories reached the 500-listen cap. Missing artist metadata is preserved and MBID coverage is reported rather than imputed. These data support cleaning validation and descriptive repeat-listening exploration, but not reliable population-level or synchronized cross-user artist-growth claims. Repeated listens and listens on distinct days may be reported descriptively; this cleaning step does not assign a final continued-engagement label.
"""
    return report


def main():
    """Read the raw file, validate, write derived outputs, and print a summary."""
    if not SOURCE_PATH.is_file():
        raise FileNotFoundError(f"Raw source file not found: {SOURCE_PATH}")

    # Disable pandas' automatic NA token conversion so raw text such as "NA",
    # identifiers, names, and empty cells are not rewritten during ingestion.
    source = pd.read_csv(
        SOURCE_PATH,
        dtype=str,
        keep_default_na=False,
        na_filter=False,
    )
    missing_columns = [column for column in RAW_COLUMNS if column not in source.columns]
    if missing_columns:
        raise ValueError(f"Source CSV is missing required columns: {missing_columns}")
    unexpected_columns = [column for column in source.columns if column not in RAW_COLUMNS]
    if unexpected_columns:
        raise ValueError(
            f"Source CSV has unexpected columns; review the schema before proceeding: "
            f"{unexpected_columns}"
        )

    # Preserve exactly the documented nine raw fields and their source order.
    source = source.loc[:, RAW_COLUMNS].copy()
    source_rows = len(source)

    # Only an exact repeat of all nine raw values is considered a duplicate
    # event. Repeated IDs alone never cause a row to be removed.
    duplicate_mask = source.duplicated(subset=RAW_COLUMNS, keep="first")
    exact_duplicate_rows = int(duplicate_mask.sum())
    cleaned = source.loc[~duplicate_mask, RAW_COLUMNS].copy()

    # Convert the raw epoch value in a separate column. Invalid timestamps are
    # reported and retained as NaT in the derived column, never dropped.
    source_timestamp_utc = pd.to_datetime(
        pd.to_numeric(source["listened_at"], errors="coerce"),
        unit="s",
        utc=True,
        errors="coerce",
    )
    cleaned["listened_at_utc"] = pd.to_datetime(
        pd.to_numeric(cleaned["listened_at"], errors="coerce"),
        unit="s",
        utc=True,
        errors="coerce",
    )

    # Parse artist MBID lists safely for diagnostics and downstream analysis.
    # The original JSON text stays in artist_mbids; the new field is a JSON
    # representation of the parsed list and the event table is not exploded.
    mbid_results = [parse_artist_mbids(value) for value in source["artist_mbids"]]
    mbid_validation = {
        "valid_arrays": sum(status == "valid_array" for _, status, _ in mbid_results),
        "invalid_json": sum(status == "invalid_json" for _, status, _ in mbid_results),
        "not_arrays": sum(status == "not_array" for _, status, _ in mbid_results),
        "invalid_ids": sum(invalid_ids for _, _, invalid_ids in mbid_results),
    }
    parsed_json = [
        json.dumps(parsed, ensure_ascii=False) if parsed is not None else ""
        for parsed, status, _ in mbid_results
    ]
    cleaned["artist_mbids_parsed"] = [
        parsed_json[index] for index in cleaned.index
    ]

    # Summarize unique resolved artist IDs without changing or expanding events.
    all_artist_mbids = [
        mbid
        for parsed, status, _ in mbid_results
        if status == "valid_array"
        for mbid in parsed
        if isinstance(mbid, str)
    ]
    artist_mbid_coverage = {
        "populated_rows": sum(not is_blank(value) for value in source["artist_mbids"]),
        "missing_rows": sum(is_blank(value) for value in source["artist_mbids"]),
        "coverage_percent": (
            100 * sum(not is_blank(value) for value in source["artist_mbids"]) / source_rows
            if source_rows
            else 0.0
        ),
        "id_occurrences": len(all_artist_mbids),
        "unique_ids": len(set(all_artist_mbids)),
    }

    # Gather before/after diagnostics. Entity-ID repetitions are reported
    # separately and are not used to alter the cleaned event table.
    source_missing = missing_counts(source)
    final_missing = missing_counts(cleaned)
    source_key_check = key_diagnostics(source)
    final_key_check = key_diagnostics(cleaned)
    source_timestamp_range = timestamp_range(source_timestamp_utc)
    final_timestamp_range = timestamp_range(cleaned["listened_at_utc"])
    repeated_ids = {
        column: repeated_identifier_diagnostics(cleaned, column)
        for column in ("recording_msid", "recording_mbid", "release_mbid")
    }

    # User cap status is based on original fetched rows, while row_count reports
    # retained cleaned events. Observation durations use parsed UTC timestamps.
    user_summary = make_user_observation_summary(source, cleaned)

    # Write only derived outputs. SOURCE_PATH is never opened for writing.
    cleaned.to_csv(CLEANED_PATH, index=False, encoding="utf-8")
    user_summary.to_csv(USER_SUMMARY_PATH, index=False, encoding="utf-8")

    report = create_validation_report(
        source=source,
        cleaned=cleaned,
        user_summary=user_summary,
        source_duplicate_rows=exact_duplicate_rows,
        source_key_check=source_key_check,
        final_key_check=final_key_check,
        source_missing=source_missing,
        final_missing=final_missing,
        source_timestamps=source_timestamp_range,
        final_timestamps=final_timestamp_range,
        source_timestamp_failures=int(source_timestamp_utc.isna().sum()),
        final_timestamp_failures=int(cleaned["listened_at_utc"].isna().sum()),
        mbid_validation=mbid_validation,
        artist_mbid_coverage=artist_mbid_coverage,
        repeated_ids=repeated_ids,
    )
    REPORT_PATH.write_text(report, encoding="utf-8")

    # Print a concise, human-readable summary that mirrors the saved report.
    print("=== ListenBrainz Cleaning Validation ===")
    print(f"Source rows: {source_rows:,}")
    print(f"Cleaned rows: {len(cleaned):,}")
    print(f"Rows removed (exact duplicate rows only): {exact_duplicate_rows:,}")
    print(f"Source columns: {len(RAW_COLUMNS):,}; cleaned columns: {len(cleaned.columns):,}")
    print(f"Exact duplicate rows: {exact_duplicate_rows:,}")
    print(
        "Candidate event key unique: "
        f"source={source_key_check['unique']}, cleaned={final_key_check['unique']}"
    )
    print(f"Unique users: source={source['username'].nunique():,}, cleaned={cleaned['username'].nunique():,}")
    print("Missing-value counts (source -> cleaned):")
    for column in RAW_COLUMNS:
        print(f"  {column}: {source_missing[column]:,} -> {final_missing[column]:,}")
    print(
        "Distinct artist_name values: "
        f"source={source['artist_name'].nunique():,}, cleaned={cleaned['artist_name'].nunique():,}"
    )
    print(
        "Timestamp conversion failures: "
        f"source={int(source_timestamp_utc.isna().sum()):,}, "
        f"cleaned={int(cleaned['listened_at_utc'].isna().sum()):,}"
    )
    print(f"Timestamp range UTC: {source_timestamp_range[0]} to {source_timestamp_range[1]}")
    print(
        "Artist MBID arrays: "
        f"{mbid_validation['valid_arrays']:,} valid; "
        f"{mbid_validation['invalid_json']:,} invalid JSON; "
        f"{mbid_validation['not_arrays']:,} non-arrays; "
        f"{mbid_validation['invalid_ids']:,} invalid ID elements"
    )
    print(
        "Artist MBID coverage: "
        f"{artist_mbid_coverage['populated_rows']:,}/{source_rows:,} rows "
        f"({artist_mbid_coverage['coverage_percent']:.2f}%), "
        f"{artist_mbid_coverage['unique_ids']:,} unique IDs"
    )
    print("Repeated recording/release IDs (reported separately from duplicates):")
    for column, values in repeated_ids.items():
        print(
            f"  {column}: {values['repeated_distinct_ids']:,} repeated IDs; "
            f"{values['rows_with_repeated_id']:,} rows affected"
        )
    print("Per-user observation windows:")
    for row in user_summary.itertuples(index=False):
        first = row.first_listen_utc.isoformat() if pd.notna(row.first_listen_utc) else "unavailable"
        last = row.last_listen_utc.isoformat() if pd.notna(row.last_listen_utc) else "unavailable"
        duration = str(row.observed_duration) if pd.notna(row.observed_duration) else "unavailable"
        print(
            f"  {row.username}: {row.row_count:,} rows; {first} to {last}; "
            f"duration {duration}; 500-listen cap reached={row.sampling_cap_reached}"
        )
    print(f"Outputs: {CLEANED_PATH.name}, {USER_SUMMARY_PATH.name}, {REPORT_PATH.name}")


if __name__ == "__main__":
    main()
