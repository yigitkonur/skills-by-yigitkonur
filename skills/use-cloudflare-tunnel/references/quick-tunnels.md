# Cloudflare Quick Tunnels (TryCloudflare)

Quick Tunnels (`trycloudflare.com`) provide instant, zero-authentication, ephemeral public HTTPS endpoints for local development servers and containers.

## Core Characteristics

| Dimension | Quick Tunnels (`trycloudflare.com`) | Named Tunnels (Production) |
|---|---|---|
| **Account Requirement** | None (no login, no API token) | Required (Cloudflare Zero Trust account) |
| **Domain** | Random subdomain on `trycloudflare.com` | Custom domain/subdomain with Cloudflare DNS |
| **Configuration** | CLI flags only (no `config.yml` needed) | `config.yml` or remote dashboard management |
| **Lifetime** | Tied to process runtime (ephemeral) | Persistent across process restarts and reboots |
| **Protocol Support** | HTTP, HTTPS, WebSockets | HTTP, HTTPS, WebSockets, TCP, SSH, RDP |
| **Primary Use Cases** | Prototyping, remote testing, webhooks | Production deployments, private networks |

---

## 1. Starting a Quick Tunnel (Agent-Safe Recipe)

When running from an AI coding agent or automated script, always use `setsid` process group isolation, capture logs, record the PID, and disable autoupdates:

```bash
# 1. Clean previous state
rm -rf /tmp/cloudflared-8080.log /tmp/cloudflared-8080.pid ~/.cloudflared/

# 2. Launch detached daemon (never dies on subshell exit)
setsid nohup cloudflared tunnel \
  --url http://127.0.0.1:8080 \
  --logfile /tmp/cloudflared-8080.log \
  --pidfile /tmp/cloudflared-8080.pid \
  --no-autoupdate \
  --protocol quic </dev/null >/dev/null 2>&1 &

DAEMON_PID=$!
```

---

## 2. Extracting the Public URL

Cloudflared logs the assigned public URL during startup. The URL matches the pattern `https://[-a-z0-9.]*trycloudflare.com`.

```bash
# Wait up to 15 seconds for the tunnel to establish
TIMEOUT=15
START=$(date +%s)
URL=""

while [[ $(( $(date +%s) - START )) -lt $TIMEOUT ]]; do
  if [[ -f /tmp/cloudflared-8080.log ]]; then
    URL=$(grep -o 'https://[-a-z0-9.]*trycloudflare.com' /tmp/cloudflared-8080.log | tail -n 1 || true)
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

## 3. The DNS Propagation & 5-Minute NXDOMAIN Negative-Cache Trap

When Cloudflare registers a new random `*.trycloudflare.com` subdomain, global DNS propagation takes 1–3 seconds.

### The Failure Mechanism:
1. If the client machine (or local resolver like Tailscale MagicDNS `100.100.100.100`) sends a DNS query **before** Cloudflare edge nameservers publish the record, the resolver receives an `NXDOMAIN` response.
2. The resolver caches this `NXDOMAIN` with Cloudflare's SOA negative TTL (**300 seconds / 5 minutes**).
3. Even though the tunnel is healthy and working on the edge, the client machine is **locked out of resolving the domain for 5 minutes**.

### The Prevention Algorithm (2-Step Handshake):
Always wait for global authoritative DNS before making the first client query:

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
| `--protocol <proto>` | `quic` \| `http2` | `quic` | Transport protocol between host and Cloudflare edge. Fall back to `http2` if UDP is blocked. |
| `--logfile <path>` | path | `stderr` | File to store logs, which contains the assigned URL and connection health checks. |
| `--pidfile <path>` | path | none | Records the process ID for deterministic process management and termination. |
| `--no-autoupdate` | boolean | `false` | Prevents cloudflared from blocking on or downloading background updates during runs. |
| `--no-prechecks` | boolean | `false` | Skips initial DNS/UDP connectivity pre-checks, speeding up cold startup by 2–4 seconds. |
| `--http-host-header <host>` | string | target host | Rewrites the `Host` header sent to origin (useful for vhost-based servers). |

---

## 5. Lifecycle Management & Teardown

Never leave orphaned tunnel processes or stale session tokens:

```bash
# Terminate running quick tunnels
pkill -f "cloudflared tunnel" || true

# Clean up session state
rm -rf /tmp/cloudflared* ~/.cloudflared/
```
