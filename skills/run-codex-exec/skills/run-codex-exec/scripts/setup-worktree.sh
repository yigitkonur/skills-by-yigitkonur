#!/usr/bin/env bash
# setup-worktree.sh — create a git worktree for a codex agent, link shared
# heavy artifacts (node_modules, .env.local), regenerate any codegen that
# needs to be per-worktree (Prisma client), and verify the baseline compiles.
#
# Usage: setup-worktree.sh <worktree-name> <branch-name> [<base-branch>]
#
# Example: setup-worktree.sh wave1-reports wave1/reports-scheduled-pipeline main
#
# Environment variables:
#   PROJECT_DIR        — repo root (default: cwd)
#   WORKTREE_DIR_NAME  — worktree subdir (default: .worktrees)
#   LINK_NODE_MODULES  — 1 to symlink parent node_modules (default: 1)
#   LINK_ENV_FILE      — path to env file to symlink, empty to skip (default: .env.local)
#   PRISMA_GENERATE    — 1 to run `npx prisma generate` after setup (default: 1 if schema.prisma exists)
set -uo pipefail

WORKTREE_NAME="${1:?worktree name required (arg 1)}"
BRANCH_NAME="${2:?branch name required (arg 2)}"
BASE_BRANCH="${3:-main}"

PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
WT_DIR_NAME="${WORKTREE_DIR_NAME:-.worktrees}"
WORKTREE_DIR="$PROJECT_DIR/$WT_DIR_NAME/$WORKTREE_NAME"
LINK_NODE_MODULES="${LINK_NODE_MODULES:-1}"
LINK_ENV_FILE="${LINK_ENV_FILE:-.env.local}"

# Auto-detect Prisma
if [[ -z "${PRISMA_GENERATE:-}" ]]; then
  if [[ -f "$PROJECT_DIR/prisma/schema.prisma" ]]; then
    PRISMA_GENERATE=1
  else
    PRISMA_GENERATE=0
  fi
fi

cd "$PROJECT_DIR"

# ── Sanity checks ─────────────────────────────────────────────
if [[ ! -d .git ]]; then
  echo "ERROR: $PROJECT_DIR is not a git repo (no .git directory)." >&2
  exit 1
fi

if [[ -d "$WORKTREE_DIR" ]]; then
  echo "ERROR: worktree $WORKTREE_DIR already exists. Remove it first or use a different name." >&2
  exit 1
fi

# ── Verify .gitignore excludes worktrees ──────────────────────
if ! git check-ignore -q "$WT_DIR_NAME/.test" 2>/dev/null; then
  echo "WARN: $WT_DIR_NAME/ is not in .gitignore. Worktree contents may leak into git status."
  echo "      Add '$WT_DIR_NAME/' to .gitignore and commit before creating worktrees."
  echo "      Continuing anyway — but expect noise."
fi

# ── Create worktree ───────────────────────────────────────────
echo "[setup] creating worktree $WORKTREE_DIR on branch $BRANCH_NAME from $BASE_BRANCH"
mkdir -p "$(dirname "$WORKTREE_DIR")"
git worktree add "$WORKTREE_DIR" -b "$BRANCH_NAME" "$BASE_BRANCH"

# ── Link shared artifacts ─────────────────────────────────────
if [[ "$LINK_NODE_MODULES" == "1" && -d "$PROJECT_DIR/node_modules" ]]; then
  echo "[setup] symlinking node_modules"
  ln -s "../../node_modules" "$WORKTREE_DIR/node_modules"
fi

if [[ -n "$LINK_ENV_FILE" && -f "$PROJECT_DIR/$LINK_ENV_FILE" ]]; then
  echo "[setup] symlinking $LINK_ENV_FILE"
  ln -s "../../$LINK_ENV_FILE" "$WORKTREE_DIR/$LINK_ENV_FILE" 2>/dev/null || true
fi

# ── Regenerate per-worktree codegen ───────────────────────────
if [[ "$PRISMA_GENERATE" == "1" ]]; then
  echo "[setup] regenerating Prisma client"
  (cd "$WORKTREE_DIR" && npx prisma generate 2>&1 | tail -2)
fi

# ── Verify baseline compiles (advisory) ───────────────────────
echo "[setup] verifying baseline tsc"
if command -v npx >/dev/null && [[ -f "$WORKTREE_DIR/tsconfig.json" ]]; then
  TSC_ERRORS=$(cd "$WORKTREE_DIR" && npx tsc --noEmit 2>&1 | grep -c "error TS" || echo "0")
  if [[ "$TSC_ERRORS" != "0" ]]; then
    echo "WARN: baseline has $TSC_ERRORS tsc errors. Codex will inherit these — fix on $BASE_BRANCH first for a clean baseline."
  else
    echo "[setup] baseline tsc: 0 errors"
  fi
fi

echo "[setup] ready: $WORKTREE_DIR (branch $BRANCH_NAME)"
echo "[setup] next: codex-wrapper.sh $WORKTREE_NAME <plan-slug> \"<task prompt>\""
