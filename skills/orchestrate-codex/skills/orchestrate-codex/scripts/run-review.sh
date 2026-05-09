#!/usr/bin/env bash
# run-review.sh — review mode convergence runner.
#
# One invocation loops review rounds until every branch reaches a terminal
# state: converged, blocked, failed, or cap_reached. Each round uses native
# `codex exec review`, normalizes findings for classify-review-feedback.py,
# and records the terminal decision in the manifest.
#
# Usage:
#   run-review.sh --manifest <manifest.json> [--base main] [--max-rounds 10]
#                 [--concurrency N] [--only id,id] [--dry-run]

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=codex-flags.sh
. "$SCRIPT_DIR/codex-flags.sh"

MANIFEST="${ORCHESTRATE_MANIFEST:-}"
DRY_RUN="${DRY_RUN:-0}"
JOBS="${JOBS:-4}"
BASE_REF="${BASE_REF:-main}"
MAX_ROUNDS="${MAX_ROUNDS:-10}"
PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
FILTER_LEVEL="${FILTER_LEVEL:-normal}"
STATE_DIR="${STATE_DIR:-}"
ONLY_IDS="${ONLY_IDS:-}"
CONCURRENCY_JUSTIFICATION="${ORCHESTRATE_CONCURRENCY_JUSTIFICATION:-}"
REVIEW_FIXTURES="${ORCHESTRATE_REVIEW_FIXTURES:-}"
export ORCHESTRATE_MODE="${ORCHESTRATE_MODE:-review}"

usage() {
  cat >&2 <<'EOF'
run-review.sh — run codex exec review until terminal branch states.

Usage:
  run-review.sh --manifest <manifest.json> [--base main] [--max-rounds 10]
                [--concurrency N] [--only id,id] [--dry-run]
EOF
  exit 3
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest) MANIFEST="$2"; shift 2 ;;
    --base) BASE_REF="$2"; shift 2 ;;
    --max-rounds) MAX_ROUNDS="$2"; shift 2 ;;
    --concurrency|--jobs) JOBS="$2"; shift 2 ;;
    --project-dir) PROJECT_DIR="$2"; shift 2 ;;
    --state-dir) STATE_DIR="$2"; shift 2 ;;
    --only) ONLY_IDS="$2"; shift 2 ;;
    --i-have-measured) CONCURRENCY_JUSTIFICATION="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage ;;
    *)
      echo "unknown arg: $1" >&2
      usage
      ;;
  esac
done

[[ -n "$MANIFEST" ]] || usage
export ORCHESTRATE_MANIFEST="$MANIFEST"

if [[ ! -f "$MANIFEST" ]]; then
  echo "FATAL manifest not found: $MANIFEST" >&2
  exit 1
fi
if ! jq -e . "$MANIFEST" >/dev/null 2>&1; then
  echo "FATAL manifest is not valid JSON: $MANIFEST" >&2
  exit 1
fi
if ! [[ "$MAX_ROUNDS" =~ ^[1-9][0-9]*$ ]]; then
  echo "FATAL --max-rounds must be a positive integer, got: $MAX_ROUNDS" >&2
  exit 3
fi
if ! [[ "$JOBS" =~ ^[1-9][0-9]*$ ]]; then
  echo "FATAL JOBS must be a positive integer, got: $JOBS" >&2
  exit 3
fi
if [[ "$JOBS" -gt 100 ]]; then
  echo "FATAL JOBS=$JOBS exceeds hard cap of 100" >&2
  exit 3
fi
if [[ "$JOBS" -gt 20 && -z "$CONCURRENCY_JUSTIFICATION" ]]; then
  echo "FATAL JOBS=$JOBS exceeds 20; pass --i-have-measured <justification>" >&2
  exit 3
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "FATAL jq not found on PATH" >&2
  exit 2
fi
if ! command -v codex >/dev/null 2>&1 && [[ "$DRY_RUN" != "1" ]]; then
  echo "FATAL codex CLI not found on PATH" >&2
  exit 2
fi

STATE_DIR="${STATE_DIR:-$(dirname "$MANIFEST")}"
ROUNDS_DIR="$STATE_DIR/rounds"
mkdir -p "$ROUNDS_DIR"
JSON_FILTER="$SCRIPT_DIR/codex-json-filter.sh"

build_worklist() {
  local out="$1"
  jq -r '
    .entries[]
    | select((.status // "queued") != "converged"
             and (.status // "queued") != "blocked"
             and (.status // "queued") != "failed"
             and (.status // "queued") != "cap_reached")
    | [
        .id,
        (.slug // .id),
        (.branch // ""),
        (.base_branch // "'"$BASE_REF"'"),
        (.worktree_path // ""),
        (.status // "queued")
      ]
    | @tsv
  ' "$MANIFEST" > "$out"

  if [[ -n "$ONLY_IDS" ]]; then
    local filtered
    filtered="$(mktemp)"
    awk -F'\t' -v only="$ONLY_IDS" '
      BEGIN { n = split(only, ids, ","); for (i = 1; i <= n; i++) wanted[ids[i]] = 1 }
      wanted[$1]
    ' "$out" > "$filtered"
    mv "$filtered" "$out"
  fi
}

write_review_json_from_text() {
  local raw="$1" out="$2" branch="$3" round="$4"
  jq -n --arg branch "$branch" --argjson round "$round" --rawfile raw "$raw" \
    '{branch:$branch, round:$round, raw_text:$raw}' > "$out"
}

run_one() {
  local row="$1"
  IFS=$'\t' read -r id slug branch base wt_path _status <<<"$row"

  if [[ -z "$branch" ]]; then
    echo "FAIL  $id (no branch in manifest entry)"
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
      status=failed finished_at=now last_error="missing branch" 2>/dev/null || true
    return 1
  fi

  local findings="$ROUNDS_DIR/${slug}.r${ROUND_NUM}.md"
  local jsonl="$ROUNDS_DIR/${slug}.r${ROUND_NUM}.jsonl"
  local errlog="$ROUNDS_DIR/${slug}.r${ROUND_NUM}.err.log"
  local review_json="$ROUNDS_DIR/${slug}.r${ROUND_NUM}.review.json"
  local class_json="$ROUNDS_DIR/${slug}.r${ROUND_NUM}.classification.json"

  echo "START $id (round $ROUND_NUM branch=$branch base=$base)"
  "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
    status=running started_at=now attempts=+1 round="$ROUND_NUM" 2>/dev/null || true

  local wt_resolved=""
  if [[ -n "$wt_path" && -d "$wt_path" ]]; then
    wt_resolved="$wt_path"
  elif [[ "$DRY_RUN_LOCAL" == "1" ]]; then
    wt_resolved="<dry-run-wt>/$slug"
  else
    local setup_out
    if ! setup_out="$(ALLOW_REUSE=1 "$SCRIPT_DIR_ABS/setup-worktree.sh" "$slug" "$branch" "$base" 2>&1)"; then
      echo "FAIL  $id (setup-worktree failed)"
      printf '%s\n' "$setup_out" | sed 's/^/  [setup] /'
      "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
        status=failed finished_at=now last_error="setup-worktree failed" 2>/dev/null || true
      return 1
    fi
    wt_resolved="$(printf '%s\n' "$setup_out" | awk -F= '/^WORKTREE_PATH=/ { sub(/^WORKTREE_PATH=/, ""); print; exit }')"
    if [[ -z "$wt_resolved" ]]; then
      echo "FAIL  $id (could not parse WORKTREE_PATH from setup-worktree)"
      "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
        status=failed finished_at=now last_error="setup-worktree parse failed" 2>/dev/null || true
      return 1
    fi
  fi
  "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
    worktree_path="$wt_resolved" 2>/dev/null || true

  local -a flags=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && flags+=("$f")
  done <<<"$CODEX_FLAGS_STR"

  if [[ "$DRY_RUN_LOCAL" == "1" ]]; then
    if [[ -n "$REVIEW_FIXTURES_LOCAL" && -f "$REVIEW_FIXTURES_LOCAL/${slug}.r${ROUND_NUM}.json" ]]; then
      cp "$REVIEW_FIXTURES_LOCAL/${slug}.r${ROUND_NUM}.json" "$review_json"
      jq -r '.raw_text // (.items // [] | tostring)' "$review_json" > "$findings"
    elif [[ -n "$REVIEW_FIXTURES_LOCAL" && -f "$REVIEW_FIXTURES_LOCAL/${slug}.r${ROUND_NUM}.md" ]]; then
      cp "$REVIEW_FIXTURES_LOCAL/${slug}.r${ROUND_NUM}.md" "$findings"
      write_review_json_from_text "$findings" "$review_json" "$branch" "$ROUND_NUM"
    else
      jq -n --arg branch "$branch" --argjson round "$ROUND_NUM" \
        '{branch:$branch, round:$round, items:[]}' > "$review_json"
      printf 'dry-run review: no findings for %s round %s\n' "$branch" "$ROUND_NUM" > "$findings"
    fi
    printf '{"type":"turn.completed","dry_run":true}\n' > "$jsonl"
  else
    local start_ts end_ts elapsed exit_code
    start_ts="$(date +%s)"
    set +e
    if [[ -x "$JSON_FILTER" ]]; then
      (cd "$wt_resolved" && codex exec review "${flags[@]}" --base "$base" --json -o "$findings" 2>"$errlog") \
        | tee "$jsonl" \
        | CODEX_FILTER_LEVEL="$FILTER_LEVEL" "$JSON_FILTER" \
        | sed "s/^/[review:$slug] /"
      exit_code="${PIPESTATUS[0]}"
    else
      (cd "$wt_resolved" && codex exec review "${flags[@]}" --base "$base" --json -o "$findings" 2>"$errlog") \
        | tee "$jsonl" \
        | sed "s/^/[review:$slug] /"
      exit_code="${PIPESTATUS[0]}"
    fi
    set -u
    end_ts="$(date +%s)"
    elapsed=$(( end_ts - start_ts ))
    if [[ "$exit_code" -ne 0 ]]; then
      echo "FAIL  $id (codex review exit=$exit_code runtime=${elapsed}s; see $errlog)"
      "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
        status=failed finished_at=now exit_code="$exit_code" last_error="codex review exit $exit_code" \
        last_findings_path="$findings" 2>/dev/null || true
      return 1
    fi
    if [[ ! -s "$findings" ]]; then
      echo "FAIL  $id (codex review exit=0 but findings empty)"
      "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
        status=failed finished_at=now exit_code=0 last_error="empty findings" \
        last_findings_path="$findings" 2>/dev/null || true
      return 1
    fi
    write_review_json_from_text "$findings" "$review_json" "$branch" "$ROUND_NUM"
  fi

  local classify_out classify_rc major_count
  set +e
  classify_out="$(python3 "$SCRIPT_DIR_ABS/classify-review-feedback.py" --review-json "$review_json" --json 2>"$class_json.err")"
  classify_rc=$?
  set -u
  if [[ "$classify_rc" -eq 2 ]]; then
    echo "FAIL  $id (classifier failed; see $class_json.err)"
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
      status=failed finished_at=now last_error="classifier failed" \
      last_findings_path="$findings" 2>/dev/null || true
    return 1
  fi
  printf '%s\n' "$classify_out" > "$class_json"
  major_count="$(jq -r '(.counts.major // 0)' "$class_json")"

  if [[ "$major_count" -eq 0 ]]; then
    echo "DONE  $id (converged round=$ROUND_NUM findings=$findings)"
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
      status=converged finished_at=now exit_code=0 \
      last_findings_path="$findings" classification_path="$class_json" 2>/dev/null || true
    return 0
  fi

  echo "DONE  $id (blocked: $major_count major finding(s); see $class_json)"
  "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
    status=blocked finished_at=now exit_code=0 \
    last_error="major review findings require main-agent evaluation/apply queue" \
    last_findings_path="$findings" classification_path="$class_json" 2>/dev/null || true
}

CODEX_FLAGS_STR="$(printf '%s\n' "${CODEX_FLAGS[@]}")"
export CODEX_FLAGS_STR
export SCRIPT_DIR_ABS="$SCRIPT_DIR"
export ORCHESTRATE_MANIFEST="$MANIFEST"
export ROUNDS_DIR JSON_FILTER FILTER_LEVEL PROJECT_DIR
export DRY_RUN_LOCAL="$DRY_RUN"
export REVIEW_FIXTURES_LOCAL="$REVIEW_FIXTURES"
export -f run_one write_review_json_from_text

round=1
while [[ "$round" -le "$MAX_ROUNDS" ]]; do
  WORKLIST="$(mktemp)"
  build_worklist "$WORKLIST"
  if [[ ! -s "$WORKLIST" ]]; then
    rm -f "$WORKLIST"
    break
  fi
  echo "[run-review] manifest: $MANIFEST"
  echo "[run-review] round:    $round/$MAX_ROUNDS"
  echo "[run-review] entries:  $(wc -l < "$WORKLIST" | tr -d ' ') non-terminal"
  export ROUND_NUM="$round"
  awk -F'\t' 'NF >= 6' "$WORKLIST" \
    | tr '\n' '\0' \
    | xargs -0 -n 1 -P "$JOBS" bash -c 'run_one "$0"'
  rm -f "$WORKLIST"
  round=$((round + 1))
done

if [[ "$round" -gt "$MAX_ROUNDS" ]]; then
  # Any branch still not terminal after the cap becomes cap_reached.
  jq -r '
    .entries[]
    | select((.status // "queued") != "converged"
             and (.status // "queued") != "blocked"
             and (.status // "queued") != "failed"
             and (.status // "queued") != "cap_reached")
    | .id
  ' "$MANIFEST" | while IFS= read -r id; do
    [[ -n "$id" ]] || continue
    "$SCRIPT_DIR/manifest-update.sh" entry "$MANIFEST" "$id" \
      status=cap_reached finished_at=now last_error="review max rounds reached" 2>/dev/null || true
    echo "FAIL  $id (review max rounds reached)"
  done
fi

echo "--- all jobs finished ---"
