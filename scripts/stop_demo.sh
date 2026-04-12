#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDDIR="$ROOT/.pids"

kill_pidfile () {
  local f="$1"
  if [ -f "$f" ]; then
    local pid
    pid="$(cat "$f" || true)"
    if [ -n "${pid:-}" ]; then
      echo "Killing PID $pid from $f"
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$f"
  fi
}

kill_pidfile "$PIDDIR/demo_runner.pid"
kill_pidfile "$PIDDIR/frontend.pid"
kill_pidfile "$PIDDIR/oracle.pid"
kill_pidfile "$PIDDIR/hardhat.pid"

echo "Also freeing ports 3000/3001/8001/8545"
lsof -ti tcp:3000 | xargs -r kill -9 || true
lsof -ti tcp:3001 | xargs -r kill -9 || true
lsof -ti tcp:8001 | xargs -r kill -9 || true
lsof -ti tcp:8545 | xargs -r kill -9 || true

echo "Stopped."
