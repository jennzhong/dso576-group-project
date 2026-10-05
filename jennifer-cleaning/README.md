# DSO 576 Module 6 Data Cleaning

**Student:** Jingxuan (Jennifer) Zhong  
**Project:** Emerging Artist Discovery Through Listening Behavior  
**Individual branch:** `cleaning-jennifer`  
**Branch URL:** https://github.com/jennzhong/dso576-group-project/tree/cleaning-jennifer  
**Submitted commit ID:** `c0a3c351ac3a9a00ad1699056af2e744b3c37150`

## Data source and version

The source is the ListenBrainz listening sample collected on 21 September 2026 and preserved at `data/raw/listenbrainz_sample.csv`. It has 1,940 listen-event rows and nine source columns. The original CSV is not changed by the cleaning script.

## Run instructions

From this directory, install the dependencies and run the cleaner:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python clean_listenbrainz.py
```

To review the executed walkthrough, open `listenbrainz_cleaning.ipynb` in Jupyter and use Run All.

## Expected outputs

- `data/processed/listenbrainz_cleaned.csv` — full cleaned dataset for local validation; excluded from GitHub.
- `cleaned_sample.csv` — up to 50 cleaned rows for the assignment submission. It includes missing metadata, multiple artist credits, repeated recordings, placeholder artist names, and names with punctuation when those cases are present.
- `submission/Jennifer_Zhong_Module_6_Cleaning_Report.pdf` — the 14-item checklist and verification evidence for Gradescope; excluded from GitHub.

The cleaning decision log is in the notebook and report. The event dataset keeps `artist_mbids` as supplied; no separate artist mapping table or metadata merge is needed for this cleaning assignment.
