# DSO 576 Phase 2 — Member 4: Backend Analysis (KPIs)

## Input and version decision
The input is Member 3's canonical event table `listenbrainz_final_cleaned.csv`, **1,940 rows × 11 columns**. It has five users. I checked that its nine source columns are identical (`DataFrame.equals`) to the frozen Module 6 file `listenbrainz_sample.csv` (SHA-256 `463000bf…`). Every count below therefore lines up with the team's cleaning work.

The canonical file is missing the fields that artist-level metrics need. `load_listens()` / `derive_columns()` in `kpi_analysis.py` add them on load. The canonical file itself is never modified.

| Added column | Rule | Why |
|---|---|---|
| `listen_id` | `username` + `\|` + Unix seconds | Unique listen key (0 repeats) |
| `listen_day` | UTC calendar date of `listened_at_utc` | Active days and returns |
| `artist_name_clean`, `track_name_clean` | Trim + Unicode NFC | Display text |
| `artist_key` | Casefold, drop `" - Topic"`, alias table; placeholder names (`Unknown`, …) become missing | Groups spelling variants of the same name |
| `artist_id`, `artist_id_source` | First artist MBID (`mbid`), else the key's single MBID (`key_mbid`, rule R7b), else `name:<artist_key>` (`name`) | One stable identity per artist |
| `is_countable` | False when the same user replays the same recording < 60 s after the previous play (suspected double-scrobble, R9) | Removes logging errors without deleting rows |

## KPI definitions
These definitions are ready for BUILD_SPEC.md.
- **Scope:** every KPI uses **countable listens with an artist** (1,880 of 1,940).
- **Period filter:** `filter_period(start, end, users)` runs **before** any metric, so every value is "within the selected period". Both dates are inclusive UTC days.
- **Rounding:** output CSVs are rounded to 4 decimals.

| KPI (column) | Level | Question it answers | Source columns | Calculation |
|---|---|---|---|---|
| `countable_listens` | artist, pair | How much is this artist played? | `listen_id`, `is_countable` | Count of rows |
| `unique_listeners` | artist | How many people play it? | `username` | Number of listener × artist pairs |
| `returning_listeners`, `return_rate` | artist | Do listeners come back on another day? | `listen_day` | Pairs with `active_days ≥ 2`; rate = returning ÷ unique |
| `avg_active_days` | artist | How many separate days does a typical listener play it? | `listen_day` | Mean of pair `active_days` |
| `distinct_tracks`, `multi_track_rate` | artist | Do listeners explore beyond one song? | `recording_msid` | Distinct recordings; share of pairs with ≥ 2 recordings |
| `listens_per_listener` | artist | How intense is each listener's engagement? | — | `countable_listens ÷ unique_listeners` |
| `median_days_to_return` | artist, pair (`days_to_return`) | How soon do listeners come back? | `listen_day` | Second active day − first active day (days); median over pairs that returned |
| `return_momentum`, `momentum_pairs` | artist, pair | After discovery, is the artist gaining or losing share of the listener's listening? | `listened_at_utc` | See rule 5 below. Range −1 to 1; 0 = keeps pace with the listener |
| `rank` | artist | Default order of the ranking table | `return_rate`, `avg_active_days`, `countable_listens`, `return_momentum` | Sort by those four (all descending; missing momentum last), tie-break `artist_id`. `unique_listeners` is deliberately not a key: the only 2-listener artists are mainstream overlaps (Queen, Miles Davis) with little engagement |
| KPI cards (`kpi_summary.json`) | dataset | How big is the selection, and how engaged? | all | Listeners, artists, listens, exclusions, pairs, pair return rate, multi-track rate, % artists with a return, artists with momentum, median momentum |

**Shortlist filter, `EmergingFilter`.** It is applied after the KPIs are computed:
- `min_listens`
- `min_avg_active_days`
- `max_listeners`
- `mbid_status` (`any` / `mbid` / `no_mbid`)
- `exclude_artist_ids`: the editor's list of established artists

**`artist_detail(artist_id)`** returns three things for one artist:
- its KPI row
- its listener × artist rows
- a track table

## Consolidated rules
1. **Countable listens only.** The 58 suspected double-scrobbles are kept in the table but excluded from every metric. 41 of them are one looped track by H-music.
2. **Artist rows need an artist.** The 2 countable listens with a placeholder name ("Unknown") are counted in `excluded_missing_artist` and are not dropped silently.
3. **New identity rule R7b** (recorded in `cleaning_rules.md` → Changes to rules):
   - **Problem:** R7 alone split artists whose listens were only partly matched to MusicBrainz. Arthrn appeared as 125 MBID listens plus 57 `name:` listens.
   - **Rule:** if a key has exactly one MBID, its unmatched rows take that MBID.
   - **Effect:** 116 rows change (113 countable) and artists go from 679 to 669. Keys with 2+ MBIDs are left alone.
4. **Multi-artist credits count for the first credited artist.** "Drake, Rihanna" counts as Drake. This keeps one row per listen, so listen counts are never inflated.
5. **Return momentum replaces unique-listener growth.**
   - **Why the change:** 671 of 679 artists have exactly one listener, so growth in unique listeners is flat for almost every artist. The first alternative, listens in the late half vs the early half of each listener's window, came out at exactly ±1 for 84% of pairs. That number reflected *when* the listener discovered the artist, not growth.
   - **Return window:** from midnight UTC after the pair's first listen to the listener's last countable listen.
   - **Momentum:** (share of the pair's return listens that fall in the window's late half) − (the listener's own late-half share over the same window, across all artists).
   - **When it is missing:** NaN unless the pair has ≥ 3 return listens and the window is ≥ 2 days. Both are parameters: `min_return_listens` and `min_return_window_days`.
   - **Artist value:** pooled across pairs, Σ(L − exp·R) ÷ ΣR.
6. **All days are UTC.** Only 1 of 169 returning pairs has every day-change under 12 hours, so a 12-hour gap rule would change only that one.

## Verified results (full data, no period filter)
| Metric | Value |
|---|---|
| Listens: total / countable / with an artist | 1,940 / 1,882 / 1,880 |
| Excluded: double-scrobbles / missing artist | 58 / 2 |
| Listeners / artists / listener × artist pairs | 5 / 669 / 677 |
| Artists with 2+ listeners | 8 |
| Pair return rate / pair multi-track rate | 24.96% / 21.86% |
| Artists with any returning listener | 25.26% |
| Artists with a momentum value / median momentum | 48 / −0.157 |

**Top of the default ranking:** Arthrn (19 active days, 182 listens); Taylor Swift (8, 17); Mixed Matches (7, 12); Sachin-Jigar, Arijit Singh, Amitabh Bhattacharya (7, 11); Diljit Dosanjh (6, 22). Established names such as Taylor Swift are what `exclude_artist_ids` is for.

**Highest momentum:** JAY-Z & Kanye West (+0.61); Run The Jewels (+0.50); Olivia Newton-John and Beatles (+0.47).
**Lowest momentum:** Toshiro Masuda (−0.63); Famous Addonis (−0.45); Dua Lipa (−0.44).

**Checks:**
- **Built into `compute_kpis()`, so every run fails loudly if one breaks:**
  - pair listens = artist listens = 1,880
  - Σ unique listeners = number of pairs
  - countable + excluded = total
  - rates within [0, 1] and momentum within [−1, 1]
  - ranks run 1…n
- **`tests/test_kpi_analysis.py`, 17 tests:**
  - a hand-computed 12-row example
  - empty periods
  - late discovery gives NaN
  - pooled vs mean momentum
  - each filter parameter
  - no mutation of inputs
  - **parity with the Module 6 outputs:** `artist_key` and `is_countable` match on all 1,940 rows, and `artist_id` differs only on the 116 R7b rows. Listen counts per `artist_key` equal `outputs/artist_summary.csv`.
- **Cross-check:** three independent reimplementations (vectorized pandas, plain loops, an edge-case hunt) recomputed all 669 artist rows, all 677 pair rows and all 16 headline values from the definitions above. They matched with **0 differences**.

## Downstream use and limitations
- **Member 5 (aggregations):** import, don't recompute:
  - `load_listens`, `filter_period`, `countable_artist_listens`, `user_windows`
  - `pair_kpis`: `listener_artist_kpis.csv` with flags `returned`, `multi_track`, `return_momentum`
- **Member 2 / BUILD_SPEC:**
  - The UC1 table is `artist_kpis()` and the KPI cards are `headline_kpis()`. UC2/UC3 use `artist_detail()`.
  - The column contract is `ARTIST_COLUMNS` / `PAIR_COLUMNS`.
  - Label the growth metric **"return momentum"** and show "n/a" when it is missing (≈ 93% of artists).
- **Phase 3 app:** functions are pure and framework-free. Cache `load_listens()` and the period-filtered results with `@st.cache_data` in the app layer, keyed by start, end and filter values.
- **Member 3:** consider adding `artist_key`, `artist_id` (with R7b) and `is_countable` to the canonical file. `derive_columns()` would then shrink to type conversion.
- **Limitations:**
  - **Five sampled listeners with non-overlapping windows.** A period filter effectively selects users.
  - **Three users hit the 500-listen cap,** so their windows are cut off at the early end.
  - **A first listen here is not necessarily the listener's true first listen.**
  - **Listener counts can't tell new artists from established ones.** Taylor Swift ranks highly, so the editor's exclude list and the no-MBID flag (188 artists) are the practical levers.
  - **No MusicBrainz metadata (type, area) is joined yet.**
  - **Display names come from free text.**
    - 69 MBID artists show a collaboration spelling (e.g. "Pritam, Arijit Singh"), because `artist_mbids` lists fewer artists than the name does.
    - MBID `99790314…` (TLC) shows as "Creep": an H-music row has track and artist swapped in the source, and the 1–1 tie breaks alphabetically.
    - A MusicBrainz name lookup by MBID would fix both.
