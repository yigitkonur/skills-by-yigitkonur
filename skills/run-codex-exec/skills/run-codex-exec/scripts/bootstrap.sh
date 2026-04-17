#!/usr/bin/env bash
# bootstrap.sh — one-command pre-flight for a new project.
#
# Creates the monitor root, copies the other three scripts into it, pins the
# baseline to current HEAD, verifies codex is authenticated, and advises on
# .gitignore / build-tool exclude lines the skill requires.
#
# Usage (from inside the project repo):
#   bash /path/to/skill/scripts/bootstrap.sh [MONITOR_ROOT]
#
# Environment:
#   PROJECT_DIR    — repo root (default: cwd)
#   MONITOR_ROOT   — where logs + baseline.sha live (default: /tmp/codex-monitor)
#   WT_DIR_NAME    — worktree subdir name (default: .worktrees)
set -uo pipefail

PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
MONITOR_ROOT="${1:-${MONITOR_ROOT:-/tmp/codex-monitor}}"
WT_DIR_NAME="${WT_DIR_NAME:-.worktrees}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_DIR"

echo "━━━ codex-exec pre-flight ━━━"
echo "  project : $PROJECT_DIR"
echo "  monitor : $MONITOR_ROOT"
echo "  worktree: $WT_DIR_NAME/"

# ── 1. Sanity: is this a git repo? ─────────────────────────────
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "✗ $PROJECT_DIR is not a git repo. Run \`git init\` first." >&2
  exit 1
fi

# ── 2. Is codex authenticated? ─────────────────────────────────
if ! command -v codex >/dev/null 2>&1; then
  echo "✗ \`codex\` CLI not found on PATH. Install with: npm i -g @openai/codex" >&2
  exit 1
fi
echo "✓ codex: $(codex --version)"

# ── 3. Monitor root ────────────────────────────────────────────
mkdir -p "$MONITOR_ROOT/logs"
echo "✓ monitor root: $MONITOR_ROOT/logs/"

# ── 4. Copy scripts in ─────────────────────────────────────────
for s in codex-monitor.sh codex-wrapper.sh setup-worktree.sh codex-json-filter.sh; do
  if [[ -f "$SCRIPT_DIR/$s" ]]; then
    cp "$SCRIPT_DIR/$s" "$MONITOR_ROOT/$s"
    chmod +x "$MONITOR_ROOT/$s"
    echo "✓ installed: $MONITOR_ROOT/$s"
  else
    echo "⚠ missing source: $SCRIPT_DIR/$s" >&2
  fi
done

# ── 5. Pin baseline ────────────────────────────────────────────
if [[ -f "$MONITOR_ROOT/baseline.sha" ]]; then
  OLD=$(cat "$MONITOR_ROOT/baseline.sha")
  echo "ℹ baseline already pinned at ${OLD:0:8} (delete $MONITOR_ROOT/baseline.sha to re-pin)"
else
  git rev-parse HEAD > "$MONITOR_ROOT/baseline.sha"
  echo "✓ baseline pinned: $(cat "$MONITOR_ROOT/baseline.sha" | cut -c1-8)"
fi

# ── 6. .gitignore advice ───────────────────────────────────────
if ! git check-ignore -q "$WT_DIR_NAME/.test" 2>/dev/null; then
  echo ""
  echo "⚠ $WT_DIR_NAME/ is NOT in .gitignore. Add this line and commit:"
  echo "    $WT_DIR_NAME/"
  echo "  Without it, the parent repo's \`git status\` shows every worktree file as untracked."
else
  echo "✓ .gitignore excludes $WT_DIR_NAME/"
fi

# ── 7. Build-tool exclude advice ───────────────────────────────
declare -a MISSES=()
if [[ -f "$PROJECT_DIR/tsconfig.json" ]]; then
  grep -q "$WT_DIR_NAME" "$PROJECT_DIR/tsconfig.json" || MISSES+=("tsconfig.json: add \"$WT_DIR_NAME/**\" to \"exclude\"")
fi
for v in vitest.config.ts vitest.config.mts vitest.config.js; do
  [[ -f "$PROJECT_DIR/$v" ]] && { grep -q "$WT_DIR_NAME" "$PROJECT_DIR/$v" || MISSES+=("$v: add \"**/$WT_DIR_NAME/**\" to test.exclude"); break; }
done
for e in eslint.config.mjs eslint.config.js .eslintrc.cjs .eslintrc.json; do
  [[ -f "$PROJECT_DIR/$e" ]] && { grep -q "$WT_DIR_NAME" "$PROJECT_DIR/$e" || MISSES+=("$e: add \"$WT_DIR_NAME/**\" to globalIgnores() / ignorePatterns"); break; }
done
if [[ ${#MISSES[@]} -gt 0 ]]; then
  echo ""
  echo "⚠ Build tools will scan $WT_DIR_NAME/ unless you exclude it:"
  for m in "${MISSES[@]}"; do echo "   • $m"; done
  echo "  Without these, running tsc/vitest/eslint in main picks up sibling-worktree files."
fi

# ── 8. Quick-start next steps ──────────────────────────────────
cat <<EOF

━━━ ready ━━━
Next steps:

  # Create a worktree (pass a short name + branch name):
  $MONITOR_ROOT/setup-worktree.sh feature-name branch/name

  # Start the monitor (long-running; pick ONE of):
  #   a) In Claude Code: use the Monitor tool with command=\$MONITOR_ROOT/codex-monitor.sh
  #   b) Standalone background: PROJECT_DIR=$PROJECT_DIR MONITOR_ROOT=$MONITOR_ROOT $MONITOR_ROOT/codex-monitor.sh &

  # Dispatch a codex agent (auto-commit wrapper):
  PROJECT_DIR=$PROJECT_DIR MONITOR_ROOT=$MONITOR_ROOT \\
    $MONITOR_ROOT/codex-wrapper.sh feature-name plan-slug "YOUR TASK PROMPT" &

  # OR for streaming (single agent, live JSONL events in chat):
  codex exec --json --full-auto -C $PROJECT_DIR "YOUR TASK" 2>&1 \\
    | $MONITOR_ROOT/codex-json-filter.sh

See references/workflow-playbook.md for the canonical 4-step recipe.
EOF
