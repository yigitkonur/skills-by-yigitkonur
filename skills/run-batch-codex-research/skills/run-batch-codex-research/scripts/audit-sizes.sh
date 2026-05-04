#!/usr/bin/env bash
# audit-sizes.sh — post-run quality audit by output file size.
#
# Prints:
#   - DONE / FAIL / SKIP counts from the runner log
#   - per-answer byte size, sorted ascending
#   - bottom decile flagged for review
#   - any answer below the absolute floor MIN
#
# Size is a probabilistic quality signal, not a verdict. Always read the
# head of any flagged answer before deciding to retry — see
# references/output-size-signals.md for the heuristics.
#
# Usage:
#   audit-sizes.sh [ANSWERS_DIR] [LOG] [MIN_BYTES]

set -u
# Run from the user's cwd. ANSWERS / LOG default to relative paths from cwd
# (workdir convention), or absolute paths if the user passes them.

ANSWERS="${1:-answers}"
LOG="${2:-logs/_runner.log}"
MIN="${3:-10000}"

if [ ! -d "$ANSWERS" ]; then
  echo "answers dir not found: $ANSWERS" >&2
  exit 1
fi

echo "=== Runner log summary ==="
if [ -f "$LOG" ]; then
  printf 'DONE: %s\n' "$(grep -c '^DONE'  "$LOG")"
  printf 'FAIL: %s\n' "$(grep -c '^FAIL'  "$LOG")"
  printf 'SKIP: %s\n' "$(grep -c '^SKIP'  "$LOG")"
else
  echo "(no runner log at $LOG)"
fi

echo ""
echo "=== Answer file sizes (bytes, ascending) ==="
sizes_file="$(mktemp)"
trap 'rm -f "$sizes_file"' EXIT
for f in "$ANSWERS"/*.md; do
  [ -f "$f" ] || continue
  printf '%d\t%s\n' "$(wc -c < "$f")" "$(basename "$f")"
done | sort -n > "$sizes_file"

cat "$sizes_file" | awk -F'\t' '{ printf "%8d  %s\n", $1, $2 }'

# Stats
total="$(wc -l < "$sizes_file")"
[ "$total" -eq 0 ] && { echo ""; echo "(no answers yet)"; exit 0; }

echo ""
echo "=== Stats ==="
awk -F'\t' '
  { sum += $1; sumsq += $1*$1; n++ }
  END {
    if (n == 0) { print "(empty)"; exit }
    mean = sum / n
    var  = (sumsq - sum*sum/n) / (n>1 ? n-1 : 1)
    sd   = (var > 0) ? sqrt(var) : 0
    printf "count: %d\n", n
    printf "mean:  %.0f bytes\n", mean
    printf "stdev: %.0f bytes\n", sd
  }
' "$sizes_file"

echo ""
echo "=== Bottom decile (10% smallest) ==="
decile=$(( (total + 9) / 10 ))
[ "$decile" -lt 1 ] && decile=1
head -n "$decile" "$sizes_file" | awk -F'\t' '{ printf "  %8d  %s\n", $1, $2 }'

echo ""
echo "=== Below absolute floor (MIN=$MIN bytes) ==="
flagged=$(awk -F'\t' -v min="$MIN" '$1 < min { count++ } END { print count+0 }' "$sizes_file")
if [ "$flagged" -eq 0 ]; then
  echo "  (none — all answers above floor)"
else
  awk -F'\t' -v min="$MIN" '$1 < min { printf "  %8d  %s\n", $1, $2 }' "$sizes_file"
fi

echo ""
echo "Recommendation:"
if [ "$flagged" -gt 0 ]; then
  echo "  Read the head of each flagged answer before retrying. Some are"
  echo "  legitimately concise (thin source, parked domain). For real retries:"
  echo "    mkdir -p answers/.prev"
  echo "    mv answers/<name>.md answers/.prev/"
  echo "    JOBS=10 ./bin/run-batch.sh > logs/_runner.log 2>&1 &"
  echo "  After retry, compare sizes — codex is non-deterministic, retries"
  echo "  can be worse. Restore from .prev/ if needed."
else
  echo "  All sizes look healthy. No retry needed."
fi
