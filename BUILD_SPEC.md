# BUILD_SPEC — Emerging Artist Discovery Dashboard
## 1. Vision & Use Cases
- **User:** a music editorial curator (streaming-playlist editor or label A&R) looking for lesser-known artists to feature.
- **Decision:** which artists to shortlist, based on whether listeners came back to them, not on how many plays they have.
- **Why this beats current practice:** curators usually rank by total plays, which favors artists who are already big. This tool ranks artists by repeat engagement (return rate, active days, return momentum) and lets the curator exclude established names, so a small artist with loyal returning listeners becomes visible.

| # | User selects/inputs → | Dashboard shows → | User decides |
|---|---|---|---|
| UC1 | Date range, listeners, and shortlist filters (min listens, min avg active days, max listeners, MBID status, artists to exclude) | KPI cards and the ranked artist table | Which artists go on the shortlist |
| UC2 | One artist from the table | That artist's KPIs, a per-listener timeline of plays, its listener rows and its tracks | Whether the engagement is sustained or a one-off |
| UC3 | The Listeners tab (optionally one listener) | Per-listener summary and each listener's daily activity | Which listeners' habits are reliable early signals, and how much to trust each one's data |

## 2. Data
- **Canonical file:** `listenbrainz_final_cleaned.csv` (repo root), produced by `final_cleaning.py` from `listenbrainz_sample.csv`. 1,940 rows, 11 columns, 5 users.
- **Source version:** this committed file is canonical. Do **not** re-run `pull_listenbrainz_sample.py`: it fetches each user's latest listens, so every pull differs (team pulls gave 1,940 and 2,214 rows). The team chose the cleaned, validated 1,940-row extract.
- **Grain:** one row = one listen, unique on `username + listened_at + recording_msid`.
- **Columns:** 9 source fields (`username`, `listened_at`, `track_name`, `artist_name`, `release_name`, `recording_msid`, `artist_mbids`, `recording_mbid`, `release_mbid`) plus `listened_at_utc` (UTC time; used for all time logic) and `artist_mbids_parsed` (JSON list).
- **Derived on load** by `kpi_analysis.load_listens()`; the file itself is never changed:

| Column | Rule |
|---|---|
| `listen_day` | UTC date of `listened_at_utc` |
| `artist_id` | First artist MBID; else the single MBID seen for that name (rule R7b); else `name:<normalized name>`. **The artist key everywhere.** |
| `artist_name_clean`, `display_name` | Trimmed name; most common spelling shown in tables |
| `is_countable` | False for a suspected double-scrobble (same user and recording within 60 s). Kept in the table, excluded from every metric. |

- **Definitions:**
  - **Countable artist listen:** `is_countable` and the artist name is not a placeholder (1,880 rows).
  - **Continued engagement:** a listener plays the artist on 2 or more distinct UTC days (`returned` in `pair_kpis`).
  - **Emerging artist:** an artist that passes the curator's `EmergingFilter` (Section 3). The data has no popularity metadata, so "emerging" is the curator's filter plus exclude list, applied to repeat-engagement evidence.
- **Ignore** any untracked `data/` folder (an old 2,214-row extract); the app uses only the root CSV.
- **Decision records:** `cleaning_integration_log.md` (cleaning), `kpi_analysis_log.md` (KPI rules), `validation_summary.json`, `user_observation_summary.csv`.

**Data limits. Every view must respect these.**

| Finding | Rule for views |
|---|---|
| 5 users with non-overlapping windows (2019 ×2, 2024, 2025–26, 2026) | Never put several listeners on one shared calendar axis. Listener charts are one small chart per listener, each on its own dates. The single-artist monthly chart (Tab 2) may use calendar months because 661 of 669 artists have one listener; its caption lists the usernames from `artist_detail(...).listeners` for the current filters. Results are listener-level evidence, not market trends. |
| 3 users hit the 500-listen extract cap (H-music, iliekcomputers, s_john_s) | Show a "capped" badge wherever these listeners appear. Their histories are cut off, so never read their last listen as the end of engagement. |
| 661 of 669 artists have one listener | Never rank by listener count. Ranking uses depth of engagement (`rank_artists`). |
| `return_momentum` exists for only 48 artists | Show "n/a" when missing; never treat it as 0. |
| 39% of rows lack an artist MBID | Identity uses `artist_id` (name fallback); never drop rows without an MBID. |
| First listen here is not necessarily the listener's true first listen | Label it "first observed listen". |

## 3. Dashboard

**Layout:** sidebar filters + three tabs. **Starting view:** the Shortlist tab with all filters at their defaults (full period, all listeners, default `EmergingFilter()`).

**Sidebar filters (apply to every tab)**

| Control | Default | Passed to |
|---|---|---|
| Date range (UTC days) | full data range | `filter_period(listens, start, end, users)` |
| Listeners (multi-select, capped ones marked) | all 5 | `filter_period(..., users=...)` |
| Min listens | 1 | `EmergingFilter.min_listens` |
| Min avg active days | 1.0 | `EmergingFilter.min_avg_active_days` |
| Max listeners | none | `EmergingFilter.max_listeners` |
| MBID status | any | `EmergingFilter.mbid_status` (`any` / `mbid` / `no_mbid`) |
| Exclude artists (multi-select; options are `artist_id`s shown as `display_name`, with the first 8 characters of `artist_id` appended when two artists share a name) | none | `EmergingFilter.exclude_artist_ids` |

**Filter scope.** Date range and Listeners apply to every tab: `filter_period` runs first and every function receives its output. The five shortlist controls (`EmergingFilter`) apply only to the Shortlist table and the Tab 2 artist picker; they do not change the KPI cards or Tab 3. Under the table, show "N of M artists match the shortlist filters".

**Tab 1 — Shortlist (UC1, starting view)**

| Element | Question it answers | Source | Calculation | Function |
|---|---|---|---|---|
| KPI cards: listeners, artists, countable listens, listener–artist pairs, pair return rate, % artists with a return, artists with momentum | How big is the selection and how engaged is it? | filtered listens | as named | `headline_kpis(listens, pairs, artists)` |
| Ranked artist table: rank, display_name, countable_listens, unique_listeners, return_rate, avg_active_days, distinct_tracks, median_days_to_return, return_momentum | Which artists show the strongest repeat engagement? | `artist_kpis(listens)` | Sorted by `rank`; rows filtered by `apply_emerging_filter(artists, EmergingFilter(...))` | `artist_kpis`, `apply_emerging_filter` |

Selecting a table row (`st.dataframe(..., on_select="rerun", selection_mode="single-row")`) stores its `artist_id` in `st.session_state`; the curator then opens Tab 2, which shows that artist. Streamlit cannot switch tabs programmatically, so no automatic navigation. If the shortlist is empty, show "No artists match these filters" instead of the table.

**Tab 2 — Artist detail (UC2)**

| Element | Question it answers | Function |
|---|---|---|
| Artist picker (defaults to the selected or top-ranked artist) | — | options from the filtered artist table |
| KPI row for the artist: countable_listens, unique_listeners, return_rate, avg_active_days, distinct_tracks, return_momentum | How engaged are its listeners? | M4 `artist_detail(listens, artist_id).summary` |
| 30-day return and depth: `return_rate_pct`, `share_3plus_days_pct`, `share_3plus_tracks_pct` | Do listeners come back soon and go deep? | M5 `build_artist_engagement(events)` row where `artist_mbid == artist_id`; show "n/a — no MBID" when `artist_id` starts with `name:` |
| Bar chart: x = `month`, y = `total_listens`, hover `unique_listeners` | Is listening sustained across months or a one-off? | M5 `build_artist_monthly_growth(events)` rows for the same `artist_mbid` (same "n/a" rule) |
| Listener table: username, countable_listens, active_days, days_to_return, return_momentum | Who is driving it? | M4 `artist_detail(...).listeners` |
| Track table | Is it one song or several? | M4 `artist_detail(...).tracks` |

`events = build_artist_listen_events(listens)` is computed once per filter state and passed to both M5 artist functions. M5 uses only each row's own MBIDs, so its artist figures cover MBID-matched listens only (M4's inferred `key_mbid` rows are not included); caption them "MBID-matched listens".

**Invalid selection:** if a filter change removes the selected artist, Tab 2 falls back to the top-ranked artist in the current shortlist; if the shortlist is empty, Tab 2 shows "No artist selected".

**Tab 3 — Listeners (UC3)**

| Element | Question it answers | Function |
|---|---|---|
| Listener table: total_listens, first/last listen ("first observed listen"), observation_days, active_days, unique_artists, listens_per_active_day, repeat_listen_pct, plus a "capped" badge for H-music, iliekcomputers, s_john_s | How much data does each listener give us, and how repetitive are they? | M5 `build_listener_engagement(listens)` |
| Daily activity: one small line chart per listener (x = `date` within that listener's own window, y = `total_listens`, second line `unique_artists`) | Is this listener exploring or repeating? | M5 `build_daily_activity(listens)` |
| Observation coverage: bar chart of `active_listeners` by `month`, titled "Sampled listeners active per month" (not "growth") | When does each part of the sample come from? | M5 `build_audience_growth(listens)` |

**Formatting:** rates as percentages with 1 decimal; momentum with 2 decimals and "n/a" when missing; dates as YYYY-MM-DD; table hover shows `artist_id`. When the filtered listens are empty, every tab shows "No listens in this period" instead of calling the functions.

**Out of scope for the MVP:** branding, mobile layout, authentication, saved filter settings and deployment configuration. Build for a desktop browser with Streamlit's default theme.

## 4. Architecture

Data flows one way: `listenbrainz_sample.csv → final_cleaning.py → listenbrainz_final_cleaned.csv → kpi_analysis.load_listens() → filter_period() → M4 KPI functions + M5 aggregation functions → app.py`

| Module | Owner | Job | Input → Output |
|---|---|---|---|
| `final_cleaning.py` | M3 | Raw → canonical CSV + validation files | raw CSV → canonical CSV |
| `kpi_analysis.py` | M4 | Load + derive columns; period filter; artist ranking and KPIs | path → listens; listens → KPI DataFrames/dicts |
| `member5-aggregations/aggregation_functions.py` | M5 | Chart-ready listener and artist aggregations | listens → DataFrames |
| `app.py` (Phase 3) | — | Layout, controls, charts only | calls the functions above |
| `tests/` | M4, M6 | `test_kpi_analysis.py` (M4), `test_spec_checks.py` (Section 7 checks) | — |

The M5 folder name contains a hyphen, so `app.py` and the tests import it with `sys.path.insert(0, str(ROOT / "member5-aggregations"))` and then `import aggregation_functions as m5`. Do not rename or move M5's files.

**Function contract**

| Owner | Function | Returns |
|---|---|---|
| M4 | `load_listens(path=DEFAULT_INPUT)` | listens DataFrame (canonical + derived columns) |
| M4 | `filter_period(listens, start=None, end=None, users=None)` | filtered copy |
| M4 | `pair_kpis(listens)` / `artist_kpis(listens)` | listener × artist rows (`PAIR_COLUMNS`) / artist rows (`ARTIST_COLUMNS`) |
| M4 | `headline_kpis(listens, pairs, artists)` | dict of JSON-ready values |
| M4 | `apply_emerging_filter(artists, EmergingFilter(...))` | filtered artist table |
| M4 | `artist_detail(listens, artist_id)` | `(summary, listeners, tracks)`; raises `KeyError` if absent |
| M5 | `build_listener_engagement(listens)` | one row per listener |
| M5 | `build_daily_activity(listens)` | one row per date × listener |
| M5 | `build_audience_growth(listens)` | one row per calendar month |
| M5 | `build_artist_listen_events(listens)` | one row per listen × credited artist MBID |
| M5 | `build_artist_engagement(events)` / `build_artist_monthly_growth(events)` | one row per MBID / per MBID × month |

**Linking M4 and M5:** for artists whose `artist_id_source` is `mbid` or `key_mbid`, `artist_id` equals M5's `artist_mbid`. M4 is the source of truth for ranking and identity; M5 adds per-listener activity and MBID-level depth metrics. M5 counts all listens (it does not apply M4's double-scrobble rule), so M5 listen counts can be slightly higher than M4's; label M5 values as "all logged listens".

**Rules**
1. Only `load_listens()` reads the canonical file in the app. (M5's `generate_outputs()` reads it only for its batch CSV export and is not used by the app.)
2. Every function takes DataFrames, returns new ones, and never modifies its inputs, prints or keeps global state.
3. `app.py` performs no metric calculations; every number on screen comes from one function in the table above.
4. Returned column names are the contract. A change updates the function, its test and this section together.

Changing a metric touches only its function and test; changing the layout touches only `app.py`.

## 5. Technical Choices

| Choice | Why |
|---|---|
| Python 3.12 via `uv` (`uv sync --python 3.12`, then `uv run ...`); `pyproject.toml` + `uv.lock` are the dependency source of truth | `kpi_analysis.py` needs 3.10+; the macOS system `python3` (3.9) fails, and pandas 2.2.3 does not build on 3.14 |
| CSV in the repo, no database | Small, static data versioned with the code |
| Streamlit + Plotly | Fast to build interactive tabs, filters and hover; runs locally with `streamlit run app.py` and deploys to Streamlit Community Cloud |
| `@st.cache_data` on `load_listens()` and on the filtered KPI results, keyed by the filter values | Data loads once; filter changes stay responsive |
| `st.session_state` holds only the selected `artist_id` | The one cross-tab state; everything else is recomputed from the filters |
| Paths from `pathlib` relative to the module (`DEFAULT_INPUT`) | Runs the same from any working directory and when deployed |
| pytest | Backend checked without the UI |

## 6. Build Order

| Step | Build | Done when |
|---|---|---|
| 1 | `uv sync --python 3.12`, then `uv add streamlit plotly pytest` | `uv run pytest -q tests` passes (23 tests) |
| 2 | `app.py` shell: page title, sidebar filters, cached `load_listens()` | A1 passes |
| 3 | Tab 1: KPI cards + ranked table with `EmergingFilter` | A2, A3 pass |
| 4 | Tab 2: artist picker, KPI row, timeline, listener and track tables; row click → Tab 2 | A4 passes |
| 5 | Tab 3: listener table, per-listener daily charts, monthly coverage chart | A5 passes |
| 6 | Data-limit labels (capped badge, "n/a", "first observed listen") and formatting | A6 passes |

## 7. Acceptance Checks

**Data and backend** (automated in `tests/test_spec_checks.py` and `tests/test_kpi_analysis.py`; run `uv run pytest -q tests`)
- [ ] D1 `load_listens()` returns 1,940 rows. D2 No duplicate `username + listened_at + recording_msid`. D3 `listened_at_utc` is UTC with no missing values. D4 5 users.
- [ ] D5 Unfiltered KPIs: 1,882 countable listens, 1,880 artist listens, 669 artists, 677 listener–artist pairs.
- [ ] D6 Capped listeners = H-music, iliekcomputers, s_john_s.
- [ ] B1 `uv run pytest -q tests` passes.
- [ ] B2 Every function named in Section 3 exists with the signature in Section 4.
- [ ] B3 Functions are repeatable and do not modify their input.
- [ ] B4 A date range with no listens returns empty M4 tables, and the app shows "No listens in this period" without calling M5.
- [ ] B5 `app.py` never calls `read_csv`; the app loads data only through `load_listens()`.

**App**
- [ ] A1 `streamlit run app.py` opens on the Shortlist tab in under 3 seconds locally, with no errors.
- [ ] A2 With default filters the KPI cards show 5 listeners, 669 artists and 677 pairs.
- [ ] A3 Changing any filter updates the cards and the table; setting min avg active days = 2 leaves 168 artists.
- [ ] A4 Selecting the rank-1 row, then opening Tab 2, shows that artist with its KPI row equal to `artist_kpis(...)` rank 1.
- [ ] A5 Tab 3 lists 5 listeners with exactly 3 capped badges; Tab 2 for Arthrn shows its M5 30-day return row.
- [ ] A6 No chart puts several listeners on one calendar axis; momentum shows "n/a" where missing; M5 artist figures are captioned "MBID-matched listens".