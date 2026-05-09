#!/usr/bin/env bash
# codex-flags.sh — single source of truth for every codex spawn the skill makes.
#
# Sourced (not executed) by every runner in scripts/. After sourcing, an array
# named CODEX_FLAGS is exported with the policy the skill enforces on every
# `codex exec` it fans out. Callers expand it as "${CODEX_FLAGS[@]}".
#
#   . "$(dirname "$0")/codex-flags.sh"
#   codex exec "${CODEX_FLAGS[@]}" --json -o "$out" "$prompt"
#
# Why an array, not a string: codex flag values like
# `model_reasoning_effort=xhigh` contain `=` and need word-boundary safety
# under `set -u` and `bash -c` subshells (xargs spawns these). String-splitting
# into argv loses that.
#
# Why hard-coded model/effort: the skill is opinionated by design. The user
# opts in to bypass + xhigh + gpt-5.5 when they invoke the skill. Per-spawn
# overrides are a foot-gun (silent semantic drift); per-session overrides are
# documented in references/universal/codex-flags.md.

# Idempotent — sourcing twice is fine.
if [[ "${ORCHESTRATE_CODEX_FLAGS_LOADED:-}" == "1" ]]; then
  return 0 2>/dev/null || exit 0
fi
ORCHESTRATE_CODEX_FLAGS_LOADED=1

# Per-session overrides (from env). The skill documents these in
# references/universal/codex-flags.md.
CODEX_MODEL="${ORCHESTRATE_CODEX_MODEL:-gpt-5.5}"
CODEX_EFFORT="${ORCHESTRATE_CODEX_EFFORT:-xhigh}"

# The flag set every direct `codex exec` invocation MUST carry. Order matters
# for reading the resulting command line; --dangerously-bypass... comes first
# so it's visible without scrolling.
CODEX_FLAGS=(
  --dangerously-bypass-approvals-and-sandbox
  --skip-git-repo-check
  -m "$CODEX_MODEL"
  -c "model_reasoning_effort=$CODEX_EFFORT"
)

# `codex review` (and `codex exec review`) accept a narrower flag set. The
# review subcommand has no --skip-git-repo-check, no -o, no --json, no -m.
# Use this array for review spawns.
CODEX_REVIEW_FLAGS=(
  -c "model_reasoning_effort=$CODEX_EFFORT"
)

export CODEX_MODEL CODEX_EFFORT CODEX_FLAGS CODEX_REVIEW_FLAGS
