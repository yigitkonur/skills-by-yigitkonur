# Background Daemon Lifecycle & Process Management

Running `cloudflared` inside agentic workflows, subagents, or automated CI systems requires predictable process controls to prevent orphaned daemons and port conflicts.

---

## 1. Background Execution Pattern for AI Agents

When an AI coding agent starts a tunnel, the process must run asynchronously while the agent captures its output and proceeds with testing.

### The Robust Background Recipe:
1. Ensure no previous instance is holding the target log/port.
2. Launch with explicit `--logfile` and `--pidfile`.
3. Disable autoupdates (`--no-autoupdate`) to avoid background restarts.
4. Extract the assigned URL using a bounded polling loop.

```bash
PORT=8099
LOGFILE="/tmp/cloudflared-${PORT}.log"
PIDFILE="/tmp/cloudflared-${PORT}.pid"

# 1. Clean previous state
rm -f "$LOGFILE" "$PIDFILE"

# 2. Launch background daemon
cloudflared tunnel \
  --url "http://127.0.0.1:${PORT}" \
  --logfile "$LOGFILE" \
  --pidfile "$PIDFILE" \
  --no-autoupdate >/dev/null 2>&1 &

DAEMON_PID=$!

# 3. Poll for URL with 15-second timeout
TIMEOUT=15
START=$(date +%s)
URL=""

while [[ $(( $(date +%s) - START )) -lt $TIMEOUT ]]; do
  if [[ -f "$LOGFILE" ]]; then
    URL=$(grep -o 'https://[-a-z0-9.]*trycloudflare.com' "$LOGFILE" | head -n 1 || true)
    if [[ -n "$URL" ]]; then break; fi
  fi
  sleep 0.5
done

if [[ -z "$URL" ]]; then
  echo "Error: Tunnel failed to initialize" >&2
  kill "$DAEMON_PID" 2>/dev/null || true
  exit 1
fi

echo "Active Tunnel URL: $URL"
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

## 3. Deterministic Teardown & Zombie Cleanup

Never leave orphaned `cloudflared` processes running in the background when a task ends.

### Clean Shutdown via PID File:
```bash
if [[ -f /tmp/cloudflared-8099.pid ]]; then
  PID=$(cat /tmp/cloudflared-8099.pid)
  kill -SIGINT "$PID" 2>/dev/null || true
  rm -f /tmp/cloudflared-8099.pid
fi
```

### Aggressive Process Reaper:
```bash
# Terminate any running cloudflared quick tunnels
pkill -f "cloudflared tunnel --url" || true

# Free a hung origin port
fuser -k 8099/tcp 2>/dev/null || true
```
