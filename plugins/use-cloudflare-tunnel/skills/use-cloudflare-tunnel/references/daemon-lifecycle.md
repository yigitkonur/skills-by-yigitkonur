# Background Daemon Lifecycle & Process Management

Running `cloudflared` inside agentic workflows, subagents, or automated CI systems requires predictable process controls to prevent orphaned daemons, process group termination, and port conflicts.

---

## 1. Process Group Isolation for AI Agents (`setsid`)

When an AI coding agent executes bash commands via tools (e.g. `run_command`), each tool invocation creates a subshell. Standard background commands (`cmd &` or `nohup cmd &`) remain bound to the tool process group and standard input.

When the tool invocation finishes:
* The subshell sends `SIGHUP` and `SIGTERM` to all child processes in the process group.
* Standard `cloudflared &` background processes terminate immediately upon tool exit.

### The Agent-Safe Background Recipe

To ensure the tunnel persists across tool calls, agents **must** use `setsid` with detached `stdio`:

```bash
PORT=8099
LOGFILE="/tmp/cloudflared-${PORT}.log"
PIDFILE="/tmp/cloudflared-${PORT}.pid"

# 1. Clean previous state & session tokens
rm -rf "$LOGFILE" "$PIDFILE" ~/.cloudflared/

# 2. Launch detached daemon with process group isolation
setsid nohup cloudflared tunnel \
  --url "http://127.0.0.1:${PORT}" \
  --logfile "$LOGFILE" \
  --pidfile "$PIDFILE" \
  --no-autoupdate \
  --protocol quic </dev/null >/dev/null 2>&1 &

DAEMON_PID=$!

# 3. Poll for URL with 15-second timeout
TIMEOUT=15
START=$(date +%s)
URL=""

while [[ $(( $(date +%s) - START )) -lt $TIMEOUT ]]; do
  if [[ -f "$LOGFILE" ]]; then
    URL=$(grep -o 'https://[-a-z0-9.]*trycloudflare.com' "$LOGFILE" | tail -n 1 || true)
    if [[ -n "$URL" ]]; then break; fi
  fi
  sleep 0.5
done

if [[ -z "$URL" ]]; then
  echo "Error: Tunnel failed to initialize" >&2
  kill "$DAEMON_PID" 2>/dev/null || true
  exit 1
fi

echo "Active Persistent Tunnel URL: $URL"
```

---

## 2. Health Checks and Metrics Endpoints

`cloudflared` includes an embedded HTTP server for metrics and health checking.

### Enabling Metrics:
Pass `--metrics 127.0.0.1:20241` to bind a predictable local port:
```bash
cloudflared tunnel --metrics 127.0.0.1:20241 --url http://127.0.0.1:8080 ...
```

### Health Endpoints:
* **Ready Probe:** `curl -s http://127.0.0.1:20241/ready`
  * Returns HTTP 200 when the tunnel has successfully registered with Cloudflare edge data centers.
  * Returns HTTP 503 if still establishing or retrying connections.
* **Prometheus Metrics:** `curl -s http://127.0.0.1:20241/metrics`
  * `cloudflared_tunnel_total_requests`: Total request count.
  * `cloudflared_tunnel_active_streams`: Currently open concurrent streams.
  * `cloudflared_tunnel_ha_connections`: Number of active redundant edge connections.

---

## 3. Deterministic Teardown & Session Reset

Never leave orphaned `cloudflared` processes running in the background when a task ends.

### Clean Shutdown via PID File:
```bash
if [[ -f /tmp/cloudflared-8099.pid ]]; then
  PID=$(cat /tmp/cloudflared-8099.pid)
  kill -SIGINT "$PID" 2>/dev/null || true
  rm -f /tmp/cloudflared-8099.pid
fi
```

### Complete Cleanup (Processes + Session Cache):
```bash
# Terminate any running cloudflared quick tunnels
pkill -f "cloudflared tunnel" || true

# Free hung origin port
fuser -k 8099/tcp 2>/dev/null || true

# Remove stale session tokens to guarantee fresh subdomain on next run
rm -rf /tmp/cloudflared* ~/.cloudflared/
```
