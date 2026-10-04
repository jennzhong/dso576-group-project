# DSO 576 Module 6 - Project Data Cleaning

**Student:** Shivanee Kooner  
**Project:** Emerging Artist Discovery Through Listening Behavior  
**Individual branch:** `cleaning-shivanee`  
**Branch URL:** https://github.com/jennzhong/dso576-group-project/tree/cleaning-shivanee  
**Submitted cleaning commit ID:** `7f4a60bcecc30a2480348c1c451f0dd8487b7739`

## Project vision and question

A music-streaming editorial team must decide which emerging artists should receive additional exposure and which listener segments are most likely to continue engaging after discovery.

**Business question:** Can listening behavior - especially growth in unique listeners and repeat engagement - help a music-streaming editorial team identify promising emerging artists for additional exposure?

One row in the ListenBrainz input represents **one listen event: one user playing one track at one point in time**.

## Data source and version

Primary source: **ListenBrainz public API**

Endpoint used:

`GET /1/user/{username}/listens`

Historical cutoff used to recreate the team's sample:

`2026-09-22 00:00:00 UTC`

Because the ListenBrainz `max_ts` parameter is exclusive, this cutoff includes listens through September 21, 2026.

The recreation uses the five users and target row counts documented in the team project:

- `iliekcomputers`: 500
- `H-music`: 500
- `s_john_s`: 500
- `John V`: 226
- `music_af`: 214

The original project exploration reported 1,940 total listens, five listeners, and 756 unique free-text artist names. The pull script writes `pull_validation.json` so any differences caused by later ListenBrainz history or server-side MBID resolution changes are explicit rather than hidden.

ListenBrainz API documentation:
- https://listenbrainz.readthedocs.io/en/latest/users/api/core.html
- https://listenbrainz.readthedocs.io/en/latest/users/json.html

## Cleaning rules

1. Keep the raw extract unchanged.
2. Parse `listened_at` as a UTC datetime.
3. Trim only leading/trailing whitespace from text and identifier fields.
4. Preserve case, punctuation, accents, and meaningful internal spacing.
5. Normalize `artist_mbids` to a reproducible JSON-list representation while preserving artist-credit order.
6. Remove only exact duplicate rows.
7. Keep repeated listening events because repeat engagement is part of the project question.
8. Do not impute missing MusicBrainz identifiers or release names.
9. Flag suspicious/invalid core values rather than silently inventing replacements.
10. Do not perform the planned MusicBrainz metadata merge in this cleaning step; the current assignment cleans the ListenBrainz event table first.

## How to run from the original source

Use Python 3.10+.

```bash
python -m pip install -r requirements.txt
python pull_listenbrainz_sample.py
python clean_listenbrainz.py
python build_report.py
```

Or open `module6_cleaning.ipynb` and choose **Run All**.

The raw `listenbrainz_sample.csv` is intentionally kept separate from the cleaned outputs and should remain ignored by Git.

## Expected generated files

The pull step creates:

- `listenbrainz_sample.csv` - raw recreated extract
- `pull_validation.json` - comparison with the September 2026 team reference

The cleaning step creates:

- `listenbrainz_cleaned.csv` - full cleaned data for local verification
- `cleaned_sample_50.csv` - up to 50 cleaned rows for the GitHub submission
- `cleaning_decision_log.csv` - cleaning rule, reason, and check
- `record_checks.csv` - five original/expected/actual record checks
- `cleaning_summary.json` - row-count, missingness, duplicate, and metric reconciliation
- `checklist.json` - structured 14-item checklist evidence
- `checklist_evidence.md` - readable 14-item checklist

The report step creates:

- `Shivanee_Kooner_Module6_Cleaning_Report.pdf` - Gradescope PDF

## 50-row sample selection

The sample intentionally includes the five record-check rows, oldest and newest listens for users where available, rows with missing artist MBIDs, multi-artist-credit cases when present, and a deterministic random sample (`random_state=576`) to reach 50 rows.

## Reproducibility

Run the notebook or the three scripts in order from the repository root. The scripts reconstruct the historical input, apply the written cleaning rules, create the evidence files, and rebuild the PDF.

Before submitting, run:

```bash
python validate_submission.py
```

## Finalization workflow

After the first commit that contains the completed cleaning code and generated evidence:

```bash
git rev-parse HEAD
```

Copy that commit ID and run:

```bash
python finalize_submission.py YOUR_COMMIT_ID
```

This updates the README and PDF with the submitted cleaning commit ID. Commit those metadata updates in one final small commit.
