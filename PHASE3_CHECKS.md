# Phase 3 acceptance and deployment checks

Assignment: Project MVP, due November 9. Sources: the supplied Phase 3 project
instructions and Module 11 deployment handout. The host route for this Python
app is Streamlit Community Cloud; the team GitHub repository stays private.

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
- Public deployment and anonymous live-link checks are deferred at the user's request.
- GitHub currently shows Public source visibility; the user chose to leave
  that setting for the team to resolve against the assignment's private-source requirement.

## Deployment settings

- Repository: `jennzhong/dso576-group-project`
- Branch: `dashboard-phase3`
- Main file: `app.py`
- Python: `3.12`
- Secrets: none; never commit `.streamlit/secrets.toml`
- Sharing: public app, private source repository
- Dependency manager: Cloud prioritizes the root `uv.lock`

## Remaining submission gates

- Complete Streamlit sign-in/account authorization and private-repository access.
- Deploy, read logs if needed, and record the actual `.streamlit.app` URL.
- Verify anonymous access while the laptop server is stopped. Compare the
  reference selections above and check a live chart and artist selection.
- Ask a teammate to open the public URL on another device.
- Record and upload the demo; verify its link without sign-in.
- Replace the pending app/video entries in README with verified links.
- Submit all three links on Gradescope, one submission per team, by November 9.

Do not claim these gates passed until the account, deployment, and links have
actually been verified. A local app or a successful cloud build alone does
not satisfy the public-live-app requirement.
