# Bridge internals

This document describes the internal architecture of the bridge subsystem that backs every persistent `mcpc` session. Read this before debugging connection problems, writing tests that control session lifecycles, or extending the IPC layer.

**Key syntax reminder:**
- Create a session: `mcpc <target> connect @<session>`
- Destroy a session: `mcpc @session close`

---

## Overview of the three-layer stack

```
CLI process
  └─ SessionClient          (IMcpClient wrapper, auto-recovery)
       └─ BridgeClient      (Unix socket, newline-delimited JSON)
            └─ bridge IPC   (~/.mcpc/bridges/<session>.sock)
                  └─ BridgeProcess (separate OS process)
                       └─ McpClient → MCP server
```

Each layer has a single, non-overlapping responsibility:

| Layer | File | Owns |
|---|---|---|
| `BridgeClient` | `src/lib/bridge-client.ts` | Raw socket I/O, message framing, per-request timeouts |
| `bridge-manager` | `src/lib/bridge-manager.ts` | Process spawning, health checking, error classification |
| `SessionClient` | `src/lib/session-client.ts` | `IMcpClient` interface, one-shot restart on socket failure |

---

## Bridge spawning: how `startBridge()` works

`startBridge()` in `bridge-manager.ts` is the entry point that turns a session record into a running OS process.

### Argument sanitization before spawn

Headers passed via `--header` flags are **never** placed on the command line — they would be visible in `ps` output. Instead:

1. A `sanitizedTarget` is built by cloning `serverConfig` and deleting the `headers` key.
2. The sanitized config is JSON-serialized and passed as `args[1]`.
3. If a `--profile` was specified, `--profile <name>` is appended; if only raw headers were given (no OAuth profile), `--profile dummy` is appended so the bridge knows to wait for credentials before connecting.

Other flags forwarded verbatim: `--verbose`, `--proxy-host`, `--proxy-port`, `--mcp-session-id`, `--x402`, `--insecure`.

### The spawn call

```ts
spawn('node', [bridgeExecutable, ...args], {
  detached: true,
  stdio: 'ignore',
})
```

- `detached: true` — the child is placed in its own process group; it survives the parent CLI process exiting.
- `stdio: 'ignore'` — stdin/stdout/stderr are not inherited; all bridge output goes to its rotating log file at `~/.mcpc/logs/bridge-<session>.log`.
- `bridgeProcess.unref()` — Node's event loop does not wait for the child; the CLI can exit freely.

### Socket-file gate

After spawning, `startBridge()` calls `waitForFile(socketPath, { timeoutMs: 5000 })`. The socket file at `~/.mcpc/bridges/<session>.sock` is only created once the bridge's `net.createServer()` is listening. If the file does not appear within 5 s, the spawned process is sent `SIGTERM` and a `ClientError` is thrown.

Before spawning, any pre-existing socket file is deleted with `unlink()` so that `waitForFile()` cannot pick up a stale file from a previous run.

### Auth credential delivery

After the socket file appears, if `profileName` or `headers` were provided, `sendAuthCredentialsToBridge()` opens a short-lived `BridgeClient` connection, fires a one-way `set-auth-credentials` IPC message, and immediately closes. The bridge holds a `Promise` (`authCredentialsReceived`) that resolves when this message arrives, blocking the MCP connect step until credentials are in memory.

If `x402` mode is enabled, a second one-way `set-x402-wallet` message follows using the same pattern.

---

## Bridge startup sequence (20 steps)

The `BridgeProcess` inside `src/bridge/index.ts` executes this sequence on startup:

1. Parse CLI args (`sessionName`, serialized `serverConfig`, flags).
2. Initialize file logger at `~/.mcpc/logs/bridge-<session>.log` (10 MB max, 5 rotating files).
3. Apply `--insecure` flag (skip TLS verification) and `--proxy-host`/`--proxy-port` (configure HTTP proxy via `initProxy`).
4. Ensure bridges directory exists (`~/.mcpc/bridges/`).
5. Clean up orphaned log files from dead sessions.
6. Build the socket path from session name via `getSocketPath()` (Unix: `~/.mcpc/bridges/<session>.sock`; Windows: named pipe).
7. Create `mcpClientReady` promise — all incoming `getServerDetails` requests block on this until MCP handshake completes.
8. Create `authCredentialsReceived` promise (only when `profileName` is set) — MCP connect blocks on this.
9. Create `x402WalletReceived` promise (only when `--x402` flag is set).
10. Create Unix socket server with `net.createServer()`.
11. Register `connection` handler — each new CLI connection gets its own socket instance with newline-delimited JSON framing and a 10 MB buffer guard.
12. Start listening on the socket path — **this creates the socket file** that unblocks `waitForFile()` in the CLI.
13. Register `SIGTERM` handler for graceful shutdown.
14. Await `authCredentialsReceived` (if needed) — execution pauses here until the CLI sends credentials via IPC.
15. Await `x402WalletReceived` (if needed).
16. Build `OAuthProvider` / `OAuthTokenManager` from received credentials, or use raw headers.
17. Call `createMcpClient()` with transport config, auth provider, and optional x402 fetch middleware.
18. Perform MCP initialization handshake (`initialize` → `initialized`).
19. Resolve `mcpClientReady` — any queued `getServerDetails` calls can now return.
20. Start keepalive ping loop (30 s interval).

---

## BridgeClient: Unix socket connection

`BridgeClient` (`src/lib/bridge-client.ts`) is a thin `EventEmitter` that wraps a Node.js `net.Socket`.

### Constants

| Constant | Value | Purpose |
|---|---|---|
| `CONNECT_TIMEOUT` | 5 s | Max wait for `socket.on('connect')` |
| `REQUEST_TIMEOUT` | 3 min | Default per-request timeout (MCP operations can be slow) |
| `MAX_BUFFER_SIZE` | 10 MB | If the accumulation buffer exceeds this, the socket is destroyed |

### Connection

`connect()` calls `net.connect(socketPath)`. A `setTimeout` fires after `CONNECT_TIMEOUT` ms; if the `connect` event has not fired yet, the socket is destroyed and a `NetworkError` is thrown. On success, `setupSocket()` wires up `data`, `end`, and `error` handlers.

### Message framing

The protocol is newline-delimited JSON (`\n` as delimiter). Incoming `data` events are appended to `this.buffer`. The buffer is scanned for `\n` in a `while` loop; each complete line is parsed as `IpcMessage` and passed to `handleMessage()`.

### Request/response correlation

`request(method, params, timeout?, requestId?)` generates a UUID (or uses the provided `requestId`), registers a `{ resolve, reject, timeoutId }` entry in `this.pendingRequests`, serializes the message, and writes it to the socket. When `handleMessage()` sees a `response` with a matching `id`, it clears the timeout and resolves or rejects the promise.

### Error code mapping (bridge → CLI)

When the bridge sends a response with an `error`, the numeric `code` field is mapped:

| Code | Error class |
|---|---|
| 1 | `ClientError` |
| 2 | `ServerError` |
| 3 | `NetworkError` |
| 4 | `AuthError` |

### One-way messages

`sendAuthCredentials()` and `sendX402Wallet()` call the internal `send()` method, which writes a JSON line without registering a pending request — there is no response expected.

### Notifications and task-updates

- `notification` messages are re-emitted on the `BridgeClient` instance as `'notification'` events.
- `task-update` messages are emitted as `'task-update:<requestId>'` events, letting the correct `callToolWithTask` caller receive progress updates.

---

## SessionClient: `IMcpClient` wrapper with `withRetry()`

`SessionClient` (`src/lib/session-client.ts`) implements the full `IMcpClient` interface by delegating every call to a `BridgeClient` instance. Its only added behavior is one-shot restart on `NetworkError`.

### `withRetry()` pattern

Every public method (e.g., `listTools`, `callTool`, `ping`) is wrapped:

```
try { return await operation() }
catch (error) {
  if (!(error instanceof NetworkError)) throw;   // MCP errors not retried
  close failed client
  restartBridge(sessionName)                      // spawns new bridge process
  new BridgeClient(socketPath); connect()
  return await operation()                        // one retry
}
```

Non-network errors (server errors, auth errors, client errors) are **not** retried. Instead, the log file path (`~/.mcpc/logs/bridge-<session>.log`) is appended to the error message to guide debugging.

### `callToolWithTask()` crash resilience

This method tracks whether a background task ID was received before the crash. If `capturedTaskId` is set when a `NetworkError` fires:

1. The bridge is restarted and reconnected (same as `withRetry()`).
2. `pollTask(capturedTaskId)` is called instead of re-invoking the tool.

This prevents double-execution of side-effectful tool calls across a bridge crash.

### `createSessionClient()` factory

```ts
const socketPath = await ensureBridgeReady(sessionName);
const bridgeClient = new BridgeClient(socketPath);
await bridgeClient.connect();
return new SessionClient(sessionName, bridgeClient);
```

`ensureBridgeReady()` (see below) is the single gate that guarantees the bridge process is alive and the MCP connection is healthy before any socket is opened.

---

## Health checking: `ensureBridgeReady()` and `checkBridgeHealth()`

### `checkBridgeHealth(socketPath)`

Opens a short-lived `BridgeClient`, calls `request('getServerDetails')`, and closes. Because `getServerDetails` in the bridge blocks on the `mcpClientReady` promise, this call blocks until the bridge's MCP handshake has completed (or fails). Returns `{ healthy: boolean, error?: Error }`.

### `ensureBridgeReady(sessionName)`

This is the top-level entry point called before every CLI operation:

1. Load session from `sessions.json`; throw if missing.
2. Bail immediately with typed errors if `session.status === 'unauthorized'` or `'expired'`.
3. Check `isProcessAlive(session.pid)`.
4. If alive: call `checkBridgeHealth()`.
   - Healthy → return socket path.
   - `NetworkError` → fall through to restart.
   - Session/auth error → classify and throw (see below).
   - Other error → throw `ClientError` with message.
5. If not alive (or after a `NetworkError`): call `restartBridge()`.
6. Call `checkBridgeHealth()` on the restarted bridge; classify and throw on any failure.

---

## Error classification in `bridge-manager`

Two helper predicates gate session state transitions:

### `isSessionExpiredError(message)`

Matches error messages indicating the MCP server responded with 404 or "session not found". When matched:
- `updateSession(sessionName, { status: 'expired' })` is called.
- A `ClientError` is thrown with the message: `Session <name> expired (server rejected session ID). Use "mcpc <name> restart" to start a new session.`

### `isAuthenticationError(message)`

Matches 401/403/unauthorized patterns. When matched:
- `updateSession(sessionName, { status: 'unauthorized' })` is called.
- `createServerAuthError(target, { sessionName })` is thrown.

### Classification order

Session expiry is checked **before** auth errors because a 404 response can carry an "unauthorized" substring in some server implementations. Matching expiry first prevents misclassification.

### Neither pattern matches

- If the error is a `NetworkError` (socket failure) → caller falls through to bridge restart.
- If the error is another type → a `ClientError` wrapping the original message is thrown, with the log path appended.

---

## Bridge crash recovery flow

```
CLI calls SessionClient.listTools()
  → BridgeClient.request('listTools') throws NetworkError
  → withRetry() catches NetworkError
  → bridgeClient.close()
  → restartBridge(sessionName)
      → stopBridge()         SIGTERM → wait 1000 ms → SIGKILL if still alive
      → read headers from keychain
      → startBridge()        spawn new process, waitForFile, send auth credentials
      → updateSession({ pid: newPid })
  → new BridgeClient(socketPath).connect()
  → retry listTools() — succeeds
```

Headers are never lost across restarts: `restartBridge()` reads them from the OS keychain (`readKeychainSessionHeaders()`), cross-checks against the expected keys stored in `session.server.headers`, and delivers them to the new bridge via IPC.

---

## Keepalive ping loop

After the MCP handshake completes, the bridge starts a `setInterval` at `KEEPALIVE_INTERVAL_MS` (30 s). Each tick:

1. Sends an MCP `ping` request to the server.
2. On success: calls `updateSession(sessionName, { lastSeenAt: new Date().toISOString() })` to update the heartbeat timestamp in `sessions.json`.
3. On failure: logs the error but does not crash — the bridge continues and the next ping will retry.

The CLI uses `lastSeenAt` to display session state:
- Within 2 minutes → `live`
- Stale > 2 minutes → `disconnected` (bridge running but server unreachable)

---

## Process lifecycle: SIGTERM → wait → SIGKILL

`stopBridge(sessionName)` implements a two-phase shutdown:

```ts
process.kill(session.pid, 'SIGTERM');
await new Promise(resolve => setTimeout(resolve, 1000));
if (isProcessAlive(session.pid)) {
  process.kill(session.pid, 'SIGKILL');
}
```

The 1 s grace period allows the bridge's `SIGTERM` handler to send an HTTP `DELETE` to the MCP server (Streamable HTTP session termination) before the process is force-killed.

Session records and keychain headers are **not** deleted by `stopBridge()`. They are preserved for failover. Full deletion happens only in `closeSession()` (`mcpc @session close`).

---

## How auth credentials flow

```
mcpc <server> connect @<session> --profile personal
         │
         ├─ getAuthProfile(serverUrl, 'personal')
         ├─ readKeychainOAuthTokenInfo() → refreshToken
         ├─ readKeychainOAuthClientInfo() → clientId
         │
         └─ sendAuthCredentialsToBridge(socketPath, ...)
               └─ BridgeClient.sendAuthCredentials({
                    serverUrl, profileName, refreshToken, clientId
                  })
                     └─ IPC: set-auth-credentials message
                           └─ BridgeProcess.setAuthCredentials()
                                ├─ new OAuthTokenManager({ refreshToken, clientId, ... })
                                │     ├─ onBeforeRefresh: readKeychainOAuthTokenInfo()
                                │     └─ onTokenRefresh: storeKeychainOAuthTokenInfo()
                                └─ new OAuthProvider(tokenManager)
                                      └─ passed to createMcpClient() as authProvider
```

For header-only auth (no OAuth), the flow is the same except `refreshToken`/`clientId` are absent and `credentials.headers` carries the raw key-value pairs. The bridge stores them in `this.headers` and injects them into each HTTP request.

The `--profile dummy` sentinel is used when only headers are provided: it causes the bridge to wait for the `set-auth-credentials` IPC message before proceeding, without attempting to look up a real OAuth profile.

---

## Debugging bridge issues

### Log files

Each bridge writes to a rotating log at:

```
~/.mcpc/logs/bridge-<session>.log
```

Maximum size: 10 MB per file, 5 files retained. Enable verbose output by passing `--verbose` at connect time or setting `MCPC_VERBOSE=1`.

### Socket files

Active bridge sockets are at:

```
~/.mcpc/bridges/<session>.sock   # Unix
\\.\pipe\mcpc-<session>          # Windows
```

If a socket file exists but the PID in `sessions.json` is not alive, the bridge has crashed. The next CLI command will trigger automatic restart via `ensureBridgeReady()`.

### PID checking

```bash
# Check if bridge process is alive
ps -p $(cat ~/.mcpc/sessions.json | jq -r '.["<session>"].pid')

# Force-restart a session's bridge
mcpc <session> restart
```

### Manual health probe

```bash
# One-shot health check via getServerDetails (blocks until MCP ready or error)
mcpc @<session> ping
```

### Common failure patterns

| Symptom | Likely cause | Fix |
|---|---|---|
| `socket file not created within timeout` | Bridge crashed at startup (bad config, bad executable path) | Check log file for stack trace |
| `Session expired` | MCP server returned 404 for the session ID | `mcpc <session> restart` |
| `unauthorized` status | 401/403 from server or token refresh failed | `mcpc login <server>` then `mcpc <session> restart` |
| `Connection to bridge timed out` | Bridge alive but not accepting connections (overloaded or deadlocked) | Kill PID manually, then retry |
| Keepalive stale > 2 min | Network partition between bridge and MCP server | Bridge will auto-reconnect; use `mcpc @<session>` to check `lastSeenAt` |
