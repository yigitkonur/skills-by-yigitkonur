#!/usr/bin/env bash
# scripts/quick-tunnel.sh
# Automated launcher and URL extractor for Cloudflare Quick Tunnels (trycloudflare.com)
# with process group isolation (setsid) and global DNS publication checks.
set -euo pipefail

PORT=""
HOST="127.0.0.1"
PROTOCOL="quic"
LOGFILE=""
PIDFILE=""
OUTFILE=""
TIMEOUT=20
JSON_OUTPUT=false
VERIFY_DNS=true

print_usage() {
  cat <<HELP
Usage: $(basename "$0") --port <PORT> [options]

Options:
  -p, --port <PORT>        Local port to expose (required, e.g. 3000, 8080, 8099)
  -h, --host <HOST>        Local host address (default: 127.0.0.1)
      --protocol <proto>   Protocol to use: quic or http2 (default: quic)
  -l, --logfile <path>     Path for cloudflared log (default: /tmp/cloudflared-<PORT>.log)
      --pidfile <path>     Path to record daemon PID (default: /tmp/cloudflared-<PORT>.pid)
  -o, --out <path>         File to write the public tunnel URL into
  -t, --timeout <sec>      Max seconds to wait for URL extraction (default: 20)
      --no-dns-wait        Skip global DNS publication check
      --json               Output result as JSON
      --help               Show this help message

Example:
  $(basename "$0") --port 8099 --out /tmp/tunnel-url.txt
HELP
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--port) PORT="$2"; shift 2 ;;
    -h|--host) HOST="$2"; shift 2 ;;
    --protocol) PROTOCOL="$2"; shift 2 ;;
    -l|--logfile) LOGFILE="$2"; shift 2 ;;
    --pidfile) PIDFILE="$2"; shift 2 ;;
    -o|--out) OUTFILE="$2"; shift 2 ;;
    -t|--timeout) TIMEOUT="$2"; shift 2 ;;
    --no-dns-wait) VERIFY_DNS=false; shift ;;
    --json) JSON_OUTPUT=true; shift ;;
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

# Clean up previous state
rm -rf "$LOGFILE" "$PIDFILE" ~/.cloudflared/

# Launch cloudflared quick tunnel in background with process group isolation
setsid nohup cloudflared tunnel \
  --url "http://${HOST}:${PORT}" \
  --protocol "$PROTOCOL" \
  --logfile "$LOGFILE" \
  --pidfile "$PIDFILE" \
  --no-autoupdate </dev/null >/dev/null 2>&1 &

DAEMON_PID=$!

# Wait for the trycloudflare.com URL to appear in logs
TUNNEL_URL=""
START_TIME=$(date +%s)
while true; do
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

# Optional: Wait for global DNS publication to prevent NXDOMAIN poisoning
DNS_RESOLVED=false
if [[ "$VERIFY_DNS" == "true" ]]; then
  HOST_ONLY=$(echo "$TUNNEL_URL" | sed -E 's#^https?://##')
  for i in {1..15}; do
    IP1=$(dig @1.1.1.1 +short "$HOST_ONLY" 2>/dev/null | tail -n 1 || true)
    IP2=$(dig @8.8.8.8 +short "$HOST_ONLY" 2>/dev/null | tail -n 1 || true)
    if [[ -n "$IP1" && -n "$IP2" ]]; then
      DNS_RESOLVED=true
      break
    fi
    sleep 1
  done
fi

# Write out to output file if requested
if [[ -n "$OUTFILE" ]]; then
  echo "$TUNNEL_URL" > "$OUTFILE"
fi

if [[ "$JSON_OUTPUT" == "true" ]]; then
  cat <<JSON
{
  "ok": true,
  "url": "${TUNNEL_URL}",
  "localTarget": "http://${HOST}:${PORT}",
  "pid": ${DAEMON_PID},
  "pidfile": "${PIDFILE}",
  "logfile": "${LOGFILE}",
  "protocol": "${PROTOCOL}",
  "dnsResolved": ${DNS_RESOLVED}
}
JSON
else
  echo "================================================================"
  echo "  Cloudflare Quick Tunnel Online (Process Isolated)"
  echo "  Public URL   : ${TUNNEL_URL}"
  echo "  Local Origin : http://${HOST}:${PORT}"
  echo "  Daemon PID   : ${DAEMON_PID}"
  echo "  DNS Ready    : ${DNS_RESOLVED}"
  echo "  Log File     : ${LOGFILE}"
  echo "  PID File     : ${PIDFILE}"
  echo "================================================================"
fi
