# DSO 576 Phase 2 — Member 3: Data Cleaning & Integration

## Source and version decision
The user-supplied `listenbrainz_sample (1).csv` has **1,940 rows and nine fields**, with **five unique users**. This matches the 1,940-row source reported in Shivanee’s Module 6 work. A separate teammate script documents an **expected 2,214 rows**, apparently from a different dataset extract; no records from that different extract have been appended or inferred. Confirm with teammates that this 1,940-row file is the source approved for Phase 2.

## Team cleaning comparison
| Input | Cleaning approach | Integration resolution |
|---|---|---|
| `clean_listenbrainz (1).py` | Trims outer whitespace, parses UTC dates, standardizes Python/JSON MBID list strings, removes exact duplicates after normalization | Keep original fields as supplied and create derived parsed fields to avoid unnecessary changes to event-level source metadata |
| `clean_listenbrainz.py` | Preserves raw fields, removes exact nine-field duplicates, adds UTC timestamps and serialized artist MBID arrays | Chosen baseline for the consolidated event table |
| `listenbrainz_cleaning.ipynb` | Original event-data preservation and audits | Compatible with chosen baseline |
| `listenbrainz_cleaning (1).ipynb` | Artist-oriented countability and bridge analyses | Keep supplementary aggregates outside core event table |
| `listenbrainz_cleaning (2).ipynb` | Flags problems including unknown artist labels | Preserve literal source values; defer proposed recodes to separate derived flags |
| `cleaned_sample (1).csv` | 49-row example with additional derived columns | Not concatenated with full dataset, preventing artificial duplication |

## Consolidated rules
1. Preserve the nine original event columns without overwriting values.
2. Remove only exact duplicates across all nine original columns. Replays remain meaningful listening events.
3. Add a parseable `listened_at_utc` column while retaining source `listened_at` text.
4. Parse Python- or JSON-style `artist_mbids` lists into compact JSON in `artist_mbids_parsed`, keeping multi-artist credit order intact.
5. Leave unresolved artist IDs and optional metadata missing, rather than guessing.
6. Keep one row per event, with user observation summary in a separate CSV.
7. Validate counts, timestamps, duplicate event keys, MBID coverage, and preservation of original columns.

## Verified results for supplied 1,940-row extract
- Input and final event rows: **1,940 → 1,940**.
- Exact duplicate rows removed: **0**.
- Unique users: **5**; distinct artist name strings: **756**.
- Timestamp parsing failures: **0**.
- Artist MBID arrays: **1,181 valid**, **759 missing**; no invalid parsed values detected.
- Repeated candidate event-key rows (`username`, `listened_at`, `recording_msid`): **0**.
- Original nine columns preserved exactly: **yes**.

These counts describe this uploaded source version; the 2,214-row number referenced in other team work does not describe this file.

## Downstream use and limitations
Members 4 and 5 should read `data/listenbrainz_final_cleaned.csv`. Use `listened_at_utc` for time analyses, `username` and `artist_name` for listener/artist summaries, and `artist_mbids_parsed` for ID-aware logic. The five sampled listeners have different observation windows; do not present results as a representative population trend. A first play observed here is not necessarily the user's true first listen. Missing artist MBIDs should not be imputed. No external MusicBrainz enrichment was performed.
