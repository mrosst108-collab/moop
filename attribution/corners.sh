#!/bin/sh
# H2: the four X/theta corners of one event (h2.md). Usage:
#   sh corners.sh CLONE P E "<-D for (X_E,theta_P)>" "<-D for (X_P,theta_E)>"
# theta's flags come from each commit's own Makefile (R_CFLAGS minus
# -Werror and make variables); the probe is compiled the same way always.
set -e
R=$1; P=$2; E=$3; DXE_TP=$4; DXP_TE=$5; here=$(cd "$(dirname "$0")" && pwd)
flags() { git -C "$R" show "$1:Makefile" 2>/dev/null | sed -n 's/^R_CFLAGS *= *//p' | sed 's/-Werror//; s/\$([A-Z_]*)//g; s/-fPIC//'; }
corner() { # name, source commit, flags commit, defines
  w=$(mktemp -d); git -C "$R" show "$2:cJSON.c" > "$w/cJSON.c"; git -C "$R" show "$2:cJSON.h" > "$w/cJSON.h"
  if gcc $(flags "$3") $4 -w -c "$w/cJSON.c" -o "$w/cJSON.o" 2>/dev/null && gcc -O0 -w -I"$w" -c "$here/probe.c" -o "$w/probe.o" && gcc "$w/cJSON.o" "$w/probe.o" -lm -o "$w/probe"; then
    timeout 5 "$w/probe" > "$w/out" 2>&1 || true
    printf '%-10s %s  %s\n' "$1" "$(md5sum < "$w/out" | cut -c1-12)" "$(grep -E '^(num|str|depth)' "$w/out" | tr '\n\t' '| ' | sed 's/  */ /g' | cut -c1-160)"
  else printf '%-10s NOBUILD\n' "$1"; fi; rm -rf "$w"; }
echo "flags(P)=[$(flags "$P")]"; echo "flags(E)=[$(flags "$E")]"
corner "XP,tP" "$P" "$P" ""
corner "XE,tE" "$E" "$E" ""
corner "XE,tP" "$E" "$P" "$DXE_TP"
corner "XP,tE" "$P" "$E" "$DXP_TE"
