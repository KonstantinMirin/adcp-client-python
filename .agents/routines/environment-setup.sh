#!/bin/bash
# Cloud environment setup for adcp-client-python routines.
# Paste into the "Setup script" field when creating the routine's
# environment at claude.ai/code/routines. Runs as root on Ubuntu 24.04;
# result is cached ~7 days.

set -euo pipefail

# gh CLI for `gh issue`, `gh pr create`, etc. — not pre-installed.
apt-get update
apt-get install -y gh

# Install the package with dev extras (pytest, mypy, black, ruff, etc.).
# Python 3.x + pip are pre-installed.
if [ -f pyproject.toml ]; then
  pip install -e ".[dev]"
fi

echo "Setup complete."
