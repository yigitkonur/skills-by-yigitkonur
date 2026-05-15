#!/usr/bin/env bash
# audit-sizes.sh — post-batch quality audit by output file size.
#
# Prints:
#   - DONE / FAIL / SKIP counts from the runner log (when available)
#   - per-answer byte size, sorted ascending
#   - bottom decile flagged for review
#   - any answer below the absolute floor MIN
#
# Size is a probabilistic quality signal, not a verdict. Always read the
# head of any flagged answer before deciding to retry.
#
# Usage:
#   audit-sizes.sh --manifest <manifest.json> [MIN_BYTES]
#   audit-sizes.sh [ANSWERS_DIR] [LOG] [MIN_BYTES]
#
# Manifest mode (preferred): when --manifest <path> is passed, the audit reads
# the dispatcher-seeded `answers_dir` from the manifest's top-level field (or,
# if absent, derives it from the manifest entries' `answer_path`). This is the
# correct shape for runs dispatched with `--answers-dir <override>`, where the
# dispatcher's `--answers-dir custom/` lands outputs at `<cwd>/custom/<slug>.md`
# rather than `<cwd>/answers/`. Without the manifest hint, the audit defaults
# to `./answers/` and silently inspects the wrong directory.
#
# Inputs (positional or env):
#   ANSWERS_DIR / $1                answers dir (default: ./answers)
#   LOG / $2 / $LOG                 runner log path (default: ./logs/_runner.log).
#                                   When the dispatcher manages the run, the
#                                   runner stdout is redirected to
#                                   ${monitor_root}/logs/<run_id>/_runner.log
#                                   — set LOG= explicitly to that path.
#   MIN_BYTES / $3 / $MIN_BYTES     absolute floor (default: 10000)
#
# Flag inputs:
#   --manifest <path>               read answers_dir, runner_log_path, and
#                                   monitor_root from the manifest. Overrides
#                                   the positional ANSWERS_DIR / LOG defaults.
#                                   MIN_BYTES still defaults to 10000 unless
#                                   set positionally / via env.
#
# Exit codes: 0 audit ran (regardless of flags), 1 ANSWERS_DIR not found,
#             2 manifest unreadable / malformed.

set -u

MANIFEST=""
POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest)
      if [[ $# -lt 2 ]]; then
        echo "audit-sizes.sh: --manifest requires a path argument" >&2
        exit 2
      fi
      MANIFEST="$2"
      shift 2
      ;;
    --manifest=*)
      MANIFEST="${1#--manifest=}"
      shift
      ;;
    -h|--help)
      sed -n '2,42p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

if [[ -n "$MANIFEST" ]]; then
  if [[ ! -f "$MANIFEST" ]]; then
    echo "audit-sizes.sh: --manifest path not found: $MANIFEST" >&2
    exit 2
  fi
  if ! command -v jq >/dev/null 2>&1; then
    echo "audit-sizes.sh: --manifest mode requires jq on PATH" >&2
    exit 2
  fi
  # Top-level `answers_dir` is the dispatcher-seeded canonical location. If
  # absent (older manifests, hand-edited paths), derive from the first entry's
  # `answer_path` (entries point at <answers_dir>/<slug>.md).
  m_answers="$(jq -r '.answers_dir // (.paths.answers_dir // "")' "$MANIFEST" 2>/dev/null || echo "")"
  if [[ -z "$m_answers" || "$m_answers" == "null" ]]; then
    m_answers="$(jq -r '
      ((.entries // []) | map(.answer_path // empty) | first) // ""
      | if . == "" then "" else (. | split("/")[:-1] | join("/")) end
    ' "$MANIFEST" 2>/dev/null || echo "")"
  fi
  m_log="$(jq -r '.paths.runner_log // ""' "$MANIFEST" 2>/dev/null || echo "")"
  if [[ -z "$m_log" || "$m_log" == "null" ]]; then
    m_monroot="$(jq -r '.monitor_root // ""' "$MANIFEST" 2>/dev/null || echo "")"
    m_runid="$(jq -r '.run_id // ""' "$MANIFEST" 2>/dev/null || echo "")"
    if [[ -n "$m_monroot" && "$m_monroot" != "null" && -n "$m_runid" && "$m_runid" != "null" ]]; then
      m_log="$m_monroot/logs/$m_runid/_runner.log"
    fi
  fi
  if [[ -z "$m_answers" || "$m_answers" == "null" ]]; then
    echo "audit-sizes.sh: manifest does not declare answers_dir and has no entries with answer_path" >&2
    exit 2
  fi
  ANSWERS="$m_answers"
  LOG="${m_log:-${LOG:-logs/_runner.log}}"
  MIN="${POSITIONAL[0]:-${MIN_BYTES:-10000}}"
else
  ANSWERS="${POSITIONAL[0]:-${ANSWERS:-answers}}"
  LOG="${POSITIONAL[1]:-${LOG:-logs/_runner.log}}"
  MIN="${POSITIONAL[2]:-${MIN_BYTES:-10000}}"
fi

if [[ ! -d "$ANSWERS" ]]; then
  echo "answers dir not found: $ANSWERS" >&2
  exit 1
fi

echo "=== Runner log summary ==="
if [[ -f "$LOG" ]]; then
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
  [[ -f "$f" ]] || continue
  printf '%d\t%s\n' "$(wc -c < "$f")" "$(basename "$f")"
done | sort -n > "$sizes_file"

awk -F'\t' '{ printf "%8d  %s\n", $1, $2 }' "$sizes_file"

# Stats
total="$(wc -l < "$sizes_file" | tr -d ' ')"
if [[ "$total" -eq 0 ]]; then
  echo ""
  echo "(no answers yet)"
  exit 0
fi

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
[[ "$decile" -lt 1 ]] && decile=1
head -n "$decile" "$sizes_file" | awk -F'\t' '{ printf "  %8d  %s\n", $1, $2 }'

echo ""
echo "=== Below absolute floor (MIN=$MIN bytes) ==="
flagged="$(awk -F'\t' -v min="$MIN" '$1 < min { count++ } END { print count+0 }' "$sizes_file")"
if [[ "$flagged" -eq 0 ]]; then
  echo "  (none — all answers above floor)"
else
  awk -F'\t' -v min="$MIN" '$1 < min { printf "  %8d  %s\n", $1, $2 }' "$sizes_file"
fi

echo ""
echo "Recommendation:"
if [[ "$flagged" -gt 0 ]]; then
  echo "  Read the head of each flagged answer before retrying. Some are"
  echo "  legitimately concise (thin source, parked domain). For real retries:"
  echo "    mkdir -p $ANSWERS/.prev"
  echo "    mv $ANSWERS/<name>.md $ANSWERS/.prev/"
  echo "    JOBS=10 run-batch.sh > $LOG 2>&1 &"
  echo "  After retry, compare sizes — codex is non-deterministic, retries"
  echo "  can be worse. Restore from .prev/ if needed."
else
  echo "  All sizes look healthy. No retry needed."
fi
