# Individual App Audit

## Auditor

- Name: Jennifer Zhong
- App version/commit: 7206e9799ebf043e971a6e7f3e8c25b39942fd39
- Feature audited: Dashboard availability and artist-performance data
- Number audited: Total artist-resolved listens in `artist_performance.csv`

## Feature Check

- Intended user and task: Editorial team members use the dashboard to shortlist emerging artists and examine audience and engagement patterns (`project-start.md`).
- Steps: At commit `7206e97`, inspect the repository README, project brief, tracked files, and aggregation code; search for Streamlit app files and an app prompt.
- Expected: A runnable dashboard with controls and visualizations for examining artist performance, as described in the project brief.
- Actual: The repository contains the project brief, pandas aggregation code, and chart-ready CSV outputs, but no Streamlit app code or app prompt. The dashboard workflow cannot be run or its controls exercised from this commit.
- Conclusion: The dashboard feature is missing from the checked repository version; data preparation exists, but it does not satisfy the promised interactive task.

## Number Check

- Definition: Sum of `total_listens` across artists in `artist_performance.csv`; one qualifying source listen row is counted for an artist when username, artist name, and UTC timestamp are present. This is a listen-row count, not unique listeners.
- Method: `audit/audit_check.py` independently parses the source timestamp, applies the same non-missing conditions as `build_artist_performance`, groups by artist name, and compares its count with the generated table. It reports retained/excluded rows, missing artist names, time bounds, per-artist minimum and maximum, and both totals.
- Expected: 1,940 artist-resolved listen rows.
- Actual: 1,940 in the generated `artist_performance.csv`; no App display value is available because the App is absent.
- Conclusion: Independent result and generated output agree. This validates the exported data metric, not an App KPI display.

## Final Conclusion

The checked commit has reproducible artist-performance data, and its total listen count matches the independent pandas check. The promised dashboard itself and its interactions remain untested because no App is present; the missing dashboard is recorded as CR-JZ-01.

## Personal Contribution and AI Use

I selected and evaluated the audit evidence, verified the results, and made the final conclusions. AI helped inspect the code, create the reproducible check, and organize the report.
