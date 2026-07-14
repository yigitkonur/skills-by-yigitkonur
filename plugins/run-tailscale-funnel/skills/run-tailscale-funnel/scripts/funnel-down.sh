#!/usr/bin/env bash
# funnel-down.sh — tear down one specific Funnel mapping safely.
#
# Usage: funnel-down.sh <funnel-port>
#
# Refuses to act if this port mapping was not created by this skill's funnel-up.sh
# (state file at /tmp/tailscale-funnel-state-$(uid)-<port>.txt is required), unless
# --force is passed. This is the guard against `make local-down` tearing down
# another project's mapping.
#
# Never runs `tailscale funnel reset` — only `tailscale funnel --https=<port> off`.

set -euo pipefail

FUNNEL_PORT="${1:-}"
FORCE="${2:-}"
STATE_DIR="${TMPDIR:-/tmp}"
STATE_FILE="$STATE_DIR/tailscale-funnel-state-$(id -u)-${FUNNEL_PORT}.txt"

log()  { printf '[funnel-down] %s\n' "$*" >&2; }
warn() { printf '[funnel-down] WARNING: %s\n' "$*" >&2; }
die()  { printf '[funnel-down] ERROR: %s\n' "$*" >&2; exit 1; }

[[ -n "$FUNNEL_PORT" ]] || die "usage: $0 <funnel-port> [--force]"
[[ "$FUNNEL_PORT" =~ ^(443|8443|10000)$ ]] || die "funnel-port must be 443, 8443, or 10000 (got: $FUNNEL_PORT)"

command -v tailscale >/dev/null || die "tailscale CLI not found on PATH"

# Confirm the mapping exists and that we own it
if [[ -f "$STATE_FILE" ]]; then
  log "found state file from previous funnel-up: $STATE_FILE"
  cat "$STATE_FILE" | sed 's/^/  /' >&2
else
  if [[ "$FORCE" != "--force" ]]; then
    warn "no state file at $STATE_FILE — this script may not have created the current mapping for port $FUNNEL_PORT"
    warn "tailscale funnel status currently shows:"
    tailscale funnel status 2>&1 | sed 's/^/  /' >&2
    warn "if this mapping is yours and you want to remove it anyway:"
    warn "  $0 $FUNNEL_PORT --force"
    warn "if it belongs to another project, do NOT remove it — find the project that owns it"
    die  "refusing to remove a mapping this script did not create — see references/port-slot-management.md"
  else
    warn "--force given; removing without state-file verification"
  fi
fi

# If a previous-mapping snapshot exists (funnel-up.sh saves these when it would
# have clobbered something), restore that instead of just removing.
if [[ -f "$STATE_FILE.previous" ]]; then
  log "found previous-mapping snapshot — restoring after removal"
  # shellcheck disable=SC1090
  source "$STATE_FILE.previous"
  if [[ -n "${PREVIOUS_TARGET:-}" ]]; then
    log "removing current mapping on port $FUNNEL_PORT"
    tailscale funnel --https="$FUNNEL_PORT" off >/dev/null || true
    log "restoring previous mapping: :$FUNNEL_PORT → $PREVIOUS_TARGET"
    tailscale funnel --bg --https="$FUNNEL_PORT" "$PREVIOUS_TARGET" >/dev/null
    rm -f "$STATE_FILE" "$STATE_FILE.previous"
    log "done — previous mapping restored"
    exit 0
  fi
fi

log "removing funnel mapping on port $FUNNEL_PORT"
tailscale funnel --https="$FUNNEL_PORT" off >/dev/null
rm -f "$STATE_FILE"
log "done"
log "current state:"
tailscale funnel status 2>&1 | sed 's/^/  /' >&2 || true
