import pandas as pd

df = pd.read_csv("listenbrainz_sample.csv", parse_dates=["listened_at"])

print("=== BASIC SHAPE ===")
print(f"Rows (listens): {len(df)}")
print(f"Columns: {list(df.columns)}")
print(f"Unique listeners: {df['username'].nunique()}")
print(f"Unique artists (by name): {df['artist_name'].nunique()}")

print("\n=== MISSING VALUES ===")
print(df.isna().sum())

print("\n=== LISTENS PER USER ===")
print(df["username"].value_counts())

# Add a month column so we can check time coverage
df["month"] = df["listened_at"].dt.to_period("M")

print("\n=== HOW MANY MONTHS DOES EACH USER COVER? ===")
print(df.groupby("username")["month"].nunique().sort_values(ascending=False))

print("\n=== CAN WE MEASURE ARTIST GROWTH? ===")
# For growth we need: same artist, multiple months, multiple listeners
artist_stats = df.groupby("artist_name").agg(
    listeners=("username", "nunique"),
    months=("month", "nunique"),
    listens=("artist_name", "size"),
)

multi_listener = artist_stats[artist_stats["listeners"] > 1]
multi_month = artist_stats[artist_stats["months"] > 1]
both = artist_stats[(artist_stats["listeners"] > 1) & (artist_stats["months"] > 1)]

print(f"Artists total: {len(artist_stats)}")
print(f"Artists heard by >1 listener: {len(multi_listener)}")
print(f"Artists heard in >1 month: {len(multi_month)}")
print(f"Artists with BOTH (growth is measurable): {len(both)}")

print("\nTop artists by listener count:")
print(artist_stats.sort_values("listeners", ascending=False).head(10))

print("\n=== MUSICBRAINZ MATCH RATE BY USER ===")
match_by_user = df.groupby("username")["artist_mbids"].apply(
    lambda s: f"{s.notna().sum()}/{len(s)} ({s.notna().mean():.0%})"
)
print(match_by_user)