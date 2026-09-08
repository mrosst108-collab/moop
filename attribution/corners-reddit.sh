#!/bin/sh
# Phase 3 (reddit.md): derive the four corner transcripts of one event,
# mechanically, from a classified transcript. This script never executes
# the reddit; `run` only invokes the binary on literal files.
#   sh corners-reddit.sh events TRANSCRIPT              list F events and intervals
#   sh corners-reddit.sh derive TRANSCRIPT N OUTDIR      write H00 H01 H10 H11 for the event at line N
#   sh corners-reddit.sh run BIN OUTDIR                  replay each corner with the same binary, then
#                                                        `show` every track named in (N, M]; write the artifact
set -e
classify() { case "$1" in
    post|comment|vote|cast|cross|all|profile|rank|weigh) echo sigma ;;
    rules|lock|ban|follow|unfollow|pagerank|blend) echo F ;;
    sub) echo structural ;;
    tick) echo clock ;;
    show|sweep|gamma) echo operation ;;
    save|help|quit) echo session ;;
    *) echo unknown ;; esac; }
check() { n=0; while read -r line; do n=$((n+1)); k=$(classify "${line%% *}")
    case "$k" in unknown|session) echo "line $n: $k: $line" >&2; exit 1 ;; esac; done < "$1"; }
interval_end() { # first line after N that is an F line, minus one; else the last line
  total=$(wc -l < "$1"); m=$2
  while [ "$m" -lt "$total" ]; do next=$(sed -n "$((m+1))p" "$1"); [ "$(classify "${next%% *}")" = F ] && break; m=$((m+1)); done
  echo "$m"; }
case "$1" in
events)
  check "$2"; n=0
  while read -r line; do n=$((n+1))
    [ "$(classify "${line%% *}")" = F ] && printf 'event at %d: %s   interval (%d, %d]\n' "$n" "$line" "$n" "$(interval_end "$2" "$n")"
  done < "$2" ;;
derive)
  check "$2"; N=$3; out=$4; mkdir -p "$out"; M=$(interval_end "$2" "$N")
  cp "$2" "$out/source.txt"; printf '%s %s\n' "$N" "$M" > "$out/NM"
  corner() { # name drop_F drop_sigma  — keep lines <= M, drop per flags, no edits inside a line
    awk -v N="$N" -v M="$M" -v df="$2" -v ds="$3" '
      NR>M {exit}
      { w=$1; s=(w=="post"||w=="comment"||w=="vote"||w=="cross"||w=="all"||w=="profile")
        if (df && NR==N) next; if (ds && s && NR>N && NR<=M) next; print }' "$out/source.txt" > "$out/$1.txt"; }
  corner H00 0 0; corner H01 1 0; corner H10 0 1; corner H11 1 1
  printf 'event %d, interval (%d, %d]: H00 unchanged, H01 minus F_%d, H10 minus sigma in (%d,%d], H11 both\n' "$N" "$N" "$M" "$N" "$N" "$M" ;;
run)
  bin=$2; out=$3; read -r N M < "$out/NM"
  tracks=$(sed -n "$((N+1)),${M}p" "$out/source.txt" | awk '{print $2}' | grep -vE '^[0-9]+$' | sort -u)
  for h in H00 H01 H10 H11; do
    f="$out/$h.txt"; { for t in $tracks; do echo "show $t"; done; echo quit; } | "$bin" "$f" > "$out/$h.obs" 2>&1 && st=0 || st=$?
    printf '%s  sha256=%s  lines=%d  exit=%d\n' "$h" "$(sha256sum < "$f" | cut -c1-12)" "$(wc -l < "$f")" "$st"
  done ;;
*) echo "usage: see header" >&2; exit 2 ;;
esac
