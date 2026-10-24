# Change requests

The Module 9 template was not in the module repository, so this file follows the homework's three parts: claims, findings, requested changes.

## Claims

| Name | Feature audited | Number audited |
|---|---|---|
| Andy Chen | Tab 1 row click → Tab 2 artist detail (UC1 → UC2, check A4) | Tab 2 "30-day return rate" (M5 `build_artist_engagement().return_rate_pct`) |

## Findings

Audited at commit `f7032fe` plus the untracked `app.py` (sha256 prefix `89a8083fec12`). Reproduce everything with `uv run pytest -q audit` (all 3 checks fail on this version, by design).

### F1 — "30-day return rate" counts same-session listens as returns (Andy Chen)
- **Where:** `member5-aggregations/aggregation_functions.py:183`. A listen counts as a return if `listened_at_utc > first_listen` and is within 30 days, so the next track a few minutes later qualifies.
- **Spec conflict:** BUILD_SPEC §2 defines continued engagement as plays on 2+ distinct UTC days. Tab 2 places this number next to M4's "Return rate", which uses that definition.
- **Evidence 1 (small case):** `audit/test_andy_audit.py::test_30_day_return_small_case`. 3 listeners: one plays 2 tracks 3 minutes apart, one returns 9 days later, one listens once. Expected 33.33% (1 of 3); M5 returns **66.67%**.
- **Evidence 2 (real data):** `test_30_day_return_never_exceeds_all_time_return`. A 30-day return can never be more common than a return at any time, yet **53 of 481** artists show a 30-day return rate above M4's all-time return rate. The test compares like with like: only rows with their own artist MBID and only the primary credited artist, so F2 and multi-artist credits cannot explain the gap. All 53 have exactly 1 active day. Comparing the numbers as the dashboard shows them (all rows), 61 of 481 artists break the rule. Example: Willie Nelson has 13 tracks in one 46-minute session on 2026-09-18 (John V). M4 shows 0.0%; M5 shows 100.0%.
- **Also noted:** M5 does not remove double-scrobbles (the spec notes this), so a duplicate scrobble seconds later would also count as a "return".

### F2 — M5 30-day return misses R7b-borrowed rows (Andy Chen, secondary)
- Mixed Matches (`e55d138d…`): H-music played it on 8 distinct days between 2019-08-26 and 2019-11-02. 11 of the 12 rows have `artist_id_source = key_mbid`, so M5 sees 1 listen and shows a **0.0%** 30-day return, while M4 shows a 100% return rate. The spec acknowledges the "MBID-matched listens" scope, but a curator reading 0% would conclude nobody came back.

### F3 — Clicking a shortlist row does not change the Tab 2 artist (Andy Chen)
- **Where:** `app.py:164-167`. The picker uses `key="artist_picker"`, so once it has a value Streamlit ignores the new `index=` argument. Line 167 then writes the stale picker value back into `selected_artist_id`, which undoes the click.
- **Evidence:** `test_row_click_changes_artist_detail` (Streamlit AppTest). It sets `selected_artist_id` to rank 5 (Diljit Dosanjh), as line 151 does on a click, and reruns; the picker still shows rank 1 (Arthrn).
- **Scope:** AppTest cannot click a dataframe row, so the test reproduces what the click handler does, not the click itself. Manual check: run `uv run streamlit run app.py`, click the rank-5 row, then open Artist detail.

## Requested changes

| ID | Finding | Change | Owner | Status |
|---|---|---|---|---|
| CR-1 | F1 | Count a return only on a later UTC day (`date > first date` and `≤ first date + 30 days`), or rename the metric to make clear it includes same-day repeats. Add the small case to `tests/`. | M5 | Open |
| CR-2 | F2 | On Tab 2, show the M5 row's listen count next to M4's ("based on N of M listens"), or show "n/a" when most of the artist's listens are `key_mbid`. | M5 / app | Open |
| CR-3 | F3 | Make one place the source of truth for the selected artist: before the selectbox, if `selected_artist_id` changed, copy it into `st.session_state.artist_picker`, and drop the `index=` argument. | app | Open |
