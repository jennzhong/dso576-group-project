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
| Submitted commit (code + outputs) | `1bb28dfa98123ad288b06ae51393a96f4800de14` — https://github.com/jennzhong/dso576-group-project/commit/1bb28dfa98123ad288b06ae51393a96f4800de14 |

The commit after the submitted one changes only this README section.
Outputs are byte-identical at both commits.
