#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m PyInstaller --noconfirm --clean gh-img-resize.spec

if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "Built dist/gh-img-resize.app"
else
  echo "Built dist/gh-img-resize"
fi
