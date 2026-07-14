#!/usr/bin/env bash
# funnel-up.sh — set up a Tailscale Funnel mapping for a local HTTP server
#   and verify the three rungs (auth DNS, ingress curl, local loopback).
#
# Usage: funnel-up.sh <local-port> <funnel-port>
#   local-port  : where the app is bound on 127.0.0.1 (e.g. 4321)
#   funnel-port : 443, 8443, or 10000 (the three Funnel slots)
#
# Exits 0 on success and prints the public URL. Exits non-zero on any failure
# with a hint pointing at the right reference doc.
#
# Never runs `tailscale funnel reset` or `tailscale serve reset`.

set -euo pipefail

LOCAL_PORT="${1:-}"
FUNNEL_PORT="${2:-}"
STATE_DIR="${TMPDIR:-/tmp}"
STATE_FILE="$STATE_DIR/tailscale-funnel-state-$(id -u)-${FUNNEL_PORT}.txt"

log()  { printf '[funnel-up] %s\n' "$*" >&2; }
warn() { printf '[funnel-up] WARNING: %s\n' "$*" >&2; }
die()  { printf '[funnel-up] ERROR: %s\n' "$*" >&2; exit 1; }

[[ -n "$LOCAL_PORT" && -n "$FUNNEL_PORT" ]] || die "usage: $0 <local-port> <funnel-port>"
[[ "$FUNNEL_PORT" =~ ^(443|8443|10000)$ ]] || die "funnel-port must be 443, 8443, or 10000 (got: $FUNNEL_PORT)"

command -v tailscale >/dev/null || die "tailscale CLI not found on PATH"
command -v dig       >/dev/null || die "dig not found on PATH"
command -v curl      >/dev/null || die "curl not found on PATH"

# 1 ─ Identity
TAILSCALE_JSON="$(tailscale status --json 2>/dev/null)" || die "tailscale daemon not reachable (is it running and logged in?)"
FQDN=$(printf '%s' "$TAILSCALE_JSON" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('Self', {}).get('DNSName', '').rstrip('.'))
" 2>/dev/null || true)
[[ -n "$FQDN" ]] || die "could not read tailnet FQDN — see references/architecture.md"

MAGICDNS=$(printf '%s' "$TAILSCALE_JSON" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('CurrentTailnet', {}).get('MagicDNSEnabled', False))
" 2>/dev/null || echo False)
[[ "$MAGICDNS" == "True" ]] || die "MagicDNS not enabled on this tailnet — enable at https://login.tailscale.com/admin/dns"

log "node fqdn: $FQDN"

# 2 ─ Local app reachable on loopback?
if ! curl -sf --max-time 3 -o /dev/null "http://127.0.0.1:${LOCAL_PORT}/"; then
  warn "nothing listening on 127.0.0.1:${LOCAL_PORT} — Funnel will return 502 until the backend starts"
fi

# 3 ─ Preflight: existing mappings (never clobber)
log "current serve+funnel mappings:"
tailscale serve status   2>&1 | sed 's/^/  /' >&2 || true
tailscale funnel status  2>&1 | sed 's/^/  /' >&2 || true

# Check if the slot is already mapped — and if so, to what.
# Match the URL header line for *this* FQDN+port exactly, then read the
# next "|-- / proxy <target>" line. (Looser matching picked up unrelated
# mappings on a node with many entries.)
if [[ "$FUNNEL_PORT" == "443" ]]; then
  URL_PATTERN="^https://${FQDN} "
else
  URL_PATTERN="^https://${FQDN}:${FUNNEL_PORT} "
fi
CURRENT_TARGET=$(tailscale funnel status 2>/dev/null \
  | awk -v pat="$URL_PATTERN" '
      $0 ~ pat { found=1; next }
      found && /^\|-- / && /proxy/ { print $NF; exit }
    ' || true)

DESIRED_TARGET="http://127.0.0.1:${LOCAL_PORT}"

if [[ -n "$CURRENT_TARGET" && "$CURRENT_TARGET" != "$DESIRED_TARGET" ]]; then
  warn "funnel slot ${FUNNEL_PORT} is already mapped to: ${CURRENT_TARGET}"
  warn "remapping it to ${DESIRED_TARGET} will lose the previous mapping"
  warn "if that mapping belongs to another project, stop now and pick a different slot (443 | 8443 | 10000)"
  warn "to proceed anyway: tailscale funnel --https=${FUNNEL_PORT} off && this script"
  # Snapshot for restore
  printf 'PREVIOUS_TARGET=%s\n' "$CURRENT_TARGET" > "$STATE_FILE.previous"
  log  "snapshotted previous target to: $STATE_FILE.previous"
  die  "refusing to clobber existing mapping — see references/port-slot-management.md"
fi

# 4 ─ Set up the mapping (idempotent if it already matches)
if [[ "$CURRENT_TARGET" == "$DESIRED_TARGET" ]]; then
  log "mapping already correct, skipping funnel --bg"
else
  log "mapping :${FUNNEL_PORT} → ${DESIRED_TARGET}"
  tailscale funnel --bg --https="${FUNNEL_PORT}" "${DESIRED_TARGET}" >/dev/null
fi

# Record what this script set up — used by funnel-down.sh to confirm ownership
printf 'FQDN=%s\nFUNNEL_PORT=%s\nLOCAL_PORT=%s\nCREATED_AT=%s\n' \
  "$FQDN" "$FUNNEL_PORT" "$LOCAL_PORT" "$(date -u +%FT%TZ)" > "$STATE_FILE"

# 5 ─ Rung 1: auth DNS (is the ACL gate open?)
sleep 1
AUTH_A=$(dig @ns1.dnsimple.com "$FQDN" A +short +time=3 +tries=1 2>/dev/null || true)
if [[ -z "$AUTH_A" ]]; then
  warn "rung 1 (auth DNS) ✗ — public DNS for $FQDN is empty"
  warn "this usually means the tailnet ACL gate is closed"
  warn "ask the admin to:"
  warn "  1. enable HTTPS Certificates at https://login.tailscale.com/admin/dns"
  warn "  2. grant 'funnel' nodeAttr in https://login.tailscale.com/admin/acls"
  warn "see references/troubleshooting.md § ACL gate"
  die  "rung 1 failed — Funnel device-side state is fine but tailnet has not authorized public DNS"
fi
log "rung 1 (auth DNS) ✓ — public DNS resolves to: $AUTH_A"

# 6 ─ Rung 2: public ingress curl
PUBLIC_URL="https://${FQDN}"
[[ "$FUNNEL_PORT" != "443" ]] && PUBLIC_URL="${PUBLIC_URL}:${FUNNEL_PORT}"

RUNG2_FAIL=0
for ip in 208.111.34.11 208.111.35.209; do
  HTTP=$(curl --max-time 15 -sS -o /dev/null \
    -w '%{http_code}' \
    --resolve "${FQDN}:${FUNNEL_PORT}:${ip}" \
    "${PUBLIC_URL}/" 2>&1 || true)
  if [[ "$HTTP" == "000" ]]; then
    warn "rung 2 ingress=$ip — no response (cert may still be issuing; try again in 60s)"
    RUNG2_FAIL=1
  elif [[ "$HTTP" == "403" ]]; then
    warn "rung 2 ingress=$ip HTTP=403 — backend Host-header validation"
    warn "see references/backend-host-validation.md (Astro/Vite/Next allowedHosts, or switch to static server)"
    RUNG2_FAIL=1
  elif [[ "$HTTP" == "502" ]]; then
    warn "rung 2 ingress=$ip HTTP=502 — backend not running on 127.0.0.1:${LOCAL_PORT}"
    warn "start the backend, then run this script again (or just wait — Funnel will recover automatically)"
    RUNG2_FAIL=1
  elif [[ "$HTTP" =~ ^[23] ]]; then
    log "rung 2 ingress=$ip HTTP=$HTTP ✓"
  else
    warn "rung 2 ingress=$ip HTTP=$HTTP (unexpected — investigate)"
    RUNG2_FAIL=1
  fi
done

if [[ "$RUNG2_FAIL" == "1" ]]; then
  warn "rung 2 partially or fully failed — public URL will not work until cause is fixed"
  warn "the Funnel mapping itself is set up correctly; the problem is on the backend side or in cert issuance"
  # do not exit non-zero — the user can fix the backend and retry without re-running funnel
fi

# Done — print public URL on its own line for easy capture
log "rung 3 (external client test) — verify manually from a non-tailnet client (phone on cellular, public probe)"
log "public URL:"
printf '%s/\n' "$PUBLIC_URL"
log "to tear down: tailscale funnel --https=${FUNNEL_PORT} off"
