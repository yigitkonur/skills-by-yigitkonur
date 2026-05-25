#!/usr/bin/env bash
# orient.sh — read-only "world snapshot" for the run-babysitter skill (phase ① ORIENT).
# Usage: orient.sh [last_seen_sha]
# Prints a markdown block to stdout. NEVER mutates the repo. Best-effort: a missing
# gh, missing remote, or disabled issues are reported (so the cycle can degrade to
# draft-only), not treated as fatal.
set -uo pipefail

last_seen="${1:-}"
emit() { printf '%s\n' "$*"; }

# --- git context -------------------------------------------------------------
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  emit "## ORIENT — ERROR"
  emit "Not inside a git repository. The babysitter must run inside a git repo."
  exit 1
fi

head_sha="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
dirty_count="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"

emit "## ORIENT — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
emit ""
emit "### Git"
emit "- HEAD: \`$head_sha\`   branch: \`$branch\`   dirty files: $dirty_count"
emit ""
emit "### Commits since last cycle"
if [ -n "$last_seen" ] && git cat-file -e "${last_seen}^{commit}" 2>/dev/null; then
  range="${last_seen}..HEAD"
  n="$(git rev-list --count "$range" 2>/dev/null || echo 0)"
  emit "- since \`$last_seen\` ($n commit(s)):"
  if [ "$n" = "0" ]; then
    emit "  - (none — no new commits since last run)"
  else
    git log --oneline --no-decorate "$range" 2>/dev/null | sed 's/^/  - /' || true
  fi
else
  [ -n "$last_seen" ] && emit "- last-seen \`$last_seen\` not found; showing recent history:"
  git log --oneline --no-decorate -15 2>/dev/null | sed 's/^/  - /' || true
fi

# --- GitHub context ----------------------------------------------------------
emit ""
emit "### GitHub"
if ! command -v gh >/dev/null 2>&1; then
  emit "- gh: NOT INSTALLED → degrade to draft-only for issue filing."
elif ! gh auth status >/dev/null 2>&1; then
  emit "- gh: installed but NOT AUTHENTICATED → degrade to draft-only."
else
  repo="$(gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || echo unknown)"
  emit "- repo: \`$repo\`"
  issues_err="$(gh issue list --limit 1 2>&1 >/dev/null || true)"
  if printf '%s' "$issues_err" | grep -qi 'disabled'; then
    emit "- issues: DISABLED on this repo → degrade to draft-only."
  else
    open_n="$(gh issue list --state open --limit 100 --json number --jq 'length' 2>/dev/null || echo '?')"
    emit "- open issues: $open_n"
    emit "- babysitter-authored open issues:"
    gh issue list --state open --label babysitter --json number,title \
      --jq '.[] | "  - #\(.number) \(.title)"' 2>/dev/null \
      || emit "  - (marker label not present yet, or none)"
  fi
  runs="$(gh run list --limit 3 \
    --json status,conclusion,workflowName,headBranch \
    --jq '.[] | "  - \(.workflowName): \(.status)/\(.conclusion // "—") [\(.headBranch)]"' 2>/dev/null || true)"
  if [ -n "$runs" ]; then
    emit "- recent CI runs:"
    printf '%s\n' "$runs"
  fi
fi

emit ""
emit "_End ORIENT. Read-only snapshot; no repo state changed._"
