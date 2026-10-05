# Raw ListenBrainz Sample: Cleaning and Preparation Plan

## Scope and observed baseline

This plan is based on the inspected `listenbrainz_sample.csv` (2,214 rows, 9 columns). No cleaning has been performed. The source CSV remains the authoritative raw extract; proposed parsing and flags should be produced in derived analysis data while retaining the raw values and listen events.

One row represents one user's listen to one track at one timestamp. The sample contains five users: `iliekcomputers` (500 rows), `H-music` (500), `s_john_s` (500), `John V` (500), and `music_af` (214).

Columns are `username`, `listened_at`, `track_name`, `artist_name`, `release_name`, `recording_msid`, `artist_mbids`, `recording_mbid`, and `release_mbid`. A CSV file has no stored type metadata. Values infer as text except `listened_at`, which is integer-form Unix seconds; `artist_mbids` contains JSON text encoding an array when populated.

## Proposed handling by observed issue

### 1. Optional metadata is missing

- **Columns:** `release_name`, `artist_mbids`, `recording_mbid`, `release_mbid`.
- **Observed issue:** `release_name` is blank on 1,027 rows (46.39%); `artist_mbids` and `release_mbid` are each blank on 974 (43.99%); `recording_mbid` is blank on 943 (42.59%). The core event fields `username`, `listened_at`, `track_name`, `artist_name`, and `recording_msid` have no blanks. Artist MBID availability varies from 95/500 for John V (19.0%) to 213/214 for music_af (99.5%).
- **Human decision recorded — APPROVED:** Keep all valid listen events when any of these optional fields are missing. Do not impute or infer missing identifiers. Represent blanks as missing only in derived analysis data and preserve the raw values in the source file.
- **Reason:** An unresolved metadata field does not invalidate the listening event. Filling values would assert information not present in the source; dropping unmatched events would distort the user mix.
- **Validation:** Compare per-column and per-user missing counts before and after parsing. Confirm all 2,214 source events remain and that only the four observed optional fields have missing values.
- **Project impact:** MBID-only artist analyses cover a non-random subset of users. Listener growth and segment summaries must show their matched-row coverage and avoid presenting identifier-matched results as representative of all five users without qualification.
- **Human review:** The retention and no-imputation decision is approved. A later decision is still needed on whether unresolved events appear in a separate name-based view and how to report uneven MBID coverage.

### 2. `artist_mbids` is JSON text and can contain multiple artists

- **Columns:** `artist_mbids` (and its relationship to `artist_name`, `recording_mbid`, and `release_mbid`).
- **Observed issue:** 1,240 rows contain a value and 974 are blank. All 1,240 populated values parse as JSON arrays; no malformed JSON, non-array values, empty arrays, or non-UUID-shaped elements were found. The arrays contain 1,008 single-ID rows, 190 two-ID rows, 26 three-ID rows, 10 four-ID rows, 4 five-ID rows, and 2 six-ID rows. There are 611 distinct individual artist MBIDs across 1,538 ID occurrences.
- **Human decision recorded — APPROVED WITH DECISION:** Keep the primary cleaned listen table at one row per listen. Parse populated JSON strings into usable lists only in derived processing and retain the source text unchanged. Do not explode the main event table. If artist-level attribution is needed later, use a separate bridge table with the source event key and one MBID per row.
- **Reason:** The field is consistently structured, but a listen may credit multiple artists. Expanding it is a modeling choice that can change attribution and row counts.
- **Validation:** Check that every populated string parses to a list of UUID-shaped strings, preserve the observed array-length counts, and verify each expanded row maps back to one source event. Report source-event count and expanded artist-credit count separately.
- **Project impact:** Counting every credited artist for a collaboration may increase listener counts for multiple artists. Artist discovery and growth metrics could change depending on whether all credited artists receive the listen or only a primary artist does.
- **Human review:** The primary-table shape and separate event-to-artist bridge are approved. The bridge should contain a link for each artist MBID on a listen; any later choice to apply a primary-artist-only attribution rule would require a separate decision.

### 3. Timestamp representation and time-window comparability

- **Columns:** `listened_at`, with `username` for window comparisons.
- **Observed issue:** All 2,214 timestamp strings parse as integer Unix seconds; there are zero invalid or unparseable timestamps. The range is 2019-03-07 13:17:39 UTC through 2026-10-02 22:25:37 UTC, with 2,214 distinct timestamp values. User windows differ: `s_john_s` spans 2019-03-07 to 2019-03-20 (1 calendar month); `H-music`, 2019-07-15 to 2019-11-15 (5 months); `iliekcomputers`, 2024-11-16 to 2024-12-16 (2 months); `music_af`, 2025-09-17 to 2026-03-25 (7 months); and `John V`, 2026-09-25 to 2026-10-02 (2 months). These observed windows do not overlap.
- **Human decision recorded — APPROVED WITH LIMITATION:** Convert `listened_at` to a usable UTC datetime in derived data while preserving every raw timestamp and listen event. Do not artificially force users into a shared observation window during cleaning. Document each user's observed window and treat cross-user growth comparisons as a limitation because four histories are truncated by the 500-listen cap.
- **Reason:** UTC parsing is reproducible and avoids accidental timezone shifts. Different and non-overlapping windows make direct cross-user temporal comparisons misleading.
- **Validation:** Confirm all 2,214 values parse, preserve min/max and row count, check timezone is UTC, and report each user's observed date range and covered months.
- **Project impact:** A rise in unique listeners across different users' windows is not sufficient evidence of artist growth. Growth metrics should use comparable within-user or explicitly bounded periods and expose coverage. Repeat engagement should be computed only where the user's observation window can show a return.
- **Human review:** The UTC conversion, preservation of raw timestamps/events, and handling of differing windows are approved with the stated limitation. Any later growth metric still needs a clearly documented comparison period and coverage basis.

### 4. Repeated identifiers are not exact duplicate events

- **Columns:** All columns for exact-row comparison; `username`, `listened_at`, `recording_msid`, `recording_mbid`, and `release_mbid` for event/recording identity.
- **Observed issue:** There are zero exact duplicate rows. `recording_msid` has 1,525 distinct values; 345 values repeat, occurring on 1,034 rows (689 occurrences beyond the first). `recording_mbid` has 930 distinct populated values, of which 188 repeat. `release_mbid` has 631 distinct populated values, of which 195 repeat. The combination `username` + `listened_at` + `recording_msid` is unique for all 2,214 rows. The most repeated MSID, `711271db-ea46-4f97-8da0-457e5f4d4713`, occurs 116 times for `Road ii Eternity` by `Roseboy666` in H-music's history; timestamps differ.
- **Human decision recorded — APPROVED:** Do not remove repeated recordings, releases, artists, or listens because identifiers repeat; these may be real repeat engagement. Only exact duplicate events are considered duplicates. The current raw dataset has zero exact duplicate rows, so no rows are proposed for removal.
- **Reason:** Repeated plays are meaningful behavior for repeat-engagement analysis. Recording and release IDs identify music entities, not individual listens.
- **Validation:** Exact duplicate count must remain zero; the source event count must remain 2,214; check uniqueness of the candidate event key; report repeated entity-ID counts separately from duplicate-event counts.
- **Project impact:** Deduplicating by `recording_msid`, `recording_mbid`, or `release_mbid` would erase repeat listening and bias continued-engagement measures downward.
- **Human review:** The repeated-identifier and exact-duplicate rule is approved. The 116-play MSID can be examined as an unusual pattern, but it remains preserved and is not classified as an error based on repetition alone.

### 5. Artist names and identifiers do not map one-to-one

- **Columns:** `artist_name`, `artist_mbids`.
- **Observed issue:** There are 795 distinct submitted artist-name strings and 611 distinct individual artist MBIDs. In the observed associations, 139 artist-name strings connect to multiple MBIDs, and 74 MBIDs connect to multiple artist-name strings. Some cases are multi-artist credits (for example `Drake, Rihanna`); others include display-name variation such as `Arthrn`/`arthrn`. Nine repeated MSIDs have more than one exact track/artist/release text combination, with observed differences largely involving capitalization.
- **Human decision recorded — APPROVED:** Preserve each submitted `artist_name` exactly. Do not automatically lowercase, normalize spelling, merge similar names, or infer missing artist MBIDs. Use artist MBID as the preferred resolved identity when available, while keeping unresolved name/MBID relationships flagged.
- **Reason:** Names are free text and may represent collaborations, variants, or different entities. Automated normalization could merge distinct artists or split collaborative credits incorrectly.
- **Validation:** Produce counts of name-to-MBID and MBID-to-name multiplicity before and after any proposed matching; review representative conflicts and confirm raw names remain unchanged. For a metadata join, validate match coverage and one-to-many relationships by MBID before using the result.
- **Project impact:** Incorrect artist grouping changes unique-listener counts and growth rankings, especially for emerging artists with few listens. Multi-artist credits may attribute an event to several artists and inflate audience counts if that is not an explicit project rule.
- **Human review:** The identity and name-preservation policy is approved. Any unresolved name/MBID relationships remain flagged, not automatically resolved. Multi-artist attribution is addressed through a separate bridge-table decision below.

### 6. Numeric-looking IDs and display values must retain text fidelity

- **Columns:** `recording_msid`, `recording_mbid`, `release_mbid`, `artist_mbids`, `username`, `track_name`, `artist_name`, `release_name`, and `listened_at`.
- **Observed issue:** Identifier fields are UUID-shaped strings, the MBID list is serialized text, and names include meaningful case and punctuation differences. No malformed populated IDs were found. The source is CSV, so it has no explicit type schema.
- **Human decision recorded — APPROVED:** Keep identifiers and display-name fields as text and preserve their original case, punctuation, spacing, and values. Create separate derived representations only for `listened_at` as a UTC datetime and `artist_mbids` as parsed arrays; preserve both raw source fields.
- **Reason:** Automatic numeric or text normalization can damage keys or erase distinctions needed for audit and matching.
- **Validation:** Compare source strings to imported values for all identifier/name columns; check UUID formatting without rewriting values; verify the raw and parsed MBID representations agree.
- **Project impact:** Damaged identifiers cause failed or incorrect artist links; name normalization can conceal unresolved identity cases.
- **Human review:** The text-fidelity and separate-derived-representation decision is approved. Any future proposal to standardize labels or resolve identity conflicts remains subject to review.

### 7. Sample caps and uneven user coverage constrain inference

- **Columns:** `username`, `listened_at`, and all artist fields used in counts.
- **Observed issue:** Four users contribute exactly 500 rows, matching the downloader's per-user cap; `music_af` contributes 214. The five date windows are separated by years and do not overlap. The sample therefore has unequal observation length and likely truncated histories for the four capped users.
- **Human decision recorded — APPROVED WITH LIMITATION:** Keep all 2,214 listen events. Record each user's observation window and whether the 500-listen cap was reached. The sample is sufficient for this data-cleaning assignment, exploratory repeat-listening analysis, and a dashboard prototype, but not for reliable population-level or synchronized cross-user artist-growth claims.
- **Reason:** Different sampling lengths and dates affect the chance of observing new listeners, repeat plays, and return behavior.
- **Validation:** Reconcile counts to 500/500/500/500/214; report first/last timestamps, covered days/months, and cap status for every user; ensure any metric denominator reflects observed exposure time.
- **Project impact:** The sample can support cleaning validation, descriptive repeat-listening analysis, and a dashboard prototype. It cannot support reliable population-level or synchronized cross-user artist-growth claims. The five users' differing windows and four capped histories must be visible in summaries.
- **Human review:** The sample-adequacy decision is approved with this limitation. Do not classify artists as emerging during cleaning; the threshold is deferred because no defensible audience or sustained-growth threshold has been set.

## MusicBrainz metadata relationship (not yet joined)

The MusicBrainz metadata dataset is not currently present. **Do not perform a MusicBrainz metadata merge in this cleaning stage.** Preserve the future relationship: ListenBrainz listen → each server-resolved `artist_mbids` value → MusicBrainz artist MBID. The 1,240 mapped listen rows contain 1,538 artist-ID occurrences and 611 distinct MBIDs; 974 rows have no artist MBID and must remain unmatched rather than receiving inferred identities.

If metadata is retrieved later, join it to a separate event-to-artist bridge using MBID, retain unmatched listens, and record match status and coverage. Validate uniqueness of the MusicBrainz artist-MBID key, inspect duplicate metadata keys, measure matched/unmatched event and artist counts, and verify that metadata fields do not multiply listen events unexpectedly. Keep the primary event table at one row per listen; report the bridge row count separately.

## Human Decisions Recorded

1. **Missing optional metadata — APPROVED:** Keep valid listen events; do not impute or infer missing identifiers.
2. **Multi-artist credits — APPROVED WITH DECISION:** Keep one row per listen in the primary event table. Do not explode it. If artist-level attribution is needed, use a separate event-to-artist bridge and report its row count separately.
3. **Timestamp and observation windows — APPROVED WITH LIMITATION:** Create a derived UTC datetime while preserving raw timestamps and all events. Do not force a shared window during cleaning; document each user's window and treat cross-user growth comparison as limited by differing windows and the four capped histories.
4. **Repeated identifiers — APPROVED:** Keep repeated recordings, releases, artists, and listens. Only exact duplicate events are duplicates; the raw dataset has zero exact duplicate rows.
5. **Artist names and identity — APPROVED:** Preserve submitted artist names exactly, prefer MBIDs as resolved identity when available, and flag unresolved relationships without automatic normalization, merging, or inference.
6. **Identifier and text fidelity — APPROVED:** Keep identifiers and display names as text. Create separate derived representations only for UTC `listened_at` and parsed `artist_mbids`.
7. **Uneven user coverage — APPROVED WITH LIMITATION:** Keep all 2,214 events and record user windows and cap status. The sample supports this cleaning assignment, exploratory repeat-listening work, and a prototype dashboard, not population-level or synchronized cross-user growth claims.
8. **Emerging-artist definition — DEFERRED:** Do not classify artists as emerging during cleaning. The materials do not define a defensible audience-size or sustained-growth threshold.
9. **Unmatched artist MBIDs — RESOLVED:** Keep unmatched events in the cleaned event table. For MBID-only analysis, mark them unmatched and report coverage. A separate name-based exploratory view may use submitted names but must not imply resolved identity.
10. **Continued engagement — DEFERRED TO ANALYSIS:** Do not assign a final label in cleaning. Descriptive evidence may include repeated listens and listens on multiple distinct days; decide a final threshold during analysis.
11. **Sample adequacy — RESOLVED:** The five-user sample is adequate for cleaning validation and a prototype dashboard, but not population-level artist-growth claims.
12. **MusicBrainz merge — DEFERRED:** No metadata dataset is present, so do not merge it during cleaning. Preserve the documented MBID-based merge plan for future work.

## Proposed Validation Checklist

- [ ] **Rows before/after:** Record 2,214 source rows and 9 columns. Any derived bridge/expanded table must be reported separately; raw-event row count remains 2,214.
- [ ] **Missing values before/after:** Preserve baseline counts: `release_name` 1,027; `artist_mbids` 974; `recording_mbid` 943; `release_mbid` 974; zero in the other five columns. Report changes only when they are representation changes, not fabricated values.
- [ ] **Duplicates:** Exact duplicate rows are 0. Verify no listen events were removed. Report repeated recording/release identifiers separately; check the candidate event key `username` + `listened_at` + `recording_msid` remains unique.
- [ ] **Data types:** Names and identifiers remain text; `listened_at` parses as integer Unix seconds and any derived datetime is UTC; parsed `artist_mbids` remains an array without changing the source text.
- [ ] **Timestamp range:** Confirm 0 invalid/unparseable values and the range remains 2019-03-07 13:17:39 UTC to 2026-10-02 22:25:37 UTC.
- [ ] **Categorical values:** Reconcile five usernames and listen counts (500, 500, 500, 500, 214); compare distinct artist-name count (795) and inspect spelling/case variants without automatically merging them.
- [ ] **Artist identifiers:** Reconcile 974 blank artist-MBID rows, 1,240 populated arrays, 1,538 ID occurrences, and 611 distinct artist MBIDs; confirm all populated JSON values parse and preserve multi-ID credits.
- [ ] **Merge coverage, if applicable:** Before a MusicBrainz join, validate MBID key uniqueness, event/artist match rates, unmatched records, and row multiplication; keep unmatched events and separate join results from raw data.
- [ ] **Five difficult record checks:**
  1. Inspect all 116 listens with `recording_msid` `711271db-ea46-4f97-8da0-457e5f4d4713`; confirm distinct timestamps remain separate events.
  2. Inspect a row with multiple artist MBIDs (the dataset includes arrays of up to six IDs) and verify expansion maps each ID back to one source event.
  3. Inspect the `Arthrn`/`arthrn` and other multi-name/multi-MBID cases; ensure no silent normalization or merge occurs.
  4. Inspect a listen with blank `artist_mbids` and populated core event fields; confirm it is retained and no identity is inferred.
  5. Inspect the first and last listens for each user, especially John V's 500-row window from 2026-09-25 to 2026-10-02, and verify date coverage/cap status is reflected in summaries.
