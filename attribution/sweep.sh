#!/bin/sh
# The instrument: the probe's behavior at every first-parent commit of the
# target, oldest first. Output: index, sha, md5 of the probe's output (or
# NOBUILD / NOFILE / CRASH). Same compiler flags for every commit.
#   sh sweep.sh /path/to/cjson-clone > record.tsv
set -e
R=${1:?target clone}; here=$(cd "$(dirname "$0")" && pwd); w=$(mktemp -d)
git -C "$R" rev-list --first-parent --reverse origin/master | { n=0; while read h; do
  n=$((n+1))
  if ! git -C "$R" show "$h:cJSON.c" > "$w/cJSON.c" 2>/dev/null || ! git -C "$R" show "$h:cJSON.h" > "$w/cJSON.h" 2>/dev/null; then printf '%s\t%s\tNOFILE\n' "$n" "$h"; continue; fi
  if gcc -O0 -w -I"$w" "$here/probe.c" "$w/cJSON.c" -lm -o "$w/probe" 2>/dev/null; then out=$(timeout --preserve-status 5 "$w/probe" 2>&1 | md5sum | cut -c1-12); printf '%s\t%s\t%s\n' "$n" "$h" "${out:-CRASH}"; else printf '%s\t%s\tNOBUILD\n' "$n" "$h"; fi
done; }
rm -rf "$w"
