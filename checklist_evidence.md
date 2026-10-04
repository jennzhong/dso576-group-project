# DSO 576 Module 6 - 14-Item Cleaning Checklist

**Project:** Emerging Artist Discovery Through Listening Behavior  
**Student:** Shivanee Kooner

## 1. State the project vision and question
**Status:** Done

**Evidence or explanation:** Project vision: a music-streaming editorial team uses listener growth and repeat engagement to shortlist emerging artists. Business question: Can listening behavior - especially growth in unique listeners and repeat engagement - help a music-streaming editorial team identify promising emerging artists for additional exposure? Main comparison: artist-level unique-listener growth and repeat engagement over time.

## 2. Define one row
**Status:** Done

**Evidence or explanation:** One row represents one listen event: one user playing one track at one point in time. Audit event key: ['username', 'listened_at', 'recording_msid']. Repeated track or artist plays are legitimate behavior and are not automatically duplicates.

## 3. Preserve the source
**Status:** Done

**Evidence or explanation:** Source: ListenBrainz public API, historical cutoff 2026-09-22 00:00:00 UTC, recreated with pull_listenbrainz_sample.py. Raw file listenbrainz_sample.csv is never overwritten. Cleaning output is written separately.

## 4. Inspect columns and types
**Status:** Done

**Evidence or explanation:** Expected nine columns were checked. listened_at was converted to UTC datetime. Failed date conversions: 0. Text and identifier fields remain text; artist_mbids remains a serialized list value.

## 5. Standardize text
**Status:** Done

**Evidence or explanation:** Trimmed only leading/trailing whitespace in text and identifier fields. Preserved case, punctuation, accents, and internal spacing because these can be meaningful in artist and track names. artist_mbids was normalized to compact JSON list text.

## 6. Investigate duplicates
**Status:** Done

**Evidence or explanation:** Raw exact duplicate copies: 0. Normalized exact duplicate copies removed: 0. Rows involved in repeated event keys after cleaning: 0. Only exact duplicates were removed; repeated listening was retained.

## 7. Handle missing data
**Status:** Done

**Evidence or explanation:** Missing counts before: {'username': 0, 'listened_at': 0, 'track_name': 0, 'artist_name': 0, 'release_name': 754, 'recording_msid': 0, 'artist_mbids': 759, 'recording_mbid': 728, 'release_mbid': 759}. Missing counts after: {'username': 0, 'listened_at': 0, 'track_name': 0, 'artist_name': 0, 'release_name': 754, 'recording_msid': 0, 'artist_mbids': 759, 'recording_mbid': 728, 'release_mbid': 759}. Missing MusicBrainz identifiers and release names were not imputed because guessing could create incorrect joins. Core ListenBrainz event fields were checked separately.

## 8. Check suspicious values
**Status:** Done

**Evidence or explanation:** Invalid/failed dates: 0; dates at or after historical cutoff: 0; core-field missing counts: {'username': 0, 'track_name': 0, 'artist_name': 0, 'recording_msid': 0}. Unusual values are flagged rather than silently rewritten.

## 9. Verify merges
**Status:** Not applicable

**Evidence or explanation:** No table merge is performed in this Module 6 cleaning step. The project plans a later MusicBrainz enrichment using artist_mbids -> MusicBrainz artist MBID. This assignment cleans the ListenBrainz event table first.

## 10. Reconcile changes
**Status:** Done

**Evidence or explanation:** Starting rows: 1940; final rows: 1940; difference: 0. The difference is explained by 0 exact duplicate copies removed. Unique listeners after cleaning: 5; unique artist names: 756.

## 11. Check calculations
**Status:** Done

**Evidence or explanation:** Audit groupby with dropna=False reconciles to 1940 listens versus 1940 final rows. Resolved artist-MBID rows: 1181 of 1940. MBID-based metrics must state that unresolved rows are excluded; overall row/listener audits include all rows.

## 12. Verify individual records
**Status:** Done

**Evidence or explanation:** Five difficult/representative records are documented in record_checks.csv. All expected-versus-actual checks match: True.

## 13. Test reproducibility
**Status:** Done

**Evidence or explanation:** Reproduction command: install requirements, run pull_listenbrainz_sample.py, then clean_listenbrainz.py, then build_report.py; alternatively Run All in module6_cleaning.ipynb. The scripts rebuild the raw extract, cleaned evidence files, 50-row sample, and report from source.

## 14. Document remaining limitations
**Status:** Done

**Evidence or explanation:** The sample contains only five self-selected ListenBrainz users, so listener counts are sample-specific. User observation windows are uneven and do not share one common time period. The historical extract is capped for several users, so it is not each user's complete listening history. MusicBrainz identifiers are missing for some listens, and the missingness is uneven across users. A listener's first play in this extract may not be their true first exposure to an artist. The data has no listener demographics, skip signal, or source-of-discovery field, so segmentation is behavioral only. ListenBrainz server-side MBID resolution and historical records can change after the original September 2026 project extract.
