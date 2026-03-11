# CopilotClient: Transport Modes

## Transport Selection Overview

The SDK supports three transport configurations, selected by constructor options:

| Mode | Option | Subprocess? | Network? | Use When |
|------|--------|-------------|----------|----------|
| stdio (default) | `useStdio: true` | Yes (spawned) | No | Local dev, desktop apps, single-user |
| TCP (local spawn) | `useStdio: false`, no `cliUrl` | Yes (spawned) | Localhost | Rare; testing TCP path locally |
| TCP (external) | `cliUrl: "host:port"` | No | Yes | Backend services, multi-client, containers |
| Child process | `isChildProcess: true` | No | No (stdio) | SDK embedded as plugin inside CLI |

## stdio Mode (Default)

The SDK spawns the CLI as a child process and communicates over stdin/stdout pipes using JSON-RPC (vscode-jsonrpc protocol).

Activation:

```typescript
const client = new CopilotClient();
// or explicitly:
const client = new CopilotClient({ useStdio: true });
```

Internal CLI args added automatically:
```
--headless --no-auto-update --log-level debug --stdio
```

Connection flow:
1. SDK calls `spawn(cliPath, [...cliArgs, "--headless", "--no-auto-update", "--log-level", logLevel, "--stdio"])`
2. stdio config: `["pipe", "pipe", "pipe"]` (stdin/stdout/stderr all piped)
3. SDK immediately connects JSON-RPC over `cliProcess.stdout` (reader) and `cliProcess.stdin` (writer)
4. Resolves without waiting for any port announcement (unlike TCP mode)

When to use stdio:
- Personal projects and local development
- Desktop applications (Electron, Tauri) where CLI binary is bundled
- CLI tools shipped to users
- Any single-user scenario where process isolation matters

Never mix stdio mode with `cliUrl`. The constructor throws immediately if both are specified.

CLI stderr in stdio mode:
- Captured in `stderrBuffer` (internal)
- Forwarded to `process.stderr` with `[CLI subprocess]` prefix for visibility
- Included in error messages when CLI crashes

## TCP Mode: Local Spawn

Use when you need a TCP socket to the CLI instead of stdio, while still spawning the CLI as a child process:

```typescript
const client = new CopilotClient({
  useStdio: false,
  port: 4321,   // 0 = random available port
});
```

Internal CLI args added automatically:
```
--headless --no-auto-update --log-level debug --port 4321
```

Connection flow:
1. SDK spawns CLI with stdio config `["ignore", "pipe", "pipe"]` (stdin ignored, stdout/stderr piped)
2. SDK waits for stdout line matching `/listening on port (\d+)/i` to determine actual port
3. Timeout: 10 seconds waiting for port announcement — throws `"Timeout waiting for CLI server to start"`
4. SDK opens `net.Socket` and connects to `localhost:actualPort`
5. JSON-RPC connection established over the TCP socket

This mode is rarely needed in production. Use stdio for local spawn or `cliUrl` for external server.

## TCP Mode: External Server

Connect to a pre-running CLI server without spawning any subprocess:

```typescript
const client = new CopilotClient({
  cliUrl: "localhost:4321",
});
```

cliUrl format parsing:
- `"4321"` → connects to `localhost:4321`
- `"localhost:4321"` → connects to `localhost:4321`
- `"http://127.0.0.1:4321"` → connects to `127.0.0.1:4321`
- `"https://cli-server.internal:4321"` → connects to `cli-server.internal:4321`
- Port must be 1–65535. Invalid port throws synchronously in constructor.

No subprocess is spawned. Auth options (`githubToken`, `useLoggedInUser`) are forbidden — the external CLI server manages its own auth.

Start the CLI server externally (headless mode):

```bash
# Fixed port
copilot --headless --port 4321

# Random port (prints URL to stdout)
copilot --headless
# Output: Listening on http://localhost:52431
```

Docker deployment:

```bash
docker run -d --name copilot-cli \
  -p 4321:4321 \
  -e COPILOT_GITHUB_TOKEN="$TOKEN" \
  ghcr.io/github/copilot-cli:latest \
  --headless --port 4321
```

Multiple SDK clients can share one external CLI server:

```typescript
// All three clients connect to the same CLI server
const client1 = new CopilotClient({ cliUrl: "localhost:4321" });
const client2 = new CopilotClient({ cliUrl: "localhost:4321" });
const client3 = new CopilotClient({ cliUrl: "localhost:4321" });
```

Session isolation across clients is enforced by unique session IDs — the CLI server routes events by session ID.

## Child Process Mode (`isChildProcess`)

Use when your Node.js code is spawned by the CLI itself and communicates via the parent process's stdio:

```typescript
const client = new CopilotClient({
  isChildProcess: true,
  useStdio: true,  // Required
});
```

In this mode:
- No CLI subprocess is spawned
- JSON-RPC connection uses `process.stdin` (reader) and `process.stdout` (writer)
- `isExternalServer` is set internally (no lifecycle management of parent)
- The parent CLI process owns the connection; your code is the "client" side

## Bundled CLI vs Local CLI vs External Server

### Bundled CLI (recommended for distribution)

Explicitly set `cliPath` to a binary you ship with your application:

```typescript
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

const client = new CopilotClient({
  cliPath: join(__dirname, "../vendor/copilot"),
  useStdio: true,
});
```

Benefits: controlled CLI version, no dependency on user's system PATH.

### Local CLI (dev/prototyping)

Omit `cliPath` — SDK auto-resolves bundled CLI from `@github/copilot` npm package:

```typescript
const client = new CopilotClient();  // Uses @github/copilot bundled binary
```

Requires `@github/copilot` to be installed as a dependency.

### External Server (backend services, scaling)

Start CLI independently and connect via `cliUrl`:

```typescript
const client = new CopilotClient({ cliUrl: "localhost:4321" });
```

Benefits: CLI process lifecycle is independent from your app, multiple app instances share one CLI.

## Multi-Client Transport Considerations

When multiple `CopilotClient` instances connect to the same external CLI server (via `cliUrl`):

- Each client maintains its own TCP socket connection
- JSON-RPC messages are multiplexed per connection, not globally
- Protocol v3 servers use broadcast events (`external_tool.requested`, `permission.requested`) scoped by `sessionId`
- Protocol v2 servers use request/response RPC (`tool.call`, `permission.request`) — client registers handlers at connection setup
- Both protocol versions are supported simultaneously — the SDK registers v2 handlers at startup and a v3 server simply never sends v2-style requests
- Session IDs must be globally unique across all clients when sharing one CLI server

Protocol version negotiation happens at `start()` via `ping()` response:

```typescript
// Throws if server version is outside [MIN=2, MAX=sdkProtocolVersion]:
// "SDK protocol version mismatch: SDK supports versions 2-N, but server reports version M"
await client.start();
```

## Backend Service Architecture

Long-running server pattern (CLI as persistent sidecar):

```
[Your API Server]  ──TCP──▶  [Copilot CLI --headless --port 4321]
     │                              │
     │ (multiple requests)          │ (manages sessions on disk)
     │                              │
[CopilotClient]                [~/.copilot/session-state/]
```

Shared client for Express:

```typescript
import express from "express";
import { CopilotClient, approveAll } from "@github/copilot-sdk";

const client = new CopilotClient({
  cliUrl: process.env.CLI_URL ?? "localhost:4321",
});

// Single client shared across all requests
// autoStart: true means first createSession() triggers start()

const app = express();
app.use(express.json());

app.post("/api/chat", async (req, res) => {
  const session = await client.createSession({
    sessionId: `user-${req.body.userId}`,
    model: "gpt-4.1",
    onPermissionRequest: approveAll,
  });

  const response = await session.sendAndWait({ prompt: req.body.message });
  await session.disconnect();

  res.json({ content: response?.data.content });
});
```

Per-user isolated CLI pattern (stronger isolation, higher resource cost):

```typescript
class CLIPool {
  private instances = new Map<string, CopilotClient>();

  async getClient(userId: string): Promise<CopilotClient> {
    if (this.instances.has(userId)) {
      return this.instances.get(userId)!;
    }
    // Each user gets their own CLI server process
    const client = new CopilotClient({ useStdio: true });
    this.instances.set(userId, client);
    return client;
  }

  async releaseClient(userId: string): Promise<void> {
    const client = this.instances.get(userId);
    if (client) {
      await client.stop();
      this.instances.delete(userId);
    }
  }
}
```

## Connection State Management

The client tracks connection state internally:

```typescript
type ConnectionState = "disconnected" | "connecting" | "connected" | "error";

client.getState(); // Returns current ConnectionState
```

State transitions:
- `disconnected` → `connecting` → `connected`: normal startup
- `connected` → `disconnected` → `connected`: autoRestart after crash
- `connecting` → `error`: startup failure (network refused, CLI binary not found, protocol mismatch)

Check state before conditional operations:

```typescript
if (client.getState() !== "connected") {
  await client.start();
}
```

## Reconnection

When `autoRestart: true` (default), reconnection is triggered automatically on:
- CLI process `exit` event (after successful startup)
- JSON-RPC connection `close` event

Reconnection logic (`private async reconnect()`):
1. Sets `state = "disconnected"`
2. Calls `stop()` (cleans up existing sessions, connection, process)
3. Calls `start()` again (re-spawns CLI if needed, reconnects)
4. Errors during reconnect are silently swallowed — no retry backoff, single attempt

For external servers (`cliUrl`), reconnection only re-establishes the TCP connection (no process management).

Disable autoRestart to get explicit error propagation:

```typescript
const client = new CopilotClient({
  autoRestart: false,
  cliUrl: "localhost:4321",
});

// Connection loss will NOT trigger reconnect
// Your code must handle errors and call start() manually
client.on("session.deleted", (event) => {
  console.error("Session lost:", event.sessionId);
});
```

## Docker Compose Example

```yaml
services:
  copilot-cli:
    image: ghcr.io/github/copilot-cli:latest
    command: ["--headless", "--port", "4321"]
    environment:
      - COPILOT_GITHUB_TOKEN=${COPILOT_GITHUB_TOKEN}
    ports:
      - "4321:4321"
    restart: always
    volumes:
      - session-data:/root/.copilot/session-state

  api:
    build: .
    environment:
      - CLI_URL=copilot-cli:4321
    depends_on:
      - copilot-cli

volumes:
  session-data:
```

```typescript
// In your API container
const client = new CopilotClient({
  cliUrl: process.env.CLI_URL!,  // "copilot-cli:4321"
});
```
