#!/usr/bin/env bash
# Run one skill against one storyboard.
# Usage: bash scripts/skill-run.sh <skill> <port> <storyboard>
# Reads .context/dx-runs/<skill>/agent.py, writes <storyboard>.json next to it.
set -euo pipefail

SKILL="${1:?skill name required}"
PORT="${2:?port required}"
STORY="${3:?storyboard id required}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
RUN_DIR="$ROOT/.context/dx-runs/$SKILL"
AGENT="$RUN_DIR/agent.py"
OUT="$RUN_DIR/$STORY.json"
LOG="$RUN_DIR/agent.log"

[[ -f "$AGENT" ]] || { echo "[run] missing $AGENT"; exit 2; }
[[ -x "$PY" ]] || { echo "[run] venv missing — run scripts/skill-build-setup.sh"; exit 2; }
mkdir -p "$RUN_DIR"

echo "[run] $SKILL :$PORT $STORY"
# Spawn the venv python directly by absolute path so no shell wrapper sits
# between us and the child. $! is then the real server PID, killable directly.
ADCP_PORT="$PORT" "$PY" "$AGENT" >"$LOG" 2>&1 &
PID=$!
cleanup() {
  kill "$PID" 2>/dev/null || true
  wait "$PID" 2>/dev/null || true
  # Belt-and-suspenders: drop anything still holding the port.
  lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT

URL="http://localhost:$PORT/mcp"
# Readiness: full MCP initialize. tools/list without a session returns 400,
# so only a 200 on initialize proves the agent is really serving.
INIT='{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"skill-run","version":"1"}}}'
for i in $(seq 1 60); do
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST \
    -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
    -d "$INIT" "$URL" 2>/dev/null || echo 000)
  [[ "$code" == "200" ]] && break
  kill -0 "$PID" 2>/dev/null || { echo "[run] agent died before ready"; tail -n 40 "$LOG"; exit 3; }
  sleep 0.5
  [[ "$i" == 60 ]] && { echo "[run] agent never initialized (last=$code)"; tail -n 40 "$LOG"; exit 3; }
done
echo "[run] agent ready"

set +e
npx -y -p @adcp/client adcp storyboard run "$URL" "$STORY" --json >"$OUT"
RC=$?
set -e

# The storyboard runner exits 0 even on partial/failing overall_status, so
# the process return code alone is not enough to tell a clean pass from a
# buried failure. Parse the JSON it writes to distinguish passing / partial
# / failing, and surface that in the final log line.
STATUS=""
if [[ -s "$OUT" ]]; then
  STATUS=$(python3 -c '
import json, sys
try:
    with open(sys.argv[1]) as f:
        doc = json.load(f)
except Exception:
    sys.exit(0)
overall = doc.get("overall_status") or ""
summary = doc.get("summary") or {}
passed = summary.get("tracks_passed", 0)
partial = summary.get("tracks_partial", 0)
failed = summary.get("tracks_failed", 0)
total = passed + partial + failed + summary.get("tracks_skipped", 0)
headline = summary.get("headline") or ""
print(f"{overall}\t{passed}\t{partial}\t{failed}\t{total}\t{headline}")
' "$OUT" 2>/dev/null || echo "")
fi

if [[ -z "$STATUS" ]]; then
  echo "[run] FAIL: no storyboard output — $OUT"
  exit 1
fi

OVERALL=$(printf '%s' "$STATUS" | cut -f1)
PASSED=$(printf '%s' "$STATUS" | cut -f2)
PARTIAL=$(printf '%s' "$STATUS" | cut -f3)
FAILED=$(printf '%s' "$STATUS" | cut -f4)
TOTAL=$(printf '%s' "$STATUS" | cut -f5)
HEADLINE=$(printf '%s' "$STATUS" | cut -f6)

case "$OVERALL" in
  passing)
    echo "[run] PASS — $OUT"
    exit 0
    ;;
  partial)
    echo "[run] WARN: partial — $PASSED of $TOTAL tracks passing ($PARTIAL partial, $FAILED failed) — $OUT"
    exit 0
    ;;
  failing)
    REASON="${HEADLINE:-overall_status=failing}"
    echo "[run] FAIL: $REASON — $OUT"
    exit 1
    ;;
  *)
    echo "[run] FAIL: no storyboard output — $OUT"
    exit 1
    ;;
esac
