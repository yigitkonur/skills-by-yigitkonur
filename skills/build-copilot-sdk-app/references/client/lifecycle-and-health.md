# CopilotClient: Lifecycle and Health

## Method Signatures

```typescript
class CopilotClient {
  // Startup
  async start(): Promise<void>

  // Graceful shutdown — returns errors encountered, never throws
  async stop(): Promise<Error[]>

  // Forceful shutdown — never throws
  async forceStop(): Promise<void>

  // State inspection
  getState(): ConnectionState  // "disconnected" | "connecting" | "connected" | "error"

  // Health probe
  async ping(message?: string): Promise<{ message: string; timestamp: number; protocolVersion?: number }>

  // Server status
  async getStatus(): Promise<GetStatusResponse>
  async getAuthStatus(): Promise<GetAuthStatusResponse>

  // Session management
  async createSession(config: SessionConfig): Promise<CopilotSession>
  async resumeSession(sessionId: string, config: ResumeSessionConfig): Promise<CopilotSession>
  async deleteSession(sessionId: string): Promise<void>
  async listSessions(filter?: SessionListFilter): Promise<SessionMetadata[]>
  async getLastSessionId(): Promise<string | undefined>

  // Lifecycle event subscription
  on(eventType: SessionLifecycleEventType, handler: TypedSessionLifecycleHandler): () => void
  on(handler: SessionLifecycleHandler): () => void
}
```

## `start()`

Establishes connection to CLI. Idempotent when already connected (returns immediately).

What it does:
1. Sets `state = "connecting"`
2. If not external server: calls `startCLIServer()` — spawns subprocess
3. Calls `connectToServer()` — creates JSON-RPC MessageConnection
4. Calls `verifyProtocolVersion()` — sends `ping` RPC, validates protocol version is in range `[2, MAX]`
5. Sets `state = "connected"`
6. On any failure: sets `state = "error"`, re-throws

```typescript
const client = new CopilotClient({ autoStart: false });

try {
  await client.start();
  console.log("Connected, state:", client.getState()); // "connected"
} catch (err) {
  console.error("Startup failed:", err.message);
  // Possible errors:
  // "Copilot CLI not found at /path/to/cli"
  // "Timeout waiting for CLI server to start"
  // "Failed to connect to CLI server: ECONNREFUSED"
  // "SDK protocol version mismatch: SDK supports versions 2-N, but server reports version M"
  // "CLI server exited with code 1\nstderr: ..."
}
```

`start()` is called automatically by `createSession()` and `resumeSession()` when `autoStart: true` (default).

## `stop()`

Graceful shutdown with up to 3 retry attempts per session disconnect.

Shutdown sequence:
1. For each active session: calls `session.disconnect()` with exponential backoff (100ms, 200ms between retries)
2. Clears `sessions` map
3. Disposes JSON-RPC connection (`connection.dispose()`)
4. Closes TCP socket via `socket.end()` (graceful half-close)
5. Kills CLI subprocess via `cliProcess.kill()` (SIGTERM on Unix)
6. Sets `state = "disconnected"`, resets internal state

Session data on disk is preserved — sessions can be resumed later. To permanently delete session data, call `deleteSession()` before `stop()`.

```typescript
const errors = await client.stop();

if (errors.length > 0) {
  for (const err of errors) {
    console.error("Cleanup error:", err.message);
    // "Failed to disconnect session abc-123 after 3 attempts: ..."
    // "Failed to dispose connection: ..."
    // "Failed to close socket: ..."
    // "Failed to kill CLI process: ..."
  }
}
// errors.length === 0 means clean shutdown
```

`stop()` does NOT kill the CLI when `cliUrl` is set (external server) — only the TCP connection is closed.

## `forceStop()`

Immediate teardown, no cleanup attempts. Use when `stop()` hangs or times out.

Force shutdown sequence:
1. Sets `forceStopping = true`
2. Clears `sessions` map immediately (no disconnect calls)
3. Disposes connection (ignores errors)
4. Destroys TCP socket via `socket.destroy()` (hard close, no FIN)
5. Sends SIGKILL to CLI process (`cliProcess.kill("SIGKILL")`)
6. Sets `state = "disconnected"`

```typescript
// Pattern: try graceful, fall back to force
const STOP_TIMEOUT_MS = 5000;

try {
  await Promise.race([
    client.stop(),
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error("stop() timed out")), STOP_TIMEOUT_MS)
    ),
  ]);
} catch {
  console.warn("Graceful stop failed — forcing shutdown");
  await client.forceStop();
}
```

## Auto-Start Behavior

When `autoStart: true` (default), `createSession()` and `resumeSession()` call `start()` automatically if not connected:

```typescript
const client = new CopilotClient();
// state: "disconnected"

// This internally calls start() before creating the session
const session = await client.createSession({
  onPermissionRequest: approveAll,
  model: "gpt-4.1",
});
// state: "connected"
```

With `autoStart: false`, calling `createSession()` before `start()` throws:

```typescript
const client = new CopilotClient({ autoStart: false });

// Throws: "Client not connected. Call start() first."
const session = await client.createSession({ onPermissionRequest: approveAll });
```

## Health Check Mechanism

Use `ping()` to verify connectivity at any time:

```typescript
// Returns: { message: string, timestamp: number, protocolVersion?: number }
const response = await client.ping("health-check");
console.log(`Server alive at ${new Date(response.timestamp)}, protocol v${response.protocolVersion}`);
```

`ping()` throws `"Client not connected"` if not in `connected` state.

Use `getStatus()` for richer diagnostics (CLI version, protocol info):

```typescript
const status = await client.getStatus();  // Sends "status.get" RPC
```

Use `getAuthStatus()` to check current authentication:

```typescript
const auth = await client.getAuthStatus();  // Sends "auth.getStatus" RPC
```

Implement a periodic health monitor:

```typescript
function startHealthMonitor(client: CopilotClient, intervalMs = 30_000): NodeJS.Timer {
  return setInterval(async () => {
    try {
      if (client.getState() !== "connected") {
        console.warn("Client not connected, state:", client.getState());
        return;
      }
      await client.ping();
    } catch (err) {
      console.error("Health check failed:", err);
      // autoRestart: true will trigger reconnect automatically
      // autoRestart: false — handle reconnection manually here
    }
  }, intervalMs);
}

const timer = startHealthMonitor(client);
// On shutdown:
clearInterval(timer);
await client.stop();
```

## Process Management

CLI subprocess spawning details (stdio mode):

```typescript
// Internal: spawn with piped stdio
spawn(cliPath, ["--headless", "--no-auto-update", "--log-level", logLevel, "--stdio"], {
  stdio: ["pipe", "pipe", "pipe"],
  cwd: options.cwd,
  env: envWithoutNodeDebug,  // NODE_DEBUG stripped
  windowsHide: true,
});
```

For `.js` files (`cliPath.endsWith(".js")`), SDK spawns `node path/to/index.js` using `process.execPath` (or `"node"` under Bun).

stderr forwarding: All CLI stderr lines are printed to `process.stderr` with prefix `[CLI subprocess] `. Do not suppress `process.stderr` in your application — it's the only visibility into CLI errors.

Startup timeout: 10 seconds (hardcoded). If CLI does not signal ready within 10s, throws `"Timeout waiting for CLI server to start"`. No configurable override exists for this timeout.

Process exit tracking: An internal `processExitPromise` rejects when the CLI exits. This is raced against the `ping()` call during `verifyProtocolVersion()` to surface early crash errors quickly.

## Graceful Shutdown Patterns

### In a server process with signal handling:

```typescript
const client = new CopilotClient({ cliUrl: process.env.CLI_URL! });

async function shutdown(signal: string) {
  console.log(`Received ${signal}, shutting down`);

  const errors = await client.stop();
  if (errors.length > 0) {
    console.error("Shutdown errors:", errors.map(e => e.message));
  }

  process.exit(0);
}

process.on("SIGTERM", () => void shutdown("SIGTERM"));
process.on("SIGINT",  () => void shutdown("SIGINT"));
```

### In a long-lived application (desktop/CLI tool):

```typescript
const client = new CopilotClient();

// Register before any createSession calls
process.on("exit", () => {
  // Synchronous context — cannot await
  // forceStop is async but we fire and forget on exit
  void client.forceStop();
});

process.on("uncaughtException", async (err) => {
  console.error("Uncaught:", err);
  await client.forceStop();
  process.exit(1);
});
```

### With explicit session cleanup before stop:

```typescript
// Clean up old sessions before stopping to free disk space
const sessions = await client.listSessions();
const oneWeekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;

for (const s of sessions) {
  if (s.modifiedTime.getTime() < oneWeekAgo) {
    await client.deleteSession(s.sessionId);
  }
}

await client.stop();
```

## Error States and Recovery

State `"error"` is set when `start()` throws. From `"error"`, call `start()` again to retry:

```typescript
async function startWithRetry(client: CopilotClient, maxAttempts = 3): Promise<void> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      await client.start();
      return;
    } catch (err) {
      if (attempt === maxAttempts) throw err;
      console.warn(`Start attempt ${attempt} failed, retrying...`);
      await new Promise(r => setTimeout(r, 1000 * attempt));
    }
  }
}
```

`autoRestart: true` handles crash recovery after successful connection, but does NOT retry failed initial `start()` calls.

When `autoRestart: true` and CLI crashes post-connection:
1. `cliProcess.on("exit")` or `connection.onClose()` fires
2. Internal `reconnect()` calls `stop()` then `start()` in sequence
3. Active sessions in `sessions` map are lost — any pending `sendAndWait()` calls will error
4. No notification to callers that reconnect occurred

To detect reconnects, poll state or wrap calls defensively:

```typescript
async function sendWithReconnectGuard(
  client: CopilotClient,
  session: CopilotSession,
  prompt: string
) {
  try {
    return await session.sendAndWait({ prompt });
  } catch (err) {
    if (client.getState() === "disconnected") {
      // Session lost due to reconnect — recreate
      const newSession = await client.createSession({
        sessionId: session.sessionId,
        model: "gpt-4.1",
        onPermissionRequest: approveAll,
      });
      return await newSession.sendAndWait({ prompt });
    }
    throw err;
  }
}
```

## Multiple Client Instances

Multiple `CopilotClient` instances can coexist in the same process:

```typescript
// Scenario: different CLI servers for different users
const clientA = new CopilotClient({ cliUrl: "localhost:4321" });
const clientB = new CopilotClient({ cliUrl: "localhost:4322" });

// Or: different configs for same server
const readClient  = new CopilotClient({ cliUrl: "localhost:4321", logLevel: "none" });
const writeClient = new CopilotClient({ cliUrl: "localhost:4321", logLevel: "debug" });
```

Each instance maintains independent state: its own TCP socket or child process, its own sessions map, its own models cache, its own lifecycle handlers.

Stop all instances before process exit:

```typescript
async function stopAll(clients: CopilotClient[]): Promise<void> {
  await Promise.allSettled(clients.map(c => c.stop()));
}
```

## Session Lifecycle Events

Subscribe to server-emitted session lifecycle notifications:

```typescript
// Typed subscription (specific event type)
const unsubscribe = client.on("session.created", (event) => {
  console.log("New session:", event.sessionId);
});

// Wildcard subscription (all event types)
const unsubscribeAll = client.on((event) => {
  switch (event.type) {
    case "session.created":   console.log("Created:", event.sessionId); break;
    case "session.deleted":   console.log("Deleted:", event.sessionId); break;
    case "session.updated":   console.log("Updated:", event.sessionId); break;
    case "session.foreground": console.log("Foreground:", event.sessionId); break;
    case "session.background": console.log("Background:", event.sessionId); break;
  }
});

// Returns unsubscribe function — always store and call on cleanup
process.on("SIGTERM", () => {
  unsubscribe();
  unsubscribeAll();
  void client.stop();
});
```

Handler errors are silently swallowed — the SDK wraps each handler call in `try/catch`. Do not rely on thrown errors propagating out of lifecycle handlers.

## `listSessions()` and `getLastSessionId()`

```typescript
// List all sessions (metadata only — not active connections)
const sessions = await client.listSessions();
// Returns: Array<{ sessionId, startTime: Date, modifiedTime: Date, summary?, isRemote, context? }>

// With filter
const filtered = await client.listSessions({ repository: "owner/repo" });

// Get most recently modified session ID
const lastId = await client.getLastSessionId();
if (lastId) {
  const session = await client.resumeSession(lastId, { onPermissionRequest: approveAll });
}
```

Both methods require connected state — throw `"Client not connected"` otherwise.

## Backend Session Cleanup Pattern

Run periodic cleanup to prevent session data accumulation on disk:

```typescript
const IDLE_TIMEOUT_MS = 24 * 60 * 60 * 1000; // 24 hours

async function cleanupStaleSessions(client: CopilotClient): Promise<void> {
  const sessions = await client.listSessions();
  const cutoff = Date.now() - IDLE_TIMEOUT_MS;

  const stale = sessions.filter(s => s.modifiedTime.getTime() < cutoff);

  await Promise.allSettled(
    stale.map(s => client.deleteSession(s.sessionId))
  );

  console.log(`Cleaned up ${stale.length} stale sessions`);
}

// Run hourly
setInterval(() => void cleanupStaleSessions(client), 60 * 60 * 1000);
```

The CLI has a built-in 30-minute idle timeout for sessions without activity — `deleteSession()` provides explicit control.

## TUI+Server Mode: Foreground Session Control

When the CLI runs in `--ui-server` mode (TUI + RPC server combined):

```typescript
// Get session currently displayed in TUI
const foregroundId = await client.getForegroundSessionId();

// Request TUI to switch to a specific session
await client.setForegroundSessionId("my-session-id");
```

These methods throw `"Client not connected"` if not connected, and `setForegroundSessionId` throws if the server rejects the request.
