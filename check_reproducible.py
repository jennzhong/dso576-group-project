"""
Module 6 — Reproducibility check.

Re-runs clean_listens.py from the raw file into a fresh temporary folder and
compares the SHA-256 of every new output with outputs/output_checksums.txt
(the submitted files).

    uv run python check_reproducible.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

SUBMITTED = Path("outputs/output_checksums.txt")


def read_checksums(path):
    pairs = (line.split("  ", 1) for line in path.read_text().splitlines() if line)
    return {name: digest for digest, name in pairs}


with tempfile.TemporaryDirectory() as tmp:
    subprocess.run([sys.executable, "clean_listens.py", tmp], check=True)
    fresh = read_checksums(Path(tmp) / "output_checksums.txt")

submitted = read_checksums(SUBMITTED)
all_match = fresh == submitted
for name in sorted(set(fresh) | set(submitted)):
    status = "match" if fresh.get(name) == submitted.get(name) else "DIFFERENT"
    print(f"{status:9}  {name}")
print(f"\nAll {len(submitted)} submitted outputs reproduced exactly: {all_match}")
sys.exit(0 if all_match else 1)
