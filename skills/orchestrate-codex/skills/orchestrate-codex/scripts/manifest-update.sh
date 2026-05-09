#!/usr/bin/env bash
# manifest-update.sh — atomic field-update helper for the orchestrate-codex
# manifest.json. Bash callers (run-fleet, run-batch, run-single, run-review)
# use this to mutate manifest fields without racing concurrent writers.
#
# Two modes:
#
#   Entry update (per-task fields):
#     manifest-update.sh entry <manifest> <entry-id> <key=value>...
#
#       Updates entries[?id==<entry-id>].<key> for each key=value pair.
#       Special handling:
#         - status=<v>: also pushes a {ts, entry_id, from, to} row onto history
#         - <key>=now: substitute UTC ISO timestamp
#         - <key>=null: write JSON null
#         - <key>=+1: increment counter (only for known counters: attempts)
#         - exit_code/attempts/schema_version/concurrency_cap/round: numeric
#
#   Top-level update:
#     manifest-update.sh top <manifest> <key=value>...
#
# Concurrency model: flock(<manifest>.lock) for exclusive writer access;
# read → mutate → atomic os.replace via mv. 50 concurrent updates against the
# same manifest produce a manifest that parses cleanly and reflects every
# update (DoD 11).
#
# Exit codes:
#   0  OK
#   1  manifest missing or malformed (or jq filter produced invalid output)
#   2  usage error
#   3  entry id not found
#   4  jq missing
#   5  lock acquire timeout (30s)

set -uo pipefail

usage() {
  cat >&2 <<'EOF'
manifest-update.sh — atomic update for orchestrate-codex manifest.json

Usage:
  manifest-update.sh entry <manifest.json> <entry-id> <key=value>...
  manifest-update.sh top   <manifest.json> <key=value>...

Special values:
  now    → UTC ISO timestamp (current time)
  null   → JSON null
  +1     → numeric increment (counter += 1)

Examples:
  manifest-update.sh entry m.json 01-foo status=running started_at=now
  manifest-update.sh entry m.json 01-foo status=done finished_at=now exit_code=0
  manifest-update.sh entry m.json 01-foo status=failed last_error="rate limited"
  manifest-update.sh top   m.json finished_at=now
EOF
  exit 2
}

if ! command -v jq >/dev/null 2>&1; then
  echo "manifest-update: jq not found on PATH" >&2
  exit 4
fi

if [[ $# -lt 3 ]]; then usage; fi

MODE="$1"; shift
MANIFEST="$1"; shift

if [[ ! -f "$MANIFEST" ]]; then
  echo "manifest-update: manifest not found: $MANIFEST" >&2
  exit 1
fi

# Pre-validate the manifest parses before acquiring the lock — a corrupt
# manifest would otherwise block every concurrent caller behind the flock.
if ! jq -e . "$MANIFEST" >/dev/null 2>&1; then
  echo "manifest-update: manifest is not valid JSON: $MANIFEST" >&2
  exit 1
fi

LOCK="${MANIFEST}.lock"
TS_NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Numeric-coercible keys (we'll use --argjson for these when the value parses
# as a number; otherwise fall back to --arg / string).
is_numeric_key() {
  case "$1" in
    exit_code|attempts|schema_version|concurrency_cap|round) return 0 ;;
    *) return 1 ;;
  esac
}

# Builds two parallel structures from the trailing key=value pairs:
#   - JQ_ARGS: array of jq argument flags ( --arg vN VAL ... )
#   - CHAIN:   pipeline fragment ( | .key = $vN | .key2 = ... )
# Caller declares JQ_ARGS and CHAIN before invoking.
build_chain() {
  local i=0 pair key value
  for pair in "$@"; do
    if [[ "$pair" != *=* ]]; then
      echo "manifest-update: bad pair (no '='): $pair" >&2
      exit 2
    fi
    key="${pair%%=*}"
    value="${pair#*=}"
    case "$value" in
      now)
        JQ_ARGS+=( --arg "v$i" "$TS_NOW" )
        CHAIN+=" | .${key} = \$v$i"
        ;;
      null)
        CHAIN+=" | .${key} = null"
        ;;
      +1)
        CHAIN+=" | .${key} = ((.${key} // 0) + 1)"
        ;;
      *)
        if is_numeric_key "$key" && [[ "$value" =~ ^-?[0-9]+(\.[0-9]+)?$ ]]; then
          JQ_ARGS+=( --argjson "v$i" "$value" )
        else
          JQ_ARGS+=( --arg "v$i" "$value" )
        fi
        CHAIN+=" | .${key} = \$v$i"
        ;;
    esac
    i=$((i + 1))
  done
}

acquire_lock() {
  # Hold an exclusive flock on $LOCK while we read+rewrite. flock auto-releases
  # when fd 9 closes (script exit). 30s timeout protects against deadlocks.
  exec 9>"$LOCK"
  if ! flock -w 30 9; then
    echo "manifest-update: failed to acquire lock $LOCK within 30s" >&2
    exit 5
  fi
}

case "$MODE" in
  entry)
    if [[ $# -lt 2 ]]; then usage; fi
    ENTRY_ID="$1"; shift
    if [[ $# -eq 0 ]]; then usage; fi

    # Detect status-change pairs to also append to history[].
    NEW_STATUS=""
    for pair in "$@"; do
      if [[ "$pair" == status=* ]]; then
        NEW_STATUS="${pair#status=}"
      fi
    done

    acquire_lock

    if ! jq -e --arg id "$ENTRY_ID" 'any(.entries[]?; .id == $id)' "$MANIFEST" >/dev/null 2>&1; then
      echo "manifest-update: entry id not found in $MANIFEST: $ENTRY_ID" >&2
      exit 3
    fi

    JQ_ARGS=( --arg id "$ENTRY_ID" --arg ts "$TS_NOW" )
    CHAIN=""
    build_chain "$@"

    # Single-pass jq filter:
    #   1. Capture old status as $old.
    #   2. Apply CHAIN to the matching entry.
    #   3. If status changed, append a history row.
    if [[ -n "$NEW_STATUS" ]]; then
      FILTER='
        . as $root
        | ($root.entries | map(select(.id == $id))[0].status // null) as $old_status
        | .entries |= map(
            if .id == $id then (.'"$CHAIN"') else . end
          )
        | (.entries | map(select(.id == $id))[0].status // null) as $new_status
        | .history = ((.history // []) + [
            { ts: $ts, entry_id: $id, from: $old_status, to: $new_status }
          ])
      '
    else
      FILTER='
        .entries |= map(
          if .id == $id then (.'"$CHAIN"') else . end
        )
      '
    fi

    TMP="$(mktemp "${MANIFEST}.tmp.XXXXXX")"
    if ! jq "${JQ_ARGS[@]}" "$FILTER" "$MANIFEST" > "$TMP" 2>/dev/null; then
      rm -f "$TMP"
      echo "manifest-update: jq filter failed (entry id=$ENTRY_ID, pairs=$*)" >&2
      exit 1
    fi
    if ! jq -e . "$TMP" >/dev/null 2>&1; then
      rm -f "$TMP"
      echo "manifest-update: produced invalid JSON; aborting" >&2
      exit 1
    fi
    mv -f "$TMP" "$MANIFEST"
    ;;

  top)
    if [[ $# -eq 0 ]]; then usage; fi
    acquire_lock

    JQ_ARGS=( --arg ts "$TS_NOW" )
    CHAIN=""
    build_chain "$@"

    # Top-level chain begins from `.` — strip the leading " | " from CHAIN.
    FILTER=".${CHAIN}"

    TMP="$(mktemp "${MANIFEST}.tmp.XXXXXX")"
    if ! jq "${JQ_ARGS[@]}" "$FILTER" "$MANIFEST" > "$TMP" 2>/dev/null; then
      rm -f "$TMP"
      echo "manifest-update: jq filter failed for top-level update (pairs=$*)" >&2
      exit 1
    fi
    if ! jq -e . "$TMP" >/dev/null 2>&1; then
      rm -f "$TMP"
      echo "manifest-update: produced invalid JSON; aborting" >&2
      exit 1
    fi
    mv -f "$TMP" "$MANIFEST"
    ;;

  *)
    usage
    ;;
esac
