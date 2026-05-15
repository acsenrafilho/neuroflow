#!/bin/sh
set -eu

echo "NeuroFlow FSL module (stub)"
echo "BIDS_ROOT=${BIDS_ROOT}"
echo "SUBJECT=${SUBJECT}"
echo "SESSION=${SESSION}"

if [ ! -d "${BIDS_ROOT}" ]; then
  echo "ERROR: BIDS_ROOT is not mounted or does not exist: ${BIDS_ROOT}" >&2
  exit 1
fi

# Production: use `flirt -version` or similar from the official FSL image.
echo "fslversion: neuroflow-stub-0.1.0"
exit 0
