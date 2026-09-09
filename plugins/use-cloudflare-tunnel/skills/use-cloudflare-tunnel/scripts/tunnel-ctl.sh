#!/usr/bin/env bash
# scripts/tunnel-ctl.sh
# Management and diagnostic control for cloudflared tunnels and unified proxies
set -euo pipefail

COMMAND="${1:-status}"

case "$COMMAND" in
  status)
    echo "=== Active Cloudflare Tunnels ==="
    pgrep -a -f "cloudflared tunnel" || echo "No active cloudflared tunnel processes."
    echo ""
    echo "=== Active Unified Proxies ==="
    pgrep -a -f "unified-proxy.mjs" || echo "No active unified proxies."
    echo ""
    echo "=== Discovered Public URLs ==="
    for log in /tmp/cloudflared*.log; do
      if [[ -f "$log" ]]; then
        URL=$(grep -o 'https://[-a-z0-9.]*trycloudflare.com' "$log" | tail -n 1 || true)
        if [[ -n "$URL" ]]; then
          echo "$log -> $URL"
        fi
      fi
    done
    ;;

  kill)
    TARGET="${2:-all}"
    if [[ "$TARGET" == "all" ]]; then
      echo "Terminating all cloudflared tunnel instances..."
      pkill -f "cloudflared tunnel" || true
      pkill -f "unified-proxy.mjs" || true
      echo "Cleaned up."
    else
      echo "Terminating process matching: $TARGET"
      pkill -f "$TARGET" || true
    fi
    ;;

  health)
    URL="${2:-}"
    if [[ -z "$URL" ]]; then
      # Try to pick latest URL from /tmp/cloudflared*.log
      for log in /tmp/cloudflared*.log; do
        if [[ -f "$log" ]]; then
          URL=$(grep -o 'https://[-a-z0-9.]*trycloudflare.com' "$log" | tail -n 1 || true)
          break
        fi
      done
    fi

    if [[ -z "$URL" ]]; then
      echo "Error: No tunnel URL provided and none found in /tmp/cloudflared*.log." >&2
      exit 1
    fi

    echo "Checking health of: $URL"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$URL" || echo "failed")
    echo "HTTP Status: $HTTP_CODE"
    if [[ "$HTTP_CODE" =~ ^(200|301|302|404)$ ]]; then
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
    echo "  kill [target] Terminate running tunnels ('all' or substring filter)"
    echo "  health [url]  Test connectivity of a tunnel URL"
    ;;
esac
