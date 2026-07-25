#!/usr/bin/env bash
# First-machine NeuroFlow bootstrap for Debian/Ubuntu (apt only).
# Does not install neuroimaging packages (FSL, FreeSurfer, etc.).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DRY_RUN=0
ASSUME_YES=0

usage() {
  cat <<'EOF'
Usage: ./scripts/setup.sh [--dry-run] [--yes]

  --dry-run   Print suggested system installs only; skip apt/Poetry installs
              and skip project dependency install.
  --yes       Run suggested system installs without prompting (labs/CI).

Ubuntu 22.04+ / Debian 12+ with apt. NeuroFlow does not install FSL,
FreeSurfer, ANTs, 3D Slicer, or ITK.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --yes) ASSUME_YES=1 ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

export PATH="${HOME}/.local/bin:${PATH}"

need_base_apt=0
need_poetry=0
need_node_distro=0
need_node_nodesource=0

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

python_ok() {
  have_cmd python3 || return 1
  python3 - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
}

node_major() {
  node -v 2>/dev/null | sed -E 's/^v([0-9]+).*/\1/' || true
}

node_ok() {
  have_cmd node && have_cmd npm || return 1
  local major
  major="$(node_major)"
  [[ -n "$major" && "$major" -ge 18 ]]
}

echo "==> Checking OS (apt required)"
if ! have_cmd apt-get && ! have_cmd apt; then
  echo "NeuroFlow setup currently supports Debian/Ubuntu with apt only." >&2
  echo "Install Python 3.10+, Poetry, and Node.js 18+ manually, then use: make install && make frontend-build" >&2
  exit 1
fi

echo "==> Checking Python / Poetry / Node"
if ! python_ok; then
  need_base_apt=1
  echo "  Python 3.10+: missing or too old"
else
  echo "  Python 3.10+: ok ($(python3 -V 2>&1))"
fi

if ! have_cmd curl; then
  need_base_apt=1
  echo "  curl: missing"
fi

if ! have_cmd poetry; then
  need_poetry=1
  echo "  Poetry: missing"
else
  echo "  Poetry: ok ($(poetry --version 2>&1))"
fi

if node_ok; then
  echo "  Node.js 18+: ok ($(node -v), npm $(npm -v))"
elif have_cmd node; then
  need_node_nodesource=1
  echo "  Node.js 18+: found $(node -v 2>/dev/null || echo unknown), need >= 18"
else
  # Prefer distro packages first; NodeSource only if distro node is absent or too old after apt.
  need_node_distro=1
  echo "  Node.js 18+: missing"
fi

# Always suggest base apt when any toolchain piece is missing (venv/pip/build tools).
if [[ "$need_poetry" -eq 1 || "$need_node_distro" -eq 1 || "$need_node_nodesource" -eq 1 ]]; then
  need_base_apt=1
fi

SUGGESTIONS=0
if [[ "$need_base_apt" -eq 1 || "$need_poetry" -eq 1 || "$need_node_distro" -eq 1 || "$need_node_nodesource" -eq 1 ]]; then
  SUGGESTIONS=1
  echo
  echo "==> Suggested system installs"
  if [[ "$need_base_apt" -eq 1 ]]; then
    echo "  # Base packages (Python toolchain)"
    echo "  sudo apt update"
    echo "  sudo apt install -y python3 python3-venv python3-pip curl build-essential"
  fi
  if [[ "$need_node_distro" -eq 1 ]]; then
    echo "  # Node.js from distro (Ubuntu 24.04+ usually provides Node >= 18)"
    echo "  sudo apt install -y nodejs npm"
  fi
  if [[ "$need_node_nodesource" -eq 1 ]]; then
    echo "  # Node.js 20.x via NodeSource (when distro Node is < 18)"
    echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
    echo "  sudo apt install -y nodejs"
  fi
  if [[ "$need_poetry" -eq 1 ]]; then
    echo "  # Poetry (official installer; not apt)"
    echo "  curl -sSL https://install.python-poetry.org | python3 -"
    echo "  # Ensure ~/.local/bin is on PATH (this script already prepends it)"
  fi
  echo
else
  echo
  echo "==> Suggested system installs: none (toolchain looks ready)"
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "==> Dry run: skipping system installs and project dependency install."
  if [[ "$SUGGESTIONS" -eq 1 ]]; then
    echo "Re-run without --dry-run after reviewing the suggestions above."
  else
    echo "Re-run without --dry-run to install project dependencies and build the UI."
  fi
  exit 0
fi

run_suggested_installs() {
  if [[ "$need_base_apt" -eq 1 ]]; then
    sudo apt update
    sudo apt install -y python3 python3-venv python3-pip curl build-essential
  fi
  if [[ "$need_node_distro" -eq 1 ]]; then
    sudo apt install -y nodejs npm
    if ! node_ok; then
      echo "Distro Node is still < 18; installing NodeSource Node 20.x…"
      curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
      sudo apt install -y nodejs
    fi
  fi
  if [[ "$need_node_nodesource" -eq 1 ]]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
  fi
  if [[ "$need_poetry" -eq 1 ]]; then
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="${HOME}/.local/bin:${PATH}"
  fi
}

if [[ "$SUGGESTIONS" -eq 1 ]]; then
  if [[ "$ASSUME_YES" -eq 1 ]]; then
    run_suggested_installs
  else
    read -r -p "Run suggested installs now? [y/N] " reply
    case "$reply" in
      y|Y|yes|YES) run_suggested_installs ;;
      *)
        echo "Skipping system installs. Continuing if tools are already available…"
        ;;
    esac
  fi
fi

# Re-check after optional installs
export PATH="${HOME}/.local/bin:${PATH}"
missing=0
if ! python_ok; then
  echo "ERROR: Python 3.10+ is required." >&2
  missing=1
fi
if ! have_cmd poetry; then
  echo "ERROR: Poetry is required (https://python-poetry.org/docs/#installation)." >&2
  missing=1
fi
if ! node_ok; then
  echo "ERROR: Node.js 18+ and npm are required." >&2
  missing=1
fi
if [[ "$missing" -eq 1 ]]; then
  echo "Install the missing tools (see suggestions above), then re-run: make setup" >&2
  exit 1
fi

echo "==> Writing .env (if missing)"
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "  created .env from .env.example"
else
  echo "  .env already exists (left unchanged)"
fi

echo "==> Installing Python dependencies"
poetry install

echo "==> Installing frontend dependencies and building UI"
(
  cd frontend
  npm install
  npm run build
)

echo "==> Ensuring data directories"
mkdir -p data/jobs data/datasets

echo "==> Host package scan (informational; neuroimaging tools are not installed by NeuroFlow)"
set +e
poetry run neuroflow scan
scan_status=$?
set -e
if [[ "$scan_status" -ne 0 ]]; then
  echo "  (scan exited with status ${scan_status}; setup continues)"
fi

echo
echo "Setup complete."
echo "  Start (dev, reload):  make api"
echo "  Desktop launcher:     make desktop-install"
echo "  Then open:            http://127.0.0.1:8000/"
echo "  Host tools (optional): install FSL/FreeSurfer/SCT/etc. on the machine separately;"
echo "                         NeuroFlow only detects them (see docs/getting-started.md)."
