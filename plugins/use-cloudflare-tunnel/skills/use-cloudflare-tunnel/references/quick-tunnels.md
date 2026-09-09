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

## 1. Starting a Quick Tunnel

### Basic Command
```bash
cloudflared tunnel --url http://127.0.0.1:8080
```

### Recommended Agentic Execution
When running from an AI coding agent or automated script, always capture logs, record the PID, and disable autoupdates:

```bash
cloudflared tunnel \
  --url http://127.0.0.1:8080 \
  --logfile /tmp/cloudflared-8080.log \
  --pidfile /tmp/cloudflared-8080.pid \
  --no-autoupdate \
  --protocol quic &
```

---

## 2. Extracting the Public URL

Cloudflared logs the assigned public URL during startup. The URL matches the pattern `https://[-a-z0-9.]*trycloudflare.com`.

### Regex Extraction via Bash
```bash
# Wait up to 15 seconds for the tunnel to establish
TIMEOUT=15
START=$(date +%s)
URL=""

while [[ $(( $(date +%s) - START )) -lt $TIMEOUT ]]; do
  if [[ -f /tmp/cloudflared-8080.log ]]; then
    URL=$(grep -o 'https://[-a-z0-9.]*trycloudflare.com' /tmp/cloudflared-8080.log | head -n 1 || true)
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

## 3. Essential CLI Flags

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

## 4. Lifecycle Management & Teardown

Because Quick Tunnels terminate as soon as the `cloudflared` process dies, managing background processes properly is critical.

### Graceful Shutdown
```bash
# Using recorded PID file
if [[ -f /tmp/cloudflared-8080.pid ]]; then
  kill -SIGINT "$(cat /tmp/cloudflared-8080.pid)" 2>/dev/null || true
  rm -f /tmp/cloudflared-8080.pid
fi

# Fallback: process pattern kill
pkill -f "cloudflared tunnel --url http://127.0.0.1:8080" || true
```

### Verifying Termination
```bash
pgrep -f "cloudflared tunnel" || echo "All tunnels clean"
```

---

## 5. Security & Availability Boundaries

1. **No SLA / Ephemeral:** Quick tunnels have no uptime guarantees and subdomains are randomized upon every launch. Never use them as hardcoded production URLs.
2. **Publicly Reachable:** Any user on the internet with the `trycloudflare.com` URL can access the exposed endpoint. If the service lacks internal authentication, add application-layer credentials or IP checks.
3. **Bandwidth & Rate Limits:** Cloudflare reserves the right to rate-limit excessive traffic or abuse on the free `trycloudflare.com` domain.
