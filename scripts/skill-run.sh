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
[[ "$RC" == 0 ]] && echo "[run] PASS — $OUT" || echo "[run] FAIL (rc=$RC) — $OUT"
exit "$RC"
