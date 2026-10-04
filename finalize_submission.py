"""
Finalize the README + Gradescope PDF after the first code/results commit.

Usage:
    python finalize_submission.py <COMMIT_ID>

The commit ID should be the commit that contains the completed cleaning code and generated evidence.
A later small metadata commit can then contain the README/PDF that reference that code/results commit.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


INFO_FILE = Path("submission_info.json")
README_FILE = Path("README.md")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python finalize_submission.py <COMMIT_ID>")

    commit_id = sys.argv[1].strip()
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", commit_id):
        raise SystemExit("Commit ID should be a 7-40 character hexadecimal Git commit hash.")

    info = json.loads(INFO_FILE.read_text(encoding="utf-8"))
    info["commit_id"] = commit_id
    INFO_FILE.write_text(json.dumps(info, indent=2), encoding="utf-8")

    readme = README_FILE.read_text(encoding="utf-8")
    readme = readme.replace("PASTE_CODE_RESULTS_COMMIT_ID_HERE", commit_id)
    README_FILE.write_text(readme, encoding="utf-8")

    subprocess.run([sys.executable, "build_report.py"], check=True)
    print("Finalized submission metadata and rebuilt the PDF.")
    print("Now commit README.md, submission_info.json, and the rebuilt PDF as a small final metadata commit.")


if __name__ == "__main__":
    main()
