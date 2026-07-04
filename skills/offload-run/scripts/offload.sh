#!/usr/bin/env bash
# offload — drive a remote Sprite (Fly.io) so build/test/serve work never touches the local machine.
# Multi-command: `offload <subcommand> ...`. Default subcommand is `run`, so `offload -- npm test`
# and `offload run -- npm test` are identical. Per project, everything targets one sprite:
# offload-<projecttype> (node/python/macos/generic), keyed to the lockfile-hashed golden checkpoint.
#
# Subcommands:
#   run [--root R][--type T][--backend B][--quiet] -- CMD   run CMD remotely, stream output, return exit (default)
#   serve [--root R][--port N][--public][--name S] -- CMD   run CMD as a persistent Service + print the public URL
#   sync  [--root R]                                        push the worktree into the sprite (no run)
#   shell [--root R]                                        open an interactive console in the sprite
#   proxy [--root R] <port|local:remote>...                 forward a sprite port to localhost (DB/dev)
#   status [--root R]                                       state (running/warm/cold), URL, cost posture
#   url   [--root R] [--public|--private]                   show or change the sprite's public URL auth
#   checkpoints [--root R]                                  list checkpoints
#   prune [--root R] [--keep N]                             delete accumulated pre-restore/old checkpoints
#   keepalive [--root R] --seconds N                        hold the sprite awake for N s (bounded; for held conns)
#   nuke  [--root R] [--yes]                                destroy the sprite (the ONLY way to stop ALL billing)
#   mcp                                                     print/run the one-liner to add the Sprites remote MCP
#   doctor                                                  check sprite CLI + auth + show the in-sprite agent docs
#   help
set -euo pipefail
# Resolve through symlinks (offload is usually invoked via a ~/bin/offload symlink).
SRC="${BASH_SOURCE[0]}"
while [ -L "$SRC" ]; do
  TGT="$(readlink "$SRC")"; case "$TGT" in /*) SRC="$TGT" ;; *) SRC="$(dirname "$SRC")/$TGT" ;; esac
done
HERE="$(cd "$(dirname "$SRC")" && pwd)"
source "$HERE/lib.sh"
for c in "${OFFLOAD_CONFIG:-}" "$HOME/.config/offload-run/config.sh"; do
  [ -n "$c" ] && [ -f "$c" ] && { source "$c"; break; }
done
# Validate the remote workdir at the source (it is interpolated into remote shell strings).
: "${OFFLOAD_WORKDIR:=/work}"
[[ "$OFFLOAD_WORKDIR" == /* ]] || die "OFFLOAD_WORKDIR must be an absolute path (got '$OFFLOAD_WORKDIR')"
[[ "$OFFLOAD_WORKDIR" =~ ^/[A-Za-z0-9_./-]+$ ]] || die "OFFLOAD_WORKDIR has unsafe characters (got '$OFFLOAD_WORKDIR')"
export OFFLOAD_WORKDIR

# Print the leading comment block (range-independent: stops at the first non-comment line).
usage() { awk 'NR==1{next} /^#/{sub(/^# ?/,"");print;next}{exit}' "$0"; }

# ---- run (default): dispatch CMD to the project's backend ------------------------------------
cmd_run() {
  local root="$PWD" force_type="" force_backend=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --root) root="$2"; shift 2 ;;
      --type) force_type="$2"; shift 2 ;;
      --backend) force_backend="$2"; shift 2 ;;
      --quiet|-q) OFFLOAD_QUIET=1; export OFFLOAD_QUIET; shift ;;
      --) shift; break ;;
      -h|--help) usage; exit 0 ;;
      *) die "run: unknown flag '$1' (put the command after '--')" ;;
    esac
  done
  [ $# -gt 0 ] || die "run: no command. Example: offload -- npm test"
  local type hash backend
  type="${force_type:-$(detect_project "$root")}"
  hash="$(lockfile_hash "$root")"
  if [ "$type" = "macos" ]; then backend="${force_backend:-${OFFLOAD_MACOS_BACKEND:-tart}}"
  else backend="${force_backend:-${OFFLOAD_LINUX_BACKEND:-sprites}}"; fi
  log "project=$type  deps-hash=$hash  backend=$backend  root=$root"
  case "$backend" in
    sprites) source "$HERE/backends/sprites.sh"; sprites_backend "$type" "$hash" "$root" "$@" ;;
    e2b)     source "$HERE/backends/e2b.sh";     e2b_backend     "$type" "$hash" "$root" "$@" ;;
    tart)    source "$HERE/backends/tart.sh";    tart_backend    "$type" "$hash" "$root" "$@" ;;
    *)       die "unknown backend: $backend (sprites | e2b | tart)" ;;
  esac
}

# ---- sprite-ops subcommands (Sprites backend only) ------------------------------------------
ops() {  # ops <opname> <args...>
  local op="$1"; shift
  source "$HERE/sprites-ops.sh"
  "ops_$op" "$@"
}

main() {
  local sub="${1:-help}"
  case "$sub" in
    run)        shift; cmd_run "$@" ;;
    --|-q|--quiet|--root|--type|--backend) cmd_run "$@" ;;   # bare `offload -- ...` / flags => run
    serve|sync|shell|proxy|status|url|checkpoints|prune|keepalive|nuke|mcp|doctor)
                shift; ops "$sub" "$@" ;;
    help|-h|--help) usage ;;
    *)          die "unknown subcommand '$sub'. Run 'offload help'." ;;
  esac
}
main "$@"
