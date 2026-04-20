#!/usr/bin/env bash
# One-time setup for the skill-build harness. Idempotent.
# Creates a shared venv, installs the SDK editable, warms npx cache,
# and checks the skill-build port range (3001-3020).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
PY="$VENV/bin/python"

echo "[setup] root=$ROOT"
if [[ ! -x "$PY" ]]; then
  echo "[setup] creating venv at $VENV"
  "${PYTHON:-python3}" -m venv "$VENV"
fi

if ! "$PY" -m pip --version >/dev/null 2>&1; then
  "$PY" -m ensurepip --upgrade >/dev/null 2>&1 || \
    curl -sSL https://bootstrap.pypa.io/get-pip.py | "$PY"
fi
"$PY" -m pip install --quiet --upgrade pip
"$PY" -m pip install --quiet -e "$ROOT"
"$PY" -c "import adcp, adcp.server" >/dev/null
echo "[setup] adcp installed"

echo "[setup] warming npx cache for @adcp/client"
npx -y -p @adcp/client adcp storyboard list >/dev/null

busy=()
for port in $(seq 3001 3020); do
  lsof -iTCP:"$port" -sTCP:LISTEN -n -P >/dev/null 2>&1 && busy+=("$port")
done
(( ${#busy[@]} > 0 )) && echo "[setup] WARN: ports in use: ${busy[*]}"

mkdir -p "$ROOT/.context/dx-runs"
echo "[setup] done"
