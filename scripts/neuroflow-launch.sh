#!/usr/bin/env bash
# Start NeuroFlow for end users (no reload) and open the browser.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PATH="${HOME}/.local/bin:${PATH}"

HOST="${NEUROFLOW_LAUNCH_HOST:-127.0.0.1}"
PORT="${NEUROFLOW_LAUNCH_PORT:-8000}"
URL="http://${HOST}:${PORT}/"
PID_FILE="${ROOT}/data/neuroflow-serve.pid"
LOG_FILE="${ROOT}/data/neuroflow-serve.log"

# Desktop entries set this so the server stays up after the launcher exits.
BACKGROUND="${NEUROFLOW_LAUNCH_BACKGROUND:-0}"

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

server_up() {
  if have_cmd curl; then
    curl -sf -o /dev/null --max-time 2 "${URL}api/v1/health" 2>/dev/null \
      || curl -sf -o /dev/null --max-time 2 "${URL}" 2>/dev/null
  else
    # Fallback: TCP connect check
    (echo >/dev/tcp/"${HOST}"/"${PORT}") >/dev/null 2>&1
  fi
}

open_browser() {
  if have_cmd xdg-open; then
    xdg-open "$URL" >/dev/null 2>&1 || true
  fi
}

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

if [[ ! -f frontend/dist/index.html ]]; then
  if [[ -d frontend/node_modules ]]; then
    echo "Building frontend (frontend/dist missing)…"
    (cd frontend && npm run build)
  else
    echo "Frontend is not built. Run: make setup" >&2
    exit 1
  fi
fi

if ! have_cmd poetry; then
  echo "Poetry not found. Run: make setup" >&2
  exit 1
fi

mkdir -p data

if server_up; then
  echo "NeuroFlow already running at ${URL}"
  open_browser
  exit 0
fi

# Stale pid file
if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "${old_pid}" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "NeuroFlow process ${old_pid} is starting; opening browser…"
    open_browser
    exit 0
  fi
  rm -f "$PID_FILE"
fi

start_server() {
  poetry run neuroflow serve --host "$HOST" --port "$PORT" --no-reload
}

wait_ready() {
  local i
  for i in $(seq 1 60); do
    if server_up; then
      return 0
    fi
    sleep 0.25
  done
  return 1
}

if [[ "$BACKGROUND" -eq 1 ]]; then
  echo "Starting NeuroFlow in background → ${URL}"
  nohup poetry run neuroflow serve --host "$HOST" --port "$PORT" --no-reload \
    >>"$LOG_FILE" 2>&1 &
  echo $! >"$PID_FILE"
  if wait_ready; then
    echo "Ready. Log: ${LOG_FILE}  (stop: ./scripts/neuroflow-stop.sh)"
    open_browser
    exit 0
  fi
  echo "Server did not become ready. Check ${LOG_FILE}" >&2
  exit 1
fi

# Foreground (terminal): open browser once health responds, then keep serving.
(
  if wait_ready; then
    open_browser
  fi
) &
echo "Starting NeuroFlow → ${URL}  (Ctrl+C to stop)"
start_server
