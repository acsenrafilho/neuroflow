#!/usr/bin/env bash
# Build a platform zip: neuroflow-{version}-{os}-{arch}.zip
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VERSION="${NEUROFLOW_VERSION:-}"
if [[ -z "$VERSION" ]]; then
  VERSION="$(
    poetry version -s 2>/dev/null || python -c "from neuroflow import __version__; print(__version__)"
  )"
fi

OS_NAME="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
case "$OS_NAME" in
  linux*) OS_LABEL="linux" ;;
  darwin*) OS_LABEL="macos" ;;
  msys*|mingw*|cygwin*) OS_LABEL="windows" ;;
  *) OS_LABEL="$OS_NAME" ;;
esac
case "$ARCH" in
  x86_64|amd64) ARCH_LABEL="x86_64" ;;
  aarch64|arm64) ARCH_LABEL="arm64" ;;
  *) ARCH_LABEL="$ARCH" ;;
esac

OUT_DIR="${ROOT}/dist/release"
ZIP_NAME="neuroflow-${VERSION}-${OS_LABEL}-${ARCH_LABEL}.zip"
mkdir -p "$OUT_DIR"

echo "Building frontend…"
(cd frontend && npm ci && npm run build)

echo "Running PyInstaller…"
rm -rf "${ROOT}/build/neuroflow" "${ROOT}/dist/neuroflow"
poetry run pyinstaller --noconfirm --clean packaging/neuroflow.spec

echo "Creating ${ZIP_NAME}…"
rm -f "${OUT_DIR}/${ZIP_NAME}"
(
  cd "${ROOT}/dist"
  if command -v zip >/dev/null 2>&1; then
    zip -r "${OUT_DIR}/${ZIP_NAME}" neuroflow
  else
    python -c "
import shutil
from pathlib import Path
src = Path('neuroflow')
out = Path('${OUT_DIR}') / '${ZIP_NAME}'
shutil.make_archive(str(out.with_suffix('')), 'zip', root_dir='.', base_dir='neuroflow')
print(out)
"
  fi
)

echo "Built ${OUT_DIR}/${ZIP_NAME}"
