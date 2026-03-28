#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/.runtime"
LOG_DIR="$ROOT_DIR/logs"

BACKEND_PID_FILE="$RUNTIME_DIR/backend-supervisor.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend-supervisor.pid"

mkdir -p "$RUNTIME_DIR" "$LOG_DIR"

start_backend() {
  if lsof -i tcp:8001 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Skipping backend supervisor: port 8001 is already in use"
    return
  fi

  if [[ -f "$BACKEND_PID_FILE" ]] && kill -0 "$(cat "$BACKEND_PID_FILE")" 2>/dev/null; then
    echo "Backend supervisor already running (PID $(cat "$BACKEND_PID_FILE"))"
    return
  fi

  nohup bash -lc "
    set -o pipefail
    cd '$ROOT_DIR/backend'
    while true; do
      echo \"[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Starting backend\"
      python3 -m uvicorn server:app --host 0.0.0.0 --port 8001
      code=\$?
      echo \"[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Backend exited with code \$code. Restarting in 3s...\"
      sleep 3
    done
  " >> "$LOG_DIR/backend-supervisor.log" 2>&1 &

  echo $! > "$BACKEND_PID_FILE"
  echo "Started backend supervisor (PID $(cat "$BACKEND_PID_FILE"))"
}

start_frontend() {
  if lsof -i tcp:3000 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Skipping frontend supervisor: port 3000 is already in use"
    return
  fi

  if [[ -f "$FRONTEND_PID_FILE" ]] && kill -0 "$(cat "$FRONTEND_PID_FILE")" 2>/dev/null; then
    echo "Frontend supervisor already running (PID $(cat "$FRONTEND_PID_FILE"))"
    return
  fi

  if [[ ! -d "$ROOT_DIR/frontend/node_modules" ]]; then
    echo "Skipping frontend: dependencies not installed at frontend/node_modules"
    return
  fi

  nohup bash -lc "
    set -o pipefail
    cd '$ROOT_DIR/frontend'
    while true; do
      echo \"[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Starting frontend\"
      npm start
      code=\$?
      echo \"[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Frontend exited with code \$code. Restarting in 3s...\"
      sleep 3
    done
  " >> "$LOG_DIR/frontend-supervisor.log" 2>&1 &

  echo $! > "$FRONTEND_PID_FILE"
  echo "Started frontend supervisor (PID $(cat "$FRONTEND_PID_FILE"))"
}

stop_service() {
  local pid_file="$1"
  local label="$2"

  if [[ ! -f "$pid_file" ]]; then
    echo "$label supervisor is not running"
    return
  fi

  local pid
  pid="$(cat "$pid_file")"

  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    echo "Stopped $label supervisor (PID $pid)"
  else
    echo "$label supervisor PID file exists but process is not running"
  fi

  rm -f "$pid_file"
}

status_service() {
  local pid_file="$1"
  local label="$2"

  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "$label: RUNNING (PID $(cat "$pid_file"))"
  else
    echo "$label: STOPPED"
  fi
}

health_check() {
  python3 - <<'PY'
from urllib.request import urlopen
from urllib.error import URLError

checks = [
    ("backend", "http://127.0.0.1:8001/api/"),
    ("frontend", "http://127.0.0.1:3000/"),
]

for name, url in checks:
    try:
        with urlopen(url, timeout=3) as resp:
            print(f"{name}: HTTP {resp.status}")
    except URLError as exc:
        print(f"{name}: DOWN ({exc})")
PY
}

usage() {
  cat <<EOF
Usage: scripts/run_24x7.sh <command>

Commands:
  start           Start backend and frontend supervisors
  start-backend   Start backend supervisor only
  start-frontend  Start frontend supervisor only
  stop            Stop backend and frontend supervisors
  stop-backend    Stop backend supervisor only
  stop-frontend   Stop frontend supervisor only
  restart         Restart backend and frontend supervisors
  status          Show supervisor status
  health          Run local HTTP health checks
  logs            Show log file paths
EOF
}

cmd="${1:-}"

case "$cmd" in
  start)
    start_backend
    start_frontend
    ;;
  start-backend)
    start_backend
    ;;
  start-frontend)
    start_frontend
    ;;
  stop)
    stop_service "$BACKEND_PID_FILE" "Backend"
    stop_service "$FRONTEND_PID_FILE" "Frontend"
    ;;
  stop-backend)
    stop_service "$BACKEND_PID_FILE" "Backend"
    ;;
  stop-frontend)
    stop_service "$FRONTEND_PID_FILE" "Frontend"
    ;;
  restart)
    stop_service "$BACKEND_PID_FILE" "Backend"
    stop_service "$FRONTEND_PID_FILE" "Frontend"
    start_backend
    start_frontend
    ;;
  status)
    status_service "$BACKEND_PID_FILE" "Backend"
    status_service "$FRONTEND_PID_FILE" "Frontend"
    ;;
  health)
    health_check
    ;;
  logs)
    echo "Backend log:  $LOG_DIR/backend-supervisor.log"
    echo "Frontend log: $LOG_DIR/frontend-supervisor.log"
    ;;
  *)
    usage
    exit 1
    ;;
esac
