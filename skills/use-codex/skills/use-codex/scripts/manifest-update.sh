#!/usr/bin/env bash
# manifest-update.sh — atomic field-update helper for the use-codex
# manifest.json. Bash callers (run-fleet, run-batch, run-single, run-review)
# use this to mutate manifest fields without racing concurrent writers.
#
# Two modes:
#
#   Entry update (per-task fields):
#     manifest-update.sh entry <manifest> <entry-id> <key=value>...
#
#       Updates entries[?id==<entry-id>].<key> for each key=value pair.
#       <key> may be a dotted path (e.g. mode_state.codex_pid); intermediate
#       objects are auto-created via jq's setpath.
#       Special handling:
#         - status=<v>: also pushes a {ts, entry_id, from, to, actor, reason}
#           row onto history
#         - <key>=now: substitute UTC ISO timestamp
#         - <key>=null: write JSON null
#         - <key>=+1: increment counter (uses ((... // 0) + 1))
#         - exit_code/attempts/schema_version/concurrency_cap/round/
#           codex_pid/post_verify_exit/answer_size_bytes/major_count/
#           minor_count: numeric (also when leaf-segment of dotted key)
#
#   Top-level update:
#     manifest-update.sh top <manifest> <key=value>...
#
# Optional flags (may appear before mode or after the manifest):
#   --reason "<text>"   record reason on history rows for status changes
#   --actor "<name>"    override actor (default: script basename)
#
# Concurrency model: flock(<manifest>.lock) for exclusive writer access;
# read → mutate → atomic os.replace via mv. 50 concurrent updates against the
# same manifest produce a manifest that parses cleanly and reflects every
# update.
#
# Exit codes (canonical table — python sibling agrees):
#   0  OK — update applied
#   2  usage error / bad input / manifest missing or malformed / entry not found
#   3  environmental error (lock acquire timeout, write failure)
#   4  hard failure (resulting manifest invalid JSON)
#   5  missing required dependency (jq)

set -uo pipefail

usage() {
  cat >&2 <<'EOF'
manifest-update.sh — atomic update for use-codex manifest.json

Usage:
  manifest-update.sh entry <manifest.json> <entry-id> <key=value>...
  manifest-update.sh top   <manifest.json> <key=value>...

Optional flags (anywhere before the trailing key=value list):
  --reason "<text>"  record on history rows
  --actor "<name>"   override the actor recorded on history rows

Special values:
  now    UTC ISO timestamp (current time)
  null   JSON null
  +1     numeric increment (counter += 1)

Examples:
  manifest-update.sh entry m.json 01-foo status=running started_at=now
  manifest-update.sh entry m.json 01-foo status=done finished_at=now exit_code=0
  manifest-update.sh entry m.json 01-foo mode_state.codex_pid=12345
  manifest-update.sh entry m.json 01-foo --reason "rescue redispatch" status=queued
  manifest-update.sh top   m.json finished_at=now
EOF
  exit 2
}

# ── Pre-flight ─────────────────────────────────────────────────
if ! command -v jq >/dev/null 2>&1; then
  echo "manifest-update: jq not found on PATH" >&2
  exit 5
fi

ACTOR=""
REASON=""

# Pull --reason / --actor out of the argv (anywhere). Remaining argv shifts
# down so the positional layout below still works.
declare -a POSARGS=()
while (( $# > 0 )); do
  case "$1" in
    --reason)
      shift
      [[ $# -gt 0 ]] || { echo "manifest-update: --reason requires a value" >&2; exit 2; }
      REASON="$1"
      shift
      ;;
    --reason=*)
      REASON="${1#--reason=}"
      shift
      ;;
    --actor)
      shift
      [[ $# -gt 0 ]] || { echo "manifest-update: --actor requires a value" >&2; exit 2; }
      ACTOR="$1"
      shift
      ;;
    --actor=*)
      ACTOR="${1#--actor=}"
      shift
      ;;
    *)
      POSARGS+=("$1")
      shift
      ;;
  esac
done

# Restore positional args.
set -- "${POSARGS[@]+"${POSARGS[@]}"}"

if [[ $# -lt 3 ]]; then usage; fi

MODE="$1"; shift
MANIFEST="$1"; shift

if [[ -z "$ACTOR" ]]; then
  ACTOR="$(basename -- "$0")"
fi

if [[ ! -f "$MANIFEST" ]]; then
  echo "manifest-update: manifest not found: $MANIFEST" >&2
  exit 2
fi

# Pre-validate the manifest parses before acquiring the lock — a corrupt
# manifest would otherwise block every concurrent caller behind the flock.
if ! jq -e . "$MANIFEST" >/dev/null 2>&1; then
  echo "manifest-update: manifest is not valid JSON: $MANIFEST" >&2
  exit 2
fi

LOCK="${MANIFEST}.lock"
TS_NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Numeric-coercible leaf keys (we'll use --argjson for these when the value
# parses as a number; otherwise fall back to --arg / string). Matches the
# python sibling's NUMERIC_KEYS allowlist.
is_numeric_leaf() {
  case "$1" in
    exit_code|attempts|schema_version|concurrency_cap|round) return 0 ;;
    codex_pid|post_verify_exit|answer_size_bytes) return 0 ;;
    major_count|minor_count) return 0 ;;
    *) return 1 ;;
  esac
}

# Bug 2 fix — boolean-coercible leaf keys. When the leaf segment of the
# dotted key matches one of these AND the raw value is exactly `true` or
# `false`, write a JSON boolean instead of a JSON string. The runner emits
# `mode_state.below_floor=true` after every batch-mode answer write; without
# coercion the manifest accumulated string-typed `"true"` / `"false"` values
# that broke `=== true` comparisons in downstream consumers. The python
# sibling already coerces every literal `true`/`false` (manifest-update.py:
# coerce_value); this allowlist mirrors that behaviour for bash callers
# while staying conservative — only known-boolean fields coerce, so a string
# value that happens to be the word "true" stays a string.
is_boolean_leaf() {
  case "$1" in
    below_floor|dry_run|bypass|cleaned_up|reuse_worktree) return 0 ;;
    *) return 1 ;;
  esac
}

# Convert a dotted key path "a.b.c" to a jq array literal: ["a","b","c"].
# Single-segment keys produce ["a"]. Empty segments are rejected.
dotted_to_jq_path() {
  local key="$1"
  local IFS='.'
  # shellcheck disable=SC2206
  local -a parts=( $key )
  local out="["
  local first=1 seg
  for seg in "${parts[@]}"; do
    if [[ -z "$seg" ]]; then
      echo "manifest-update: bad dotted key (empty segment): $key" >&2
      exit 2
    fi
    if (( first )); then
      first=0
    else
      out+=","
    fi
    # JSON-escape the segment by encoding via jq -nR.
    local escaped
    escaped="$(printf '%s' "$seg" | jq -nR 'inputs')"
    out+="$escaped"
  done
  out+="]"
  printf '%s' "$out"
}

# Returns the leaf segment of a dotted key (the part after the last `.`).
leaf_of() {
  local key="$1"
  printf '%s' "${key##*.}"
}

# Builds two parallel structures from the trailing key=value pairs:
#   - JQ_ARGS: array of jq argument flags ( --arg vN VAL ... --argjson pN PATH ... )
#   - CHAIN:   pipeline fragment ( | setpath($p0; $v0) | ... )
# Caller declares JQ_ARGS and CHAIN before invoking.
build_chain() {
  local i=0 pair key value path_arr leaf
  for pair in "$@"; do
    if [[ "$pair" != *=* ]]; then
      echo "manifest-update: bad pair (no '='): $pair" >&2
      exit 2
    fi
    key="${pair%%=*}"
    value="${pair#*=}"
    if [[ -z "$key" ]]; then
      echo "manifest-update: empty key in pair: $pair" >&2
      exit 2
    fi
    path_arr="$(dotted_to_jq_path "$key")"
    leaf="$(leaf_of "$key")"
    JQ_ARGS+=( --argjson "p$i" "$path_arr" )
    case "$value" in
      now)
        JQ_ARGS+=( --arg "v$i" "$TS_NOW" )
        CHAIN+=" | setpath(\$p$i; \$v$i)"
        ;;
      null)
        CHAIN+=" | setpath(\$p$i; null)"
        ;;
      +1)
        # Increment leaf counter: read current via getpath, default 0.
        CHAIN+=" | setpath(\$p$i; ((getpath(\$p$i) // 0) + 1))"
        ;;
      *)
        if is_numeric_leaf "$leaf" && [[ "$value" =~ ^-?[0-9]+(\.[0-9]+)?$ ]]; then
          JQ_ARGS+=( --argjson "v$i" "$value" )
        elif is_boolean_leaf "$leaf" && { [[ "$value" == "true" ]] || [[ "$value" == "false" ]]; }; then
          # Bug 2 fix: coerce known-boolean fields to JSON booleans (--argjson
          # parses `true` / `false` as boolean literals).
          JQ_ARGS+=( --argjson "v$i" "$value" )
        else
          JQ_ARGS+=( --arg "v$i" "$value" )
        fi
        CHAIN+=" | setpath(\$p$i; \$v$i)"
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
    exit 3
  fi
}

case "$MODE" in
  entry)
    if [[ $# -lt 2 ]]; then usage; fi
    ENTRY_ID="$1"; shift
    if [[ $# -eq 0 ]]; then usage; fi

    # Detect status-change pairs to also append to history[]. Only top-level
    # `status=` triggers history; nested `mode_state.status=` does not.
    NEW_STATUS=""
    for pair in "$@"; do
      if [[ "$pair" == status=* ]]; then
        NEW_STATUS="${pair#status=}"
      fi
    done

    acquire_lock

    if ! jq -e --arg id "$ENTRY_ID" 'any(.entries[]?; .id == $id)' "$MANIFEST" >/dev/null 2>&1; then
      echo "manifest-update: entry id not found in $MANIFEST: $ENTRY_ID" >&2
      exit 2
    fi

    JQ_ARGS=( --arg id "$ENTRY_ID" --arg ts "$TS_NOW" --arg actor "$ACTOR" )
    if [[ -n "$REASON" ]]; then
      JQ_ARGS+=( --arg reason "$REASON" )
      REASON_JQ='$reason'
    else
      REASON_JQ='null'
    fi
    CHAIN=""
    build_chain "$@"

    # Single-pass jq filter:
    #   1. Capture old status as $old_status.
    #   2. Apply CHAIN to the matching entry (CHAIN starts with " | ", so we
    #      anchor on `.` and the pipeline composes cleanly).
    #   3. If status changed, append a history row with actor/reason.
    if [[ -n "$NEW_STATUS" ]]; then
      FILTER='
        . as $root
        | ($root.entries | map(select(.id == $id))[0].status // null) as $old_status
        | .entries |= map(
            if .id == $id then (.'"$CHAIN"') else . end
          )
        | (.entries | map(select(.id == $id))[0].status // null) as $new_status
        | .history = ((.history // []) + [
            { ts: $ts, entry_id: $id, from: $old_status, to: $new_status,
              actor: $actor, reason: '"$REASON_JQ"' }
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
      exit 4
    fi
    if ! jq -e . "$TMP" >/dev/null 2>&1; then
      rm -f "$TMP"
      echo "manifest-update: produced invalid JSON; aborting" >&2
      exit 4
    fi
    if ! mv -f "$TMP" "$MANIFEST"; then
      rm -f "$TMP"
      echo "manifest-update: failed to write $MANIFEST" >&2
      exit 3
    fi
    ;;

  top)
    if [[ $# -eq 0 ]]; then usage; fi
    acquire_lock

    JQ_ARGS=( --arg ts "$TS_NOW" )
    CHAIN=""
    build_chain "$@"

    # Top-level chain composes from `.` — CHAIN already begins with " | ".
    FILTER=".${CHAIN}"

    TMP="$(mktemp "${MANIFEST}.tmp.XXXXXX")"
    if ! jq "${JQ_ARGS[@]}" "$FILTER" "$MANIFEST" > "$TMP" 2>/dev/null; then
      rm -f "$TMP"
      echo "manifest-update: jq filter failed for top-level update (pairs=$*)" >&2
      exit 4
    fi
    if ! jq -e . "$TMP" >/dev/null 2>&1; then
      rm -f "$TMP"
      echo "manifest-update: produced invalid JSON; aborting" >&2
      exit 4
    fi
    if ! mv -f "$TMP" "$MANIFEST"; then
      rm -f "$TMP"
      echo "manifest-update: failed to write $MANIFEST" >&2
      exit 3
    fi
    ;;

  *)
    usage
    ;;
esac
