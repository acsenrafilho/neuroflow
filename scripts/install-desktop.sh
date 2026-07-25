#!/usr/bin/env bash
# Install NeuroFlow into the application menu and Desktop (Linux).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="${ROOT}/packaging/neuroflow.desktop.in"
ICON_PATH="${ROOT}/assets/images/neuroflow_icon.png"
APPS_DIR="${HOME}/.local/share/applications"
DESKTOP_DIR="${HOME}/Desktop"
TARGET_APPS="${APPS_DIR}/neuroflow.desktop"
TARGET_DESKTOP="${DESKTOP_DIR}/neuroflow.desktop"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "Missing template: ${TEMPLATE}" >&2
  exit 1
fi

if [[ ! -x "${ROOT}/scripts/neuroflow-launch.sh" ]]; then
  chmod +x "${ROOT}/scripts/neuroflow-launch.sh"
fi
if [[ ! -x "${ROOT}/scripts/neuroflow-stop.sh" ]]; then
  chmod +x "${ROOT}/scripts/neuroflow-stop.sh"
fi

mkdir -p "$APPS_DIR"

sed \
  -e "s|@REPO_ROOT@|${ROOT}|g" \
  -e "s|@ICON_PATH@|${ICON_PATH}|g" \
  "$TEMPLATE" >"$TARGET_APPS"
chmod +x "$TARGET_APPS"

echo "Installed application menu entry: ${TARGET_APPS}"

if [[ -d "$DESKTOP_DIR" ]]; then
  cp "$TARGET_APPS" "$TARGET_DESKTOP"
  chmod +x "$TARGET_DESKTOP"
  # Mark as trusted on GNOME when gio is available
  if command -v gio >/dev/null 2>&1; then
    gio set "$TARGET_DESKTOP" metadata::trusted true 2>/dev/null || true
  fi
  echo "Installed Desktop shortcut: ${TARGET_DESKTOP}"
else
  echo "No ~/Desktop directory; skipped Desktop shortcut."
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APPS_DIR" 2>/dev/null || true
fi

echo
echo "You can start NeuroFlow from the application menu or Desktop icon."
echo "Stop a background instance with: ./scripts/neuroflow-stop.sh"
echo "URL: http://127.0.0.1:8000/"
