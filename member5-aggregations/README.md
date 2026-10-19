# DSO 576 Phase 2 — Member 5 Aggregation Analysis

## Purpose

This folder contains the Member 5 backend aggregation work for the ListenBrainz dashboard.

The analysis provides reusable pandas functions for:

- observed audience growth
- listener engagement
- daily listener activity
- artist performance
- artist growth over time
- listener engagement by artist

The generated tables are designed for use in dashboard charts, KPI displays, tables, and filters.

## Input Dataset

The analysis uses the cleaned dataset prepared by Member 3:

`../listenbrainz_final_cleaned.csv`

Dataset dimensions:

- 1,940 listening events
- 5 sampled users
- 11 columns

The source dataset is read but never modified.

## Folder Contents

- `aggregation_functions.py` — reusable aggregation functions and output-generation pipeline
- `aggregation_analysis.ipynb` — documented analysis, validation, and development process
- `outputs/` — generated chart-ready CSV files
- `README.md` — usage instructions, metric definitions, and limitations

## limitation
- A listener's first play in this dataset may not represent their true first discovery of an artist.
- The 30-day return metric therefore measures return after the first observed listen in the sample.
- The proposed quiet-period discovery rule is not implemented because the quiet-period threshold has not yet been defined.
- The current outputs provide the component metrics for emerging-artist evaluation but do not apply a final emerging-artist ranking rule.
- MusicBrainz metadata enrichment and comparison with public artist-listener counts require additional external data.

## Reproduce the Outputs

From the repository root, run:

```bash
python member5-aggregations/aggregation_functions.py

