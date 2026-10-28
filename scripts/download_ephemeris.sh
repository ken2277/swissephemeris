#!/usr/bin/env bash
# Copyright (c) 2026 Ken Kusuki
# SPDX-License-Identifier: AGPL-3.0-only

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EPHE_DIR="${SCRIPT_DIR}/../ephe"

BASE_URL="https://www.astro.com/ftp/swisseph/ephe"

FILES=(
  "sepl_18.se1"
  "semo_18.se1"
  "seas_18.se1"
)

mkdir -p "${EPHE_DIR}"

echo "Downloading Swiss Ephemeris data files to ${EPHE_DIR} ..."

for FILE in "${FILES[@]}"; do
  DEST="${EPHE_DIR}/${FILE}"

  if [ -f "${DEST}" ]; then
    echo "  - ${FILE} already exists, skipping."
    continue
  fi

  echo "  - downloading ${FILE} ..."

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "${BASE_URL}/${FILE}" -o "${DEST}"
  elif command -v wget >/dev/null 2>&1; then
    wget -q "${BASE_URL}/${FILE}" -O "${DEST}"
  else
    echo "Error: neither curl nor wget was found. Please install one of them." >&2
    echo "  e.g. sudo apt install curl" >&2
    exit 1
  fi

  if [ ! -s "${DEST}" ]; then
    echo "Error: failed to download ${FILE} (the file is empty)." >&2
    rm -f "${DEST}"
    exit 1
  fi
done

echo "Done. The following files are available:"
ls -lh "${EPHE_DIR}"/*.se1
