# DSO 576 Phase 2 — Member 3 Deliverables

**Primary output:** `data/listenbrainz_final_cleaned.csv` (1,940 rows, 11 columns; nine source fields plus two analysis-ready fields).

## Files and upload paths
- `data/listenbrainz_final_cleaned.csv` — consolidated event table for teammates.
- `data/user_observation_summary.csv` — per-user observation dates, counts, sampling-cap indicators.
- `docs/validation_summary.json` — machine-readable validation metrics.
- `scripts/final_cleaning.py` — rerunnable cleaning and validation pipeline.
- `docs/cleaning_integration_log.md` — team-method comparison, integration decisions, checks, limitations.
- `README.md` — this usage guide.

## Reproduce
From repository root:
```bash
pip install pandas
python scripts/final_cleaning.py --input 'listenbrainz_sample.csv' --outdir data
```
The command generates the two CSV files and `data/validation_summary.json`. Move that JSON into `docs/` if following this packaging layout.

## Dataset-version note
The supplied original CSV contains 1,940 rows, consistent with Shivanee's Module 6 extract. Another teammate's program refers to a separate 2,214-row baseline. **Confirm the team's accepted source version before merging this branch.** Never combine overlapping exports without checking provenance and true duplicate events.

Suggested GitHub workflow: commit to `cleaning-shivanee` (or the team's designated Member 3 branch), then open a PR for review. Place files in existing equivalent repository folders if different from this suggested layout.
