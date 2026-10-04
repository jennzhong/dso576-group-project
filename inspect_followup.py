import pandas as pd
import ast

df = pd.read_csv("listenbrainz_sample.csv", dtype=str,
                 keep_default_na=False, na_values=[""])

print("=== THE 31-ROW GAP ===")
has_rec = df["recording_mbid"].notna()
has_art = df["artist_mbids"].notna()
print(f"recording_mbid but no artist_mbids: {(has_rec & ~has_art).sum()}")
print(f"artist_mbids but no recording_mbid: {(~has_rec & has_art).sum()}")
print("Example rows with one but not the other:")
odd = df[has_rec != has_art][["artist_name", "track_name",
                              "artist_mbids", "recording_mbid"]]
print(odd.head(5).to_string())

print("\n=== ARTIST CREDIT vs TRUE ARTIST ===")
parsed = df["artist_mbids"].dropna().apply(ast.literal_eval)
all_mbids = [m for lst in parsed for m in lst]
print(f"Credit strings (artist_name unique):  {df['artist_name'].nunique()}")
print(f"True artists (distinct MBIDs):        {len(set(all_mbids))}")

print("\nCredit strings containing a comma (likely multi-artist):")
multi = df[df["artist_name"].str.contains(",", na=False)]
print(f"  {len(multi)} listens, {multi['artist_name'].nunique()} distinct strings")
for n in multi["artist_name"].unique()[:8]:
    print(f"  {n!r}")

print("\n=== SAME ARTIST, DIFFERENT CREDIT STRING? ===")
# Build mbid -> set of names it appears under
exploded = df[df["artist_mbids"].notna()].copy()
exploded["mbids"] = exploded["artist_mbids"].apply(ast.literal_eval)
solo = exploded[exploded["mbids"].apply(len) == 1].copy()
solo["mbid"] = solo["mbids"].apply(lambda x: x[0])
names_per_mbid = solo.groupby("mbid")["artist_name"].unique()
conflicts = names_per_mbid[names_per_mbid.apply(len) > 1]
print(f"MBIDs appearing under more than one name: {len(conflicts)}")
for mbid, names in conflicts.head(8).items():
    print(f"  {mbid[:8]}...: {list(names)}")

print("\n=== TRACK IDENTITY ===")
print(f"Unique track_name:     {df['track_name'].nunique()}")
print(f"Unique recording_mbid: {df['recording_mbid'].nunique()}")
print(f"Unique recording_msid: {df['recording_msid'].nunique()}")