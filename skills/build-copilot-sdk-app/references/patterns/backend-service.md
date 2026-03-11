# Backend Service Patterns

## Architecture Overview

Backend services run the CLI in headless server mode. Your app connects to it over TCP using `cliUrl`. The CLI runs as a persistent process — independent lifecycle from your app — and your SDK client connects to it on demand.

```
┌──────────────────────┐       TCP :4321      ┌──────────────────────┐
│   Your API Server    │ ──────────────────► │  Copilot CLI (headless)│
│   (SDK Client)       │                      │  Session Manager       │
└──────────────────────┘                      └──────────────────────┘
                                                         │
                                               ☁ GitHub Copilot API
```

Key difference from default mode: default spawns CLI as child process (dies with app); headless mode runs CLI independently (survives app restarts, shared across instances).

## Starting the CLI in Headless Mode

```bash
# Production: specific port
copilot --headless --port 4321

# Docker
docker run -d --name copilot-cli \
  -p 4321:4321 \
  -e COPILOT_GITHUB_TOKEN="$TOKEN" \
  ghcr.io/github/copilot-cli:latest \
  --headless --port 4321
```

## Connecting the SDK

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient({
  cliUrl: process.env.CLI_URL || "localhost:4321",
});

// Create session with explicit sessionId for tracking
const session = await client.createSession({
  sessionId: `user-${userId}-${Date.now()}`,
  model: "gpt-4.1",
  onPermissionRequest: async () => ({ kind: "approved" }),
});

const response = await session.sendAndWait({ prompt: message });
```

## Express API Integration

```typescript
import express from "express";
import { CopilotClient } from "@github/copilot-sdk";

const app = express();
app.use(express.json());

// Shared client — single connection to CLI for all requests
const client = new CopilotClient({
  cliUrl: process.env.CLI_URL || "localhost:4321",
});

app.post("/api/chat", async (req, res) => {
  const { sessionId, message } = req.body;

  // Create or resume session by sessionId
  let session;
  try {
    session = await client.resumeSession(sessionId);
  } catch {
    session = await client.createSession({
      sessionId,
      model: "gpt-4.1",
      onPermissionRequest: async () => ({ kind: "approved" }),
    });
  }

  const response = await session.sendAndWait({ prompt: message });
  res.json({
    sessionId,
    content: response?.data.content,
  });
});

// Graceful shutdown
process.on("SIGTERM", async () => {
  console.log("Draining sessions...");
  await client.stop();
  process.exit(0);
});

app.listen(3000);
```

## Session Pool Management

Maintain an in-memory pool of active sessions. Limit concurrency. Evict idle sessions to free resources.

```typescript
class SessionPool {
  private pool = new Map<string, { session: CopilotSession; lastUsed: number }>();
  private maxSize: number;

  constructor(
    private client: CopilotClient,
    maxSize = 50
  ) {
    this.maxSize = maxSize;
    // Cleanup idle sessions every 5 minutes
    setInterval(() => this.evictIdle(30 * 60 * 1000), 5 * 60 * 1000);
  }

  async get(sessionId: string): Promise<CopilotSession> {
    const existing = this.pool.get(sessionId);
    if (existing) {
      existing.lastUsed = Date.now();
      return existing.session;
    }

    if (this.pool.size >= this.maxSize) {
      await this.evictOldest();
    }

    let session: CopilotSession;
    try {
      session = await this.client.resumeSession(sessionId);
    } catch {
      session = await this.client.createSession({
        sessionId,
        model: "gpt-4.1",
        onPermissionRequest: async () => ({ kind: "approved" }),
      });
    }

    this.pool.set(sessionId, { session, lastUsed: Date.now() });
    return session;
  }

  async release(sessionId: string): Promise<void> {
    const entry = this.pool.get(sessionId);
    if (entry) {
      await entry.session.disconnect();
      this.pool.delete(sessionId);
    }
  }

  private async evictOldest(): Promise<void> {
    let oldestKey: string | undefined;
    let oldestTime = Infinity;
    for (const [key, { lastUsed }] of this.pool) {
      if (lastUsed < oldestTime) {
        oldestTime = lastUsed;
        oldestKey = key;
      }
    }
    if (oldestKey) await this.release(oldestKey);
  }

  private async evictIdle(maxAgeMs: number): Promise<void> {
    const now = Date.now();
    const toEvict = [...this.pool.entries()]
      .filter(([, { lastUsed }]) => now - lastUsed > maxAgeMs)
      .map(([key]) => key);
    await Promise.all(toEvict.map(key => this.release(key)));
  }
}
```

## User-to-Session Mapping

Map users to sessions using deterministic session IDs. Include a purpose or context suffix to allow multiple concurrent sessions per user.

```typescript
function sessionIdFor(userId: string, purpose = "chat"): string {
  return `user-${userId}-${purpose}`;
}

// Different sessions for different purposes
const chatSession = await pool.get(sessionIdFor(req.user.id, "chat"));
const codeReviewSession = await pool.get(sessionIdFor(req.user.id, "review"));
```

## Health Monitoring and Auto-Recovery

```typescript
class CliHealthMonitor {
  private isHealthy = true;
  private reconnectAttempts = 0;
  private readonly maxAttempts = 5;

  constructor(private client: CopilotClient) {
    setInterval(() => this.check(), 30_000);
  }

  async check(): Promise<void> {
    try {
      await this.client.getStatus();
      this.isHealthy = true;
      this.reconnectAttempts = 0;
    } catch {
      this.isHealthy = false;
      await this.reconnect();
    }
  }

  private async reconnect(): Promise<void> {
    if (this.reconnectAttempts >= this.maxAttempts) {
      console.error("CLI server unreachable — max reconnect attempts exceeded");
      process.exit(1);
    }
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30_000);
    console.warn(`CLI unhealthy — reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    await new Promise(r => setTimeout(r, delay));
    try {
      await this.client.start();
      console.log("Reconnected to CLI server");
    } catch {
      // Will retry on next check interval
    }
  }

  get healthy(): boolean {
    return this.isHealthy;
  }
}
```

## Graceful Shutdown with Session Cleanup

```typescript
async function gracefulShutdown(pool: SessionPool, client: CopilotClient): Promise<void> {
  console.log("Shutdown: stopping new requests...");
  // Stop accepting new connections (framework-specific)

  console.log("Shutdown: cleaning up sessions...");
  await pool.drainAll();

  console.log("Shutdown: stopping CLI client...");
  await client.stop();

  process.exit(0);
}

process.on("SIGTERM", () => gracefulShutdown(pool, client));
process.on("SIGINT", () => gracefulShutdown(pool, client));
```

## Docker Compose Deployment

```yaml
version: "3.8"

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
    ports:
      - "3000:3000"
    restart: unless-stopped

volumes:
  session-data:
    # Persistent volume preserves sessions across container restarts
```

## Background Worker Pattern

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient({
  cliUrl: process.env.CLI_URL || "localhost:4321",
});

async function processJob(job: { id: string; prompt: string }): Promise<string> {
  const session = await client.createSession({
    sessionId: `job-${job.id}`,
    model: "gpt-4.1",
    onPermissionRequest: async () => ({ kind: "approved" }),
  });

  try {
    const response = await session.sendAndWait({ prompt: job.prompt }, 300_000);
    return response?.data.content ?? "";
  } finally {
    await session.disconnect(); // Preserve session state for audit
  }
}
```

## Per-User Token Authentication

```typescript
app.post("/chat", authMiddleware, async (req, res) => {
  // Create a client per request using the user's own token
  const client = new CopilotClient({
    cliUrl: process.env.CLI_URL,
    githubToken: req.user.githubToken,
    useLoggedInUser: false,
  });

  const session = await client.createSession({
    sessionId: `user-${req.user.id}-chat`,
    model: "gpt-4.1",
  });

  const response = await session.sendAndWait({ prompt: req.body.message });
  res.json({ content: response?.data.content });
});
```

## Limitations

| Limitation | Details |
|---|---|
| Session state is file-based | Mount persistent volumes for container deployments |
| 30-min idle timeout | Sessions without activity are auto-cleaned by CLI |
| No auth between SDK and CLI | Secure the network path — same host, VPC, or mTLS |
| Single CLI = single point of failure | See scaling.md for multi-CLI patterns |
