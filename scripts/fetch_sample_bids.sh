#!/usr/bin/env bash
# Download or create a minimal BIDS sample under data/sample/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${ROOT}/data/sample"

if [[ -f "${DEST}/dataset_description.json" ]]; then
  echo "Sample BIDS dataset already present at ${DEST}"
  exit 0
fi

echo "Preparing minimal BIDS sample at ${DEST}..."

mkdir -p "${DEST}"
cat > "${DEST}/dataset_description.json" <<'JSON'
{
  "Name": "NeuroFlow Sample",
  "BIDSVersion": "1.8.0",
  "DatasetType": "raw"
}
JSON

mkdir -p "${DEST}/sub-01/anat"
# Empty NIfTI placeholder (0 bytes) — replace with real data for visualization tests
touch "${DEST}/sub-01/anat/sub-01_T1w.nii.gz"

cat > "${DEST}/README" <<'EOF'
NeuroFlow minimal BIDS sample (synthetic).

For a full public dataset, install AWS CLI and run:
  aws s3 sync --no-sign-request s3://openneuro.org/ds000001 data/sample --exclude "*" --include "dataset_description.json" --include "sub-01/*"
EOF

echo "Done. BIDS root: ${DEST}"
echo "Optional: validate with  poetry run python -c \"from neuroflow.bids.layout import list_subjects; print(list_subjects(__import__('pathlib').Path('${DEST}')))\" "
