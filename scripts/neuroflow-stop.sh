#!/usr/bin/env bash
# Stop a NeuroFlow server started by neuroflow-launch.sh (background / Desktop).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="${ROOT}/data/neuroflow-serve.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "No pid file at ${PID_FILE} (server not started via Desktop launcher?)."
  exit 0
fi

pid="$(cat "$PID_FILE" 2>/dev/null || true)"
if [[ -z "${pid}" ]]; then
  rm -f "$PID_FILE"
  echo "Removed empty pid file."
  exit 0
fi

if kill -0 "$pid" 2>/dev/null; then
  kill "$pid" 2>/dev/null || true
  # Wait briefly, then force if needed
  for _ in $(seq 1 20); do
    if ! kill -0 "$pid" 2>/dev/null; then
      break
    fi
    sleep 0.25
  done
  if kill -0 "$pid" 2>/dev/null; then
    kill -9 "$pid" 2>/dev/null || true
  fi
  echo "Stopped NeuroFlow (pid ${pid})."
else
  echo "Process ${pid} is not running."
fi

rm -f "$PID_FILE"
