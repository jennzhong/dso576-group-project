# dso576-group-project

## Submission Metadata

- **GitHub branch:** `lewis-li`
- **Branch URL:** [lewis-li](https://github.com/jennzhong/dso576-group-project/tree/lewis-li)
- **Submitted commit ID:** c10ad7379338e783f780ae20a81073fa1f9a4bd5

## Data-Cleaning Workflow

### Project area and goal

**Project area:** Emerging Artist Discovery Through Listening Behavior.

This cleaning stage prepares ListenBrainz listening events for exploratory analysis and dashboard prototyping. The broader project asks whether listening behavior can help an editorial team identify promising emerging artists and listener groups likely to continue engaging with them. This stage preserves and validates the listen events; it does not decide which artists are emerging or define a final continued-engagement threshold.

### Data and row definition

The source is the project's public ListenBrainz sample, stored locally as `listenbrainz_sample.csv`. It contains **2,214 raw rows** and 9 source columns across five users. **One row represents one user's listen to one track at one timestamp.** Repeated recordings can therefore represent separate listen events.

The cleaned event table contains **2,214 rows** and 11 columns: the original nine columns plus `listened_at_utc` and `artist_mbids_parsed`. It remains one row per listen.

### Cleaning approach and approved decisions

- Load the source fields as text and preserve their original values. Keep raw `listened_at` and add a separate UTC datetime. Parse `artist_mbids` safely into a separate JSON-array representation while retaining its original text.
- Remove a row only if all nine raw event fields exactly duplicate a prior row. The current source has **0 exact duplicate rows**, so the cleaned event count remains **2,214** and **0 rows are removed**.
- Keep valid listen events when optional `release_name`, `artist_mbids`, `recording_mbid`, or `release_mbid` values are missing. Do not fill or infer missing metadata.
- Do not remove repeated recordings, releases, artist IDs, or listens based on identifier repetition. Those may represent real repeat engagement.
- Preserve submitted artist names, track names, release names, usernames, and identifiers exactly. Do not lowercase, normalize spelling, or merge similar names. Prefer an available artist MBID as resolved identity and flag unresolved relationships.
- Keep multi-artist credits in the primary event table without exploding it. If artist-level attribution is needed later, use a separate event-to-artist bridge and report its row count separately.
- Do not merge MusicBrainz metadata in this cleaning stage; the metadata dataset is not currently present. The future join is ListenBrainz event → resolved `artist_mbids` → MusicBrainz artist MBID.

### Validation results

The validation report records source and cleaned row/column counts, missing values, exact duplicate and candidate event-key checks, timestamp conversion and range, user counts, artist-name and artist-MBID coverage, parsed-array validity, repeated identifiers, and per-user observation windows. The current results are:

- Source rows: **2,214**; cleaned rows: **2,214**; rows removed: **0**.
- Exact duplicate rows: **0**; candidate event key is unique.
- Timestamp conversion failures: **0**; range: 2019-03-07 13:17:39 UTC to 2026-10-02 22:25:37 UTC.
- Five individual record-level checks passed, covering repeated recordings, multi-artist MBIDs, artist-name case variation, missing artist MBIDs, and a capped user's observation-window boundary.

### Sampling and analysis limitations

The five users have different, non-overlapping observation windows. Four histories reached the 500-listen sampling cap; the fifth has 214 listens. Artist MBID availability also varies by user. The sample is approved for this cleaning assignment, descriptive repeat-listening exploration, and a dashboard prototype, but it is not sufficient for reliable population-level or synchronized cross-user artist-growth claims. The cleaning stage records the windows and cap status rather than forcing a shared observation period.

Emerging-artist criteria and a final continued-engagement threshold are deferred to the analysis phase. Until then, repeat listens and listens on multiple distinct days may be shown as descriptive evidence only.

### Project files

| File | Purpose |
|---|---|
| `project-start.md` | Project vision and source notes. |
| `pull_listenbrainz_sample.py` | Retrieves the documented ListenBrainz sample. |
| `listenbrainz_sample.csv` | Raw 2,214-row ListenBrainz source sample. |
| `explore_sample.py` | Prints exploratory summaries for the raw sample. |
| `clean_listenbrainz.py` | Reproducible pandas cleaning and validation workflow. |
| `cleaned_listenbrainz.csv` | Cleaned 2,214-row event table with two derived columns. |
| `user_observation_summary.csv` | Per-user row counts, observation windows, durations, and cap status. |
| `validation_report.md` | Generated validation counts and results. |
| `record_checks.md` | Five record-level comparisons of raw and cleaned values. |
| `plan.md` | Dataset-based cleaning plan and recorded human decisions. |
| `listenbrainz_cleaning.ipynb` | Explanatory notebook reproducing the validation workflow. |
| `cleaned_sample.csv` | Deterministic 50-row submission sample from the cleaned table. |
| `requirements.txt` | External Python dependencies used by the project scripts. |

Full CSV datasets are intentionally ignored by Git. `cleaned_sample.csv` is the exception: it is a 50-row submission sample and is allowed to be tracked. The raw, full cleaned, and user-summary CSVs remain ignored.

### Environment setup and reproduction

From the repository root, install the external dependencies and run the cleaning script:

```bash
python3 -m pip install -r requirements.txt
python3 clean_listenbrainz.py
```

The script reads `listenbrainz_sample.csv` without modifying it and creates `cleaned_listenbrainz.csv`, `user_observation_summary.csv`, and `validation_report.md`. Open `listenbrainz_cleaning.ipynb` in VS Code with a Python environment that has the requirements installed to review or execute the notebook cells. The notebook demonstrates the same checks without writing or replacing the datasets.
