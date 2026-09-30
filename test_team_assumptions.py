import pandas as pd
import ast

df = pd.read_csv("listenbrainz_sample.csv", parse_dates=["listened_at"])

# artist_mbids was saved as a string like "['abc-123']" — convert back to a real list
def parse_mbids(value):
    if pd.isna(value):
        return None
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return None

df["artist_mbids"] = df["artist_mbids"].apply(parse_mbids)

print("=== TEST 1: SHIVANEE'S JOIN — WHAT SURVIVES? ===")
print(f"Starting listens: {len(df)}")

# This is Shivanee's step: expand the list so one row = one credited artist
lb_artists = df.dropna(subset=["artist_mbids"]).explode("artist_mbids")
lb_artists = lb_artists.rename(columns={"artist_mbids": "artist_mbid"})

print(f"Listens with an MBID: {df['artist_mbids'].notna().sum()}")
print(f"Rows after explode: {len(lb_artists)} "
      f"(more than listens, because some tracks credit multiple artists)")
print(f"Unique artist MBIDs available to join: {lb_artists['artist_mbid'].nunique()}")
print(f"Share of original listens that survive: {df['artist_mbids'].notna().mean():.0%}")

print("\nSurvival rate by user (who gets represented in the join):")
print(df.groupby("username")["artist_mbids"].apply(lambda s: f"{s.notna().mean():.0%}"))

print("\n=== TEST 2: DOES 'FULL HISTORY' HOLD? ===")
print("Benazira's metrics assume each user's full listening history.")
print("What we actually have per user:\n")
for user, group in df.groupby("username"):
    span = (group["listened_at"].max() - group["listened_at"].min()).days
    print(f"  {user}: {len(group)} listens, {span} days "
          f"({group['listened_at'].min().date()} to {group['listened_at'].max().date()})")
print("\nThese are recent-activity snapshots, not complete histories.")

print("\n=== TEST 3: BENAZIRA'S GROWTH METRIC ===")
df["month"] = df["listened_at"].dt.to_period("M")

# Her metric: distinct users per artist per month, compared month over month
monthly = (df.groupby(["artist_mbids_key", "month"])["username"].nunique()
           if False else
           df.groupby([df["artist_name"], "month"])["username"].nunique())
monthly = monthly.reset_index(name="unique_listeners")

artist_summary = monthly.groupby("artist_name").agg(
    months_present=("month", "nunique"),
    max_listeners_in_a_month=("unique_listeners", "max"),
)

qualifying = artist_summary[
    (artist_summary["months_present"] > 1) &
    (artist_summary["max_listeners_in_a_month"] > 1)
]

print(f"Artists in sample: {len(artist_summary)}")
print(f"Artists present in >1 month: {(artist_summary['months_present'] > 1).sum()}")
print(f"Artists with >1 listener in some month: "
      f"{(artist_summary['max_listeners_in_a_month'] > 1).sum()}")
print(f"Artists where growth is actually measurable: {len(qualifying)}")

if len(qualifying) > 0:
    print("\nThose artists:")
    print(qualifying)
else:
    print("\nNo artist in this sample supports a month-over-month growth calculation.")

print("\n=== TEST 4: REPEAT ENGAGEMENT (this one should work better) ===")
# Benazira's engagement measures don't need cross-user overlap
engagement = df.groupby(["username", "artist_name"]).agg(
    listens=("track_name", "size"),
    distinct_tracks=("track_name", "nunique"),
    distinct_days=("listened_at", lambda s: s.dt.date.nunique()),
)
returned = engagement[engagement["distinct_days"] > 1]
print(f"Listener-artist pairs: {len(engagement)}")
print(f"Pairs where the listener returned on another day: {len(returned)} "
      f"({len(returned)/len(engagement):.0%})")
print(f"Pairs where the listener explored >1 track: "
      f"{(engagement['distinct_tracks'] > 1).sum()}")
print("\nTop engagement examples:")
print(engagement.sort_values("listens", ascending=False).head(10))