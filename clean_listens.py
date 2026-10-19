"""
Module 6 — Apply the cleaning rules in cleaning_rules.md to the raw
ListenBrainz sample and validate the result on the full dataset.

Run from the repository root:
    uv run python clean_listens.py            # writes to outputs/
    uv run python clean_listens.py some/dir   # writes to another folder

Reads (never modifies):  listenbrainz_sample.csv, record_checks_expected.csv
Writes to outputs/:      cleaned_listens.csv, listen_artist_bridge.csv,
                         artist_summary.csv, cleaned_sample.csv,
                         change_log.csv, record_checks.csv,
                         validation_report.md, output_checksums.txt
"""

import ast
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

RAW = Path("listenbrainz_sample.csv")
RAW_SHA256 = "463000bf005a3c667cfeb708b44aa12f0d35342e34f467ede3caf924426b816d"
EXPECTED_CHECKS = Path("record_checks_expected.csv")
OUT = Path("outputs")

RAW_COLUMNS = [
    "username", "listened_at", "track_name", "artist_name", "release_name",
    "recording_msid", "artist_mbids", "recording_mbid", "release_mbid",
]
TEXT_COLUMNS = ["track_name", "artist_name", "release_name"]
ID_COLUMNS = ["recording_msid", "recording_mbid", "release_mbid"]
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

DOUBLE_SCROBBLE_SECONDS = 60                                  # R9
EARLIEST_PLAUSIBLE = pd.Timestamp("2005-01-01", tz="UTC")     # R11
RETRIEVED_BY = pd.Timestamp("2026-09-21 23:59:59", tz="UTC")  # R11
PLACEHOLDER_NAMES = {"unknown", "[unknown]", "unknown artist", "n/a", "none", "null", "-"}
TOPIC_SUFFIX = " - topic"
ARTIST_ALIASES = {                                            # R6 exception
    "takanashi yasuharu / -yaiba-": "yasuharu takanashi / -yaiba-",
}

change_log = []


def log_change(rule, action, rows_affected, note=""):
    change_log.append(
        {"rule": rule, "action": action, "rows_affected": int(rows_affected), "note": note}
    )


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- load (R1)

def load_raw():
    actual = sha256(RAW)
    if actual != RAW_SHA256:
        sys.exit(f"Raw file hash changed: {actual}. Restore the original file.")
    raw = pd.read_csv(RAW, dtype=str, keep_default_na=False, na_values=[""])
    assert list(raw.columns) == RAW_COLUMNS, raw.columns
    return raw


# ---------------------------------------------------------------- clean

def nfc_strip(value):
    if pd.isna(value):
        return pd.NA
    return unicodedata.normalize("NFC", value).strip()


def make_artist_key(name):
    if pd.isna(name):
        return pd.NA
    key = name.casefold()
    if key.endswith(TOPIC_SUFFIX):
        key = key[: -len(TOPIC_SUFFIX)].strip()
    if key in PLACEHOLDER_NAMES:
        return pd.NA
    return ARTIST_ALIASES.get(key, key)


def parse_mbid_list(value):
    """Return a list of MBIDs, None if missing, or the string 'PARSE_ERROR'."""
    if pd.isna(value):
        return None
    try:
        parsed = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return "PARSE_ERROR"
    return parsed if isinstance(parsed, list) else "PARSE_ERROR"


def clean(raw):
    df = raw.copy()

    # R8 — exact duplicate rows
    exact_dupes = df.duplicated(keep="first")
    log_change("R8", "removed exact duplicate rows", exact_dupes.sum())
    df = df[~exact_dupes].copy()

    # R2 — timestamps
    df["listened_at_utc"] = pd.to_datetime(
        df["listened_at"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
    ).dt.tz_localize("UTC")
    failed = df["listened_at_utc"].isna() & df["listened_at"].notna()
    log_change("R2", "listened_at text -> UTC datetime", df["listened_at_utc"].notna().sum(),
               f"{failed.sum()} failed conversions")
    df["listen_id"] = (
        df["username"] + "|"
        + (df["listened_at_utc"].astype("int64") // 10**9).astype(str)
    )

    # R3 — artist_mbids list string -> JSON list + count
    parsed = df["artist_mbids"].apply(parse_mbid_list)
    parse_errors = parsed.apply(lambda v: v == "PARSE_ERROR")
    parsed = parsed.where(~parse_errors, None)
    df["artist_mbids_json"] = parsed.apply(
        lambda v: json.dumps(v) if isinstance(v, list) else pd.NA
    )
    df["n_credited_artists"] = parsed.apply(
        lambda v: len(v) if isinstance(v, list) else 0
    ).astype("int64")
    log_change("R3", "artist_mbids string -> JSON list", df["artist_mbids_json"].notna().sum(),
               f"{parse_errors.sum()} parse failures")

    # R4 — ID format (IDs stay as text)
    bad_ids = pd.Series(False, index=df.index)
    for col in ID_COLUMNS:
        bad_ids |= df[col].notna() & ~df[col].fillna("").str.match(UUID)
    bad_ids |= parsed.apply(
        lambda v: isinstance(v, list) and not all(UUID.match(m) for m in v)
    )
    df["flag_bad_id"] = bad_ids
    log_change("R4", "flagged rows with a malformed ID", bad_ids.sum())

    # R5 — display text: trim + NFC only
    for col in TEXT_COLUMNS:
        df[f"{col}_clean"] = df[col].apply(nfc_strip).astype("string")
        changed = df[col].notna() & (df[col] != df[f"{col}_clean"])
        log_change("R5", f"{col}: trim + NFC changed text", changed.sum())

    # R6 — artist grouping key
    df["artist_key"] = df["artist_name_clean"].apply(make_artist_key).astype("string")
    folded = df["artist_name_clean"].str.casefold()
    spellings = df.groupby("artist_key")["artist_name_clean"].transform("nunique")
    log_change("R6", "rows whose artist_key merges 2+ raw spellings",
               (spellings > 1).sum(),
               f"{df.loc[spellings > 1, 'artist_key'].nunique()} keys")
    log_change("R6", "' - Topic' suffix removed from artist_key",
               folded.str.endswith(TOPIC_SUFFIX).sum())
    log_change("R6", "alias table mapped artist_key",
               folded.isin(ARTIST_ALIASES.keys()).sum(), "; ".join(ARTIST_ALIASES))
    df["flag_placeholder_artist"] = folded.isin(PLACEHOLDER_NAMES)
    log_change("R6", "placeholder artist name -> missing artist_key",
               df["flag_placeholder_artist"].sum())

    # R7 — artist identity
    df["has_artist_mbid"] = df["artist_mbids_json"].notna()
    first_mbid = parsed.apply(lambda v: v[0] if isinstance(v, list) and v else pd.NA)
    df["artist_id"] = first_mbid.where(
        df["has_artist_mbid"], "name:" + df["artist_key"].astype(object)
    ).astype("string")
    log_change("R7", "artist_id from MBID", df["has_artist_mbid"].sum())
    log_change("R7", "artist_id from name key (no MBID)",
               (~df["has_artist_mbid"] & df["artist_key"].notna()).sum())

    # R9 — suspected double-scrobbles
    df = df.sort_values(["username", "listened_at_utc"]).copy()
    df["seconds_since_prev_same_recording"] = (
        df.groupby(["username", "recording_msid"])["listened_at_utc"]
        .diff().dt.total_seconds()
    )
    df["suspected_double_scrobble"] = (
        df["seconds_since_prev_same_recording"] < DOUBLE_SCROBBLE_SECONDS
    )
    df["is_countable"] = ~df["suspected_double_scrobble"]
    by_user = df.groupby("username")
    df["seconds_since_prev_listen"] = by_user["listened_at_utc"].diff().dt.total_seconds()
    df["same_recording_as_prev"] = df["recording_msid"] == by_user["recording_msid"].shift()
    log_change("R9", f"flagged same recording < {DOUBLE_SCROBBLE_SECONDS}s after previous",
               df["suspected_double_scrobble"].sum(), "kept in table, is_countable=False")

    # R11 — suspicious timestamps
    df["flag_suspicious_time"] = (
        (df["listened_at_utc"] < EARLIEST_PLAUSIBLE) | (df["listened_at_utc"] > RETRIEVED_BY)
    )
    log_change("R11", "flagged timestamp outside 2005 .. retrieval",
               df["flag_suspicious_time"].sum())

    # R10 — missing optional fields are kept as-is (logged for the record)
    for col in ["release_name", "artist_mbids", "recording_mbid", "release_mbid"]:
        log_change("R10", f"kept missing {col} (not filled)", df[col].isna().sum())

    # Restore source order (newest first within user, as delivered)
    df = df.loc[raw.index.intersection(df.index)]
    ordered = (
        ["listen_id"] + RAW_COLUMNS
        + ["listened_at_utc", "track_name_clean", "artist_name_clean", "release_name_clean",
           "artist_key", "artist_id", "has_artist_mbid", "artist_mbids_json",
           "n_credited_artists", "seconds_since_prev_listen", "same_recording_as_prev",
           "seconds_since_prev_same_recording",
           "suspected_double_scrobble", "is_countable", "flag_placeholder_artist",
           "flag_bad_id", "flag_suspicious_time"]
    )
    return df[ordered].reset_index(drop=True)


def build_bridge(clean_df):
    """R7: one row per listen x credited artist MBID."""
    b = clean_df.loc[clean_df["has_artist_mbid"], ["listen_id", "artist_mbids_json", "is_countable"]].copy()
    b["artist_mbid"] = b["artist_mbids_json"].apply(json.loads)
    b = b.explode("artist_mbid")
    b["credit_position"] = b.groupby("listen_id").cumcount() + 1
    return b[["listen_id", "artist_mbid", "credit_position", "is_countable"]].reset_index(drop=True)


def artist_summary(clean_df):
    """Per-artist engagement metrics on countable listens with a group key."""
    use = clean_df[clean_df["is_countable"] & clean_df["artist_key"].notna()].copy()
    use["day"] = use["listened_at_utc"].dt.date
    pairs = use.groupby(["artist_key", "username"]).agg(days=("day", "nunique"))
    pairs["returned"] = pairs["days"] > 1
    by_artist = pairs.groupby("artist_key").agg(
        unique_listeners=("days", "size"), returning_listeners=("returned", "sum")
    )
    listens = use.groupby("artist_key").agg(
        countable_listens=("listen_id", "size"),
        distinct_days=("day", "nunique"),
        display_name=("artist_name_clean", lambda s: s.mode().iloc[0]),
        artist_mbid=("artist_id", lambda s: next((v for v in s if not v.startswith("name:")), pd.NA)),
    )
    out = listens.join(by_artist)
    out["return_rate"] = (out["returning_listeners"] / out["unique_listeners"]).round(3)
    return out.reset_index().sort_values(
        ["countable_listens", "artist_key"], ascending=[False, True]
    )


# ---------------------------------------------------------------- sample (<= 50 rows)

def choose_sample(clean_df):
    """Difficult cases first, then a stratified fill so every user appears."""
    picks = []

    def add(mask, n, reason):
        rows = clean_df[mask & ~clean_df["listen_id"].isin([p[0] for p in picks])]
        for lid in rows["listen_id"].head(n):
            picks.append((lid, reason))

    expected = pd.read_csv(EXPECTED_CHECKS, dtype=str)
    keys = set(zip(expected["username"], expected["listened_at"]))
    add(clean_df.apply(lambda r: (r["username"], r["listened_at"]) in keys, axis=1), 10,
        "record check")
    add(clean_df["suspected_double_scrobble"], 4, "suspected double-scrobble")
    add(clean_df["n_credited_artists"] >= 3, 3, "3+ credited artists")
    add(clean_df["recording_mbid"].notna() & ~clean_df["has_artist_mbid"], 3,
        "recording MBID but no artist MBID")
    add(clean_df["artist_name"].str.casefold().ne(clean_df["artist_name"])
        & clean_df["artist_name"].str.casefold().isin(clean_df["artist_name"]), 2,
        "name differs from another only by case")
    add(clean_df["flag_placeholder_artist"], 2, "placeholder artist name")
    add(clean_df["track_name"] != clean_df["track_name_clean"], 2, "NFC changed text")
    add(clean_df["artist_name"].str.contains("𝔇|…", regex=True)
        | clean_df["track_name"].str.contains("…|Ɐ", regex=True), 3,
        "stylised Unicode kept (no NFKC)")
    add(clean_df["release_name"].isna() & clean_df["release_mbid"].notna(), 2,
        "release MBID but no release name")
    add(clean_df["track_name"].str.contains("10 horas", regex=False), 1,
        "unusual: 10-hour white-noise track")
    add((clean_df["seconds_since_prev_listen"] < 30) & ~clean_df["same_recording_as_prev"], 2,
        "different track < 30 s after previous (skip, kept)")
    add(clean_df["seconds_since_prev_same_recording"].between(60, 120), 2,
        "replay 60-120 s after previous (kept)")
    add(clean_df["track_name"] == "Untitled", 1, "track literally titled 'Untitled' (kept)")
    add(clean_df["recording_msid"].isin(
        clean_df.groupby("recording_msid")["artist_name"].nunique().loc[lambda s: s > 1].index), 1,
        "same recording_msid under 2 artist spellings")
    for user in sorted(clean_df["username"].unique()):
        add((clean_df["username"] == user) & clean_df["has_artist_mbid"], 2,
            f"ordinary row for {user}")
        add((clean_df["username"] == user) & ~clean_df["has_artist_mbid"], 1,
            f"ordinary row for {user}, no MBID")
    picks = picks[:50]
    reasons = dict(picks)
    sample = clean_df[clean_df["listen_id"].isin(reasons)].copy()
    sample.insert(0, "sample_reason", sample["listen_id"].map(reasons))
    return sample


# ---------------------------------------------------------------- validation

def run_record_checks(clean_df, bridge):
    expected = pd.read_csv(EXPECTED_CHECKS, dtype=str, keep_default_na=False)
    results = []
    for _, e in expected.iterrows():
        row = clean_df[(clean_df["username"] == e["username"])
                       & (clean_df["listened_at"] == e["listened_at"])]
        assert len(row) == 1, f"check {e['check_id']} matched {len(row)} rows"
        row = row.iloc[0]
        if e["field"] == "bridge_rows":
            actual = int((bridge["listen_id"] == row["listen_id"]).sum())
        else:
            actual = row[e["field"]]
        actual_text = "<NA>" if pd.isna(actual) else str(actual)
        results.append({
            **e.to_dict(),
            "actual_value": actual_text,
            "match": actual_text == e["expected_value"],
        })
    return pd.DataFrame(results)


def missing_table(raw, clean_df):
    cols = RAW_COLUMNS + ["listened_at_utc", "artist_key", "artist_id", "artist_mbids_json"]
    return pd.DataFrame({
        "raw_missing": [raw[c].isna().sum() if c in raw else pd.NA for c in cols],
        "clean_missing": [clean_df[c].isna().sum() for c in cols],
    }, index=cols)


def user_table(raw, clean_df):
    g = clean_df.groupby("username")
    t = pd.DataFrame({
        "raw_rows": raw.groupby("username").size(),
        "clean_rows": g.size(),
        "double_scrobbles": g["suspected_double_scrobble"].sum(),
        "countable_listens": g["is_countable"].sum(),
        "with_artist_mbid": g["has_artist_mbid"].sum(),
        "first_listen_utc": g["listened_at_utc"].min().dt.strftime("%Y-%m-%d"),
        "last_listen_utc": g["listened_at_utc"].max().dt.strftime("%Y-%m-%d"),
    })
    t["mbid_coverage"] = (t["with_artist_mbid"] / t["clean_rows"]).map("{:.0%}".format)
    t["hit_500_cap"] = t["raw_rows"] >= 500
    return t


def md(df, index=True):
    return df.to_markdown(index=index)


def write_report(raw, clean_df, bridge, summary, checks, sample):
    countable = clean_df[clean_df["is_countable"]]
    keyed = countable[countable["artist_key"].notna()]
    rep = []
    w = rep.append

    w("# Validation Report — generated by clean_listens.py\n")
    w(f"Raw file: `{RAW}` · SHA-256 `{RAW_SHA256}` (verified unchanged)\n")

    w("## Row counts and reconciliation\n")
    recon = pd.DataFrame([
        ("Raw rows", len(raw)),
        ("Exact duplicate rows removed (R8)", len(raw) - len(clean_df)),
        ("Cleaned event rows (cleaned_listens.csv)", len(clean_df)),
        ("Suspected double-scrobbles flagged, kept (R9)", int(clean_df["suspected_double_scrobble"].sum())),
        ("Countable listens (is_countable)", len(countable)),
        ("Countable listens with missing artist_key (excluded from artist metrics)",
         int(countable["artist_key"].isna().sum())),
        ("Countable listens used in artist metrics", len(keyed)),
        ("Bridge rows (listen x credited MBID)", len(bridge)),
    ], columns=["step", "rows"])
    w(md(recon, index=False) + "\n")
    w(f"Check: {len(raw)} - {len(raw) - len(clean_df)} - "
      f"{int(clean_df['suspected_double_scrobble'].sum())} = {len(countable)} countable listens.\n")

    w("## Per-user totals\n")
    w(md(user_table(raw, clean_df)) + "\n")

    w("## Distinct-entity totals before and after\n")
    ent = pd.DataFrame([
        ("Distinct raw artist_name strings", raw["artist_name"].nunique()),
        ("Distinct artist_key (after case / Topic / alias / placeholder rules)",
         clean_df["artist_key"].nunique()),
        ("Distinct artist_id (MBID or name key)", clean_df["artist_id"].nunique()),
        ("Distinct credited artist MBIDs (bridge)", bridge["artist_mbid"].nunique()),
        ("Distinct recording_msid", clean_df["recording_msid"].nunique()),
        ("Distinct users", clean_df["username"].nunique()),
    ], columns=["measure", "value"])
    w(md(ent, index=False) + "\n")

    w("## Types and conversions\n")
    types = pd.DataFrame({
        "raw dtype (as loaded)": raw.dtypes.astype(str),
    })
    w(md(types) + "\n")
    w("Derived column dtypes:\n")
    derived = clean_df.drop(columns=RAW_COLUMNS).dtypes.astype(str).rename("dtype").to_frame()
    w(md(derived) + "\n")

    w("## Missing values (raw vs cleaned)\n")
    w(md(missing_table(raw, clean_df)) + "\n")

    w("## Duplicates\n")
    dup = pd.DataFrame([
        ("Exact duplicate rows (all 9 columns)", int(raw.duplicated().sum())),
        ("Repeated username + listened_at", int(raw.duplicated(["username", "listened_at"]).sum())),
        ("Repeated listen_id in cleaned table", int(clean_df["listen_id"].duplicated().sum())),
        ("Repeated username + recording_msid (replays, kept)",
         int(raw.duplicated(["username", "recording_msid"]).sum())),
        ("... of which < 60 s after previous same-recording submission (flagged)",
         int(clean_df["suspected_double_scrobble"].sum())),
    ], columns=["check", "count"])
    w(md(dup, index=False) + "\n")
    gaps = clean_df["seconds_since_prev_same_recording"].dropna()
    bins = pd.cut(gaps, [0, 10, 20, 30, 40, 60, 90, 120, 300, float("inf")], right=False)
    w("Gap since the same user's previous submission of the same recording "
      "(threshold sensitivity):\n")
    w(md(bins.value_counts().sort_index().rename("repeats").to_frame()) + "\n")
    sens = pd.DataFrame(
        [(t, int((gaps < t).sum())) for t in (10, 30, 45, 60, 90)],
        columns=["threshold_seconds", "rows_flagged"],
    )
    w(md(sens, index=False) + "\n")
    w("Flagged rows by user and track:\n")
    w(md(clean_df[clean_df["suspected_double_scrobble"]]
         .groupby(["username", "track_name"]).size().rename("flagged").to_frame()) + "\n")

    w("## Text standardisation\n")
    ex = []
    for col in TEXT_COLUMNS:
        ch = clean_df[clean_df[col].notna() & (clean_df[col] != clean_df[f"{col}_clean"])]
        for _, r in ch.drop_duplicates(col).iterrows():
            ex.append((col, ascii(r[col]), ascii(r[f"{col}_clean"])))
    w(md(pd.DataFrame(ex, columns=["column", "before (escaped)", "after NFC (escaped)"]),
         index=False) + "\n")
    keyex = (clean_df[clean_df["artist_name_clean"] != clean_df["artist_key"]]
             .drop_duplicates("artist_name")[["artist_name", "artist_key"]]
             .sort_values("artist_key", na_position="last"))
    keyex = keyex[keyex["artist_name"].str.casefold() != keyex["artist_key"].fillna("")]
    w(f"artist_name -> artist_key changes beyond lowercasing ({len(keyex)} distinct names):\n")
    w(md(keyex, index=False) + "\n")
    case_groups = (clean_df.groupby("artist_key")["artist_name"].unique()
                   .loc[lambda s: s.apply(len) > 1])
    w(f"artist_key values that merged 2+ raw spellings: {len(case_groups)}\n")
    w(md(case_groups.apply(lambda v: " | ".join(sorted(v))).rename("raw spellings").to_frame())
      + "\n")
    nfkc_kept = clean_df[clean_df["track_name_clean"]
                         != clean_df["track_name_clean"].apply(lambda v: unicodedata.normalize("NFKC", v))]
    w(f"Track names NFKC *would* have altered (kept as submitted): "
      f"{', '.join(sorted(nfkc_kept['track_name_clean'].unique()))}\n")

    w("## Suspicious values\n")
    ts = clean_df["listened_at_utc"]
    sus = pd.DataFrame([
        ("Timestamp conversion failures", int(ts.isna().sum())),
        ("Earliest listen (UTC)", str(ts.min())),
        ("Latest listen (UTC)", str(ts.max())),
        ("Before 2005 or after retrieval (flagged)", int(clean_df["flag_suspicious_time"].sum())),
        ("Malformed IDs (flagged)", int(clean_df["flag_bad_id"].sum())),
        ("Placeholder artist names (flagged)", int(clean_df["flag_placeholder_artist"].sum())),
        ("Next listen < 30 s after the previous one, different recording (skips, kept)",
         int(((clean_df["seconds_since_prev_listen"] < 30) & ~clean_df["same_recording_as_prev"]).sum())),
        ("Placeholder-like track names ('Untitled', kept: real titles)",
         int((clean_df["track_name"] == "Untitled").sum())),
        ("recording_msid with >1 artist_name", int((clean_df.groupby("recording_msid")["artist_name"].nunique() > 1).sum())),
        ("recording_mbid with >1 recording_msid", int((clean_df.dropna(subset=["recording_mbid"])
                                                        .groupby("recording_mbid")["recording_msid"].nunique() > 1).sum())),
        ("Listens with recording_mbid but no artist_mbids",
         int((clean_df["recording_mbid"].notna() & ~clean_df["has_artist_mbid"]).sum())),
    ], columns=["check", "result"])
    w(md(sus, index=False) + "\n")

    w("## Merge / reshape check (listen -> artist bridge)\n")
    expected_bridge = int(clean_df["n_credited_artists"].sum())
    back = bridge.merge(clean_df[["listen_id"]], on="listen_id", how="left",
                        validate="many_to_one", indicator=True)
    mrg = pd.DataFrame([
        ("Listens with artist MBIDs (input)", int(clean_df["has_artist_mbid"].sum())),
        ("Expected bridge rows = sum(n_credited_artists)", expected_bridge),
        ("Actual bridge rows", len(bridge)),
        ("Bridge rows with no matching listen_id (unmatched)", int((back["_merge"] != "both").sum())),
        ("Rows after bridge->listens many_to_one merge", len(back)),
        ("Unexpected extra rows", len(back) - len(bridge)),
        ("Listens without MBID (not in bridge, by design)", int((~clean_df["has_artist_mbid"]).sum())),
    ], columns=["check", "count"])
    w(md(mrg, index=False) + "\n")

    w("## Metric record counts\n")
    pairs = keyed.groupby(["artist_key", "username"]).size()
    mets = pd.DataFrame([
        ("Total countable listens", len(countable), "all countable rows"),
        ("Artist-level listens", len(keyed), "countable rows with artist_key"),
        ("Artists in artist_summary.csv", len(summary), "distinct artist_key"),
        ("Listener-artist pairs (return-rate denominator)", len(pairs), "artist_key x username"),
        ("Pairs that returned on 2+ UTC days (numerator)",
         int(summary["returning_listeners"].sum()), ""),
        ("Overall return rate", f"{summary['returning_listeners'].sum() / len(pairs):.3f}", ""),
        ("Artists with 2+ unique listeners", int((summary["unique_listeners"] > 1).sum()), ""),
        ("MBID-based listens (bridge, countable)", int(bridge["is_countable"].sum()),
         "credited-artist rows; one listen may count for several artists"),
    ], columns=["metric", "value", "records used"])
    w(md(mets, index=False) + "\n")
    w("Top 10 artists by countable listens:\n")
    w(md(summary.head(10)[["display_name", "countable_listens", "unique_listeners",
                           "returning_listeners", "return_rate", "distinct_days"]], index=False) + "\n")

    w("## Effect of cleaning on an important total\n")
    before = raw.groupby("artist_name").size().sort_values(ascending=False).head(5)
    after = summary.set_index("display_name")["countable_listens"].head(5)
    w("Top 5 by raw listens per raw artist_name:\n")
    w(md(before.rename("raw_listens").to_frame()) + "\n")
    w("Top 5 by countable listens per artist_key:\n")
    w(md(after.to_frame()) + "\n")

    w("## Record checks\n")
    w(md(checks[["check_id", "username", "listened_at", "field", "original_value",
                 "expected_value", "actual_value", "match"]], index=False) + "\n")
    w(f"All checks match: **{bool(checks['match'].all())}** "
      f"({int(checks['match'].sum())}/{len(checks)})\n")

    w("## Change log\n")
    w(md(pd.DataFrame(change_log), index=False) + "\n")

    w("## Submitted sample\n")
    w(md(sample["sample_reason"].value_counts().rename("rows").to_frame()) + "\n")

    (OUT / "validation_report.md").write_text("\n".join(rep), encoding="utf-8")


def main():
    global OUT
    if len(sys.argv) > 1:
        OUT = Path(sys.argv[1])
    OUT.mkdir(parents=True, exist_ok=True)
    raw = load_raw()
    clean_df = clean(raw)
    bridge = build_bridge(clean_df)
    summary = artist_summary(clean_df)
    sample = choose_sample(clean_df)
    checks = run_record_checks(clean_df, bridge)

    clean_df.to_csv(OUT / "cleaned_listens.csv", index=False)
    bridge.to_csv(OUT / "listen_artist_bridge.csv", index=False)
    summary.to_csv(OUT / "artist_summary.csv", index=False)
    sample.to_csv(OUT / "cleaned_sample.csv", index=False)
    pd.DataFrame(change_log).to_csv(OUT / "change_log.csv", index=False)
    checks.to_csv(OUT / "record_checks.csv", index=False)
    write_report(raw, clean_df, bridge, summary, checks, sample)

    assert sha256(RAW) == RAW_SHA256, "raw file was modified during the run"
    files = sorted(p for p in OUT.iterdir() if p.name != "output_checksums.txt")
    (OUT / "output_checksums.txt").write_text(
        "".join(f"{sha256(p)}  {p.name}\n" for p in files)
    )

    print(f"raw rows {len(raw)} -> cleaned rows {len(clean_df)} "
          f"-> countable {int(clean_df['is_countable'].sum())}")
    print(f"record checks matched: {int(checks['match'].sum())}/{len(checks)}")
    print(f"outputs written to {OUT}/")
    if not checks["match"].all():
        print(checks[~checks["match"]].to_string())
        sys.exit(1)


if __name__ == "__main__":
    main()
