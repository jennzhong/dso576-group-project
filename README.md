# Discovery Atlas: Emerging Artist Discovery

**User and decision:** playlist editors and label A&R curators deciding which
artists deserve a closer look based on repeat engagement in the sample.
Rankings emphasize listening depth, rather than treating play totals or a
handful of sampled listeners as market popularity.

- **Live app:** [Open Discovery Atlas](https://dso576-group-project-a638hnfcszabvqo6mgvwfs.streamlit.app/) — deployed November 4; public access enabled.
- **Demo video:** recording pending; use the [4–5 minute walkthrough script](DEMO_SCRIPT.md), then replace this line with its viewable link.
- **Repository:** https://github.com/lewisli1027/dso576-group-project (the previous `jennzhong` URL now redirects here).
- **App branch:** `dashboard-phase3` ([PR #6](https://github.com/lewisli1027/dso576-group-project/pull/6)).
- **Optional course showcase preference:** Decide later; all-member agreement has not been confirmed.
- **Repository visibility:** GitHub showed Public on November 4. The assignment requires private source; the team will resolve this setting before submission.

## Core experience

1. **Shortlist** combines seven headline KPIs with a ranked artist table.
2. **Artist detail** connects a selected artist's return rate, active days,
   momentum, monthly listening, listeners, and tracks.
3. **Listeners** explains observation windows and capped histories with
   individual daily activity charts and a monthly sample-coverage chart.

UTC dates and listener selections update all views. Shortlist criteria affect
only the ranked table and artist picker; the cards continue to describe the
date/listener selection. Empty selections explain how to recover. Hover over
metric help icons for definitions and units. [Usage details](DASHBOARD.md).

## Run locally

Use **Python 3.12** and run from the repository root:

```sh
uv sync --python 3.12 --locked
bash run_dashboard.sh
```

Or create a Python 3.12 virtual environment, install `requirements.txt`, and
run `python -m streamlit run app.py`. No API key, database, or secrets are needed.
For tests use `uv run pytest -q tests`. Notebook tools remain available through
`uv sync --group notebooks`; they are not production app dependencies.

## Streamlit Community Cloud deployment

Keep this team repository **private**. Grant Streamlit access to this repository
through your own GitHub account, then create an app with:

| Setting | Exact value |
| --- | --- |
| Repository | `lewisli1027/dso576-group-project` |
| Branch | `dashboard-phase3` |
| Main file path | `app.py` |
| Python version (Advanced settings) | `3.12` |
| Secrets | None |
| App sharing | Public: accessible without signing in |

The repository contains the CSV, CSS, `.streamlit/config.toml`, and modules the
app reads. All paths resolve relative to the project, not this laptop. Cloud
prioritizes `uv.lock`; `requirements.txt` mirrors the same four direct runtime
pins. No custom build command or separate API service is needed.

The November 4 deployment passed live checks for the default totals, two
shortlist filters, artist selection, artist/listener charts, and empty-listener
recovery. With the fresh local preview stopped, a separate HTTP client without
login credentials reached the app and received `ok` from its health endpoint.
Streamlit's sharing panel shows public access enabled. Ask a teammate to test
the full app in a signed-out browser on another device, and keep the deployment
available through peer review. [Verification details](PHASE3_CHECKS.md).
[Official deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Data scope and limitations

The app bundles the team's **frozen 1,940-row sample of five public ListenBrainz
listeners**, in `listenbrainz_final_cleaned.csv` at the repository root. Source
listening records are CC0 as documented in [project-start.md](project-start.md).
Observations span **2019-03-07 to 2026-09-21**, with different and mostly
non-overlapping listener windows. It is a sample, not the full ListenBrainz
dataset. No new API extract is fetched at runtime or merged into this version.

Default results: **1,882 countable listens**, **669 artists**, **677
listener–artist pairs**, and **48 artists with sufficient momentum evidence**.
Suspected double-scrobbles are excluded from M4 metrics; two countable listens
have placeholder artist identities and are excluded from artist metrics.

- Five listeners cannot establish market popularity or audience growth.
- Three histories reach the 500-listen extraction cap; their last observed
  play does not establish an end of engagement.
- "Emerging" means curator filters and exclusions, not external popularity metadata.
- Missing MBIDs retain a name-based identity. M5 artist figures cover only
  MBID-matched rows and all logged listens; M4 uses countable listens and may
  infer identity. The two views have different denominators.
- M4 return rate requires two distinct UTC days; M5 30-day return includes
  any later logged play within 30 days, including same-day repeats.
- First observed listens are not necessarily true first listens. Missing
  momentum is `n/a`, never zero.

The original backend definitions and canonical data remain unchanged.
Cleaning provenance: [cleaning_integration_log.md](cleaning_integration_log.md).

## Submission

By **November 9**, submit the live app, viewable demo video, and GitHub links
on Gradescope (one submission per team). The app and video must open without
sign-in. Once the team restores private source visibility, confirm the
instructor has GitHub access. See [PHASE3_CHECKS.md](PHASE3_CHECKS.md) for the
validation matrix and remaining submission steps.
