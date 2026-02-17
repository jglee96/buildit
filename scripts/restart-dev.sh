#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$RUN_DIR/logs"
PID_DIR="$RUN_DIR/pids"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

mkdir -p "$LOG_DIR" "$PID_DIR"

kill_pid_file() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file" || true)"
    if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      sleep 0.3
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$pid_file"
  fi
}

kill_port() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -ti tcp:"$port" || true)"
    if [[ -n "${pids:-}" ]]; then
      kill $pids 2>/dev/null || true
      sleep 0.3
      kill -9 $pids 2>/dev/null || true
    fi
  fi
}

wait_for_url() {
  local url="$1"
  local name="$2"
  local retries=60

  for ((i = 1; i <= retries; i++)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done

  echo "[ERROR] $name did not become ready: $url"
  return 1
}

if [[ ! -x "$ROOT_DIR/.venv/bin/python" ]]; then
  echo "[ERROR] Python venv not found at $ROOT_DIR/.venv"
  echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

if [[ ! -d "$ROOT_DIR/web/node_modules" ]]; then
  echo "[ERROR] web/node_modules not found."
  echo "Run: cd $ROOT_DIR/web && npm install"
  exit 1
fi

echo "[INFO] Stopping existing backend/frontend..."
kill_pid_file "$BACKEND_PID_FILE"
kill_pid_file "$FRONTEND_PID_FILE"
kill_port "$BACKEND_PORT"
kill_port "$FRONTEND_PORT"

echo "[INFO] Starting backend on :$BACKEND_PORT"
(
  cd "$ROOT_DIR"
  nohup "$ROOT_DIR/.venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port "$BACKEND_PORT" \
    >"$LOG_DIR/backend.log" 2>&1 &
  echo $! >"$BACKEND_PID_FILE"
)

echo "[INFO] Starting frontend on :$FRONTEND_PORT"
(
  cd "$ROOT_DIR/web"
  nohup npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT" \
    >"$LOG_DIR/frontend.log" 2>&1 &
  echo $! >"$FRONTEND_PID_FILE"
)

wait_for_url "http://127.0.0.1:$BACKEND_PORT/health" "backend"
wait_for_url "http://127.0.0.1:$FRONTEND_PORT" "frontend"

echo "[OK] Restart complete"
echo "Backend : http://127.0.0.1:$BACKEND_PORT"
echo "Frontend: http://127.0.0.1:$FRONTEND_PORT"
echo "Logs    : $LOG_DIR/backend.log, $LOG_DIR/frontend.log"
