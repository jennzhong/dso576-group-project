
### CR-BM-1 — Default shortlist is topped by established stars
- **Finding:** With `EmergingFilter()` defaults, all 669 artists pass and the top 12 include Taylor Swift (#2), Diljit Dosanjh (#5), Arijit Singh (#7) and Sabrina Carpenter (#9).
- **Evidence:** `k.artist_kpis(k.load_listens()).head(12)` at commit f7032fe; `len(k.apply_emerging_filter(a)) == 669`.
- **Requested change:** Ship a starter exclude list of well-known artists (or a "hide established" toggle), and/or make the default `min_avg_active_days` 2 so the default view is an actual shortlist (168 artists). Update A2/A3 checks to match.

### CR-BM-2 — One artist split across many `artist_id`s defeats the exclude list
- **Finding:** "Arijit Singh" appears in 17 artist rows (solo MBID + multi-artist credit strings like `name:pritam, arijit singh, amitabh bhattacharya`). Excluding one removes 1 of 17.
- **Evidence:** `a[a.display_name.str.contains('Arijit', case=False)]` → 17 rows.
- **Requested change:** Let the exclude control match on any credited name (split credit strings on ", " / "&" / "feat.") or add a "exclude all containing…" text filter. Document in BUILD_SPEC §3.

### CR-BM-3 — Pair return rate card needs context
- **Finding:** 0.2496 is correct and reproduces independently (169/677), but it is pooled over 5 listeners; two capped listeners supply 66% of pairs and per-listener rates range 6%–36%. Name-only artist matching would give 0.2407.
- **Evidence:** `audit/recompute_return_rate.py`, `audit/toy_return_rate.py`.
- **Requested change:** Caption the card "share of listener–artist pairs played on 2+ UTC days, across the selected listeners", and show the per-listener breakdown in Tab 3. Optional: note that a session crossing UTC midnight counts as a return (0 cases in current data).
