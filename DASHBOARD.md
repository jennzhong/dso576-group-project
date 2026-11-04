# Emerging Artist Discovery Dashboard

Interactive Phase 3 implementation of `BUILD_SPEC.md`, using the committed
1,940-row `listenbrainz_final_cleaned.csv` and the existing Member 4/5 backends.

## Run

From the repository root, with [uv](https://docs.astral.sh/uv/) installed:

```sh
uv sync --python 3.12
uv run streamlit run app.py
```

Or use Python 3.12 with `pip install -r requirements.txt`, then
`streamlit run app.py`. The locked uv environment is the reference environment.

## Use

1. Start on **Shortlist** in the left navigation. The date/listener toolbar applies to all tabs. The seven
   cards summarize that selection; shortlist criteria only filter the ranked
   table and Artist detail picker. Minimum average active days of 2 gives 168
   artists with the other defaults unchanged.
   Open **Shortlist filters** to adjust the advanced criteria or exclude artists.
2. Select an artist row, then open **Artist detail**. The picker also allows
   direct selection. Filters that remove that artist select the top remaining
   artist. Artist IDs are available in an explicit table column for identity
   inspection because Streamlit's native selectable table has no per-cell
   custom hover API.
3. Open **Listeners** for observation windows, a capped-history label, daily
   activity charts on separate date axes, and monthly sample coverage. The
   listener picker narrows the daily charts only.

Empty date/listener selections and empty shortlists have separate messages.
Missing momentum is `n/a`; name-only artists retain their M4 metrics and show
`n/a — no MBID` for M5 artist figures. M5 values are labeled **all logged
listens**, with **MBID-matched listens** on artist figures. A first observed
listen is not necessarily the true first play. Capped histories must not be
read as an end of engagement. This small sample is not a popularity measure.

## Validate

```sh
uv run pytest -q tests
```

The existing backend checks remain unchanged. `tests/test_app.py` exercises
default totals, capped labels, shortlist-only filter scope, cross-tab listener
filters, empty states, name-only artists, and selection fallback through the
Streamlit testing API. Browser QA should additionally select a table row and
confirm that Artist detail follows it.

No data is fetched from ListenBrainz, no CSV is rewritten, and the M4/M5 metric
definitions are unchanged. The Phase 3 assignment requires a public deployment;
use the exact Streamlit Community Cloud settings in README and verify the
live app against PHASE3_CHECKS.md.

## Visual design

The interface uses a forest-green navigation rail, warm paper background,
serif headings, bordered metric cards, and matching green/copper chart colors.
`dashboard.css` contains the presentation styles; `.streamlit/config.toml`
sets a consistent light theme for native widgets and data tables. On narrower
screens the navigation becomes a horizontal tab row. All three views, metric
values, backend functions, filter defaults, and canonical data remain the same.
