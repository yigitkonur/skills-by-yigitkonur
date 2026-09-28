#!/usr/bin/env bash
# ==============================================================================
# worktree-manager.sh — Astro Audit Worktree Lifecycle CLI
# ==============================================================================
set -euo pipefail

usage() {
  cat << 'EOF'
Usage:
  bash scripts/worktree-manager.sh setup <ID> [BASE_REF]
  bash scripts/worktree-manager.sh status [ID]
  bash scripts/worktree-manager.sh rebase <ID>
  bash scripts/worktree-manager.sh remove <ID>
  bash scripts/worktree-manager.sh prune

Examples:
  bash scripts/worktree-manager.sh setup 64 origin/main
  bash scripts/worktree-manager.sh rebase 64
  bash scripts/worktree-manager.sh remove 64
EOF
  exit 1
}

CMD="${1:-}"
ID="${2:-}"
BASE_REF="${3:-origin/main}"

case "$CMD" in
  setup)
    [ -n "$ID" ] || usage
    WT_PATH=".worktrees/wt-${ID}"
    BRANCH="fix/audit-${ID}"
    echo "⚙️ Provisioning worktree for Workload $ID at $WT_PATH on branch $BRANCH..."
    git branch -D "$BRANCH" 2>/dev/null || true
    git worktree add -B "$BRANCH" "$WT_PATH" "$BASE_REF"
    echo "✅ Worktree created successfully at $WT_PATH"
    ;;

  status)
    if [ -n "$ID" ]; then
      WT_PATH=".worktrees/wt-${ID}"
      if [ -d "$WT_PATH" ]; then
        echo "=== Status of $WT_PATH ==="
        git -C "$WT_PATH" status -s
        git -C "$WT_PATH" log -n 1 --oneline
      else
        echo "❌ Worktree $WT_PATH does not exist."
        exit 1
      fi
    else
      echo "=== Active Audit Worktrees ==="
      git worktree list | grep wt- || echo "Zero active audit worktrees."
    fi
    ;;

  rebase)
    [ -n "$ID" ] || usage
    WT_PATH=".worktrees/wt-${ID}"
    [ -d "$WT_PATH" ] || { echo "❌ Worktree $WT_PATH not found"; exit 1; }
    echo "🔄 Rebasing $WT_PATH onto origin/main..."
    git -C "$WT_PATH" fetch origin main
    git -C "$WT_PATH" rebase origin/main
    echo "✅ Rebase complete for $WT_PATH"
    ;;

  remove)
    [ -n "$ID" ] || usage
    WT_PATH=".worktrees/wt-${ID}"
    if [ -d "$WT_PATH" ]; then
      echo "🗑️ Removing worktree $WT_PATH..."
      git worktree remove "$WT_PATH" --force
      git worktree prune
      echo "✅ Removed and pruned $WT_PATH"
    else
      echo "Worktree $WT_PATH already removed."
    fi
    ;;

  prune)
    echo "🧹 Pruning stale git worktrees..."
    git worktree prune -v
    echo "✅ Pruning complete."
    ;;

  *)
    usage
    ;;
esac
