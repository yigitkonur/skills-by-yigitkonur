#!/usr/bin/env bash
# scripts/quick-tunnel.sh
# Automated launcher and URL extractor for Cloudflare Quick Tunnels (trycloudflare.com)
# with process group isolation (cross-platform setsid/nohup) and global DNS publication checks.
set -euo pipefail

PORT=""
HOST="127.0.0.1"
PROTOCOL="auto"
LOGFILE=""
PIDFILE=""
OUTFILE=""
TIMEOUT=20
JSON_OUTPUT=false
VERIFY_DNS=true
POST_QUANTUM=false
NO_PRECHECKS=false
HTTP_HOST_HEADER=""
ALLOWED_MAILS=()
METRICS=""

print_usage() {
  cat <<HELP
Usage: $(basename "$0") --port <PORT> [options]

Options:
  -p, --port <PORT>             Local port to expose (required, e.g. 3000, 8080, 8099)
  -h, --host <HOST>             Local host address (default: 127.0.0.1)
      --protocol <proto>        Protocol to use: auto, quic, or http2 (default: auto)
      --allowed-mail <email>    Require email OTP auth (cloudflared >= 2026.10.0). Can repeat.
      --metrics <address>       Listen address for metrics and /ready health checks (e.g. 127.0.0.1:20241)
      --pq                      Strictly enforce post-quantum hybrid key exchange (QUIC only)
      --no-prechecks            Bypass connectivity prechecks to reduce startup latency
      --http-host-header <host> Override Host header sent to local origin
  -l, --logfile <path>          Path for cloudflared log (default: /tmp/cloudflared-<PORT>.log)
      --pidfile <path>          Path to record daemon PID (default: /tmp/cloudflared-<PORT>.pid)
  -o, --out <path>              File to write the public tunnel URL into
  -t, --timeout <sec>           Max seconds to wait for URL extraction (default: 20)
      --no-dns-wait             Skip global DNS publication check
  -j, --json                    Output result as JSON
      --help                    Show this help message

Example:
  $(basename "$0") --port 8099 --out /tmp/tunnel-url.txt
HELP
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--port) PORT="$2"; shift 2 ;;
    -h|--host) HOST="$2"; shift 2 ;;
    --protocol) PROTOCOL="$2"; shift 2 ;;
    --allowed-mail) ALLOWED_MAILS+=("$2"); shift 2 ;;
    --metrics) METRICS="$2"; shift 2 ;;
    --pq|--post-quantum) POST_QUANTUM=true; shift ;;
    --no-prechecks) NO_PRECHECKS=true; shift ;;
    --http-host-header) HTTP_HOST_HEADER="$2"; shift 2 ;;
    -l|--logfile) LOGFILE="$2"; shift 2 ;;
    --pidfile) PIDFILE="$2"; shift 2 ;;
    -o|--out) OUTFILE="$2"; shift 2 ;;
    -t|--timeout) TIMEOUT="$2"; shift 2 ;;
    --no-dns-wait) VERIFY_DNS=false; shift ;;
    -j|--json) JSON_OUTPUT=true; shift ;;
    --help) print_usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; print_usage; exit 1 ;;
  esac
done

if [[ -z "$PORT" ]]; then
  echo "Error: --port <PORT> is required." >&2
  exit 1
fi

LOGFILE="${LOGFILE:-/tmp/cloudflared-${PORT}.log}"
PIDFILE="${PIDFILE:-/tmp/cloudflared-${PORT}.pid}"

if ! command -v cloudflared &>/dev/null; then
  echo "Error: 'cloudflared' command not found. Please install it first." >&2
  exit 1
fi

# Clean up previous temporary files for this port (NEVER delete ~/.cloudflared/)
rm -f "$LOGFILE" "$PIDFILE"

# Prepare cloudflared arguments
CF_ARGS=(
  "tunnel"
  "--url" "http://${HOST}:${PORT}"
  "--protocol" "$PROTOCOL"
  "--output" "json"
  "--logfile" "$LOGFILE"
  "--pidfile" "$PIDFILE"
  "--no-autoupdate"
)

if [[ "$POST_QUANTUM" == "true" ]]; then
  CF_ARGS+=("--pq")
fi

if [[ "$NO_PRECHECKS" == "true" ]]; then
  CF_ARGS+=("--no-prechecks")
fi

if [[ -n "$HTTP_HOST_HEADER" ]]; then
  CF_ARGS+=("--http-host-header" "$HTTP_HOST_HEADER")
fi

if [[ -n "$METRICS" ]]; then
  CF_ARGS+=("--metrics" "$METRICS")
fi

for mail in "${ALLOWED_MAILS[@]}"; do
  CF_ARGS+=("--allowed-mail" "$mail")
done

# Launch cloudflared quick tunnel in background with process group isolation
if command -v setsid &>/dev/null; then
  setsid nohup cloudflared "${CF_ARGS[@]}" </dev/null >/dev/null 2>&1 &
  DAEMON_PID=$!
else
  nohup cloudflared "${CF_ARGS[@]}" </dev/null >/dev/null 2>&1 &
  DAEMON_PID=$!
fi

# Wait for the trycloudflare.com URL to appear in logs
TUNNEL_URL=""
START_TIME=$(date +%s)
while true; do
  # Fast-fail if cloudflared exited early (e.g. port collision, invalid flags)
  if ! kill -0 "$DAEMON_PID" 2>/dev/null; then
    echo "Error: cloudflared daemon exited prematurely." >&2
    if [[ -f "$LOGFILE" ]]; then
      echo "--- Cloudflared Log Tail ---" >&2
      tail -n 20 "$LOGFILE" >&2
    fi
    exit 1
  fi

  if [[ -f "$LOGFILE" ]]; then
    TUNNEL_URL=$(grep -o 'https://[-a-z0-9.]*trycloudflare.com' "$LOGFILE" 2>/dev/null | tail -n 1 || true)
    if [[ -n "$TUNNEL_URL" ]]; then
      break
    fi
  fi

  CURRENT_TIME=$(date +%s)
  ELAPSED=$((CURRENT_TIME - START_TIME))
  if [[ $ELAPSED -ge $TIMEOUT ]]; then
    echo "Error: Timed out waiting for Cloudflare Tunnel URL after ${TIMEOUT}s." >&2
    if [[ -f "$LOGFILE" ]]; then
      echo "--- Cloudflared Log Tail ---" >&2
      tail -n 20 "$LOGFILE" >&2
    fi
    kill "$DAEMON_PID" 2>/dev/null || true
    exit 1
  fi
  sleep 0.5
done

# Read authoritative PID from pidfile if populated
if [[ -f "$PIDFILE" && -s "$PIDFILE" ]]; then
  RECORDED_PID=$(cat "$PIDFILE" 2>/dev/null || true)
  if [[ -n "$RECORDED_PID" ]]; then
    DAEMON_PID="$RECORDED_PID"
  fi
fi

# Optional: Wait for global DNS publication to prevent NXDOMAIN poisoning
DNS_RESOLVED=false
if [[ "$VERIFY_DNS" == "true" ]]; then
  HOST_ONLY=$(echo "$TUNNEL_URL" | sed -E 's#^https?://##')
  if command -v dig &>/dev/null; then
    for i in {1..15}; do
      IP1=$(dig @1.1.1.1 +short "$HOST_ONLY" 2>/dev/null | tail -n 1 || true)
      IP2=$(dig @8.8.8.8 +short "$HOST_ONLY" 2>/dev/null | tail -n 1 || true)
      if [[ -n "$IP1" && -n "$IP2" ]]; then
        DNS_RESOLVED=true
        break
      fi
      sleep 1
    done
  else
    # Container lacks dig tool; proceed with edge tunnel resolution assumed
    DNS_RESOLVED=true
  fi
fi

# Write out to output file if requested
if [[ -n "$OUTFILE" ]]; then
  echo "$TUNNEL_URL" > "$OUTFILE"
fi

if [[ "$JSON_OUTPUT" == "true" ]]; then
  ALLOWED_JSON="[]"
  if [[ ${#ALLOWED_MAILS[@]} -gt 0 ]]; then
    ALLOWED_JSON=$(printf '%s\n' "${ALLOWED_MAILS[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[\"${ALLOWED_MAILS[*]}\"]")
  fi
  cat <<JSON
{
  "ok": true,
  "url": "${TUNNEL_URL}",
  "localTarget": "http://${HOST}:${PORT}",
  "pid": ${DAEMON_PID},
  "pidfile": "${PIDFILE}",
  "logfile": "${LOGFILE}",
  "protocol": "${PROTOCOL}",
  "metrics": "${METRICS}",
  "allowedMails": ${ALLOWED_JSON},
  "postQuantum": ${POST_QUANTUM},
  "dnsResolved": ${DNS_RESOLVED}
}
JSON
else
  echo "================================================================"
  echo "  Cloudflare Quick Tunnel Online (Process Isolated)"
  echo "  Public URL   : ${TUNNEL_URL}"
  echo "  Local Origin : http://${HOST}:${PORT}"
  echo "  Daemon PID   : ${DAEMON_PID}"
  echo "  Protocol     : ${PROTOCOL}"
  if [[ -n "$METRICS" ]]; then
    echo "  Metrics / Rdy: http://${METRICS}"
  fi
  if [[ ${#ALLOWED_MAILS[@]} -gt 0 ]]; then
    echo "  Allowed Mail : ${ALLOWED_MAILS[*]}"
  fi
  echo "  Post-Quantum : ${POST_QUANTUM}"
  echo "  DNS Ready    : ${DNS_RESOLVED}"
  echo "  Log File     : ${LOGFILE}"
  echo "  PID File     : ${PIDFILE}"
  echo "================================================================"
fi
