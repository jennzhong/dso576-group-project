# Fresh-Agent Test Log

**Method:** a new coding-agent session (VS Code Copilot, no prior context) was given the repo and this prompt:

> Read BUILD_SPEC.md and the repo. Before writing any code, list every question you would need answered and every assumption you would have to make to build the dashboard.

## Run 1 — 2026-10-18

| # | Agent's question or guess | Fix made |
|---|---|---|
| 1 | UC3 says weekly new-vs-repeat listening, but Tab 3 and M5 provide daily activity | UC3 now says daily activity, matching M5 `build_daily_activity` |
| 2 | Monthly artist chart pools calendar months, which conflicts with "no combined calendar timeline" | Rule narrowed: never several listeners on one calendar axis; single-artist monthly chart allowed (661 of 669 artists have one listener) and captioned with its listener(s) |
| 3 | M5 ignores M4's inferred `key_mbid` rows | Spec states M5 artist figures cover MBID-matched listens only and must be captioned so |
| 4 | Does a row click auto-navigate to Tab 2? | Row selection stores `artist_id`; Streamlit can't switch tabs, so the curator opens Tab 2 |
| 5 | Which filters affect which tabs and KPI cards? | Added a filter-scope rule: date/listener filters apply everywhere; shortlist filters only to the table and Tab 2 picker |
| 6 | What happens when the selected artist is filtered out, or the shortlist is empty? | Fallback to the top-ranked artist; empty-state messages specified |
| 7 | Exclude-by-display-name when names collide | Options are `artist_id`s shown by name, with an ID suffix on collisions |
| 8 | `requirements.txt` has merge-conflict markers; which manifest is authoritative? | `pyproject.toml` + `uv.lock` declared authoritative; conflict markers removed from `requirements.txt` |
| 9 | Branding, screen sizes, deployment? | Added an explicit out-of-scope line |

The agent also assumed (correctly) that the untracked `data/` folder holds an old 2,214-row extract; the spec now says to ignore it.

## Run 2 — 2026-10-18

| # | Agent's question or guess | Fix made |
|---|---|---|
| | | |

**Result:** (fill in after Run 2)