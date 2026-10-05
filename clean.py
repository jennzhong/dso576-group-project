import ast, hashlib
import pandas as pd
from pathlib import Path

RAW = Path("listenbrainz_sample.csv")
OUT = Path("data/clean"); OUT.mkdir(parents=True, exist_ok=True)
log = {}

log["raw_sha256"] = hashlib.sha256(RAW.read_bytes()).hexdigest()
raw = pd.read_csv(RAW, dtype=str, keep_default_na=False, na_values=[""])
log["rows_start"] = len(raw)
df = raw.copy()

# Rule 2: timestamps
df["listened_at"] = pd.to_datetime(df["listened_at"], errors="coerce", utc=True)
log["bad_timestamps"] = int(df["listened_at"].isna().sum())

# Rule 4: parse artist_mbids, keep first
def parse(v):
    if pd.isna(v): return []
    try: return list(ast.literal_eval(v))
    except Exception: return [v]
ids = df["artist_mbids"].map(parse)
df["artist_mbid"] = ids.map(lambda x: x[0] if x else pd.NA)
df["n_artists"] = ids.map(len)
log["multi_artist_rows"] = int((df["n_artists"] > 1).sum())

# Rule 5: text cleaning, raw columns kept
for c in ["artist_name", "track_name", "release_name"]:
    df[c + "_clean"] = df[c].str.strip().str.replace(r"\s+", " ", regex=True)
    log[f"{c}_changed"] = int((df[c].fillna("") != df[c + "_clean"].fillna("")).sum())

# Rule 7: duplicates, counted separately, exact ones removed
log["exact_dupes"] = int(df.duplicated().sum())
log["repeated_user_track_time"] = int(df.duplicated(["username", "recording_msid", "listened_at"]).sum())
df = df.drop_duplicates()

# Rule 8: missing data flagged, not filled
df["has_artist_mbid"] = df["artist_mbid"].notna()
log["missing_before"] = raw.isna().sum().to_dict()
log["missing_after"] = df[["artist_mbid", "release_name_clean"]].isna().sum().to_dict()

# Rule 10: flags
df["flag_future"] = df["listened_at"] > pd.Timestamp.now(tz="UTC")
df["flag_pre2005"] = df["listened_at"] < pd.Timestamp("2005-01-01", tz="UTC")
df["flag_same_second"] = df.duplicated(["username", "listened_at"], keep=False)
for f in ["flag_future", "flag_pre2005", "flag_same_second"]:
    log[f] = int(df[f].sum())

# Rule 11: reconcile
log["rows_final"] = len(df)
assert log["rows_start"] - log["exact_dupes"] == log["rows_final"]

# Artist key and metric counts (item 11)
df["artist_key"] = df["artist_mbid"].fillna("name:" + df["artist_name_clean"].str.casefold())
log["records_all"] = len(df)
log["records_with_mbid"] = int(df["has_artist_mbid"].sum())

df.to_csv(OUT / "listens_clean.csv", index=False)
(df[df.flag_same_second | ~df.has_artist_mbid | (df.n_artists > 1)].head(25)
   .pipe(lambda d: pd.concat([d, df.sample(25, random_state=576)]).drop_duplicates())
   .head(50).to_csv("cleaned_sample.csv", index=False))
pd.Series(log, dtype=object).to_json(OUT / "cleaning_log.json", indent=2)
for k, v in log.items(): print(k, v)
