
**Auditor:** Benazira Mussaibekova 
**Feature audited:** UC1, the Shortlist tab's default ranked artist table (`artist_kpis` → `rank_artists` → `apply_emerging_filter`)
**Number audited:** `pair_return_rate` = **0.2496** (the "pair return rate" KPI card)
**Version checked:** `main` branch of `jennzhong/dso576-group-project` at commit `f7032fe` ("Merge pull request #5 from jennzhong/build_spec.md-nita"), data file `listenbrainz_final_cleaned.csv` (1,940 rows)


## 1. Feature audit: the Shortlist as its user would use it

**Intended user and task (BUILD_SPEC §1):** a playlist editor or label A&R curator who wants a shortlist of *lesser-known* artists, ranked by repeat engagement instead of total plays, with "established names" excluded.

**Requirement checked:** the starting view is the Shortlist with default filters (`EmergingFilter()`). It should surface artists that "a small artist with loyal returning listeners becomes visible" describes.

**Reproducible steps:**
```python
import kpi_analysis as k
a = k.artist_kpis(k.load_listens())
print(len(k.apply_emerging_filter(a)))          # rows in the default shortlist
print(a[['rank','display_name','countable_listens','unique_listeners','return_rate','avg_active_days']].head(12))
print(a[a.display_name.str.contains('Arijit', case=False)][['rank','artist_id']])
```

**Results:**

| Check | Expected (from the prompt) | Actual | Verdict |
|---|---|---|---|
| Default shortlist size | A curated short list | **669 of 669** artists (the default filter removes nothing) | Misleading |
| Who is at the top | Lesser-known artists | Ranks 1–12 include **Taylor Swift (#2)**, Diljit Dosanjh (#5), **Arijit Singh (#7)** and Sabrina Carpenter (#9), plus Arijit collaborations at #4, #6 and #10 | Misleading |
| Excluding an established artist | One exclusion removes the artist | Arijit Singh appears under **17 different `artist_id`s** (solo MBID plus multi-artist credit strings such as `name:pritam, arijit singh, amitabh bhattacharya`). Excluding "Arijit Singh" removes only 1 of 17. | Missing |
| Ranking logic | Repeat engagement | Works as written: the sort is `return_rate`, then `avg_active_days`, then listens. But 661 of 669 artists have one listener, so `return_rate` is just 0 or 1 and the rank is effectively **one listener's active days**. | Works, but weak evidence |
| Reconciliation | Totals tie out | `compute_kpis` checks all pass (pair listens = artist listens = 1,880; ranks are 1..669) | Works |

**What works:** the backend is internally consistent. It never ranks by listener count, as the data-limits table requires, and `momentum` is NaN (shown as "n/a"), not 0, for the 621 artists without enough data.

**What is missing or misleading:** with the default settings, a curator opening the tool sees global superstars at the top of an "emerging" list. The only defence is the manual exclude list, and that list can't handle one artist spread across many credit strings. The prompt promises that "a small artist … becomes visible", but by default it's buried under famous names.

## 2. Number audit: `pair_return_rate` = 0.2496

**What it should mean:** of all listener × artist pairs, the share where the listener played that artist on **2 or more distinct UTC days** ("continued engagement").
- **Units:** a proportion (0–1); the card shows it as a %.
- **Numerator:** pairs with `active_days >= 2`.
- **Denominator:** listener–artist pairs built from *countable artist listens*. These exclude double-scrobbles (the same user and recording within 60 s) and placeholder artist names.
- **Sensible range:** 0–1. About 25% is plausible: most pairs are one-off plays.

### Check A: calculated by hand 

Six hand-made listens:

| Pair | Listens | Expected |
|---|---|---|
| A × X | Sep 1 10:00, Sep 3 10:00 | 2 days → returned |
| A × Y | 11:00:00 and 11:00:30, same track | 2nd play is a double-scrobble → 1 countable listen, not returned |
| B × Z | Sep 1 23:50, Sep 2 00:05 (one 15-min session) | 2 UTC days → counted as returned |

My hand result is 2 returned out of 3 pairs = **0.6667**. The team code also gives **0.6667**, so the definition is implemented as written.

### Check B: recompute it another way 
Rebuilt the denominator from the raw CSV in plain pandas:
- countable listens = **1,882** and artist listens = **1,880**, which match `kpi_summary.json`.
- pairs = **677**, returned = **169**, and 169 / 677 = **0.2496**, which matches the card. **Reproduced.**

### Check C: go deeper into the assumptions behind the number

1. **"Return" = a different UTC calendar day (`listen_day` = UTC date).** The toy case shows the weakness: one 15-minute session that crosses UTC midnight counts as a "return". I measured this on the real data. Among the 2-day returned pairs, **0** had their "return" less than 3 hours after the previous listen. Defining a return by time gaps instead gives similar results: a ≥3 h gap gives 0.2600, ≥8 h gives 0.2526 and ≥24 h gives 0.2408. **So this rule does not distort the current number (about ±1.5 points),** but it could with other listeners or time zones.
2. **Artist identity changes the denominator.** Grouping pairs by raw artist name, without the team's MBID merging, gives 752 pairs and a rate of **0.2407**, not 677 pairs and 0.2496. The identity rules (R7/R7b) move the KPI by about 0.9 points. That's small, but the card should say it depends on artist matching.
3. **The number is dominated by a few listeners.** The return rate by listener is iliekcomputers 0.363 (171 pairs), s_john_s 0.241 (278), music_af 0.218 (78), H-music 0.179 (117) and John V 0.061 (33). Two capped listeners make up 449 of the 677 pairs (66%), and listener-level rates range from 6% to 36%. So 0.2496 describes these 5 people's habits. It isn't a general "listeners return 25% of the time" fact. That matches the spec's data-limits rule.

**Conclusion on the number:** `pair_return_rate` is **correct for its written definition** and reproduces independently (0.2496). The main risk is how it's read, not the arithmetic. It's pooled over 5 listeners and dominated by two capped listeners, and it depends slightly on the artist-matching and UTC-day rules.

## 3. Conclusions, uncertainty and change requests

- **Feature (UC1):** works mechanically. But the default view is misleading for the stated user, because established stars rank at the top and one star can't be excluded with a single selection. → **CR-BM-1, CR-BM-2**
- **Number:** correct and reproduced. It needs context on the card. → **CR-BM-3**
- **Untested / remaining uncertainty:** the Streamlit app itself (`app.py` is not on `main`), so formatting, captions and the "N of M artists match" text are unchecked. I didn't run the team's pytest suite (pytest isn't installed in my environment). "Famous artist" is my own judgment, since the data has no popularity field. And I only tested the UTC-day rule on this one extract.

## 4. My contribution and AI use

**What I did:** I chose the feature and number, designed the hand-calculable toy case and the expected results, decided which assumptions to stress-test (UTC-day returns, artist identity, listener concentration), and judged what the results mean for a curator.

**How AI helped:** I used codex to help write the two pandas check scripts. I ran the scripts, compared each output with the team's `kpi_summary.json`, and the conclusions above are mine.

**Reproduce:** from the repo root, run `python audit/toy_return_rate.py` and `python audit/recompute_return_rate.py`. Both scripts are committed in `audit/`.
