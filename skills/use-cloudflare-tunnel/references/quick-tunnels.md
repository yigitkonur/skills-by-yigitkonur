# Cloudflare Quick Tunnels ([try.cloudflare.com](https://try.cloudflare.com/))

Quick Tunnels (`trycloudflare.com`) provide instant, zero-authentication, ephemeral public HTTPS endpoints for local development servers and containers. Cloudflare's dedicated developer portal at **[try.cloudflare.com](https://try.cloudflare.com/)** introduces native support for autonomous coding agents via `--output json`.

## Core Characteristics & Agent Trade-Offs

| Dimension | Quick Tunnels (`try.cloudflare.com`) | Named Tunnels (Production) |
|---|---|---|
| **Account Requirement** | None (no login, no API token, no secret leakage risk) | Required (Cloudflare Zero Trust account & tokens) |
| **Domain Stability** | Ephemeral, random subdomain (e.g. `*.trycloudflare.com`) | Custom domain/subdomain with Cloudflare DNS |
| **Configuration** | CLI flags only (no `config.yml` needed) | `config.yml` or remote dashboard management |
| **Lifetime** | Tied to process runtime (terminates with process) | Persistent across process restarts and reboots |
| **Protocol Support** | HTTP, HTTPS, WebSockets | HTTP, HTTPS, WebSockets, TCP, SSH, RDP, Unix |
| **Agent Suitability** | **Best for ad-hoc agent loops:** Zero secrets to manage or leak. | Best for long-lived endpoints needing stable URLs and Access policies. |

---

## 1. Starting a Quick Tunnel (Agent-Safe Recipe)

When running from an AI coding agent or automated script, use portable process group isolation, capture structured JSON logs, and disable autoupdates.

> [!WARNING]
> **Never delete `~/.cloudflared/` during quick tunnel cleanup.** Quick Tunnels do not use that directory, whereas Named Tunnels store permanent `cert.pem` logins and `<UUID>.json` credentials there.

```bash
PORT=8080
LOGFILE="/tmp/cloudflared-${PORT}.log"
PIDFILE="/tmp/cloudflared-${PORT}.pid"

# 1. Clean previous run state only (DO NOT touch ~/.cloudflared/)
rm -f "$LOGFILE" "$PIDFILE"

# 2. Launch detached daemon with cross-platform fallback (Linux setsid / macOS nohup)
SPAWN_CMD="cloudflared tunnel --url http://127.0.0.1:${PORT} --logfile $LOGFILE --pidfile $PIDFILE --no-autoupdate --output json"

if command -v setsid &>/dev/null; then
  setsid nohup $SPAWN_CMD </dev/null >/dev/null 2>&1 &
else
  nohup $SPAWN_CMD </dev/null >/dev/null 2>&1 &
fi

DAEMON_PID=$!
```

---

## 2. Extracting the Public URL

Cloudflare Quick Tunnels log the assigned public URL during startup. With `--output json`, events are emitted as clean NDJSON:

```bash
# Wait up to 15 seconds for the tunnel to establish
TIMEOUT=15
START=$(date +%s)
URL=""

while [[ $(( $(date +%s) - START )) -lt $TIMEOUT ]]; do
  if [[ -f "$LOGFILE" ]]; then
    # Matches URL pattern in standard or json output
    URL=$(grep -o 'https://[-a-z0-9.]*trycloudflare.com' "$LOGFILE" | tail -n 1 || true)
    if [[ -n "$URL" ]]; then break; fi
  fi
  sleep 0.5
done

if [[ -z "$URL" ]]; then
  echo "Failed to extract tunnel URL within ${TIMEOUT}s" >&2
  exit 1
fi

echo "Tunnel URL: $URL"
```

---

## 3. The DNS Propagation & 60-Second Negative-Cache Window

When Cloudflare registers a new random `*.trycloudflare.com` subdomain, global DNS propagation takes 1–3 seconds.

### The Failure Mechanism:
1. If a client machine (or local resolver like Tailscale MagicDNS `100.100.100.100`) queries the subdomain **before** Cloudflare edge nameservers publish the record, the resolver receives an `NXDOMAIN` response.
2. The resolver caches this `NXDOMAIN` based on Cloudflare's SOA minimum TTL (**60 seconds** per RFC 2308).
3. The client is temporarily delayed from resolving the domain until the 60s cache expires.

### The Prevention Algorithm (2-Step Handshake):
Wait for global authoritative DNS before making the first client query:

```bash
HOST_ONLY=$(echo "$URL" | sed -E 's#^https?://##')

# Step 1: Wait until 1.1.1.1 and 8.8.8.8 resolve the record
for i in {1..15}; do
  IP1=$(dig @1.1.1.1 +short "$HOST_ONLY" 2>/dev/null | tail -n 1 || true)
  IP2=$(dig @8.8.8.8 +short "$HOST_ONLY" 2>/dev/null | tail -n 1 || true)
  if [[ -n "$IP1" && -n "$IP2" ]]; then
    echo "✓ Global DNS published: 1.1.1.1=$IP1, 8.8.8.8=$IP2"
    break
  fi
  sleep 1
done

# Step 2: Flush client DNS cache before first query
if command -v dscacheutil &>/dev/null; then
  dscacheutil -flushcache 2>/dev/null || true
fi
```

---

## 4. Essential CLI Flags

| Flag | Type | Default | Description |
|---|---|---|---|
| `--url <address>` | string | Required | Target local service (e.g. `http://localhost:3000` or `http://127.0.0.1:8080`). |
| `--output <format>` | `default` \| `json` | `default` | Output format. Set to `json` for machine-readable NDJSON logs for agent workflows. |
| `--protocol <proto>` | `auto` \| `quic` \| `http2` | `auto` | Transport protocol to edge. `auto` is the default and recommended mode. Both QUIC (UDP) and HTTP/2 (TCP) use port 7844. |
| `--logfile <path>` | path | `stderr` | File to store logs, which contains the assigned URL and connection health checks. |
| `--pidfile <path>` | path | none | Records the process ID (written after first successful connection to edge). |
| `--no-autoupdate` | boolean | `false` | Prevents cloudflared from blocking on or downloading background updates during runs. |
| `--no-prechecks` | boolean | `false` | Skips initial DNS/connectivity pre-checks, speeding up cold startup by 2–4 seconds. |
| `--post-quantum`, `--pq` | boolean | `false` | Enables experimental post-quantum hybrid key exchange (`X25519MLKEM768`). |
| `--http-host-header <host>` | string | target host | Rewrites the `Host` header sent to origin (useful for vhost-based servers). |

---

## 5. Lifecycle Management & Teardown

Never leave orphaned tunnel processes running in the background. Clean up only the process instances:

```bash
# Terminate running quick tunnels
pkill -f "cloudflared tunnel" || true

# Clean up temporary logs (Preserve ~/.cloudflared/)
rm -f /tmp/cloudflared*.log /tmp/cloudflared*.pid
```
