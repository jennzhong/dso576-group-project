# Dashboard for the deployment class

The working Streamlit application is on the **dashboard-phase3** branch:

https://github.com/jennzhong/dso576-group-project/tree/dashboard-phase3

The branch is pushed to GitHub and proposed in PR #6. It can be run directly
without merging the PR. Select this branch when downloading a ZIP or when
choosing a source branch in class.

## Set up before class

```sh
git clone --branch dashboard-phase3 --single-branch https://github.com/jennzhong/dso576-group-project.git
cd dso576-group-project
uv sync --python 3.12 --locked
uv run pytest -q tests
```

The repository is private, so use your own GitHub account with access. A ZIP
download from the branch page is also supported; unpack it, open a terminal
in that folder, and run the two uv commands. Dependencies and Python must be
installed before class; the application itself uses the committed CSV and
does not need ListenBrainz API credentials or a live data connection.

## Start locally

```sh
bash run_dashboard.sh
```

Open the Local URL printed in the terminal (normally http://localhost:8501).
Keep the terminal running while using the dashboard. Use Ctrl+C to stop it.
If that port is occupied, run `bash run_dashboard.sh --server.port 8502`.

## Two-minute demonstration

1. **Shortlist:** with defaults, show 5 listeners, 669 artists, 1,882 countable
   listens, and 677 listener–artist pairs.
2. Open **Shortlist filters** and set **Min avg active days** to 2. The
   shortlist has 168 artists; the headline cards still describe the full
   date/listener selection.
3. Select **Arthrn** in the ranked table, then open **Artist detail**. Inspect
   its repeat engagement, monthly chart, listener rows, and tracks.
4. Open **Listeners**. Explain the three capped histories and the separate
   daily activity axes for each listener's observation window.

The frozen canonical input is `listenbrainz_final_cleaned.csv` (1,940 rows).
M4/M5 retain the team's calculation rules. The interface, source data,
dependencies, and tests are all in this repository. These steps cover local
class preparation. The November 9 Phase 3 submission additionally requires a
public, no-login deployment and a viewable demo video; follow README and
PHASE3_CHECKS.md before submitting.
