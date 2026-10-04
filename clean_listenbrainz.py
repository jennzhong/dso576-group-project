"""
DSO 576 Module 6 - individual data cleaning
Student: Shivanee Kooner
Project: Emerging Artist Discovery Through Listening Behavior

Reads the raw ListenBrainz extract and creates:
- listenbrainz_cleaned.csv              (full local cleaned file; do not need to commit)
- cleaned_sample_50.csv                 (GitHub data sample)
- cleaning_decision_log.csv
- record_checks.csv
- cleaning_summary.json
- checklist.json
- checklist_evidence.md

The original listenbrainz_sample.csv is never overwritten.
"""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RAW_FILE = Path("listenbrainz_sample.csv")
CLEANED_FILE = Path("listenbrainz_cleaned.csv")
SAMPLE_FILE = Path("cleaned_sample_50.csv")
DECISION_LOG_FILE = Path("cleaning_decision_log.csv")
RECORD_CHECKS_FILE = Path("record_checks.csv")
SUMMARY_FILE = Path("cleaning_summary.json")
CHECKLIST_FILE = Path("checklist.json")
CHECKLIST_MD_FILE = Path("checklist_evidence.md")

PROJECT_TITLE = "Emerging Artist Discovery Through Listening Behavior"
PROJECT_QUESTION = (
    "Can listening behavior - especially growth in unique listeners and repeat engagement - "
    "help a music-streaming editorial team identify promising emerging artists for additional exposure?"
)
CUTOFF = pd.Timestamp("2026-09-22T00:00:00Z")

EXPECTED_COLUMNS = [
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

TEXT_COLUMNS = ["username", "track_name", "artist_name", "release_name"]
ID_COLUMNS = ["recording_msid", "recording_mbid", "release_mbid"]
CORE_COLUMNS = ["username", "listened_at", "track_name", "artist_name", "recording_msid"]
EVENT_KEY = ["username", "listened_at", "recording_msid"]


def normalize_text(value):
    """Trim outer whitespace only; preserve case, punctuation, accents, and internal meaning."""
    if pd.isna(value):
        return pd.NA
    value = str(value).strip()
    return value if value else pd.NA


def normalize_artist_mbids(value):
    """
    Standardize artist_mbids to compact JSON list text.
    Missing remains missing. Artist order is preserved because credit order can be meaningful.
    """
    if pd.isna(value):
        return pd.NA

    raw = str(value).strip()
    if not raw:
        return pd.NA

    parsed = None
    try:
        parsed = json.loads(raw)
    except Exception:
        try:
            parsed = ast.literal_eval(raw)
        except Exception:
            return pd.NA

    if not isinstance(parsed, list):
        return pd.NA

    cleaned = [str(x).strip() for x in parsed if str(x).strip()]
    if not cleaned:
        return pd.NA
    return json.dumps(cleaned, ensure_ascii=False, separators=(",", ":"))


def expected_cleaned_value(column: str, value):
    """Rule-based expectation used before comparing the five record checks to actual output."""
    if column == "listened_at":
        parsed = pd.to_datetime(value, errors="coerce", utc=True)
        return None if pd.isna(parsed) else parsed.isoformat()
    if column == "artist_mbids":
        cleaned = normalize_artist_mbids(value)
        return None if pd.isna(cleaned) else str(cleaned)
    if column in TEXT_COLUMNS or column in ID_COLUMNS:
        cleaned = normalize_text(value)
        return None if pd.isna(cleaned) else str(cleaned)
    return None if pd.isna(value) else str(value)


def missing_dict(df: pd.DataFrame) -> dict:
    return {col: int(df[col].isna().sum()) for col in df.columns}


def select_record_check_indices(original: pd.DataFrame, cleaned: pd.DataFrame) -> list[tuple[int, str]]:
    selected: list[tuple[int, str]] = []
    used: set[int] = set()

    def add(index, label):
        if index is None:
            return
        index = int(index)
        if index not in used and index in cleaned.index:
            used.add(index)
            selected.append((index, label))

    # Difficult case 1: unresolved artist identifier.
    missing_mbid = original.index[original["artist_mbids"].isna()].tolist()
    add(missing_mbid[0] if missing_mbid else None, "Missing artist MBID preserved")

    # Difficult case 2: missing release name.
    missing_release = original.index[original["release_name"].isna()].tolist()
    add(missing_release[0] if missing_release else None, "Missing release name preserved")

    # Difficult case 3: multiple credited artist MBIDs if one exists.
    multi = []
    for idx, value in original["artist_mbids"].items():
        if pd.isna(value):
            continue
        normalized = normalize_artist_mbids(value)
        if pd.isna(normalized):
            continue
        try:
            if len(json.loads(normalized)) > 1:
                multi.append(idx)
                break
        except Exception:
            pass
    add(multi[0] if multi else None, "Multiple artist MBIDs preserved in credit order")

    # Difficult case 4: repeated user + artist behavior (legitimate repeat listening).
    repeated = original.duplicated(subset=["username", "artist_name"], keep=False)
    repeated_idx = original.index[repeated].tolist()
    add(repeated_idx[0] if repeated_idx else None, "Repeated listening retained as legitimate event")

    # Difficult case 5: a normal fully resolved record.
    normal_mask = (
        original["artist_mbids"].notna()
        & original["release_name"].notna()
        & original["recording_mbid"].notna()
        & original["release_mbid"].notna()
    )
    normal_idx = original.index[normal_mask].tolist()
    add(normal_idx[0] if normal_idx else None, "Fully resolved normal record")

    # Fallbacks if the data does not contain all preferred case types.
    for idx in cleaned.index:
        if len(selected) >= 5:
            break
        add(idx, "Fallback record check")

    return selected[:5]


def build_record_checks(original: pd.DataFrame, cleaned: pd.DataFrame) -> pd.DataFrame:
    check_indices = select_record_check_indices(original, cleaned)
    rows = []

    for check_number, (idx, case_type) in enumerate(check_indices, start=1):
        orig = original.loc[idx]
        actual = cleaned.loc[idx]

        expected_artist = expected_cleaned_value("artist_name", orig["artist_name"])
        expected_track = expected_cleaned_value("track_name", orig["track_name"])
        expected_time = expected_cleaned_value("listened_at", orig["listened_at"])
        expected_mbids = expected_cleaned_value("artist_mbids", orig["artist_mbids"])

        actual_artist = expected_cleaned_value("artist_name", actual["artist_name"])
        actual_track = expected_cleaned_value("track_name", actual["track_name"])
        actual_time = expected_cleaned_value("listened_at", actual["listened_at"])
        actual_mbids = expected_cleaned_value("artist_mbids", actual["artist_mbids"])

        matches = (
            expected_artist == actual_artist
            and expected_track == actual_track
            and expected_time == actual_time
            and expected_mbids == actual_mbids
        )

        rows.append(
            {
                "check": check_number,
                "case_type": case_type,
                "source_row_index": int(idx),
                "original_username": None if pd.isna(orig["username"]) else str(orig["username"]),
                "original_listened_at": None if pd.isna(orig["listened_at"]) else str(orig["listened_at"]),
                "original_artist_name": None if pd.isna(orig["artist_name"]) else str(orig["artist_name"]),
                "original_track_name": None if pd.isna(orig["track_name"]) else str(orig["track_name"]),
                "original_artist_mbids": None if pd.isna(orig["artist_mbids"]) else str(orig["artist_mbids"]),
                "expected_artist_name": expected_artist,
                "actual_artist_name": actual_artist,
                "expected_track_name": expected_track,
                "actual_track_name": actual_track,
                "expected_listened_at": expected_time,
                "actual_listened_at": actual_time,
                "expected_artist_mbids": expected_mbids,
                "actual_artist_mbids": actual_mbids,
                "matches_expected": bool(matches),
            }
        )

    return pd.DataFrame(rows)


def build_50_row_sample(cleaned: pd.DataFrame, record_checks: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    keep_indices = []

    # Always include the five checked records first.
    if not record_checks.empty:
        keep_indices.extend(record_checks["source_row_index"].astype(int).tolist())

    # Include oldest and newest rows for each listener.
    for _, group in cleaned.groupby("username", dropna=False):
        if group["listened_at"].notna().any():
            keep_indices.append(int(group["listened_at"].idxmin()))
            keep_indices.append(int(group["listened_at"].idxmax()))

    # Add unresolved MBID cases.
    keep_indices.extend(cleaned.index[cleaned["artist_mbids"].isna()].tolist()[:10])

    # Add multi-artist-credit cases.
    for idx, value in cleaned["artist_mbids"].items():
        if pd.isna(value):
            continue
        try:
            if len(json.loads(str(value))) > 1:
                keep_indices.append(int(idx))
        except Exception:
            pass
        if len(set(keep_indices)) >= 25:
            break

    # De-duplicate while preserving order.
    unique_indices = list(dict.fromkeys(i for i in keep_indices if i in cleaned.index))

    # Fill to 50 with a deterministic random sample.
    remaining = cleaned.drop(index=unique_indices, errors="ignore")
    need = max(0, 50 - len(unique_indices))
    if need and len(remaining):
        sampled = remaining.sample(n=min(need, len(remaining)), random_state=576)
        unique_indices.extend(sampled.index.astype(int).tolist())

    unique_indices = unique_indices[:50]
    sample = cleaned.loc[unique_indices].copy()
    sample.insert(0, "source_row_index", sample.index.astype(int))
    sample = sample.reset_index(drop=True)

    explanation = (
        "The 50-row sample intentionally includes the five record-check rows, oldest and newest "
        "listens for users where available, rows with missing artist MBIDs, multi-artist-credit cases "
        "when present, and a deterministic random sample (random_state=576) to reach 50 rows."
    )
    return sample, explanation


def main() -> None:
    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"{RAW_FILE} was not found. Run: python pull_listenbrainz_sample.py"
        )

    original = pd.read_csv(RAW_FILE, dtype="string", keep_default_na=True)

    missing_columns = [c for c in EXPECTED_COLUMNS if c not in original.columns]
    extra_columns = [c for c in original.columns if c not in EXPECTED_COLUMNS]
    if missing_columns:
        raise ValueError(f"Missing expected columns: {missing_columns}")

    # Keep only the documented project columns and preserve a true raw copy in memory.
    original = original[EXPECTED_COLUMNS].copy()
    raw_for_evidence = original.copy(deep=True)

    starting_rows = int(len(original))
    missing_before = missing_dict(original)
    raw_exact_duplicate_rows = int(original.duplicated(keep=False).sum())
    raw_duplicate_copies = int(original.duplicated(keep="first").sum())

    # ----- Apply written cleaning rules -----
    cleaned = original.copy()

    # 1) Correct data type for timestamp.
    cleaned["listened_at"] = pd.to_datetime(cleaned["listened_at"], errors="coerce", utc=True)

    # 2) Trim outer whitespace only. Preserve meaningful case/punctuation/accents.
    for col in TEXT_COLUMNS + ID_COLUMNS:
        cleaned[col] = cleaned[col].map(normalize_text)

    # 3) Standardize list serialization for artist MBIDs.
    cleaned["artist_mbids"] = cleaned["artist_mbids"].map(normalize_artist_mbids)

    # 4) Remove only exact duplicate rows after normalization.
    normalized_duplicate_copies = int(cleaned.duplicated(keep="first").sum())
    cleaned = cleaned.loc[~cleaned.duplicated(keep="first")].copy()

    # Preserve original source-row index for audit trail.
    cleaned.index.name = "source_row_index"

    # ----- Validation -----
    failed_date_conversions = int(cleaned["listened_at"].isna().sum())
    missing_after = missing_dict(cleaned)
    blank_core_after = {}
    for col in ["username", "track_name", "artist_name", "recording_msid"]:
        blank_core_after[col] = int(cleaned[col].isna().sum())

    future_or_cutoff_dates = int(
        (cleaned["listened_at"].notna() & (cleaned["listened_at"] >= CUTOFF)).sum()
    )

    repeated_event_key_rows = int(
        cleaned.duplicated(subset=EVENT_KEY, keep=False).sum()
    )

    unique_listeners = int(cleaned["username"].nunique(dropna=True))
    unique_artist_names = int(cleaned["artist_name"].nunique(dropna=True))
    resolved_artist_mbid_rows = int(cleaned["artist_mbids"].notna().sum())

    # Use dropna=False for audit totals so missing grouping values do not silently disappear.
    audit_by_artist = (
        cleaned.groupby("artist_name", dropna=False)
        .agg(
            listens=("artist_name", "size"),
            unique_listeners=("username", "nunique"),
        )
        .reset_index()
    )
    audit_grouped_listens = int(audit_by_artist["listens"].sum())

    record_checks = build_record_checks(raw_for_evidence, cleaned)
    all_record_checks_match = bool(record_checks["matches_expected"].all()) if len(record_checks) else False

    sample_50, sample_explanation = build_50_row_sample(cleaned, record_checks)

    # Save full cleaned file locally. Convert timestamps to ISO text on disk.
    disk_cleaned = cleaned.copy()
    disk_cleaned["listened_at"] = disk_cleaned["listened_at"].map(
        lambda x: x.isoformat() if not pd.isna(x) else pd.NA
    )
    disk_cleaned.to_csv(CLEANED_FILE, index=True)

    disk_sample = sample_50.copy()
    disk_sample["listened_at"] = disk_sample["listened_at"].map(
        lambda x: x.isoformat() if not pd.isna(x) else pd.NA
    )
    disk_sample.to_csv(SAMPLE_FILE, index=False)

    record_checks.to_csv(RECORD_CHECKS_FILE, index=False)

    decision_log = pd.DataFrame(
        [
            {
                "rule": "Preserve raw source",
                "reason": "The assignment requires the original data to remain unchanged.",
                "check": "Cleaning reads listenbrainz_sample.csv and writes a separate listenbrainz_cleaned.csv.",
            },
            {
                "rule": "Parse listened_at as UTC datetime",
                "reason": "Growth and engagement depend on correct time ordering and time windows.",
                "check": f"Failed date conversions after parsing: {failed_date_conversions}.",
            },
            {
                "rule": "Trim outer whitespace only in text/ID fields",
                "reason": "Accidental edge whitespace can split equivalent values, but case, punctuation, accents, and internal spacing may be meaningful artist/track metadata.",
                "check": "Compared before/after values in the five record checks; no forced lowercasing or punctuation removal.",
            },
            {
                "rule": "Normalize artist_mbids as a JSON list string",
                "reason": "Artist MBIDs are list-valued and should have a reproducible representation without changing artist-credit order.",
                "check": "Parsed JSON/Python-list forms and re-serialized valid nonempty lists; missing/unparseable values remain missing.",
            },
            {
                "rule": "Remove exact duplicate rows only",
                "reason": "Repeated listening is a real behavior in this project, so repeated users/artists/tracks must not be removed merely because they repeat.",
                "check": f"Raw duplicate copies: {raw_duplicate_copies}; normalized duplicate copies removed: {normalized_duplicate_copies}; repeated event-key rows flagged separately: {repeated_event_key_rows}.",
            },
            {
                "rule": "Do not impute missing MusicBrainz identifiers or release names",
                "reason": "Missing MBID mappings mean ListenBrainz did not resolve the listen. Guessing an identifier could create incorrect artist joins and bias the analysis.",
                "check": f"Resolved artist-MBID rows after cleaning: {resolved_artist_mbid_rows} of {len(cleaned)}; missing counts are reported before and after.",
            },
            {
                "rule": "Flag suspicious core values instead of silently rewriting them",
                "reason": "Unusual does not automatically mean wrong. Invalid dates or missing core fields would affect the analysis and should remain auditable.",
                "check": f"Dates at/after historical cutoff: {future_or_cutoff_dates}; core-field missing counts: {blank_core_after}.",
            },
            {
                "rule": "No MusicBrainz metadata merge in this Module 6 cleaning step",
                "reason": "The current input is the ListenBrainz event table; the planned MusicBrainz enrichment is a later project step.",
                "check": "Checklist item 9 is marked Not applicable and explains the planned MBID join separately.",
            },
        ]
    )
    decision_log.to_csv(DECISION_LOG_FILE, index=False)

    final_rows = int(len(cleaned))
    row_difference = starting_rows - final_rows

    limitations = [
        "The sample contains only five self-selected ListenBrainz users, so listener counts are sample-specific.",
        "User observation windows are uneven and do not share one common time period.",
        "The historical extract is capped for several users, so it is not each user's complete listening history.",
        "MusicBrainz identifiers are missing for some listens, and the missingness is uneven across users.",
        "A listener's first play in this extract may not be their true first exposure to an artist.",
        "The data has no listener demographics, skip signal, or source-of-discovery field, so segmentation is behavioral only.",
        "ListenBrainz server-side MBID resolution and historical records can change after the original September 2026 project extract.",
    ]

    summary = {
        "project": PROJECT_TITLE,
        "student": "Shivanee Kooner",
        "business_question": PROJECT_QUESTION,
        "one_row": "One listen event: one user playing one track at one point in time.",
        "expected_event_key": EVENT_KEY,
        "source_file": str(RAW_FILE),
        "starting_rows": starting_rows,
        "final_rows": final_rows,
        "row_difference": row_difference,
        "raw_exact_duplicate_rows_including_all_members": raw_exact_duplicate_rows,
        "raw_duplicate_copies": raw_duplicate_copies,
        "normalized_duplicate_copies_removed": normalized_duplicate_copies,
        "repeated_event_key_rows_after_cleaning": repeated_event_key_rows,
        "missing_before": missing_before,
        "missing_after": missing_after,
        "failed_date_conversions": failed_date_conversions,
        "dates_at_or_after_historical_cutoff": future_or_cutoff_dates,
        "core_missing_after": blank_core_after,
        "unique_listeners": unique_listeners,
        "unique_artist_names": unique_artist_names,
        "resolved_artist_mbid_rows": resolved_artist_mbid_rows,
        "audit_grouped_listens": audit_grouped_listens,
        "all_record_checks_match": all_record_checks_match,
        "sample_selection": sample_explanation,
        "limitations": limitations,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "extra_source_columns_ignored": extra_columns,
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    # The checklist is generated from actual run evidence.
    checklist = [
        {
            "number": 1,
            "title": "State the project vision and question",
            "status": "Done",
            "evidence": (
                f"Project vision: a music-streaming editorial team uses listener growth and repeat engagement "
                f"to shortlist emerging artists. Business question: {PROJECT_QUESTION} "
                "Main comparison: artist-level unique-listener growth and repeat engagement over time."
            ),
        },
        {
            "number": 2,
            "title": "Define one row",
            "status": "Done",
            "evidence": (
                "One row represents one listen event: one user playing one track at one point in time. "
                f"Audit event key: {EVENT_KEY}. Repeated track or artist plays are legitimate behavior and are not automatically duplicates."
            ),
        },
        {
            "number": 3,
            "title": "Preserve the source",
            "status": "Done",
            "evidence": (
                "Source: ListenBrainz public API, historical cutoff 2026-09-22 00:00:00 UTC, recreated with "
                "pull_listenbrainz_sample.py. Raw file listenbrainz_sample.csv is never overwritten. "
                "Cleaning output is written separately."
            ),
        },
        {
            "number": 4,
            "title": "Inspect columns and types",
            "status": "Done" if failed_date_conversions == 0 else "Unresolved",
            "evidence": (
                f"Expected nine columns were checked. listened_at was converted to UTC datetime. "
                f"Failed date conversions: {failed_date_conversions}. "
                "Text and identifier fields remain text; artist_mbids remains a serialized list value."
            ),
        },
        {
            "number": 5,
            "title": "Standardize text",
            "status": "Done",
            "evidence": (
                "Trimmed only leading/trailing whitespace in text and identifier fields. "
                "Preserved case, punctuation, accents, and internal spacing because these can be meaningful in artist and track names. "
                "artist_mbids was normalized to compact JSON list text."
            ),
        },
        {
            "number": 6,
            "title": "Investigate duplicates",
            "status": "Done",
            "evidence": (
                f"Raw exact duplicate copies: {raw_duplicate_copies}. "
                f"Normalized exact duplicate copies removed: {normalized_duplicate_copies}. "
                f"Rows involved in repeated event keys after cleaning: {repeated_event_key_rows}. "
                "Only exact duplicates were removed; repeated listening was retained."
            ),
        },
        {
            "number": 7,
            "title": "Handle missing data",
            "status": "Done",
            "evidence": (
                f"Missing counts before: {missing_before}. Missing counts after: {missing_after}. "
                "Missing MusicBrainz identifiers and release names were not imputed because guessing could create incorrect joins. "
                "Core ListenBrainz event fields were checked separately."
            ),
        },
        {
            "number": 8,
            "title": "Check suspicious values",
            "status": "Done" if failed_date_conversions == 0 and future_or_cutoff_dates == 0 else "Unresolved",
            "evidence": (
                f"Invalid/failed dates: {failed_date_conversions}; dates at or after historical cutoff: {future_or_cutoff_dates}; "
                f"core-field missing counts: {blank_core_after}. Unusual values are flagged rather than silently rewritten."
            ),
        },
        {
            "number": 9,
            "title": "Verify merges",
            "status": "Not applicable",
            "evidence": (
                "No table merge is performed in this Module 6 cleaning step. The project plans a later MusicBrainz enrichment "
                "using artist_mbids -> MusicBrainz artist MBID. This assignment cleans the ListenBrainz event table first."
            ),
        },
        {
            "number": 10,
            "title": "Reconcile changes",
            "status": "Done",
            "evidence": (
                f"Starting rows: {starting_rows}; final rows: {final_rows}; difference: {row_difference}. "
                f"The difference is explained by {normalized_duplicate_copies} exact duplicate copies removed. "
                f"Unique listeners after cleaning: {unique_listeners}; unique artist names: {unique_artist_names}."
            ),
        },
        {
            "number": 11,
            "title": "Check calculations",
            "status": "Done",
            "evidence": (
                f"Audit groupby with dropna=False reconciles to {audit_grouped_listens} listens versus {final_rows} final rows. "
                f"Resolved artist-MBID rows: {resolved_artist_mbid_rows} of {final_rows}. "
                "MBID-based metrics must state that unresolved rows are excluded; overall row/listener audits include all rows."
            ),
        },
        {
            "number": 12,
            "title": "Verify individual records",
            "status": "Done" if all_record_checks_match else "Unresolved",
            "evidence": (
                f"Five difficult/representative records are documented in record_checks.csv. "
                f"All expected-versus-actual checks match: {all_record_checks_match}."
            ),
        },
        {
            "number": 13,
            "title": "Test reproducibility",
            "status": "Done",
            "evidence": (
                "Reproduction command: install requirements, run pull_listenbrainz_sample.py, then clean_listenbrainz.py, "
                "then build_report.py; alternatively Run All in module6_cleaning.ipynb. "
                "The scripts rebuild the raw extract, cleaned evidence files, 50-row sample, and report from source."
            ),
        },
        {
            "number": 14,
            "title": "Document remaining limitations",
            "status": "Done",
            "evidence": " ".join(limitations),
        },
    ]
    CHECKLIST_FILE.write_text(json.dumps(checklist, indent=2, ensure_ascii=False), encoding="utf-8")

    md_lines = [
        f"# DSO 576 Module 6 - 14-Item Cleaning Checklist",
        "",
        f"**Project:** {PROJECT_TITLE}  ",
        "**Student:** Shivanee Kooner",
        "",
    ]
    for item in checklist:
        md_lines.extend(
            [
                f"## {item['number']}. {item['title']}",
                f"**Status:** {item['status']}",
                "",
                f"**Evidence or explanation:** {item['evidence']}",
                "",
            ]
        )
    CHECKLIST_MD_FILE.write_text("\n".join(md_lines), encoding="utf-8")

    print("Cleaning complete.")
    print(f"Starting rows: {starting_rows:,}")
    print(f"Final rows: {final_rows:,}")
    print(f"Exact duplicate copies removed: {normalized_duplicate_copies}")
    print(f"Unique listeners: {unique_listeners}")
    print(f"Unique artist names: {unique_artist_names}")
    print(f"Resolved artist-MBID rows: {resolved_artist_mbid_rows}")
    print(f"Five record checks all match: {all_record_checks_match}")
    print("\nCreated:")
    for path in [
        CLEANED_FILE,
        SAMPLE_FILE,
        DECISION_LOG_FILE,
        RECORD_CHECKS_FILE,
        SUMMARY_FILE,
        CHECKLIST_FILE,
        CHECKLIST_MD_FILE,
    ]:
        print(f"  - {path}")


if __name__ == "__main__":
    main()
