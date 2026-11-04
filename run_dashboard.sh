#!/usr/bin/env bash
# Start from the repository root so the data and Streamlit theme resolve correctly.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$project_dir"

if .venv/bin/python -c 'import streamlit' >/dev/null 2>&1; then
  exec .venv/bin/python -m streamlit run app.py "$@"
fi

if command -v uv >/dev/null 2>&1; then
  uv sync --python 3.12 --locked
  exec uv run --frozen streamlit run app.py "$@"
fi

printf '%s\n' 'Install Python 3.12 and uv, then run:' \
  '  uv sync --python 3.12 --locked' \
  '  uv run streamlit run app.py' >&2
exit 1
