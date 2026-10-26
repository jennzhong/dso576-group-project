# Change Requests

## Claims

- Jennifer Zhong audited the presence of the promised editorial dashboard at commit `7206e9799ebf043e971a6e7f3e8c25b39942fd39`; the dashboard is absent from the repository.
- Jennifer Zhong independently checked the artist-performance total listen count: 1,940 source rows and 1,940 in the generated output (`audit/audit_check.py`).

## Findings

### CR-JZ-01 — Deliver the editorial dashboard

- **Expected:** The repository contains a runnable dashboard for editorial users to explore artist performance and audience/engagement patterns, as described in `project-start.md`.
- **Actual:** The checked commit contains aggregation code and CSV outputs, but no Streamlit App code or App prompt.
- **Evidence:** `git ls-files`/repository file inspection at commit `7206e9799ebf043e971a6e7f3e8c25b39942fd39`; only `member5-aggregations/aggregation_functions.py` and generated output tables provide dashboard data. See `audit/my-audit.md`.
- **Requested Change:** Add and document a runnable dashboard that presents the prepared artist metrics and supports the editorial team's stated exploration task.
