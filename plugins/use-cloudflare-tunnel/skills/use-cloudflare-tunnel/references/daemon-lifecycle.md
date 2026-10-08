# Background Daemon Lifecycle & Process Management

Running `cloudflared` inside agentic workflows, subagents, or automated CI systems requires predictable process controls to prevent orphaned daemons, process group termination, and port conflicts.

---

## 1. Process Group Isolation for AI Agents

When an AI coding agent executes shell commands via tools (e.g. `run_command`), each tool invocation creates a subshell. Standard background commands (`cmd &` or `nohup cmd &`) remain bound to the tool process group and standard input.

When the tool invocation finishes:
* The subshell sends `SIGHUP` and `SIGTERM` to all child processes in the process group.
* Bare background processes may terminate prematurely upon tool exit.

### The Agent-Safe Cross-Platform Background Recipe

To ensure the tunnel persists across tool calls on both Linux and macOS, decouple stdio and check for `setsid`:

```bash
PORT=8099
LOGFILE="/tmp/cloudflared-${PORT}.log"
PIDFILE="/tmp/cloudflared-${PORT}.pid"

# 1. Clean previous run state (DO NOT touch ~/.cloudflared/)
rm -f "$LOGFILE" "$PIDFILE"

# 2. Launch detached daemon with cross-platform fallback
SPAWN_CMD="cloudflared tunnel --url http://127.0.0.1:${PORT} --logfile $LOGFILE --pidfile $PIDFILE --no-autoupdate --output json"

if command -v setsid &>/dev/null; then
  setsid nohup $SPAWN_CMD </dev/null >/dev/null 2>&1 &
else
  nohup $SPAWN_CMD </dev/null >/dev/null 2>&1 &
fi

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

## 2. Health Checks, Metrics & Built-in Diagnostics

`cloudflared` includes an embedded HTTP server for metrics and health checking, as well as an automated diagnostic suite.

### Diagnostic Command: `cloudflared tunnel diag`
To inspect tunnel state, system info, goroutine/heap profiles, and automated connectivity pre-checks (port 7844 UDP/TCP reachability):
```bash
cloudflared tunnel diag
```

### Enabling Local Metrics:
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

> [!NOTE]
> The `--pidfile` path is populated **after the first successful connection** to Cloudflare edge is established, not synchronously at initial process fork.

---

## 3. Deterministic Teardown & Safe Reset

Never leave orphaned `cloudflared` processes running in the background when a task ends.

### Clean Shutdown via PID File:
```bash
if [[ -f /tmp/cloudflared-8099.pid ]]; then
  PID=$(cat /tmp/cloudflared-8099.pid)
  kill -SIGINT "$PID" 2>/dev/null || true
  rm -f /tmp/cloudflared-8099.pid
fi
```

### Complete Cleanup (Processes & Logs):
```bash
# Terminate running quick tunnels
pkill -f "cloudflared tunnel" || true

# Free hung origin port portably across macOS and Linux
if command -v lsof &>/dev/null; then
  lsof -ti :8099 | xargs kill -9 2>/dev/null || true
elif command -v fuser &>/dev/null; then
  fuser -k 8099/tcp 2>/dev/null || true
fi

# Clean temporary logs only (PRESERVE ~/.cloudflared/)
rm -f /tmp/cloudflared*
```
