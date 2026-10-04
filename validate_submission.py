"""
Quick pre-submission check. Run after finalize_submission.py.
"""

from pathlib import Path
import json
import re

REQUIRED = [
    "pull_listenbrainz_sample.py",
    "clean_listenbrainz.py",
    "build_report.py",
    "module6_cleaning.ipynb",
    "requirements.txt",
    "README.md",
    "submission_info.json",
    "cleaned_sample_50.csv",
    "cleaning_decision_log.csv",
    "record_checks.csv",
    "cleaning_summary.json",
    "checklist.json",
    "checklist_evidence.md",
    "Shivanee_Kooner_Module6_Cleaning_Report.pdf",
]

missing = [name for name in REQUIRED if not Path(name).exists()]
if missing:
    print("MISSING REQUIRED FILES:")
    for name in missing:
        print(" -", name)
    raise SystemExit(1)

info = json.loads(Path("submission_info.json").read_text())
commit_id = info.get("commit_id", "")
if not re.fullmatch(r"[0-9a-fA-F]{7,40}", commit_id):
    print("submission_info.json still has a missing/invalid commit ID.")
    raise SystemExit(1)

readme = Path("README.md").read_text()
if "PASTE_CODE_RESULTS_COMMIT_ID_HERE" in readme:
    print("README still contains the commit placeholder.")
    raise SystemExit(1)

print("Submission check passed.")
print("Branch:", info.get("branch_name"))
print("Branch URL:", info.get("branch_url"))
print("Submitted cleaning commit:", commit_id)
