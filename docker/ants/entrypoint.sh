#!/bin/sh
set -eu

echo "NeuroFlow ANTs module (stub)"
echo "BIDS_ROOT=${BIDS_ROOT}"
echo "SUBJECT=${SUBJECT}"
echo "SESSION=${SESSION}"

if [ ! -d "${BIDS_ROOT}" ]; then
  echo "ERROR: BIDS_ROOT is not mounted or does not exist: ${BIDS_ROOT}" >&2
  exit 1
fi

# Production: use `antsRegistration --version` from antsx/ants image.
echo "antsVersion: neuroflow-stub-0.1.0"
exit 0
