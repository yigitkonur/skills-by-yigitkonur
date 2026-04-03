# Logging and debugging reference

## Logger architecture

`mcpc` uses a two-layer logging system defined in `src/lib/logger.ts` and `src/lib/file-logger.ts`.

### Log levels

Four levels are defined with numeric priority:

| Level | Priority | When emitted |
|-------|----------|--------------|
| `debug` | 0 | Verbose mode only (console); always written to file |
| `info`  | 1 | Default threshold for console output |
| `warn`  | 2 | Conditions worth noting but non-fatal |
| `error` | 3 | Failures that affect the operation |

The internal `currentLogLevel` starts at `info`. Enabling verbose mode calls `setLogLevel('debug')` automatically.

### Module-level singletons

- `isVerbose` — set by `--verbose` or `MCPC_VERBOSE`
- `isJsonMode` — set by `--json` or `MCPC_JSON`; suppresses **all** console output to keep stderr clean for structured output
- `fileLogger` — a `FileLogger` instance, `null` until `initFileLogger()` is called

### Logger class and context prefixes

`createLogger(context)` returns a `Logger` that prefixes every message with `[context]`. `createNoOpLogger()` returns a no-op variant used in tests.

Output always goes to `process.stderr` — never stdout — so tool output on stdout stays clean for piping. File writes are unconditional: `debug`-level messages reach the log file even when suppressed on the console, so the file is always at full verbosity.

### Message format

- Console (non-verbose): raw message only, no timestamp, no level prefix
- Console (verbose): `[ISO-timestamp] [LEVEL] message`
- File: always `[ISO-timestamp] [LEVEL] message`

### Exception formatting

`formatExceptionChain(error)` produces a multi-line string containing:
1. `ErrorName: message`
2. Indented stack frames (skipping the redundant first line)
3. Any extra enumerable properties (`code`, `errno`, `syscall`, `hostname`, etc.) via `util.inspect`
4. Recursive `Cause:` block if `error.cause` is set

---

## Verbose mode activation

### Flag syntax

```bash
mcpc --verbose @session command
```

`--verbose` must appear **before** `@session`. Example:

```bash
mcpc --verbose @apify tools-list
mcpc --verbose connect mcp.apify.com @apify
```

### Environment variable

```bash
MCPC_VERBOSE=1 mcpc @session tools-call my-tool arg:=value
```

Accepted truthy values (case-insensitive): `1`, `true`, `yes`. Persist with `export MCPC_VERBOSE=1` in your shell profile.

### Effect of enabling verbose mode

- `currentLogLevel` drops to `debug`; all four log functions emit to stderr with full `[timestamp] [LEVEL]` prefix
- IPC messages, argument parsing steps, session resolution, reconnection attempts, and keepalive pings all become visible

---

## File logging

### Location

```
~/.mcpc/logs/bridge-<session-name>.log
```

The bridge process calls `initFileLogger('bridge-<session>.log')` at startup. The CLI process does not currently open a separate file log; bridge logs capture the MCP-protocol-level activity.

Example paths:

```
~/.mcpc/logs/bridge-apify.log
~/.mcpc/logs/bridge-filesystem.log
```

### Startup banner

Every bridge start/restart writes a separator block to mark session boundaries:

```
[2025-03-24T10:00:00.000Z] ========================================
[2025-03-24T10:00:00.000Z] mcpc v1.2.3
[2025-03-24T10:00:00.000Z] Command: mcpc-bridge apify
[2025-03-24T10:00:00.000Z] ========================================
```

---

## Log rotation

Rotation is implemented in `FileLogger` (append-mode write stream, size tracked in bytes).

| Parameter | Value |
|-----------|-------|
| Max file size | 10 MB (10 × 1024 × 1024 bytes) |
| Max rotated files kept | 5 |

### Rotation behavior

1. On `init()`: if the file is already ≥ 10 MB, rotate before opening the stream.
2. On each `write()`: accumulated byte count is checked; if it crosses 10 MB, `rotateAsync()` fires in the background without blocking writes.
3. Rotation shifts: `bridge-apify.log` → `.log.1`, `.log.1` → `.log.2`, …, `.log.4` → `.log.5`; any file at index ≥ 5 is deleted.

Maximum total log data per session: ~60 MB (6 files × 10 MB).

---

## What verbose mode shows

### CLI side

- Argument parsing steps: how `@session` is resolved, which session entry is loaded from `sessions.json`
- IPC socket connection to `~/.mcpc/bridges/<session>.sock`
- JSON-RPC messages sent from CLI to bridge and responses received
- Bridge restart events when socket connection fails and bridge is relaunched

### Bridge side

- Transport handshake: HTTP connection setup, protocol version negotiation (`MCP-Protocol-Version: 2025-11-25`)
- Full MCP `initialize` request and server's capability response
- `initialized` notification sent to activate session
- Every MCP request forwarded to the server and every response returned to the CLI
- Keepalive pings (`ping` requests) and their roundtrip times
- Reconnection attempts after network drop, including exponential backoff intervals (1 s → 30 s max)
- File locking operations on `sessions.json` (acquire/release/timeout)
- Session state transitions (`live` → `disconnected` → `live`, etc.)

---

## Reading and interpreting log files

### Tail a live bridge log

```bash
tail -f ~/.mcpc/logs/bridge-apify.log
```

### Read all rotated files in chronological order

```bash
cat $(ls -r ~/.mcpc/logs/bridge-apify.log{,.1,.2,.3,.4,.5} 2>/dev/null)
```

### Log line anatomy

```
[2025-03-24T10:12:34.567Z] [DEBUG] [bridge] Sending MCP request: tools/list
│                          │       │         └─ message text
│                          │       └─ context prefix (from createLogger)
│                          └─ level
└─ ISO 8601 timestamp (UTC)
```

---

## Filtering logs with grep patterns

```bash
# All errors and warnings
grep -E '\[(ERROR|WARN)\]' ~/.mcpc/logs/bridge-apify.log

# MCP requests only
grep 'Sending MCP request' ~/.mcpc/logs/bridge-apify.log

# MCP responses only
grep 'MCP response' ~/.mcpc/logs/bridge-apify.log

# Reconnection events
grep -E 'reconnect|backoff|retry' ~/.mcpc/logs/bridge-apify.log

# Auth events (token refresh, 401 responses)
grep -iE 'token|auth|401|403|unauthorized' ~/.mcpc/logs/bridge-apify.log

# Keepalive pings
grep -i 'ping' ~/.mcpc/logs/bridge-apify.log

# Session boundary markers (find restarts)
grep '======' ~/.mcpc/logs/bridge-apify.log

# Specific time window (e.g. 10:00–10:05 UTC)
grep '2025-03-24T10:0[0-4]' ~/.mcpc/logs/bridge-apify.log
```

---

## Common debugging workflows

### Transport issues: connection failures and timeouts

**Symptoms:** exit code 3, `NetworkError`, repeated reconnect messages in log.

```bash
# 1. Check for connection errors
grep -iE 'connect|ECONNREFUSED|ENOTFOUND|timeout' ~/.mcpc/logs/bridge-apify.log

# 2. Enable verbose and retry to capture full handshake
mcpc --verbose @apify ping

# 3. Verify the session target URL is reachable
mcpc @apify   # shows session info including server URL
```

Backoff range: 1 s → 30 s. If the server is down, the bridge will queue requests for up to 3 minutes before failing with a network error.

### Auth issues: token expiry and refresh failures

**Symptoms:** exit code 4, session state `unauthorized`, 401/403 in logs.

```bash
# 1. Find auth failures
grep -iE '401|403|token|refresh|unauthorized|expired' ~/.mcpc/logs/bridge-apify.log

# 2. Check session state
mcpc @apify

# 3. Re-authenticate
mcpc login mcp.apify.com --profile personal
mcpc @apify restart   # or: mcpc @apify close && mcpc mcp.apify.com connect @apify
```

Bearer tokens stored per-session in the OS keychain (key: `mcpc:session:<name>:bearer-token`) are loaded by the bridge automatically. If a bearer token is rotated externally, the bridge must be restarted.

### Session issues: stale sessions and bridge crashes

**Symptoms:** socket connection refused, session state `crashed`, hanging CLI command.

```bash
# 1. Look for the crash boundary
grep '======' ~/.mcpc/logs/bridge-apify.log | tail -5
# Each separator marks a bridge startup; if the last one is old, the bridge is gone

# 2. Check for unhandled exceptions before the crash
grep -A5 '\[ERROR\]' ~/.mcpc/logs/bridge-apify.log | tail -30

# 3. Force-restart the bridge
mcpc @apify restart

# 4. If the session is stuck in a bad state, recreate it
mcpc @apify close
mcpc mcp.apify.com connect @apify
```

The CLI auto-restarts crashed bridges on the next command. If auto-restart itself fails, the above manual steps apply.

---

## Performance debugging

### Measure tool call latency

`mcpc @session ping` reports roundtrip time to the MCP server. For tool calls, use the `time` builtin:

```bash
time mcpc @apify tools-call my-tool query:=test
```

### Extract timestamps for a specific tool call from the log

```bash
# Find the request start and response end for a tool call
grep -E 'tools/call|my-tool' ~/.mcpc/logs/bridge-apify.log | tail -20
```

Compute the delta between the `Sending MCP request` and `MCP response` lines manually, or pipe through awk:

```bash
grep -E 'Sending MCP request|MCP response' ~/.mcpc/logs/bridge-apify.log \
  | awk 'NR%2==1{t=$1} NR%2==0{print $1, "delta from", t}'
```

### Isolate IPC overhead

The roundtrip is: CLI → Unix socket → bridge → MCP server → bridge → Unix socket → CLI. Compare `mcpc @session ping` against a direct HTTP ping to the server to measure socket overhead.

---

## Diagnostic data collection for bug reports

Run this script to collect all relevant state in one place:

```bash
#!/usr/bin/env bash
set -euo pipefail
SESSION="${1:-}"
OUTDIR="mcpc-diag-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUTDIR"

# mcpc version
mcpc --version > "$OUTDIR/version.txt" 2>&1 || true

# Session list
mcpc --json 2>/dev/null > "$OUTDIR/sessions.json" || true

# Session-specific info
if [[ -n "$SESSION" ]]; then
  mcpc --json "@$SESSION" > "$OUTDIR/session-info.json" 2>&1 || true
  LOGFILE="$HOME/.mcpc/logs/bridge-${SESSION}.log"
  if [[ -f "$LOGFILE" ]]; then
    # Last 500 lines of current log
    tail -500 "$LOGFILE" > "$OUTDIR/bridge-current.log"
  fi
  # Include one rotated file if present
  if [[ -f "${LOGFILE}.1" ]]; then
    tail -200 "${LOGFILE}.1" > "$OUTDIR/bridge-prev.log"
  fi
fi

# sessions.json metadata (no credentials)
SESSIONS_FILE="${MCPC_HOME_DIR:-$HOME/.mcpc}/sessions.json"
if [[ -f "$SESSIONS_FILE" ]]; then
  cp "$SESSIONS_FILE" "$OUTDIR/sessions-meta.json"
fi

# Node/Bun version
node --version > "$OUTDIR/runtime.txt" 2>&1 || true
bun --version >> "$OUTDIR/runtime.txt" 2>&1 || true
uname -a >> "$OUTDIR/runtime.txt"

echo "Diagnostics written to: $OUTDIR/"
echo "Review for credentials before sharing, then: tar czf ${OUTDIR}.tar.gz $OUTDIR/"
```

Usage:

```bash
bash collect-diag.sh apify   # replace 'apify' with your session name
```

The script does not include OS keychain contents or OAuth tokens. Review `sessions-meta.json` to ensure no bearer tokens appear in plaintext before sharing.
