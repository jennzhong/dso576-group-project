# DSO 576 Phase 2 — Member 4 Deliverables (Backend Analysis: KPIs)

**Primary output:** `kpi_analysis.py`, reusable KPI functions for the dashboard. Its outputs:
- `outputs_kpi/artist_kpis.csv`: 669 artists × 17 KPI columns
- `outputs_kpi/listener_artist_kpis.csv`: 677 listener × artist rows
- `outputs_kpi/kpi_summary.json`: KPI cards and reconciliation checks

## Files
- `kpi_analysis.py`: loader (adds `artist_id`, `is_countable` and other analysis columns to Member 3's table), period filter, KPI functions, shortlist filter, artist detail, CLI.
- `listenbrainz_final_cleaned.csv`: Member 3's canonical input (1,940 rows; copied from branch `Cleaned-Dataset`).
- `outputs_kpi/artist_kpis.csv`: one row per artist. This is the ranking table for use case 1.
- `outputs_kpi/listener_artist_kpis.csv`: one row per listener × artist. Use cases 2 and 3 and Member 5 build on it.
- `outputs_kpi/kpi_summary.json`: headline KPI cards plus the checks that must pass.
- `kpi_analysis_log.md`: input decision, KPI definitions table, rules (including new R7b and return momentum), verified results, downstream use, limitations.
- `tests/test_kpi_analysis.py`: 17 tests. They cover hand-computed examples, edge cases, and parity with Module 6.

## Reproduce
From the repository root:
```bash
uv sync                                    # or: pip install -r requirements.txt
uv run python kpi_analysis.py --input listenbrainz_final_cleaned.csv --outdir outputs_kpi
uv run python kpi_analysis.py --start 2019-07-15 --end 2019-08-31 --outdir /tmp/kpi_period   # one period
uv run pytest                              # expected: 17 passed
```
The first command prints `kpi_summary.json` and ends with `artists: 669  listener x artist pairs: 677`.

## Use from code (Member 5, Phase 3 app)
```python
import kpi_analysis as k
listens = k.load_listens()                                   # cache this in the app
period = k.filter_period(listens, "2024-11-16", "2024-12-16")
artists, pairs, summary = k.compute_kpis(period)             # table, pair rows, KPI cards
shortlist = k.apply_emerging_filter(artists, k.EmergingFilter(min_listens=5, min_avg_active_days=2))
detail = k.artist_detail(period, artists.loc[0, "artist_id"])  # summary, listeners, tracks
```

## Note
`kpi_analysis.py` adds one identity rule (R7b, see `cleaning_rules.md` → Changes to rules) and computes countability on load. If Member 3 adds those columns to the canonical file, only `derive_columns()` changes. The Module 6 outputs below are untouched: `check_reproducible.py` still reproduces all 7 exactly.

---

# dso576-group-project — Module 6 data cleaning (Andy Chen)

**Branch:** `cleaning-andy` ·
**Branch URL:** https://github.com/jennzhong/dso576-group-project/tree/cleaning-andy ·
**Submitted commit:** see [Submission metadata](#submission-metadata)

Project: *Emerging Artist Discovery Through Listening Behavior.*
Question for this stage: **which artists in our sample show repeat engagement
(listeners returning on 2+ days), and which listeners drive it?** Main metrics
per artist: countable listens, unique listeners, return rate.

## Data source and version

| | |
|---|---|
| Source | ListenBrainz public API, `GET https://api.listenbrainz.org/1/user/{username}/listens` (CC0 licence) |
| Sampling | 5 users found via `GET /1/search/users/` with ≥ 50 listens; up to 500 most recent listens each, paged back with `max_ts` |
| Retrieved | 21 September 2026 |
| Frozen file | `listenbrainz_sample.csv` — 1,940 rows × 9 columns, SHA-256 `463000bf005a3c667cfeb708b44aa12f0d35342e34f467ede3caf924426b816d` |
| Timestamps | `listened_at` is UTC (checked against the live API for user *John V* on 3 Oct 2026: three listens matched to the second) |

The API returns live data, so a new pull would not recreate this file. The
committed CSV is the versioned source. `clean_listens.py` refuses to run if its
hash changes and never writes to it.

## How to run

```bash
# with uv (recommended — uses uv.lock)
uv sync
uv run python clean_listens.py          # clean + validate, writes outputs/
uv run python check_reproducible.py     # rerun into a temp folder and compare hashes
uv run jupyter nbconvert --to notebook --execute listenbrainz_cleaning.ipynb --output /tmp/check.ipynb

# or with pip
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python clean_listens.py && python check_reproducible.py
```

Expected console output of `clean_listens.py`:

```
raw rows 1940 -> cleaned rows 1940 -> countable 1882
record checks matched: 17/17
outputs written to outputs/
```

`check_reproducible.py` should end with `All 7 submitted outputs reproduced exactly: True`.

## Expected output files (`outputs/`)

| File | Rows | What it is |
|---|---|---|
| `cleaned_listens.csv` | 1,940 | One row per listen: the 9 raw columns unchanged + `listen_id`, UTC time, cleaned text, `artist_key`, `artist_id`, parsed MBIDs, flags, `is_countable` |
| `listen_artist_bridge.csv` | 1,479 | One row per listen × credited artist MBID (1,181 listens with MBIDs) |
| `artist_summary.csv` | 746 | Per-artist countable listens, unique / returning listeners, return rate |
| `cleaned_sample.csv` | 50 | Submission sample; `sample_reason` says why each row was picked |
| `record_checks.csv` | 17 | Expected (written before the code) vs actual values for 7 records |
| `change_log.csv` | 19 | Rows affected by each rule |
| `validation_report.md` | — | Full-dataset checks: counts, reconciliation, missing values, duplicates, threshold sensitivity, merge check, metric denominators |
| `output_checksums.txt` | — | SHA-256 of each file above |

## Files in this branch

| File | Purpose |
|---|---|
| `inspect_raw.py`, `inspect_followup.py` | Step 1: look at the raw data before writing rules (read-only) |
| `cleaning_rules.md` | Rules R1–R12, reasons, alias exception, metric definitions — committed before the cleaning code |
| `record_checks_expected.csv` | Expected record-check results — committed before the cleaning code |
| `clean_listens.py` | Applies the rules, validates the full dataset, writes `outputs/` |
| `check_reproducible.py` | Reproducibility test |
| `listenbrainz_cleaning.ipynb` | Step-by-step walkthrough using the same functions (writes nothing) |
| `pyproject.toml`, `uv.lock`, `requirements.txt` | Dependencies |
| `explore_sample.py`, `test_team_assumptions.py` | Earlier Phase 1 exploration (unchanged) |

There is no pull script on this branch: the API serves live data, so a re-pull
would not recreate the sample. The source details above and the frozen CSV
(checked by SHA-256) document the pull.

## Key cleaning decisions (details in `cleaning_rules.md`)

- 0 exact duplicates → 0 rows removed. 610 replays kept (they are the engagement we measure).
- 58 **suspected double-scrobbles** (same user, same recording, < 60 s after the previous submission) are flagged and excluded from metrics (`is_countable = False`), not deleted. 41 of them are one looped track for user H-music.
- Missing MBIDs / release names (37–39%) are kept, not filled.
- Display text: trim + Unicode NFC only. Grouping key `artist_key`: casefold, drop `" - Topic"`, one documented alias, placeholders (`Unknown`) → missing.
- Artist identity: first artist MBID when present, otherwise `name:<artist_key>`. Multi-artist credits are expanded only in the bridge table.

## Submission metadata

| | |
|---|---|
| Branch | `cleaning-andy` |
| Branch URL | https://github.com/jennzhong/dso576-group-project/tree/cleaning-andy |
| Submitted commit (code + outputs) | `9dbd3c6a5714a0eeb4c6f8c09373101e90889bda` — https://github.com/jennzhong/dso576-group-project/commit/9dbd3c6a5714a0eeb4c6f8c09373101e90889bda |

The commit after the submitted one changes only this README section.
Outputs are byte-identical at both commits.
