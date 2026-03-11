# Scaling Patterns

## Three Isolation Patterns

Choose your isolation model first — it determines your entire scaling topology.

| Pattern | Isolation | Resource Use | Best For |
|---|---|---|---|
| CLI per user | Complete | High | Multi-tenant SaaS, compliance |
| Shared CLI + session isolation | Logical | Low | Internal tools, trusted users |
| Shared sessions | None | Lowest | Collaboration tools, team workflows |

## Pattern 1: Isolated CLI Per User

Each user gets a dedicated CLI instance. Strongest isolation — a user's sessions, memory, and subprocess state are completely separated.

```typescript
import { CopilotClient } from "@github/copilot-sdk";

class CLIPool {
  private instances = new Map<string, { client: CopilotClient; port: number }>();
  private nextPort = 5000;

  async getClientForUser(userId: string, token?: string): Promise<CopilotClient> {
    if (this.instances.has(userId)) {
      return this.instances.get(userId)!.client;
    }

    const port = this.nextPort++;

    // Spawn a dedicated CLI instance for this user
    await spawnCLI(port, token);

    const client = new CopilotClient({
      cliUrl: `localhost:${port}`,
      ...(token && { githubToken: token }),
    });

    this.instances.set(userId, { client, port });
    return client;
  }

  async releaseUser(userId: string): Promise<void> {
    const instance = this.instances.get(userId);
    if (instance) {
      await instance.client.stop();
      this.instances.delete(userId);
    }
  }
}
```

Use this pattern for multi-tenant SaaS where data isolation is a compliance requirement, or when users have different auth credentials.

## Pattern 2: Shared CLI with Session Isolation

Multiple users share one CLI server but have isolated sessions via unique session IDs.

```typescript
const sharedClient = new CopilotClient({
  cliUrl: process.env.CLI_URL || "localhost:4321",
});

// Enforce isolation through naming conventions
function getSessionId(userId: string, purpose: string): string {
  return `${userId}-${purpose}`;
}

// Access control: ensure users can only access their own sessions
async function resumeSessionWithAuth(
  sessionId: string,
  currentUserId: string
): Promise<CopilotSession> {
  const [sessionUserId] = sessionId.split("-");
  if (sessionUserId !== currentUserId) {
    throw new Error("Access denied: session belongs to another user");
  }
  return sharedClient.resumeSession(sessionId);
}
```

## Pattern 3: Shared Sessions (Collaborative)

Multiple users interact with the same session. Requires application-level locking — the SDK provides no built-in session locking.

```typescript
import Redis from "ioredis";

const redis = new Redis();

async function withSessionLock<T>(
  sessionId: string,
  fn: () => Promise<T>,
  timeoutSec = 300
): Promise<T> {
  const lockKey = `session-lock:${sessionId}`;
  const lockId = crypto.randomUUID();

  const acquired = await redis.set(lockKey, lockId, "NX", "EX", timeoutSec);
  if (!acquired) {
    throw new Error("Session is in use by another user");
  }

  try {
    return await fn();
  } finally {
    const currentLock = await redis.get(lockKey);
    if (currentLock === lockId) {
      await redis.del(lockKey);
    }
  }
}

app.post("/team-chat", authMiddleware, async (req, res) => {
  const result = await withSessionLock("team-project-review", async () => {
    const session = await client.resumeSession("team-project-review");
    return session.sendAndWait({ prompt: req.body.message });
  });
  res.json({ content: result?.data.content });
});
```

## Horizontal Scaling: Multiple CLI Instances

Run multiple CLI servers behind a load balancer. Session state must be on shared storage for any-to-any routing.

**Key requirement:** `~/.copilot/session-state/` must be on a shared filesystem (NFS, cloud storage) when using round-robin routing. With sticky sessions, local storage is sufficient.

### Load Balancer Implementation

```typescript
class CLILoadBalancer {
  private servers: string[];
  private currentIndex = 0;

  constructor(servers: string[]) {
    this.servers = servers;
  }

  // Round-robin for even distribution
  getNextServer(): string {
    const server = this.servers[this.currentIndex];
    this.currentIndex = (this.currentIndex + 1) % this.servers.length;
    return server;
  }

  // Sticky sessions: same user always hits same server (no shared storage needed)
  getServerForUser(userId: string): string {
    const hash = userId.split("").reduce((acc, char) => {
      return ((acc << 5) - acc + char.charCodeAt(0)) | 0;
    }, 0);
    return this.servers[Math.abs(hash) % this.servers.length];
  }
}

const lb = new CLILoadBalancer([
  "cli-1:4321",
  "cli-2:4321",
  "cli-3:4321",
]);

app.post("/chat", async (req, res) => {
  // Sticky: user always routes to same CLI instance
  const server = lb.getServerForUser(req.user.id);
  const client = new CopilotClient({ cliUrl: server });

  const session = await client.createSession({
    sessionId: `user-${req.user.id}-chat`,
    model: "gpt-4.1",
  });

  const response = await session.sendAndWait({ prompt: req.body.message });
  res.json({ content: response?.data.content });
});
```

## Concurrency Management: Session Manager

Limit active in-memory sessions to prevent memory exhaustion. The CLI persists session state to disk automatically; evicting from the in-memory pool is safe.

```typescript
class SessionManager {
  private activeSessions = new Map<string, CopilotSession>();
  private maxConcurrent: number;

  constructor(
    private client: CopilotClient,
    maxConcurrent = 50
  ) {
    this.maxConcurrent = maxConcurrent;
  }

  async get(sessionId: string): Promise<CopilotSession> {
    if (this.activeSessions.has(sessionId)) {
      return this.activeSessions.get(sessionId)!;
    }

    if (this.activeSessions.size >= this.maxConcurrent) {
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

    this.activeSessions.set(sessionId, session);
    return session;
  }

  private async evictOldest(): Promise<void> {
    const [oldestId] = this.activeSessions.keys();
    const session = this.activeSessions.get(oldestId)!;
    // disconnect() is safe: state is persisted to disk
    await session.disconnect();
    this.activeSessions.delete(oldestId);
  }
}
```

## Memory Management

- Each active session holds conversation history, tool state, and event listeners in memory
- Evict idle sessions aggressively — `session.disconnect()` preserves state to disk while freeing memory
- Set a TTL-based cleanup to remove sessions older than your user activity window
- The CLI auto-cleans sessions after 30 minutes of inactivity

```typescript
async function cleanupSessions(client: CopilotClient, maxAgeMs: number): Promise<void> {
  const sessions = await client.listSessions();
  const now = Date.now();
  const stale = sessions.filter(s => now - s.modifiedTime.getTime() > maxAgeMs);
  await Promise.all(stale.map(s => client.deleteSession(s.sessionId)));
  console.log(`Cleaned up ${stale.length} stale sessions`);
}

// Run every hour, TTL = 24 hours
setInterval(() => cleanupSessions(client, 24 * 60 * 60 * 1000), 60 * 60 * 1000);
```

## Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: copilot-cli
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: copilot-cli
          image: ghcr.io/github/copilot-cli:latest
          args: ["--headless", "--port", "4321"]
          env:
            - name: COPILOT_GITHUB_TOKEN
              valueFrom:
                secretKeyRef:
                  name: copilot-secrets
                  key: github-token
          ports:
            - containerPort: 4321
          volumeMounts:
            - name: session-state
              mountPath: /root/.copilot/session-state
      volumes:
        - name: session-state
          persistentVolumeClaim:
            claimName: copilot-sessions-pvc
```

For multi-replica CLI deployments with round-robin routing, `copilot-sessions-pvc` must be a `ReadWriteMany` volume (NFS, Azure Files, EFS) so all pods share session state.

## Metrics and Monitoring

Track these signals for scaling decisions:

```typescript
class Metrics {
  activeSessions = 0;
  totalRequestsServed = 0;
  requestLatencies: number[] = [];
  errors = 0;

  recordRequest(durationMs: number): void {
    this.totalRequestsServed++;
    this.requestLatencies.push(durationMs);
    if (this.requestLatencies.length > 1000) {
      this.requestLatencies.shift();
    }
  }

  p99LatencyMs(): number {
    const sorted = [...this.requestLatencies].sort((a, b) => a - b);
    return sorted[Math.floor(sorted.length * 0.99)] ?? 0;
  }

  toJSON() {
    return {
      activeSessions: this.activeSessions,
      totalRequests: this.totalRequestsServed,
      p99LatencyMs: this.p99LatencyMs(),
      errorRate: this.errors / Math.max(this.totalRequestsServed, 1),
    };
  }
}

app.get("/metrics", (req, res) => res.json(metrics.toJSON()));
```

## Auto-Scaling Triggers

| Metric | Scale Up Trigger | Scale Down Trigger |
|---|---|---|
| Active sessions per CLI | > 40 sessions | < 10 sessions for 10+ min |
| P99 request latency | > 30 seconds | < 5 seconds sustained |
| Session queue depth | > 20 pending | < 5 pending |
| CLI memory usage | > 80% of limit | N/A |

## Production Checklist

- [ ] Session cleanup cron running (removes sessions older than TTL)
- [ ] Health check endpoint with CLI ping (`client.getStatus()`)
- [ ] Persistent volume mounted for session state (`~/.copilot/session-state/`)
- [ ] Secrets managed via platform secret manager (not env vars in manifests)
- [ ] Session locking implemented if using shared sessions (Redis recommended)
- [ ] Graceful shutdown drains active sessions before SIGTERM completes
- [ ] Active session count and P99 latency in your monitoring dashboard

## Limitations

| Limitation | Impact |
|---|---|
| No built-in session locking | Must implement in application layer |
| No built-in load balancing | Requires external LB or service mesh |
| Session state is file-based | Requires shared filesystem for multi-server |
| 30-min idle timeout | Sessions auto-cleaned — design TTLs accordingly |
| CLI is single-process | Scale by adding instances, not threads |
