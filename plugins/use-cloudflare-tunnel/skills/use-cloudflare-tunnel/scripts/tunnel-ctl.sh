#!/usr/bin/env bash
# scripts/tunnel-ctl.sh
# Management and diagnostic control for cloudflared tunnels and unified proxies
set -euo pipefail

COMMAND="${1:-status}"

case "$COMMAND" in
  status)
    echo "=== Active Cloudflare Tunnels ==="
    if [[ "$OSTYPE" == "darwin"* ]]; then
      pgrep -fl "cloudflared tunnel" || echo "No active cloudflared tunnel processes."
    else
      pgrep -a -f "cloudflared tunnel" || echo "No active cloudflared tunnel processes."
    fi
    echo ""
    echo "=== Active Unified Proxies ==="
    if [[ "$OSTYPE" == "darwin"* ]]; then
      pgrep -fl "unified-proxy.mjs" || echo "No active unified proxies."
    else
      pgrep -a -f "unified-proxy.mjs" || echo "No active unified proxies."
    fi
    echo ""
    echo "=== Discovered Public URLs ==="
    shopt -s nullglob
    for log in $(ls -t /tmp/cloudflared*.log 2>/dev/null || true); do
      if [[ -f "$log" ]]; then
        URL=$(grep -o 'https://[-a-z0-9.]*trycloudflare.com' "$log" 2>/dev/null | tail -n 1 || true)
        if [[ -n "$URL" ]]; then
          echo "$log -> $URL"
        fi
      fi
    done
    ;;

  kill)
    TARGET="${2:-all}"
    if [[ "$TARGET" == "all" ]]; then
      echo "Terminating active ad-hoc quick tunnels and unified proxies..."
      # Target quick tunnels specifically to avoid killing production named tunnels
      pkill -f "cloudflared tunnel --url" || true
      pkill -f "unified-proxy.mjs" || true
      echo "Cleaned up."
    elif [[ "$TARGET" =~ ^[0-9]+$ ]]; then
      echo "Terminating tunnel for port: $TARGET"
      pkill -f "cloudflared.*:${TARGET}" || true
      pkill -f "cloudflared.*-${TARGET}.log" || true
      if [[ -f "/tmp/cloudflared-${TARGET}.pid" ]]; then
        kill $(cat "/tmp/cloudflared-${TARGET}.pid") 2>/dev/null || true
      fi
      rm -f "/tmp/cloudflared-${TARGET}".*
      echo "Cleaned up port $TARGET."
    else
      echo "Terminating process matching: $TARGET"
      pkill -f "$TARGET" || true
    fi
    ;;

  health)
    URL="${2:-}"
    if [[ -z "$URL" ]]; then
      # Pick latest URL from /tmp/cloudflared*.log sorted by modification time
      for log in $(ls -t /tmp/cloudflared*.log 2>/dev/null || true); do
        if [[ -f "$log" ]]; then
          FOUND_URL=$(grep -o 'https://[-a-z0-9.]*trycloudflare.com' "$log" 2>/dev/null | tail -n 1 || true)
          if [[ -n "$FOUND_URL" ]]; then
            URL="$FOUND_URL"
            break
          fi
        fi
      done
    fi

    if [[ -z "$URL" ]]; then
      echo "Error: No tunnel URL provided and none found in /tmp/cloudflared*.log." >&2
      exit 1
    fi

    echo "Checking health of: $URL"
    # Pass -L to follow redirects so auth/app landing pages return 200
    HTTP_CODE=$(curl -s -L -o /dev/null -w "%{http_code}" --max-time 10 "$URL" || echo "failed")
    echo "HTTP Status: $HTTP_CODE"
    if [[ "$HTTP_CODE" =~ ^(2[0-9]{2}|3[0-9]{2}|404)$ ]]; then
      echo "Status: HEALTHY (Tunnel reachable)"
    else
      echo "Status: UNHEALTHY / UNREACHABLE"
      exit 1
    fi
    ;;

  help|*)
    echo "Usage: $(basename "$0") <status|kill|health> [options]"
    echo ""
    echo "Commands:"
    echo "  status        List all running tunnels, proxies, and public URLs"
    echo "  kill [target] Terminate running tunnels ('all', port number, or regex filter)"
    echo "  health [url]  Test connectivity of a tunnel URL (follows redirects)"
    ;;
esac
