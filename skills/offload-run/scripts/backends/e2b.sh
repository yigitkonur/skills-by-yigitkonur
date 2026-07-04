#!/usr/bin/env bash
# backends/e2b.sh — alt Linux backend on E2B (snapshot warm-FORK + prebuilt agent templates).
# Use instead of Sprites when you want to FORK one warm env into many parallel sandboxes,
# or want E2B's prebuilt Codex/Claude Code templates. Driven via a tiny Node one-liner using
# the official `e2b` SDK; template-per-lockfile keeps node_modules warm.
#
# NOTE: not exercised here (no E2B key in this session). Requires: npm i -g e2b ; E2B_API_KEY set;
# a template built per lockfile hash (see references/setup.md). This is a thin reference path.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; source "$HERE/lib.sh"

e2b_backend() {
  local type="$1" hash="$2" root="$3"; shift 3
  local cmd="$*"
  local template; template="$(golden_name "$type" "$hash")"   # = an E2B template alias
  have e2b || die "e2b CLI/SDK not found — npm i -g e2b and set E2B_API_KEY"
  [ -n "${E2B_API_KEY:-}" ] || die "E2B_API_KEY not set"

  log "dispatching to E2B template $template"
  # Pack the worktree, hand path + template + cmd to a Node runner that forks the warm template,
  # uploads the tar, runs the command, streams output, and exits with the remote code.
  local tar; tar="$(mktemp -t offload).tgz"; worktree_tar "$root" >"$tar"
  E2B_TEMPLATE="$template" E2B_TAR="$tar" E2B_CMD="$cmd" E2B_WORK="${OFFLOAD_WORKDIR:-/work}" \
    node "$HERE/backends/e2b-runner.mjs"
  local rc=$?; rm -f "$tar"; return $rc
}
