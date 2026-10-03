# ListenBrainz Cleaning Validation Report

## Run summary

The source `listenbrainz_sample.csv` was read without modification. Raw source columns were loaded as text, and the cleaned event table retains all raw columns and values. The only permitted row removal is an exact duplicate across all nine raw source fields.

Source rows: 2,214
Cleaned rows: 2,214
Rows removed: 0

The cleaned table has **11 columns**: the 9 preserved raw columns plus `listened_at_utc` and `artist_mbids_parsed`. The latter is JSON-serialized parsed-array text for portability in CSV; the original `artist_mbids` text is retained unchanged. The main table remains one row per listen. No artist rows were exploded, no MusicBrainz metadata was merged, and no emerging-artist or final continued-engagement labels were created.

## Shape and event checks

| Check | Source | Cleaned | Result |
|---|---:|---:|---|
| Rows | 2,214 (expected 2,214) | 2,214 | PASS |
| Columns | 9 | 11 | PASS: raw source columns preserved; two derived columns added |
| Exact duplicate rows across raw columns | 0 | 0 | Removed only from cleaned output |
| Candidate event key duplicate rows (`username`, `listened_at`, `recording_msid`) | 0 | 0 | Unique |

Repeated recording, release, or artist identifiers are entity repeats and are not counted as duplicate listen events. No row was removed merely because an identifier repeats.

## Missing values

Blank CSV cells are preserved as blank in the raw columns. No optional metadata was filled or inferred.

| Column | Source missing | Source % | Cleaned missing | Cleaned % |
|---|---:|---:|---:|---:|
| `username` | 0 | 0.00% | 0 | 0.00% |
| `listened_at` | 0 | 0.00% | 0 | 0.00% |
| `track_name` | 0 | 0.00% | 0 | 0.00% |
| `artist_name` | 0 | 0.00% | 0 | 0.00% |
| `release_name` | 1,027 | 46.39% | 1,027 | 46.39% |
| `recording_msid` | 0 | 0.00% | 0 | 0.00% |
| `artist_mbids` | 974 | 43.99% | 974 | 43.99% |
| `recording_mbid` | 943 | 42.59% | 943 | 42.59% |
| `release_mbid` | 974 | 43.99% | 974 | 43.99% |
| `listened_at_utc` | 0 | 0.00% | 0 | 0.00% |
| `artist_mbids_parsed` | 0 | 0.00% | 974 | 43.99% |

## Timestamps

`listened_at` remains unchanged in the raw column. `listened_at_utc` is a derived, UTC-aware datetime. Timestamp conversion failures: **0 source rows** and **0 cleaned rows**. Failed conversions remain as missing derived datetimes; their source events are retained.

| Range | Earliest UTC | Latest UTC |
|---|---|---|
| Source | 2019-03-07T13:17:39+00:00 | 2026-10-02T22:25:37+00:00 |
| Cleaned | 2019-03-07T13:17:39+00:00 | 2026-10-02T22:25:37+00:00 |

## Users and artists

- Unique users: **5 source**, **5 cleaned**.
- Distinct submitted `artist_name` values: **795 source**, **795 cleaned**.
- Populated artist MBID arrays: **1,240 rows**; blank: **974 rows**; coverage: **56.01%**.
- Distinct individual artist MBIDs: **611** across **1,538 occurrences**.
- Parsed-array validity: **1,240 valid arrays**, **0 invalid JSON values**, **0 non-array values**, **0 invalid UUID-shaped elements**.

| User | Cleaned listen rows |
|---|---:|
| `H-music` | 500 |
| `John V` | 500 |
| `iliekcomputers` | 500 |
| `music_af` | 214 |
| `s_john_s` | 500 |

## Repeated identifiers (not duplicate-event removal)

| Identifier column | Distinct populated IDs | IDs appearing more than once | Rows with a repeated ID | Occurrences beyond first |
|---|---:|---:|---:|---:|
| `recording_msid` | 1,525 | 345 | 1,034 | 689 |
| `recording_mbid` | 930 | 188 | 529 | 341 |
| `release_mbid` | 631 | 195 | 804 | 609 |

## Per-user observation windows

See `user_observation_summary.csv` for row counts, first and last valid UTC listen, observed duration, source row count, and whether the 500-listen sampling cap was reached. The cap status uses source counts before any exact-duplicate removal.

## Project limitations

The dataset has five users with different, non-overlapping windows; four histories reached the 500-listen cap. Missing artist metadata is preserved and MBID coverage is reported rather than imputed. These data support cleaning validation and descriptive repeat-listening exploration, but not reliable population-level or synchronized cross-user artist-growth claims. Repeated listens and listens on distinct days may be reported descriptively; this cleaning step does not assign a final continued-engagement label.
