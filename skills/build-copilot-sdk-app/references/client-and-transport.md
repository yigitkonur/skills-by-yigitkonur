# Client and Transport

## CopilotClient constructor

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient(options?: CopilotClientOptions);
```

### CopilotClientOptions

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `cliPath` | `string` | bundled CLI | Path to CLI executable |
| `cliArgs` | `string[]` | `[]` | Extra CLI arguments (inserted before SDK-managed args) |
| `cwd` | `string` | `process.cwd()` | Working directory for CLI process |
| `port` | `number` | `0` (random) | TCP port (TCP mode only) |
| `useStdio` | `boolean` | `true` | Use stdio transport (default) |
| `isChildProcess` | `boolean` | `false` | SDK runs as child of Copilot CLI |
| `cliUrl` | `string` | — | Connect to existing server (`"host:port"`, `"http://host:port"`, or `"port"`) |
| `logLevel` | `"none"\|"error"\|"warning"\|"info"\|"debug"\|"all"` | `"debug"` | CLI log level |
| `autoStart` | `boolean` | `true` | Auto-start CLI on first use |
| `autoRestart` | `boolean` | `true` | Auto-restart if CLI crashes |
| `env` | `Record<string, string\|undefined>` | `process.env` | Environment for CLI process |
| `githubToken` | `string` | — | GitHub token (passed as `COPILOT_SDK_AUTH_TOKEN` env var) |
| `useLoggedInUser` | `boolean` | `true` (`false` when `githubToken` set) | Use stored OAuth/gh-cli tokens |
| `onListModels` | `() => Promise<ModelInfo[]> \| ModelInfo[]` | — | Custom model listing (BYOK mode) |

### Mutual exclusion rules

- `cliUrl` cannot be used with `useStdio: true` or `cliPath`
- `isChildProcess` requires `useStdio` and cannot be used with `cliUrl`
- `githubToken` and `useLoggedInUser` cannot be used with `cliUrl`

## Transport modes

### 1. Stdio (default)

SDK spawns CLI as child process, communicates via stdin/stdout pipes.

```typescript
const client = new CopilotClient(); // useStdio: true is default
// or explicitly:
const client = new CopilotClient({ useStdio: true });
```

CLI spawn args: `--headless --no-auto-update --log-level <level> --stdio`

Best for: local development, single-process apps, desktop apps.

### 2. TCP

SDK spawns CLI with `--port`, connects via `net.Socket`.

```typescript
const client = new CopilotClient({ useStdio: false, port: 4321 });
// port: 0 for random available port
```

CLI spawn args: `--headless --no-auto-update --log-level <level> --port <n>`

Best for: multi-client architectures where multiple SDK instances connect to one CLI.

### 3. External server

SDK connects to a pre-existing CLI server via TCP. No process spawning.

```typescript
const client = new CopilotClient({ cliUrl: "localhost:4321" });
// Also accepts: "4321", "http://localhost:4321", "https://host:port"
```

Start CLI separately:
```bash
copilot --headless --port 4321
```

Best for: backend services, Docker deployments, scaling patterns.

### 4. Child process mode

SDK is itself a child of the Copilot CLI. Used by CLI extensions (.mjs).

```typescript
// Do not use directly. Use joinSession from extension module instead:
import { joinSession } from "@github/copilot-sdk/extension";
const session = await joinSession({ onPermissionRequest: approveAll });
```

## Lifecycle methods

### start()

```typescript
await client.start();
```

Lifecycle: `disconnected → connecting → connected`

1. Spawns CLI process (unless external server)
2. Connects transport (stdio or TCP)
3. Protocol negotiation: pings server, verifies `2 ≤ protocolVersion ≤ 3`
4. Timeout: 10 seconds

Usually not needed — `autoStart: true` starts on first `createSession()`.

### stop()

```typescript
const errors: Error[] = await client.stop();
```

Graceful shutdown:
1. Disconnects all sessions (3 retries with exponential backoff)
2. Disposes connection
3. Kills CLI process
4. Returns collected errors

### forceStop()

```typescript
await client.forceStop();
```

Immediate: SIGKILL, no cleanup, errors ignored.

### getState()

```typescript
const state: ConnectionState = client.getState();
// "disconnected" | "connecting" | "connected" | "error"
```

### ping()

```typescript
const result = await client.ping("hello");
// { message: "pong: hello", timestamp: "...", protocolVersion: 3 }
```

### getStatus()

```typescript
const status: GetStatusResponse = await client.getStatus();
// { version: "1.0.0", protocolVersion: 3 }
```

### getAuthStatus()

```typescript
const auth: GetAuthStatusResponse = await client.getAuthStatus();
// { isAuthenticated: true, authType: "user", host: "github.com", login: "username" }
```

### listModels()

```typescript
const models: ModelInfo[] = await client.listModels();
// Cached after first call. Cleared on stop().
// When onListModels was provided: calls that instead.
```

## Session management on client

```typescript
// List persisted sessions
const sessions: SessionMetadata[] = await client.listSessions(filter?);

// Delete a persisted session
await client.deleteSession("session-id");

// Get last session ID
const lastId: string | undefined = await client.getLastSessionId();

// TUI+server mode only:
const fgId = await client.getForegroundSessionId();
await client.setForegroundSessionId("session-id");
```

### SessionListFilter

```typescript
interface SessionListFilter {
  cwd?: string;
  gitRoot?: string;
  repository?: string; // "owner/repo"
  branch?: string;
}
```

## Client lifecycle events

Subscribe to session lifecycle events (not session content events):

```typescript
// Typed
const unsub = client.on("session.created", (event) => {
  console.log("New session:", event.sessionId);
});

// Wildcard
client.on((event) => {
  // event.type: "session.created" | "session.deleted" | "session.updated"
  //           | "session.foreground" | "session.background"
});
```

## Protocol version negotiation

- SDK protocol version: **3** (current)
- Minimum server version accepted: **2**
- v2 servers: tool calls/permission requests arrive as JSON-RPC requests; SDK adapts them to v3 handlers transparently
- v3 servers: tool calls/permission requests arrive as broadcast session events

## Docker deployment

```bash
docker run -d --name copilot-cli -p 4321:4321 \
  -e COPILOT_GITHUB_TOKEN="$TOKEN" \
  ghcr.io/github/copilot-cli:latest --headless --port 4321
```

```typescript
const client = new CopilotClient({
  cliUrl: process.env.CLI_URL || "localhost:4321",
});
```

## Graceful shutdown pattern

```typescript
process.on("SIGINT", async () => {
  const errors = await client.stop();
  if (errors.length > 0) console.error("Cleanup errors:", errors);
  process.exit(0);
});

// With force-stop fallback:
const stopPromise = client.stop();
const timeout = new Promise((_, reject) =>
  setTimeout(() => reject(new Error("Timeout")), 5000)
);
try {
  await Promise.race([stopPromise, timeout]);
} catch {
  await client.forceStop();
}
```

## Steering notes

> Common mistakes agents make with the client and transport.

- **`useStdio: true` is the default and simplest option**. It spawns the Copilot CLI as a child process. Use this for CLIs, scripts, and local tools.
- **`cliUrl` and `useStdio` are mutually exclusive**. Setting both causes a runtime error. Use `cliUrl` only when connecting to an already-running Copilot CLI server.
- **Always call `client.stop()`** when your application exits. Without this, the child process (if using stdio) stays alive as an orphan. In streaming apps, call `session.disconnect()` first, then `client.stop()`.
- **`client.start()` is called implicitly** by `createSession` if the client hasn't started yet. You don't need to call it manually.
- **Protocol version negotiation** happens automatically. The SDK negotiates with the CLI and will throw if the CLI version is too old. Keep the Copilot CLI updated.
- **For Docker**: Use `cliPath` to specify the CLI binary location. The SDK won't auto-detect it inside containers.
- **Graceful shutdown pattern**: Listen for `SIGINT`/`SIGTERM`, call `session.disconnect()` then `client.stop()`. The SDK handles in-flight RPC cleanup.
