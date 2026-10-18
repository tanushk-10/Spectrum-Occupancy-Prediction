#!/usr/bin/env bash
# Resumable downloader for the NIST mds2-2553 per-site histogram and occupancy-duration files.
# NIST's server (data.nist.gov/od/ds) is often down (502/524); this keeps retrying for hours and
# resumes partial downloads.  After each site's pair of files lands it re-runs the screening scripts.
# Usage: bash scripts/fetch_nist.sh [python-exe]   (run from the repo root)
set -u
PY="${1:-python}"
B="https://data.nist.gov/od/ds/ark:/88434/mds2-2553"
MAX_TRIES=${MAX_TRIES:-400}       # x 60 s sleep ~= 6-7 h of patience per file
fetch() {                          # fetch <local path> <remote url>
  local out="$1" url="$2" i
  [ -f "$out" ] && return 0
  for i in $(seq 1 "$MAX_TRIES"); do
    if curl -sfL -C - --max-time 7200 "$url" -o "$out.part"; then
      mv "$out.part" "$out"; echo "$(date +%T) OK $out"; return 0
    fi
    echo "$(date +%T) retry $i $out"; sleep 60
  done
  echo "$(date +%T) FAILED $out"; return 1
}
# smallest sites first so results appear early
for s in 04 02 12 00 03 06 11 09 10 05 07 01; do
  fetch "data/hist/$s.csv.gz" "$B/histograms/$s.csv.gz"
  fetch "data/occ/$s.csv.gz"  "$B/occupancy%20durations/$s.csv.gz"
  "$PY" -I scripts/screen_channels.py --hist-dir data/hist --out results > results/screen_log.txt 2>&1
  "$PY" -I scripts/screen_events.py  --occ-dir  data/occ  --out results --thr -70 > results/events_log.txt 2>&1
  echo "$(date +%T) screens rerun after site $s"
done
echo "$(date +%T) ALLDONE"
