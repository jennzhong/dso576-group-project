# dso576-group-project
# dso576-group-project: data cleaning (Module 6)

- Branch: cleaning-benazira
- Branch URL: (add after push)
- Commit ID: (add after push)

## Data
ListenBrainz API sample, pulled 5 Oct 2026: 5 users, 2,214 listens (listenbrainz_sample.csv, gitignored).

## How to reproduce
pip install -r requirements.txt
python3 pull_data_team.py
python3 clean.py

## Files
clean.py, cleaning.ipynb, decisions_log.md, pull_data_team.py, requirements.txt

## Results
Final rows: 2,214 (0 exact duplicates, 0 rows dropped). Missing artist MBID: 1,025 rows (46.3%), flagged and kept.