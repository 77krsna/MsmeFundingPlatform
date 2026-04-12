#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDDIR="$ROOT/.pids"
LOGDIR="$ROOT/logs"

mkdir -p "$PIDDIR" "$LOGDIR"

kill_port () {
  local port="$1"
  local pids
  pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    echo "Killing processes on port $port: $pids"
    echo "$pids" | xargs -r kill -9
  fi
}

wait_port () {
  local port="$1"
  local tries=60
  for i in $(seq 1 $tries); do
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "Timeout waiting for port $port"
  return 1
}

echo "== Cleaning ports =="
kill_port 3000
kill_port 3001
kill_port 8001
kill_port 8545

echo "== Postgres check/start =="
if command -v brew >/dev/null 2>&1; then
  brew services start postgresql@16 >/dev/null 2>&1 || true
fi
if command -v pg_isready >/dev/null 2>&1; then
  pg_isready -h localhost -p 5432 || true
fi

echo "== Ensure env files exist =="
if [ ! -f "$ROOT/oracle/.env" ]; then
  cp "$ROOT/oracle/.env.example" "$ROOT/oracle/.env"
  echo "Created oracle/.env from .env.example (please verify DATABASE_URL etc.)"
fi
if [ ! -f "$ROOT/frontend/.env" ]; then
  cp "$ROOT/frontend/.env.example" "$ROOT/frontend/.env"
  echo "Created frontend/.env from .env.example"
fi

echo "== Start Hardhat node =="
(
  cd "$ROOT"
  npm run dev:blockchain
) >"$LOGDIR/hardhat.log" 2>&1 &
echo $! >"$PIDDIR/hardhat.pid"
wait_port 8545
echo "Hardhat running on 8545"

echo "== Deploy contracts to localhost =="
(
  cd "$ROOT/blockchain"
  npm run deploy -- --network localhost
) | tee "$LOGDIR/deploy.log"

echo "== Sync deployed contract addresses into frontend/.env =="
node "$ROOT/scripts/sync_contracts_to_frontend_env.js" | tee "$LOGDIR/sync_env.log"

echo "== Start Oracle API (8001) =="
(
  cd "$ROOT/oracle"
  source .venv/bin/activate
  python -m uvicorn app.main:app --reload --reload-dir app --port 8001
) >"$LOGDIR/oracle.log" 2>&1 &
echo $! >"$PIDDIR/oracle.pid"
wait_port 8001
echo "Oracle running on 8001"

echo "== Start Frontend (vite) =="
(
  cd "$ROOT"
  npm run dev:frontend
) >"$LOGDIR/frontend.log" 2>&1 &
echo $! >"$PIDDIR/frontend.pid"

echo "== Start Demo Runner (synthetic + API/RPC checks) =="
(
  cd "$ROOT/oracle"
  source .venv/bin/activate
  python -m synthetic.demo_runner
) >"$LOGDIR/demo_runner.log" 2>&1 &
echo $! >"$PIDDIR/demo_runner.pid"

echo ""
echo "ALL STARTED"
echo "Frontend:  http://localhost:3000  (or see logs/frontend.log)"
echo "Oracle:    http://127.0.0.1:8001/docs"
echo "Hardhat:   http://127.0.0.1:8545"
echo ""
echo "Logs in:   $LOGDIR"
echo "Stop all:  ./scripts/stop_demo.sh"
