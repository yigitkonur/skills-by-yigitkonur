#!/usr/bin/env bash
# setup-worktree.sh — create a git worktree for an orchestrate-codex worker,
# symlink shared heavy artifacts (node_modules, .env.local), and run
# per-worktree codegen (Prisma client, etc).
#
# Naming convention: `../<repo>-wt-<mode>-<slug>` (sibling of the repo,
# not inside it). Callers that prefer in-repo placement can override by
# setting WORKTREE_DIR_NAME to `<repo>/<dir>/<slug>` or by passing a
# fully-explicit WORKTREE_DIR.
#
# Usage:
#   setup-worktree.sh <slug> <branch> [<base-branch>]
#
#   slug         short identifier (used in the worktree dir name)
#   branch       git branch the worktree will track (created from base if new)
#   base-branch  base to fork from (default: main)
#
# Inputs (env):
#   PROJECT_DIR        repo root (default: cwd)
#   ORCHESTRATE_MODE   exec|batch|single|review|rescue (default: exec)
#                      The mode is folded into the worktree dir name so two
#                      modes targeting the same slug don't collide.
#   WORKTREE_DIR       absolute path override (skips the naming convention)
#   LINK_NODE_MODULES  1 to symlink ../node_modules (default: 1)
#   LINK_ENV_FILE      env file to symlink, empty to skip (default: .env.local)
#   PRISMA_GENERATE    1 to run `npx prisma generate` after setup (auto-detect
#                      from prisma/schema.prisma if unset)
#   ALLOW_REUSE        1 to refresh an existing worktree to the requested ref
#                      (default: 0)
#                      run-fleet sets this to 1 when retrying a failed entry.
#
# Exit codes: 0 OK, 1 not a git repo or worktree exists (without ALLOW_REUSE),
#             2 base branch unknown, 3 git worktree add failed.

set -uo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <slug> <branch> [<base-branch>]" >&2
  exit 1
fi

SLUG="$1"
BRANCH_NAME="$2"
BASE_BRANCH="${3:-main}"

PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
ORCHESTRATE_MODE="${ORCHESTRATE_MODE:-exec}"
LINK_NODE_MODULES="${LINK_NODE_MODULES:-1}"
LINK_ENV_FILE="${LINK_ENV_FILE:-.env.local}"
ALLOW_REUSE="${ALLOW_REUSE:-0}"

cd "$PROJECT_DIR" || { echo "ERROR: cannot cd to $PROJECT_DIR" >&2; exit 1; }

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "ERROR: $PROJECT_DIR is not a git repo" >&2
  exit 1
fi

REPO_NAME="$(basename "$PROJECT_DIR")"

# Resolve worktree path. Default to sibling-of-repo per the worktree contract;
# WORKTREE_DIR_NAME flips to in-repo placement when the user prefers it.
if [[ -n "${WORKTREE_DIR:-}" ]]; then
  WT_PATH="$WORKTREE_DIR"
elif [[ -n "${WORKTREE_DIR_NAME:-}" ]]; then
  WT_PATH="$PROJECT_DIR/$WORKTREE_DIR_NAME/$SLUG"
else
  # Sibling of the repo, default location per the plan.
  PARENT="$(cd "$PROJECT_DIR/.." && pwd)"
  WT_PATH="$PARENT/${REPO_NAME}-wt-${ORCHESTRATE_MODE}-${SLUG}"
fi

# Auto-detect codegen
if [[ -z "${PRISMA_GENERATE:-}" ]]; then
  if [[ -f "$PROJECT_DIR/prisma/schema.prisma" ]]; then
    PRISMA_GENERATE=1
  else
    PRISMA_GENERATE=0
  fi
fi

# ── Reuse path: if worktree exists and ALLOW_REUSE=1, refresh it ───
if [[ -d "$WT_PATH" ]]; then
  if [[ "$ALLOW_REUSE" == "1" ]]; then
    echo "[setup-worktree] refreshing existing $WT_PATH"
    if git rev-parse --verify "$BRANCH_NAME" >/dev/null 2>&1; then
      target_ref="$BRANCH_NAME"
    elif git rev-parse --verify "$BASE_BRANCH" >/dev/null 2>&1; then
      target_ref="$BASE_BRANCH"
    elif git rev-parse --verify "origin/$BASE_BRANCH" >/dev/null 2>&1; then
      target_ref="origin/$BASE_BRANCH"
    else
      echo "ERROR: neither branch '$BRANCH_NAME' nor base '$BASE_BRANCH' resolves for reuse" >&2
      exit 2
    fi
    if ! git -C "$WT_PATH" fetch --all --prune 2>&1 | sed 's/^/[setup-worktree] /'; then
      echo "ERROR: git fetch failed for reused worktree" >&2
      exit 3
    fi
    if ! git -C "$WT_PATH" reset --hard "$target_ref" 2>&1 | sed 's/^/[setup-worktree] /'; then
      echo "ERROR: git reset failed for reused worktree" >&2
      exit 3
    fi
    if ! git -C "$WT_PATH" clean -fd 2>&1 | sed 's/^/[setup-worktree] /'; then
      echo "ERROR: git clean failed for reused worktree" >&2
      exit 3
    fi
    echo "WORKTREE_PATH=$WT_PATH"
    exit 0
  fi
  echo "ERROR: worktree $WT_PATH already exists. Remove it or set ALLOW_REUSE=1." >&2
  exit 1
fi

# ── Verify base branch resolves locally ───────────────────────
if ! git rev-parse --verify "$BASE_BRANCH" >/dev/null 2>&1; then
  # Try origin/<base>
  if git rev-parse --verify "origin/$BASE_BRANCH" >/dev/null 2>&1; then
    BASE_BRANCH="origin/$BASE_BRANCH"
  else
    echo "ERROR: base branch '$BASE_BRANCH' not found locally or on origin" >&2
    exit 2
  fi
fi

mkdir -p "$(dirname "$WT_PATH")"
echo "[setup-worktree] mode=$ORCHESTRATE_MODE slug=$SLUG branch=$BRANCH_NAME base=$BASE_BRANCH"
echo "[setup-worktree] path=$WT_PATH"

# `git worktree add` creates the branch if it doesn't exist.
# If the branch already exists, we omit `-b` to attach to it.
if git rev-parse --verify "$BRANCH_NAME" >/dev/null 2>&1; then
  if ! git worktree add "$WT_PATH" "$BRANCH_NAME" 2>&1 | sed 's/^/[setup-worktree] /'; then
    echo "ERROR: git worktree add failed (branch existed; attach mode)" >&2
    exit 3
  fi
else
  if ! git worktree add "$WT_PATH" -b "$BRANCH_NAME" "$BASE_BRANCH" 2>&1 | sed 's/^/[setup-worktree] /'; then
    echo "ERROR: git worktree add failed (new branch from $BASE_BRANCH)" >&2
    exit 3
  fi
fi

# ── Symlink node_modules ──────────────────────────────────────
# We compute the symlink target as a relative path so the link survives a
# rename of either the repo or the worktree dir.
if [[ "$LINK_NODE_MODULES" == "1" && -d "$PROJECT_DIR/node_modules" ]]; then
  if [[ ! -e "$WT_PATH/node_modules" ]]; then
    # Compute relative path from worktree to repo's node_modules.
    rel="$(python3 -c "import os.path; print(os.path.relpath('$PROJECT_DIR/node_modules', '$WT_PATH'))" 2>/dev/null || echo "$PROJECT_DIR/node_modules")"
    ln -s "$rel" "$WT_PATH/node_modules" 2>/dev/null \
      && echo "[setup-worktree] linked node_modules → $rel" \
      || echo "[setup-worktree] WARN: node_modules symlink failed (continuing)"
  fi
fi

# ── Symlink env file ──────────────────────────────────────────
if [[ -n "$LINK_ENV_FILE" && -f "$PROJECT_DIR/$LINK_ENV_FILE" && ! -e "$WT_PATH/$LINK_ENV_FILE" ]]; then
  rel="$(python3 -c "import os.path; print(os.path.relpath('$PROJECT_DIR/$LINK_ENV_FILE', '$WT_PATH'))" 2>/dev/null || echo "$PROJECT_DIR/$LINK_ENV_FILE")"
  ln -s "$rel" "$WT_PATH/$LINK_ENV_FILE" 2>/dev/null \
    && echo "[setup-worktree] linked $LINK_ENV_FILE → $rel" \
    || echo "[setup-worktree] WARN: $LINK_ENV_FILE symlink failed (continuing)"
fi

# ── Per-worktree codegen ──────────────────────────────────────
if [[ "$PRISMA_GENERATE" == "1" ]]; then
  if [[ -f "$WT_PATH/package.json" ]] && command -v npx >/dev/null 2>&1; then
    echo "[setup-worktree] regenerating Prisma client"
    (cd "$WT_PATH" && npx --no-install prisma generate 2>&1 | tail -2 | sed 's/^/[setup-worktree:prisma] /') \
      || echo "[setup-worktree] WARN: prisma generate failed (continuing)"
  fi
fi

# Final breadcrumb so the runner can capture the resolved path.
echo "WORKTREE_PATH=$WT_PATH"
echo "[setup-worktree] ready"
