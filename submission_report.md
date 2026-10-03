# Data Cleaning and Validation Report

## Submission Metadata

- **GitHub branch:** `lewis-li`
- **Branch URL:** [lewis-li](https://github.com/jennzhong/dso576-group-project/tree/lewis-li)
- **Submitted commit ID:** [ADD AFTER FINAL CODE COMMIT]

## 1. Project Goal

This project studies **Emerging Artist Discovery Through Listening Behavior**. This cleaning stage prepares a reliable, reproducible dataset for later analysis and dashboard work on listening behavior, artist discovery, and repeat engagement.

## 2. Dataset Overview

- **Source:** ListenBrainz sample
- **Raw data:** 2,214 rows and 9 columns from five users
- **Unit of observation:** One row represents one user's listen to one track at one timestamp.
- **Cleaned result:** 2,214 rows and 11 columns, retaining all nine raw fields and adding two derived fields.

## 3. Cleaning Workflow

The workflow followed **Envision → Plan → Set rules → Human decisions → Implement → Validate → Refine**. `plan.md` was created from inspection of the actual dataset and reviewed before implementation. Approved decisions were then implemented in a reproducible pandas script and checked in the validation report, record checks, and executed notebook.

## 4. Cleaning Decision Log

| Issue | Decision | Reason |
|---|---|---|
| Missing optional metadata | Retain listen events with missing release names or MBIDs; do not infer or fill values. | Missing enrichment fields do not invalidate a listen event. |
| Exact duplicates | Remove only actual exact duplicate events; none were found, so no rows were removed. | Duplicate rows differ from legitimate repeated listening. |
| Repeated recording/release IDs | Preserve repeated identifiers and listens. | Repetition may represent genuine engagement. |
| `artist_mbids` parsing | Preserve the raw text and add a derived parsed array for analysis. | Enables validation and analysis without changing the source value. |
| Multi-artist credits | Keep one row per listen; do not explode the main table. | Prevents multiplying event counts; a separate bridge table can support future attribution. |
| Artist-name capitalization/spelling | Preserve submitted values exactly; do not normalize or merge names automatically. | Similar or differently cased names do not establish resolved identity. |
| Timestamps | Preserve raw `listened_at` and add a derived UTC datetime. | Supports time analysis while retaining source fidelity. |
| Differing user observation windows | Record each user's window; do not force synchronized windows. | Users have different coverage periods, limiting direct comparisons. |
| 500-listen sample cap | Record cap status and retain all events. | Four histories are truncated at the sampling cap. |
| MusicBrainz merge | Defer metadata merge. | MusicBrainz metadata was not present in this cleaning stage. |

## 5. Human-in-the-Loop Decisions

The team reviewed and approved the domain rules before implementation. The team decided to keep missing MBIDs unresolved, avoid automatic artist-name normalization, retain repeated listens, keep one row per listen, and preserve raw fields. The team also deferred definitions for emerging artists and continued engagement to the analysis phase, and deferred the MusicBrainz merge. Codex supported inspection and implementation; it did not make these domain decisions.

## 6. Validation Checklist

1. **PASS — Raw row count:** 2,214.
2. **PASS — Cleaned row count:** 2,214.
3. **PASS — Row-count reconciliation:** 2,214 source rows − 0 removed = 2,214 cleaned rows.
4. **PASS — Required raw columns preserved:** All 9 raw columns are retained; the output has 11 columns total.
5. **PASS — Missing values before/after:** Raw missing counts were recorded for every column; missing optional metadata remains missing, with no imputation or row removal.
6. **PASS — Exact duplicates:** 0 source exact duplicate rows.
7. **PASS — Candidate event-key uniqueness:** `(username, listened_at, recording_msid)` is unique across the 2,214 rows.
8. **PASS — Timestamp conversion failures:** 0.
9. **PASS — Timestamp range:** 2019-03-07 13:17:39 UTC to 2026-10-02 22:25:37 UTC.
10. **PASS — Categorical/user counts:** 5 users; counts are H-music 500, John V 500, iliekcomputers 500, music_af 214, and s_john_s 500.
11. **PASS — Artist-name distinct values:** 795 distinct submitted `artist_name` values.
12. **PASS — Artist MBID parsing and coverage:** 1,240 / 2,214 rows have artist MBIDs (56.01%); 611 unique artist MBIDs; 1,240 valid parsed arrays and 0 invalid arrays/elements.
13. **PASS — Repeated identifiers distinguished from duplicates:** Repeated recording, recording-MBID, and release-MBID values were reported separately; they were retained and were not counted as duplicate events.
14. **PASS — Difficult-record checks:** All five individual checks documented in `record_checks.md` passed.

## 7. Five Record-Level Checks

- **Repeated recording:** Confirmed multiple listens with the same recording MSID remain separate events.
- **Multi-artist MBIDs:** Confirmed the source MBID text is preserved, the derived list contains multiple MBIDs, and the event remains one row.
- **Artist-name case variation:** Confirmed `Arthrn` and `arthrn` remain as submitted without normalization or merging.
- **Missing artist MBID:** Confirmed a valid listen with blank `artist_mbids` remains in the cleaned table without an inferred identity.
- **Observation-window boundary:** Confirmed a capped user's final boundary listen remains, and the user's summary reports the correct first/last timestamps and cap status.

All five checks matched their expected results.

## 8. Codex Use and Human Review

Codex was used to inspect the data, draft the cleaning plan, produce reproducible cleaning code, and create validation logic. The human reviewed the proposed rules before implementation, approved domain-specific decisions, inspected the code, ran the cleaning script, checked the validation outputs, and executed the notebook.

One correction occurred before cleaning: the intended ListenBrainz CSV was not yet available for inspection. The data-acquisition workflow was corrected, the actual sample was retrieved, and the plan was rebuilt using findings from that dataset.

### Verification of a Codex Suggestion

Codex suggested that repeated recording identifiers should not automatically be treated as duplicate listen events. We checked the most repeated `recording_msid`, which appeared 116 times. The events had distinct timestamps, and all 116 were retained after cleaning. Therefore, we approved treating them as repeated listening behavior rather than duplicate events.

## 9. Limitations

- Four users reached the 500-listen cap, so their histories are truncated.
- Users have different, non-synchronized observation windows.
- Missing artist MBIDs limit analyses that require resolved artist identifiers.
- The five-user sample is not sufficient for population-level claims.
- MusicBrainz enrichment has not been performed.

## 10. Final Validation Result

The cleaning workflow preserved all 2,214 valid listen events and introduced only two documented derived columns: a UTC timestamp and a parsed artist-MBID array. It passed all dataset-level and record-level validation checks, with 0 rows removed, 0 exact duplicate rows, and 0 timestamp conversion failures.
