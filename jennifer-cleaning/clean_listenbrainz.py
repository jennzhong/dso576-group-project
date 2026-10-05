"""Clean the ListenBrainz event sample and write a reproducible 50-row sample."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

import pandas as pd

COLUMNS = [
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
ID_COLUMNS = ["recording_msid", "recording_mbid", "release_mbid"]
OPTIONAL_COLUMNS = ["release_name", "artist_mbids", "recording_mbid", "release_mbid"]
UUID_PATTERN = re.compile(r"^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")
CANDIDATE_KEYS = [
    ["username", "listened_at", "recording_msid"],
    ["username", "listened_at", "recording_mbid"],
    ["username", "listened_at", "artist_name", "track_name"],
]


def load_source(path: str | Path) -> pd.DataFrame:
    """Load CSV columns as strings and preserve empty fields for inspection."""
    frame = pd.read_csv(path, dtype="string", keep_default_na=False)
    missing = sorted(set(COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Source is missing required columns: {missing}")
    return frame.loc[:, COLUMNS].copy()


def parse_artist_mbids(value: Any) -> list[str]:
    """Read the source's list-like MBID field without changing its stored value."""
    if pd.isna(value) or not str(value).strip():
        return []
    text = str(value).strip()
    try:
        parsed = ast.literal_eval(text) if text.startswith(("[", "(", "'", '"')) else text
    except (ValueError, SyntaxError):
        return [text]
    if isinstance(parsed, (list, tuple)):
        return [str(item).strip() for item in parsed if str(item).strip()]
    if isinstance(parsed, str) and parsed.strip():
        return [parsed.strip()]
    return [text]


def valid_uuid(value: Any) -> bool | pd._libs.missing.NAType:
    """Return missing for a blank ID and otherwise test the UUID-style shape."""
    if pd.isna(value) or not str(value).strip():
        return pd.NA
    return bool(UUID_PATTERN.fullmatch(str(value).strip()))


def key_complete(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    values = frame[columns].astype("string")
    return values.notna().all(axis=1) & values.apply(lambda col: col.str.strip().ne("")).all(axis=1)


def clean_data(raw: pd.DataFrame, as_of_utc: pd.Timestamp | None = None) -> pd.DataFrame:
    """Return one cleaned row per source listen, with review and identity fields."""
    cleaned = raw.copy()
    for column in COLUMNS:
        cleaned[column] = cleaned[column].astype("string").str.strip()

    unknown = cleaned["artist_name"].str.casefold().eq("unknown").fillna(False)
    cleaned.loc[unknown, "artist_name"] = pd.NA

    date_text = cleaned["listened_at"].astype("string")
    parsed = pd.to_datetime(date_text, errors="coerce", utc=True)
    invalid = date_text.notna() & date_text.ne("") & parsed.isna()
    as_of = as_of_utc if as_of_utc is not None else pd.Timestamp.now(tz="UTC")
    future = parsed.notna() & parsed.gt(as_of)
    cleaned["listened_at"] = parsed
    cleaned["invalid_date_review"] = invalid
    cleaned["future_date_review"] = future

    cleaned["exact_duplicate_review"] = raw.duplicated(keep=False)
    candidate_review = pd.Series(False, index=raw.index)
    for key in CANDIDATE_KEYS:
        complete = key_complete(raw, key)
        candidate_review |= raw[key].duplicated(keep=False) & complete
    cleaned["candidate_key_review"] = candidate_review

    for column in ID_COLUMNS:
        cleaned[column + "_invalid_review"] = cleaned[column].map(valid_uuid).astype("boolean").eq(False).fillna(False)

    artist_ids = cleaned["artist_mbids"].map(parse_artist_mbids)
    artist_id_invalid = artist_ids.map(
        lambda ids: any(not bool(UUID_PATTERN.fullmatch(value)) for value in ids)
    )
    cleaned["artist_mbids_invalid_review"] = artist_id_invalid

    identity_keys = []
    identity_types = []
    for name, ids in zip(cleaned["artist_name"], artist_ids):
        if len(ids) == 1 and UUID_PATTERN.fullmatch(ids[0]):
            identity_keys.append("mbid:" + ids[0].casefold())
            identity_types.append("verified_mbid")
        elif len(ids) > 1:
            identity_keys.append(pd.NA)
            identity_types.append("multiple_mbid")
        elif ids:
            identity_keys.append(pd.NA)
            identity_types.append("invalid_mbid")
        elif pd.notna(name) and str(name).strip():
            identity_keys.append("name_fallback:" + str(name).strip().casefold())
            identity_types.append("name_fallback")
        else:
            identity_keys.append(pd.NA)
            identity_types.append("unresolved")
    cleaned["artist_identity_key"] = pd.Series(identity_keys, index=cleaned.index, dtype="string")
    cleaned["artist_identity_type"] = pd.Series(identity_types, index=cleaned.index, dtype="string")

    cleaned.insert(0, "source_row_number", range(2, len(cleaned) + 2))
    return cleaned


def select_cleaned_sample(
    raw: pd.DataFrame, cleaned: pd.DataFrame, max_rows: int = 50
) -> pd.DataFrame:
    """Choose a deterministic sample that includes available difficult cases."""
    if not 1 <= max_rows <= 50:
        raise ValueError("max_rows must be between 1 and 50")

    selected: dict[int, set[str]] = {}

    def add(indices, reason: str, limit: int | None = None) -> None:
        count = 0
        for index in indices:
            if index not in selected:
                selected[index] = set()
            selected[index].add(reason)
            count += 1
            if limit is not None and count >= limit:
                break

    unknown = raw["artist_name"].astype("string").str.strip().str.casefold().eq("unknown")
    add(raw.index[unknown], "Unknown artist name recoded to missing")

    multi = raw["artist_mbids"].map(lambda value: len(parse_artist_mbids(value)) > 1)
    add(raw.index[multi], "Multiple artist MBIDs retained", limit=10)

    missing_metadata = raw[OPTIONAL_COLUMNS].astype("string").apply(
        lambda col: col.isna() | col.str.strip().eq("")
    ).any(axis=1)
    add(raw.index[missing_metadata], "Missing optional metadata preserved", limit=10)

    repeated = raw["recording_msid"].astype("string").duplicated(keep=False)
    add(raw.index[repeated], "Repeated recording listen retained", limit=4)

    punctuation = raw[["track_name", "artist_name", "release_name"]].astype("string").apply(
        lambda col: col.str.contains(r"[,/&'()!.-]", regex=True, na=False)
    ).any(axis=1)
    add(raw.index[punctuation], "Name punctuation preserved", limit=5)

    if len(selected) < max_rows:
        remaining = [index for index in raw.index if index not in selected]
        take = min(max_rows - len(selected), len(remaining))
        if take:
            supplemental = raw.loc[remaining].sample(n=take, random_state=576).index
            add(supplemental, "Reproducible supplemental sample")

    chosen = sorted(selected)[:max_rows]
    sample = cleaned.loc[chosen].copy()
    sample.insert(
        1,
        "sample_reason",
        ["; ".join(sorted(selected[index])) for index in chosen],
    )
    return sample


def validate_outputs(raw: pd.DataFrame, cleaned: pd.DataFrame, sample: pd.DataFrame) -> pd.DataFrame:
    """Compare row counts, key retention, and sample size."""
    required_reasons = [
        "Unknown artist name recoded to missing",
        "Multiple artist MBIDs retained",
        "Missing optional metadata preserved",
        "Repeated recording listen retained",
        "Name punctuation preserved",
    ]
    category_presence = {
        reason: sample["sample_reason"].str.contains(re.escape(reason), regex=True).any()
        for reason in required_reasons
    }
    all_difficult_categories_present = all(category_presence.values())
    checks = [
        ("source rows retained", len(raw), len(cleaned), len(raw) == len(cleaned)),
        (
            "recording order retained",
            True,
            cleaned["recording_msid"].astype("string").reset_index(drop=True).equals(
                raw["recording_msid"].astype("string").reset_index(drop=True)
            ),
            cleaned["recording_msid"].astype("string").reset_index(drop=True).equals(
                raw["recording_msid"].astype("string").reset_index(drop=True)
            ),
        ),
        ("sample at most 50 rows", 50, len(sample), len(sample) <= 50),
        ("all difficult-case categories included", len(required_reasons), sum(category_presence.values()), all_difficult_categories_present),
    ]
    return pd.DataFrame(checks, columns=["check", "expected", "actual", "passed"])


def write_outputs(
    cleaned: pd.DataFrame,
    sample: pd.DataFrame,
    full_path: str | Path,
    sample_path: str | Path,
) -> None:
    Path(full_path).parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(full_path, index=False, na_rep="")
    sample.to_csv(sample_path, index=False, na_rep="")


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    raw_path = project_dir / "data" / "raw" / "listenbrainz_sample.csv"
    full_path = project_dir / "data" / "processed" / "listenbrainz_cleaned.csv"
    sample_path = project_dir / "cleaned_sample.csv"

    raw = load_source(raw_path)
    cleaned = clean_data(raw)
    sample = select_cleaned_sample(raw, cleaned)
    write_outputs(cleaned, sample, full_path, sample_path)

    checks = validate_outputs(raw, cleaned, sample)
    print(checks.to_string(index=False))
    if not checks["passed"].all():
        raise SystemExit("Validation failed.")
    print(f"\nSource rows: {len(raw)}; cleaned rows: {len(cleaned)}; sample rows: {len(sample)}")
    print(f"Full local output: {full_path}")
    print(f"GitHub sample: {sample_path}")


if __name__ == "__main__":
    main()
