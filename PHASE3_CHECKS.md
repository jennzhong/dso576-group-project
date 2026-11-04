# Phase 3 acceptance and deployment checks

Assignment: Project MVP, due November 9. Sources: the supplied Phase 3 project
instructions and Module 11 deployment handout. The host route for this Python
app is Streamlit Community Cloud. The assignment requires private source;
the repository visibility remains a team action.

## Implementation

| Requirement | Evidence |
| --- | --- |
| User and business decision | README describes playlist editors and A&R curators deciding which artists to investigate. |
| Complementary analytical views | Shortlist, Artist detail, and Listeners reuse the team's M4/M5 backends. |
| Meaningful controls | Date/listener filters recompute all views; shortlist controls affect only candidates. Disabled maximum-listener input cannot silently ignore a value. |
| Interpretation | Metric tooltips, UTC/date labels, M4 vs M5 denominator captions, and explicit momentum units. |
| Difficult cases | Empty listeners, empty date windows, empty shortlists, removed artist selections, missing MBID, and missing momentum have messages or fallbacks. |
| Bundled sample | Root canonical CSV; 1,940 rows, five listeners; no live API pull. |
| Runtime/dependency compatibility | Python 3.12, four direct runtime pins, uv.lock, project-relative data/CSS paths. Notebook dependencies are optional. |
| Demo preparation | DEMO_SCRIPT.md supplies a 4–5 minute user-perspective walkthrough with interactions, interpretation, a difficult case, and a limitation. |

## Reference selections for local/live comparison

| Selection | Expected result |
| --- | --- |
| Defaults | 5 listeners, 669 artists, 1,882 countable listens, 677 pairs, 48 artists with momentum. |
| Min avg active days = 2 | 168 shortlist artists; the date/listener headline cards remain unchanged. |
| H-music only, other defaults | 1 listener, 443 countable listens, 117 shortlist artists; listener table has 500 all-logged events. |
| Enable max listeners = 1 | 661 shortlist artists; default headline cards remain unchanged. |
| No-MBID shortlist | 188 candidates; detail shows n/a for MBID-dependent figures. |
| Min listens = 10,000 | Empty shortlist plus recovery guidance; listener analysis remains available. |
| Clear all listeners | Every view reports no listens and explains recovery; no stale tables/charts. |
| 2021-01-01 to 2021-01-31 | No observations and a useful message on all views. |

## Local verification — November 4

- Installed the locked project into a new Python 3.12.14 environment.
- `python -m pytest -q tests`: **32 passed**, with three existing NumPy
  deprecation warnings from the unchanged M5 backend.
- SHA-256 comparisons confirm the canonical CSV, kpi_analysis.py, and
  aggregation_functions.py are unchanged from the earlier working version.
- Evaluated the reference selections above directly with the original backend.
- GitHub currently shows Public source visibility; the user chose to leave
  that setting for the team to resolve against the assignment's private-source requirement.

## Cloud verification — November 4

- Live URL: https://dso576-group-project-a638hnfcszabvqo6mgvwfs.streamlit.app/
- Streamlit successfully cloned the dashboard branch and installed the locked
  dependencies with `uv-sync`; the app rendered without a runtime error.
- Verified live default totals, minimum average active days = 2 giving 168
  candidates, and maximum listeners = 1 giving 661 candidates.
- Changed the artist picker to Taylor Swift and verified 17 countable listens
  and 8 active days. Checked the monthly artist chart and listener charts.
- Clearing all listeners removed the artist results and displayed recovery guidance.
- Reloaded the cloud app successfully after stopping the fresh local preview
  on port 8503. A new HTTP client with no login credentials returned HTTP 200
  for the app and `ok` from `/~/+/_stcore/health`.
- The Streamlit sharing panel's "Make this app public" option is checked.
  Interactive browser QA used the signed-in developer session; a teammate's
  full signed-out browser check on a second device remains to be completed.
- GitHub now redirects the original `jennzhong` repository URL to
  `lewisli1027/dso576-group-project`; the source is still Public.

## Deployment settings

- Current repository: `lewisli1027/dso576-group-project` (original URL redirects here)
- Branch: `dashboard-phase3`
- Main file: `app.py`
- Python: `3.12`
- Secrets: none; never commit `.streamlit/secrets.toml`
- Sharing: public app enabled; private source still required by the assignment
- Dependency manager: Cloud prioritizes the root `uv.lock`

## Remaining submission gates

- Ask a teammate to open and interact with the public URL in a signed-out
  browser on another device.
- Resolve the assignment's private-source requirement and confirm instructor
  repository access. Recheck public app access after any visibility change.
- Record and upload the demo; verify its link without sign-in.
- Replace the pending video entry in README with its verified link.
- Submit all three links on Gradescope, one submission per team, by November 9.

Do not claim these gates passed until the account, deployment, and links have
actually been verified. A local app or a successful cloud build alone does
not satisfy the public-live-app requirement.
