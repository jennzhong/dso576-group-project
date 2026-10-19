"""
Module 6 — Step 1: Inspect the raw data before writing any cleaning rules.
This script only LOOKS. It does not change anything.
"""

import pandas as pd
import ast

RAW = "listenbrainz_sample.csv"

# Load with everything as text first, so pandas doesn't silently convert
# anything before we've seen it in its original state.
df = pd.read_csv(RAW, dtype=str, keep_default_na=False, na_values=[""])

print("=" * 60)
print("SHAPE AND TYPES")
print("=" * 60)
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")
print("\nDtypes as loaded (all str because we forced it):")
print(df.dtypes)

print("\n" + "=" * 60)
print("FIRST 3 ROWS, RAW")
print("=" * 60)
for i in range(min(3, len(df))):
    print(f"\n--- Row {i} ---")
    for col in df.columns:
        print(f"  {col}: {df.loc[i, col]!r}")

print("\n" + "=" * 60)
print("MISSING VALUES")
print("=" * 60)
missing = pd.DataFrame({
    "missing": df.isna().sum(),
    "pct": (df.isna().mean() * 100).round(1),
})
print(missing)

print("\n" + "=" * 60)
print("DUPLICATES (counted three ways, per assignment item 6)")
print("=" * 60)
print(f"1. Exact duplicate rows:              {df.duplicated().sum()}")
print(f"2. Repeated username + listened_at:   {df.duplicated(subset=['username','listened_at']).sum()}")
print(f"3. Repeated username + recording_msid: {df.duplicated(subset=['username','recording_msid']).sum()}")
print("   (#3 is expected — it means someone replayed a track)")

print("\n" + "=" * 60)
print("TIMESTAMP SANITY")
print("=" * 60)
ts = pd.to_datetime(df["listened_at"], errors="coerce")
print(f"Failed to parse: {ts.isna().sum()}")
print(f"Earliest: {ts.min()}")
print(f"Latest:   {ts.max()}")
print(f"After retrieval date (2026-09-21): {(ts > '2026-09-21').sum()}")
print(f"Before year 2000:                  {(ts < '2000-01-01').sum()}")

print("\n" + "=" * 60)
print("artist_mbids — THE TRICKY COLUMN")
print("=" * 60)
nonnull = df["artist_mbids"].dropna()
print(f"Non-null values: {len(nonnull)}")
print("Sample raw values (note they're strings, not real lists):")
for v in nonnull.head(3):
    print(f"  {v!r}")

# How many parse cleanly back into lists?
def try_parse(v):
    try:
        result = ast.literal_eval(v)
        return len(result) if isinstance(result, list) else -1
    except (ValueError, SyntaxError):
        return None

parsed = nonnull.apply(try_parse)
print(f"\nParse failures: {parsed.isna().sum()}")
print(f"Not a list after parsing: {(parsed == -1).sum()}")
print("Artists credited per listen:")
print(parsed[parsed > 0].value_counts().sort_index())

print("\n" + "=" * 60)
print("TEXT FIELDS — whitespace and oddities")
print("=" * 60)
for col in ["track_name", "artist_name", "release_name"]:
    s = df[col].dropna()
    print(f"\n{col}:")
    print(f"  leading/trailing whitespace: {(s != s.str.strip()).sum()}")
    print(f"  empty after stripping:       {(s.str.strip() == '').sum()}")
    print(f"  unique values:               {s.nunique()}")

print("\nArtist names containing '- Topic' (automated channels):")
topic = df[df["artist_name"].fillna("").str.contains(" - Topic", regex=False)]
print(f"  {len(topic)} listens, {topic['artist_name'].nunique()} distinct names")
for name in topic["artist_name"].unique()[:5]:
    print(f"  {name!r}")