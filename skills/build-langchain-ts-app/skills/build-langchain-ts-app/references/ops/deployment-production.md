# Deployment: Production Infrastructure Reference

> Verified against @langchain/langgraph@1.2.5, @langchain/langgraph-sdk latest, @langchain/langgraph-cli latest.
> LangGraph Platform was rebranded to LangSmith Deployment in May 2025. "LangGraph Cloud" is now "LangSmith Cloud". SDK and `langgraph.json` are unchanged.

---

## Deployment Options — Choose One

| Strategy | Managed by | Infrastructure | Best for |
|----------|-----------|---------------|---------|
| **LangSmith Cloud** | LangChain (fully managed) | LangChain's cloud | Fastest path; ~15 min to live |
| **Hybrid** | LangSmith control plane + your cloud | User-hosted runtime + LangSmith control plane | Data stays in your cloud |
| **Self-hosted with control plane** | You on K8s | Full LangSmith on K8s | On-prem, max control + UI |
| **Standalone** | You (Docker/Compose) | Docker / Docker Compose / K8s | Minimal footprint, no platform UI |

---

## Docker Deployment

### Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `REDIS_URI` | Yes | Redis connection URI (pub/sub for streaming) |
| `DATABASE_URI` | Yes | PostgreSQL connection URI (stores state, threads, runs) |
| `LANGSMITH_API_KEY` | Yes | Authenticates the server with LangSmith |
| `LANGGRAPH_CLOUD_LICENSE_KEY` | Paid tiers | License key, used once at server start |
| `LS_DEFAULT_CHECKPOINTER_BACKEND` | No | `"mongo"` for MongoDB checkpointing |
| `LS_MONGODB_URI` | No | MongoDB URI when using MongoDB backend |
| `N_JOBS_PER_WORKER` | No | Max concurrent runs per worker (default: 10) |
| `LANGSMITH_TRACING` | No | Set `"false"` to disable tracing |
| `LANGSMITH_ENDPOINT` | No | Hostname of self-hosted LangSmith instance |
| `POSTGRES_URI_CUSTOM` | No | Override external PostgreSQL |
| `REDIS_URI_CUSTOM` | No | Override external Redis |

### Single Container

Build with `langgraph build`, set `IMAGE_NAME` in `.env`, then:

```bash
docker run \
  --env-file .env \
  -p 8123:8000 \
  -e REDIS_URI="redis://host:6379" \
  -e DATABASE_URI="postgresql://user:pass@host:5432/db" \
  -e LANGSMITH_API_KEY="lsv2_..." \
  my-image
```

### Docker Compose (Recommended for Self-Hosting)

```yaml
# docker-compose.yml
volumes:
  langgraph-data:
    driver: local

services:
  langgraph-redis:
    image: redis:6
    healthcheck:
      test: redis-cli ping
      interval: 5s
      timeout: 1s
      retries: 5

  langgraph-postgres:
    image: postgres:16
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - langgraph-data:/var/lib/postgresql/data
    healthcheck:
      test: pg_isready -U postgres
      start_period: 10s
      timeout: 1s
      retries: 5
      interval: 5s

  langgraph-api:
    image: ${IMAGE_NAME}
    ports: ["8123:8000"]
    depends_on:
      langgraph-redis:
        condition: service_healthy
      langgraph-postgres:
        condition: service_healthy
    env_file: [.env]
    environment:
      REDIS_URI: redis://langgraph-redis:6379
      DATABASE_URI: postgres://postgres:postgres@langgraph-postgres:5432/postgres?sslmode=disable
      LANGSMITH_API_KEY: ${LANGSMITH_API_KEY}
```

Build and start:

```bash
npx @langchain/langgraph-cli build -t my-agent:latest
IMAGE_NAME=my-agent:latest docker compose up -d
curl http://localhost:8123/ok
```

### Docker Compose with MongoDB Checkpointing

Add to the above compose file:

```yaml
  langgraph-mongo:
    image: mongo:7
    command: ["mongod", "--replSet", "rs0"]
    ports: ["27017:27017"]
    volumes:
      - langgraph-mongo-data:/data/db
    healthcheck:
      test: mongosh --eval "try { rs.status().ok } catch(e) { rs.initiate({_id:'rs0',members:[{_id:0,host:'langgraph-mongo:27017'}]}).ok }" --quiet
      interval: 5s
      timeout: 10s
      retries: 10
      start_period: 10s
```

Add to the `langgraph-api` service `environment` block:

```yaml
    environment:
      LS_DEFAULT_CHECKPOINTER_BACKEND: mongo
      LS_MONGODB_URI: mongodb://langgraph-mongo:27017/langgraph?replicaSet=rs0
```

### Custom TypeScript Server Dockerfile

When wrapping LangGraph in a custom Fastify/Express server instead of using the LangSmith server:

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --only=production
COPY --from=builder /app/dist ./dist
COPY langgraph.json ./

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

CMD ["node", "dist/server.js"]
```

### Kubernetes (Helm)

Helm chart available at `langchain-ai/helm` repository (`charts/langgraph-cloud/`). Supports Helm v0.2.6+ with MongoDB checkpointing.

---

## LangGraph Cloud Deployment

Fully managed — no infrastructure to provision.

### Quick Start

1. Connect GitHub and LangSmith accounts.
2. Push LangGraph-compatible code to a GitHub repo (public or private).
3. In LangSmith UI → **Deployments** → **+ New Deployment** → select repo → submit.
4. Deployment completes in ~15 minutes. Copy the **API URL** from deployment details.
5. Open **Studio** from the deployment details page to test the graph visually.

### Deploy via CLI

```bash
langgraph deploy
langgraph deploy --name "my-agent-prod" --deployment-type prod
langgraph deploy list
langgraph deploy revisions
langgraph deploy logs
```

### Test the Deployment

```ts
import { Client } from "@langchain/langgraph-sdk";

const client = new Client({
  apiUrl: "<DEPLOYMENT_URL>",
  apiKey: process.env.LANGSMITH_API_KEY,
});

const stream = client.runs.stream(null, "agent", {
  input: { messages: [{ role: "user", content: "Hello" }] },
  streamMode: "messages-tuple",
});

for await (const chunk of stream) {
  if (chunk.event === "messages/partial") console.log(chunk.data);
}
```

```bash
curl --request POST \
  --url "${DEPLOYMENT_URL}/runs/stream" \
  --header "x-api-key: ${LANGSMITH_API_KEY}" \
  --header "Content-Type: application/json" \
  --data '{"assistant_id":"agent","input":{"messages":[{"role":"user","content":"Hello"}]},"stream_mode":["updates"]}'
```

---

## Hybrid / Self-Hosted with Control Plane

Data-plane components (listener, operator, CRDs) run in your K8s cluster; the control plane is managed by LangChain (cloud).

```bash
# Build multi-platform image and push to your registry
npx @langchain/langgraph-cli build --platform linux/amd64 -t my-registry.com/my-app:v1.0.0
docker push my-registry.com/my-app:v1.0.0
```

In LangSmith UI → **Deployments** → **+ New Deployment**: fill in Image URL, Listener/Compute ID, Namespace, environment variables. For updates: **+ New Revision** with a new image URL.

For private registries: set `imagePullSecrets` in `langgraph-dataplane-values.yaml`.

---

## Self-Hosted Servers (Express, Fastify, Next.js, NestJS)

Use these patterns when wrapping LangGraph in your own HTTP server instead of deploying through the LangSmith server. You lose Studio, Threads API, cron jobs, and time-travel debugging but gain full infrastructure control.

### Checkpointer Selection Pattern

```ts
// src/config/checkpointer.ts
import { MemorySaver } from "@langchain/langgraph";
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";
import { SqliteSaver } from "@langchain/langgraph-checkpoint-sqlite";

export async function createCheckpointer() {
  if (process.env.DATABASE_URL) {
    // Production: PostgreSQL with connection pooling
    return PostgresSaver.fromConnString(process.env.DATABASE_URL);
  }
  if (process.env.NODE_ENV === "test") {
    // SQLite for CI/testing
    return SqliteSaver.fromConnString(":memory:");
  }
  // Development: in-memory (lost on restart)
  return new MemorySaver();
}
```

### Fastify (Recommended for Production)

```ts
// src/server/index.ts
import fastify from "fastify";
import { MemorySaver } from "@langchain/langgraph";
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";
import { Command } from "@langchain/langgraph";
import { createSupervisorApp } from "../apps/supervisor";
import { createSwarmApp } from "../apps/swarm";

const app = fastify({ logger: true });

const checkpointer = process.env.DATABASE_URL
  ? await PostgresSaver.fromConnString(process.env.DATABASE_URL)
  : new MemorySaver();

const graphs = {
  supervisor: createSupervisorApp({ checkpointer }),
  swarm: createSwarmApp({ checkpointer }),
};

// Invoke endpoint
app.post<{ Params: { app: string } }>("/:app/invoke", async (req, reply) => {
  const graph = graphs[req.params.app as keyof typeof graphs];
  if (!graph) return reply.code(404).send({ error: "Graph not found" });

  const { messages, thread_id } = req.body as any;
  const config = thread_id ? { configurable: { thread_id } } : undefined;
  const result = await graph.invoke({ messages }, config);
  return reply.send(result);
});

// Stream endpoint (Server-Sent Events)
app.post<{ Params: { app: string } }>("/:app/stream", async (req, reply) => {
  const graph = graphs[req.params.app as keyof typeof graphs];
  if (!graph) return reply.code(404).send({ error: "Graph not found" });

  reply.raw.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
  });

  const stream = await graph.stream(req.body as any);
  for await (const chunk of stream) {
    reply.raw.write(`data: ${JSON.stringify(chunk)}\n\n`);
  }
  reply.raw.end();
});

// Resume after interrupt
app.post<{ Params: { app: string } }>("/:app/resume", async (req, reply) => {
  const graph = graphs[req.params.app as keyof typeof graphs];
  const { thread_id, decision } = req.body as any;
  const result = await graph.invoke(
    new Command({ resume: decision }),
    { configurable: { thread_id } }
  );
  return reply.send(result);
});

// Thread state inspection
app.get<{ Params: { app: string; threadId: string } }>(
  "/:app/threads/:threadId",
  async (req, reply) => {
    const graph = graphs[req.params.app as keyof typeof graphs];
    const config = { configurable: { thread_id: req.params.threadId } };
    const state = await graph.getState(config);
    return reply.send(state);
  }
);

// Health check
app.get("/health", async (_req, reply) => {
  return reply.send({
    status: "ok",
    graphs: Object.keys(graphs),
    checkpointer: process.env.DATABASE_URL ? "postgres" : "memory",
  });
});

await app.listen({ port: Number(process.env.PORT) || 3000 });
```

### Express Integration

```ts
// src/server.ts
import express from "express";
import { app as graph } from "./agent";
import { Command } from "@langchain/langgraph";

const server = express();
server.use(express.json());

server.post("/invoke", async (req, res) => {
  try {
    const { input, thread_id } = req.body;
    const config = thread_id ? { configurable: { thread_id } } : undefined;
    const result = await graph.invoke(input, config);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

server.post("/stream", async (req, res) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");

  const { input, thread_id } = req.body;
  const config = thread_id ? { configurable: { thread_id } } : undefined;
  const stream = await graph.stream(input, config);
  for await (const chunk of stream) {
    res.write(`data: ${JSON.stringify(chunk)}\n\n`);
  }
  res.end();
});

server.post("/resume", async (req, res) => {
  const { thread_id, decision } = req.body;
  const result = await graph.invoke(
    new Command({ resume: decision }),
    { configurable: { thread_id } }
  );
  res.json(result);
});

server.listen(3000);
```

### NestJS Integration

```ts
// src/langgraph/langgraph.service.ts
import { Injectable } from "@nestjs/common";
import { app as graph } from "./graph";
import { Command } from "@langchain/langgraph";

@Injectable()
export class LangGraphService {
  async invoke(input: any, threadId?: string) {
    const config = threadId ? { configurable: { thread_id: threadId } } : undefined;
    return graph.invoke(input, config);
  }

  async *stream(input: any, threadId?: string) {
    const config = threadId ? { configurable: { thread_id: threadId } } : undefined;
    yield* await graph.stream(input, config);
  }

  async resume(threadId: string, decision: string) {
    return graph.invoke(
      new Command({ resume: decision }),
      { configurable: { thread_id: threadId } }
    );
  }
}
```

```ts
// src/langgraph/langgraph.controller.ts
import { Controller, Post, Body, Headers, Res } from "@nestjs/common";
import { LangGraphService } from "./langgraph.service";
import { Response } from "express";

@Controller("graph")
export class LangGraphController {
  constructor(private readonly service: LangGraphService) {}

  @Post("invoke")
  invoke(@Body() body: any, @Headers("x-thread-id") threadId?: string) {
    return this.service.invoke(body, threadId);
  }

  @Post("stream")
  async stream(
    @Body() body: any,
    @Headers("x-thread-id") threadId: string,
    @Res() res: Response
  ) {
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    for await (const chunk of this.service.stream(body, threadId)) {
      res.write(`data: ${JSON.stringify(chunk)}\n\n`);
    }
    res.end();
  }
}
```

### Next.js API Passthrough

```ts
// src/app/api/[..._path]/route.ts
import { initApiPassthrough } from "@langchain/langgraph-api-passthrough";

const { GET, POST, PUT, PATCH, DELETE, OPTIONS, runtime } = initApiPassthrough({
  apiUrl: process.env.LANGGRAPH_API_URL,
  apiKey: process.env.LANGSMITH_API_KEY,
  // Inject user-specific headers into requests
  headers: (req) => ({
    Authorization: `Bearer ${process.env.INTERNAL_AUTH_TOKEN}`,
  }),
  // Inject user ID from incoming request into graph configurable
  bodyParameters: (req, body) => ({
    ...body,
    configurable: { ...body.configurable, userId: req.headers.get("x-user-id") },
  }),
});

export { GET, POST, PUT, PATCH, DELETE, OPTIONS, runtime };
```

> **Deprecation note**: The `langgraph-nextjs-api-passthrough` approach is officially deprecated. Prefer implementing auth directly in the LangGraph deployment.

---

## LangGraph SDK Client (`@langchain/langgraph-sdk`)

```bash
npm install @langchain/langgraph-sdk
```

### Client Instantiation

```ts
import { Client } from "@langchain/langgraph-sdk";

// Basic (dev server)
const client = new Client({ apiUrl: "http://localhost:2024" });

// With API key (production)
const client = new Client({
  apiUrl: "https://my-deployment.langgraph.app",
  apiKey: process.env.LANGSMITH_API_KEY,
});

// With custom auth headers
const client = new Client({
  apiUrl: "http://localhost:2024",
  defaultHeaders: { Authorization: `Bearer ${token}` },
});
```

### Run Methods

```ts
// Stream a run (threadless)
const stream = client.runs.stream(null, "agent", {
  input: { messages: [{ role: "user", content: "Hello" }] },
  streamMode: "updates",   // "values" | "updates" | "messages-tuple" | "events" | "debug"
});
for await (const chunk of stream) {
  console.log(chunk.event, chunk.data);
}

// Stream on an existing thread (stateful)
const stream = client.runs.stream(threadId, "agent", {
  input: { messages: [{ role: "user", content: "Continue" }] },
  streamMode: "values",
});

// Background (non-streaming) run
const run = await client.runs.create(threadId, "agent", {
  input: { messages: [{ role: "user", content: "Hello" }] },
});
await client.runs.join(threadId, run.run_id);
const finalState = await client.threads.getState(threadId);

// Get run details
const runDetails = await client.runs.get(threadId, runId);
```

### Thread Methods

```ts
// Create empty thread
const thread = await client.threads.create();
// Returns: { thread_id, created_at, updated_at, metadata, status, values }

// Create with pre-populated state (inject conversation history)
const thread = await client.threads.create({
  graph_id: "agent",
  supersteps: [
    { updates: [{ values: {}, as_node: "__input__" }] },
    {
      updates: [{
        values: { messages: [{ type: "human", content: "hello" }] },
        as_node: "__start__",
      }],
    },
  ],
});

// Copy a thread
const copied = await client.threads.copy(threadId);

// Search threads — thread states: "idle" | "busy" | "interrupted" | "error"
const idle = await client.threads.search({ status: "idle", limit: 10 });
const sorted = await client.threads.search({
  metadata: { graph_id: "agent" },
  sort_by: "created_at",
  sort_order: "desc",
  limit: 5,
});

// Get thread state
const state = await client.threads.getState(threadId);

// Get full checkpoint history
for await (const checkpoint of client.threads.getHistory(threadId)) {
  console.log(checkpoint.created_at, checkpoint.values);
}
```

### Assistants API

Assistants decouple graph logic from runtime configuration. A single deployed graph can have multiple assistant configurations (different models, prompts, tools).

```ts
// Create an assistant
const assistant = await client.assistants.create({
  graph_id: "agent",
  config: {
    configurable: { model: "gpt-4.1", temperature: 0.7 },
  },
  metadata: { version: "1.0.0" },
});

// Update (creates new version; supply ALL fields)
await client.assistants.update("assistant-id", {
  config: { configurable: { model: "gpt-4.1-mini" } },
});

// Activate a specific version
await client.assistants.setLatest("assistant-id", versionNumber);

// Search assistants
const assistants = await client.assistants.search({ graphId: "agent" });
```

### Cron Jobs

```ts
// Thread-bound cron (accumulates history on the same thread)
const thread = await client.threads.create();
await client.crons.createForThread(thread.thread_id, "agent", {
  schedule: "27 15 * * *",   // UTC: MIN HOUR DAY MONTH WEEKDAY
  input: { messages: [{ role: "user", content: "Daily report" }] },
});

// Stateless cron (new thread per run)
await client.crons.create("agent", {
  schedule: "0 9 * * 1-5",   // 9 AM UTC, weekdays
  input: { messages: [{ role: "user", content: "Morning briefing" }] },
  onRunCompleted: "keep",    // "delete" (default) removes thread after run
});

// Find runs from a cron job
const cronRuns = await client.runs.search({ metadata: { cron_id: cronJob.cron_id } });

// Delete cron
await client.crons.delete(cronId);
```

Cron jobs require PostgreSQL checkpointing. The in-memory dev server does NOT support crons.

### RemoteGraph

`RemoteGraph` lets you interact with a deployed graph as if it were a locally compiled graph — same API surface.

```ts
import { RemoteGraph } from "@langchain/langgraph/remote";
import { v4 as uuidv4 } from "uuid";

const remoteGraph = new RemoteGraph({
  graphId: "agent",
  url: "https://my-deployment.langgraph.app",
  apiKey: process.env.LANGSMITH_API_KEY,
  // headers: { Authorization: `Bearer ${token}` } for custom auth
});

// Invoke
const result = await remoteGraph.invoke(
  { messages: [{ role: "user", content: "Hello" }] }
);

// Stream
for await (const chunk of await remoteGraph.stream(
  { messages: [{ role: "user", content: "Hello" }] }
)) {
  console.log(chunk);
}

// With thread (stateful)
const config = { configurable: { thread_id: uuidv4() } };
const statefulResult = await remoteGraph.invoke(inputs, config);
const state = await remoteGraph.getState(config);
await remoteGraph.updateState(config, { messages: [] });
```

`RemoteGraph` as a node inside another graph:

```ts
import { StateGraph, MessagesAnnotation, START } from "@langchain/langgraph";
import { RemoteGraph } from "@langchain/langgraph/remote";

const remoteWorker = new RemoteGraph({ graphId: "worker", url: WORKER_URL });

const graph = new StateGraph(MessagesAnnotation)
  .addNode("coordinator", coordinatorNode)
  .addNode("worker", remoteWorker)
  .addEdge("coordinator", "worker")
  .compile({ checkpointer });
```

**Critical**: Do NOT use `RemoteGraph` to call a graph within the same deployment — this causes deadlocks and resource exhaustion. Use local composition instead.

**Thread IDs**: Always use UUIDs for `thread_id` to avoid collisions across deployments.

Constructor parameters:

| Parameter | Required | Description |
|-----------|----------|-------------|
| `name` / `graphId` | Yes | Graph name or assistant ID |
| `url` | Optional if `client` provided | Deployment URL |
| `apiKey` | Optional | LangSmith API key (also reads `LANGSMITH_API_KEY`) |
| `headers` | Optional | Custom headers (e.g., for custom auth) |
| `client` | Optional | Pre-constructed `LangGraphClient` |

---

## Generative UI (`typedUi`, `LoadExternalComponent`, `useStream`)

The server emits React component specifications; the client renders them dynamically without pre-bundling them into the client app.

### Architecture

```
LangGraph Server
  → pushes ui messages (component name + props)
  → serves component assets at /ui/{namespace}

React Client
  → useStream() connects to server
  → LoadExternalComponent renders external components
  → useStreamContext() inside components for thread access
```

### `langgraph.json` Setup

```json
{
  "node_version": "20",
  "graphs": { "agent": "./src/agent/index.ts:graph" },
  "ui": { "agent": "./src/agent/ui.tsx" }
}
```

The `ui` key maps a namespace (must match the `assistantId`) to a `.tsx` file exporting a component map.

### Define UI Components (`src/agent/ui.tsx`)

```tsx
// Can include Tailwind CSS
const WeatherComponent = (props: { city: string; temp: number }) => (
  <div className="bg-blue-500 p-4 rounded">
    <h2>Weather for {props.city}</h2>
    <p>{props.temp}°F</p>
  </div>
);

const LoadingSpinner = () => <div className="animate-spin">⟳</div>;

export default {
  weather: WeatherComponent,
  loading: LoadingSpinner,
};
```

### Emit UI from a Graph Node (`typedUi`)

```ts
import { typedUi } from "@langchain/langgraph";
import type ComponentMap from "./ui";

// Inside a node function
const weatherNode = async (state: typeof AgentState.State, config: any) => {
  const ui = typedUi<typeof ComponentMap>(config);

  // Type-safe: props are validated against ComponentMap
  ui.push({ name: "weather", props: { city: "NYC", temp: 72 } }, { message: response });

  return { messages: [response] };
};
```

`typedUi<typeof ComponentMap>` provides type-safe `ui.push()` with component name and props validation.

### React Client — Render External Components

```tsx
import { useStream } from "@langchain/react";
import { LoadExternalComponent } from "@langchain/langgraph-sdk";

function App() {
  const { thread, values, submit } = useStream({
    apiUrl: "http://localhost:2024",
    assistantId: "agent",
  });

  return (
    <div>
      {thread.messages.map(m => (
        <div key={m.id}>
          <p>{m.content}</p>
          {values.ui
            ?.filter(ui => ui.metadata?.message_id === m.id)
            .map(ui => (
              <LoadExternalComponent key={ui.id} stream={thread} message={ui} />
            ))}
        </div>
      ))}
      <button onClick={() => submit({ messages: [{ type: "human", content: "Hello" }] })}>
        Send
      </button>
    </div>
  );
}
```

### `LoadExternalComponent` Props

| Prop | Type | Description |
|------|------|-------------|
| `stream` | Thread object | Thread from `useStream()` |
| `message` | UIMessage | The UI message containing component spec |
| `components` | `Record<string, ComponentType>` | Optional: override with local components (avoids network load) |
| `fallback` | `ReactNode` | Shown while loading the remote component |

Client-side component override:

```tsx
const clientComponents = { weather: WeatherComponent };
<LoadExternalComponent stream={thread} message={ui} components={clientComponents} />;
```

### `useStreamContext()` — Inside UI Components

```tsx
import { useStreamContext } from "@langchain/langgraph-sdk/react-ui";

const MyButton = () => {
  const { thread, submit } = useStreamContext();
  return (
    <button onClick={() => submit({ messages: [{ type: "human", content: "Retry" }] })}>
      Retry
    </button>
  );
};
```

---

## CI/CD Pipeline (GitHub Actions)

Pipeline stages: **test** → **dev-server-test** → **offline evaluation** → **preview deployment** (PRs) → **production** (merge to main) → **health check**.

```yaml
# .github/workflows/deploy.yml
name: Deploy LangGraph Agent

on:
  push:
    branches: [main, development]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci && npm test
        env:
          LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}

  dev-server-test:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - name: Start dev server and wait for ready
        run: |
          npx @langchain/langgraph-cli dev &
          for i in $(seq 1 30); do
            curl -s http://localhost:2024/ok && break
            sleep 1
          done
        env:
          LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}

  preview:
    needs: test
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npx @langchain/langgraph-cli deploy --name "preview-${{ github.event.pull_request.number }}" --deployment-type dev
        env:
          LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}

  production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npx @langchain/langgraph-cli deploy --name "production" --deployment-type prod
        env:
          LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
      - name: Verify health
        run: curl --fail "${DEPLOYMENT_URL}/ok" -H "X-Api-Key: ${LANGSMITH_API_KEY}"
        env:
          DEPLOYMENT_URL: ${{ vars.DEPLOYMENT_URL }}
          LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
```

CI trigger sources: code changes on `main`/`development`, PromptHub updates, online evaluation alerts, LangSmith trace webhooks, manual trigger.

---

## Pricing Table (LangSmith Deployment, 2025–2026)

| Plan | Cost | Key limits |
|------|------|-----------|
| **Open Source** | $0 | MIT library; no platform included |
| **Developer** | $0 up to 100K nodes/mo | Self-hosted server; core orchestration |
| **Plus** | Pay-as-you-go | Managed SaaS; Studio; $39/user/mo |
| **Enterprise** | Custom | Hybrid/self-hosted; SLA; SSO/RBAC; dedicated support |

### Plus Plan Usage Fees

| Item | Cost |
|------|------|
| Node execution | $0.001 per node executed |
| Standby time (dev deployment) | $0.0007/min |
| Standby time (prod deployment) | $0.0036/min |
| Traces (14-day retention) | $2.50/1K traces |
| Traces (400-day retention) | $4.50/1K traces |
| Additional seats | $39/user/mo |

**Example**: 1M node executions ≈ $1,000 (excluding standby and seat costs).

### Cost Reduction Strategies

1. **Minimize node count** — fewer nodes = fewer billable executions.
2. **Stateless crons with `onRunCompleted: "delete"`** — avoid accumulating thread storage.
3. **Set `checkpointer.ttl`** — auto-delete old threads.
4. **Self-host with Docker Compose** — no per-node charges; pay only for your own infra (Docker images are free/MIT).
5. **Use `langgraph dev` for development** — zero cloud cost (in-memory, no LangSmith resources consumed).
6. **Set `N_JOBS_PER_WORKER=10`** — one worker handles 10 concurrent runs.

---

## Production Scaling Patterns

### Server Architecture

```
Client Request
    → API Server (HTTP, serves SSE streaming)
    → Job Queue (backed by Redis pub/sub)
    → Queue Workers (execute graph code, write checkpoints)
    → Checkpoint Store (PostgreSQL default; MongoDB optional)
```

### Runtime Modes

| Mode | Description | When to use |
|------|-------------|-------------|
| **Single host** | API server and queue in same process (default) | Dev, low traffic |
| **Split API + queue** | Dedicated queue workers on separate hosts; `queue.enabled: true` | Medium traffic, horizontal scaling |
| **Distributed runtime** | Separate orchestration and execution processes | High concurrency (100s of simultaneous runs) |

### Scaling Options

| Approach | When to use |
|----------|-------------|
| Increase `N_JOBS_PER_WORKER` | Handle more concurrent requests on same hardware |
| Add queue workers (split mode) | Scale execution capacity independently from API |
| Distributed runtime | Very high concurrency |
| Horizontal pod autoscaling (K8s) | Cloud-native elastic scaling |

### Durability Modes

| Mode | Behavior | Use case |
|------|----------|---------|
| `async` (default) | Writes checkpoint after each superstep | Full fault tolerance; resume mid-graph |
| `exit` | Writes only final state | Lower overhead; acceptable for short-lived tasks |

### AWS Reference Architecture

```
User → API Gateway / ALB
    → ECS Fargate (API + Queue Workers)
    → RDS PostgreSQL (checkpoints)
    → ElastiCache Redis (streaming pub/sub)
    → S3 (optional: artifact storage)
```

Key considerations: IAM roles for secrets (not env var secrets in task definitions), VPC private subnets for DB/Redis, autoscale on queue depth.

### Alternative Hosting Platforms

- **Fly.io** — simple CLI deployment, close-to-user edge hosting
- **Render** — easy Docker container deployment with managed databases
- **Railway** — environment-based deployments with automatic scaling
- **GCP Cloud Run + Cloud SQL + Memorystore** — serverless-style scaling with pay-per-request (set min instances ≥ 1 to avoid cold-start SSE issues)

### Multi-Tenant Row-Level Isolation

```typescript
// langgraph.json auth handler — enforce row-level security by tenant
// Configure in langgraph.json: "auth": { "path": "./src/auth.ts:handler" }
export async function handler(ctx: { user: { org_id: string } }, value: Record<string, any>) {
  value.metadata = value.metadata ?? {};
  value.metadata.tenant_id = ctx.user.org_id;
  return { tenant_id: ctx.user.org_id };
}
```

### Thread TTL Configuration

```json
{
  "checkpointer": {
    "ttl": {
      "strategy": "delete",
      "sweep_interval_minutes": 60,
      "default_ttl": 10080
    }
  }
}
```

---

## Health Checks & Monitoring

### Health Check Endpoints

```bash
# Liveness probe
curl https://your-deployment.langgraph.app/ok \
  -H "X-Api-Key: ${LANGSMITH_API_KEY}"
# {"ok":true}

# Readiness probe (also verifies DB connectivity)
curl "https://your-deployment.langgraph.app/ok?check_db=1" \
  -H "X-Api-Key: ${LANGSMITH_API_KEY}"
```

| Endpoint | Description |
|----------|-------------|
| `GET /ok` | Liveness probe; returns `{"ok":true}` |
| `GET /ok?check_db=1` | Readiness probe; returns 500 if DB unreachable |
| `GET /system/server-information` | Server version, runtime info |
| `GET /system/system-metrics` | CPU, memory, queue depth |
| `GET /docs` | Full OpenAPI spec (interactive Swagger UI) |

### LangSmith Tracing

All runs automatically emit traces to LangSmith when `LANGSMITH_API_KEY` is set. Traces include:
- Per-node execution with prompts, tool calls, results
- Latency per node
- Token counts
- Exceptions

Disable tracing:

```env
LANGSMITH_TRACING=false
```

Set the project:

```env
LANGSMITH_PROJECT=my-production-project
```

### Third-Party Observability

- **LangSmith** (native) — traces, datasets, evaluations, alerts
- **Langfuse** (open source) — LangGraph trace graph view, self-hostable
- **Dynatrace** — agent/model service health, real-time metrics, bottleneck detection

### Production Checklist

- [ ] PostgreSQL checkpointing — never use in-memory checkpointer in production
- [ ] Redis running — required for streaming pub/sub from workers to API server
- [ ] `N_JOBS_PER_WORKER` tuned to expected concurrency (default: 10)
- [ ] `durability.mode: "async"` set for fault-tolerant checkpoint recovery
- [ ] Custom auth implemented for any deployment accessible over the internet
- [ ] Per-resource authorization for multi-tenant use cases
- [ ] Thread TTLs configured in `checkpointer.ttl` to control storage growth
- [ ] `GET /ok` monitored by load balancer for liveness
- [ ] `GET /ok?check_db=1` used for readiness probes
- [ ] `LANGSMITH_API_KEY` set for automatic tracing
- [ ] CI/CD pipeline with preview environments per PR
- [ ] Tested with `langgraph up` (production-like Docker) before promoting to cloud
- [ ] `LANGGRAPH_CLOUD_LICENSE_KEY` set if using paid standalone tier
- [ ] `RemoteGraph` NOT calling graphs within same deployment (deadlock risk)
- [ ] UUIDs used for `thread_id` across deployments to prevent collisions
- [ ] CORS configured for production domain(s) in `langgraph.json`
- [ ] Secrets managed via IAM roles or secrets manager, not environment variable literals

---

## Known Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| Cron jobs not firing | In-memory checkpointer used | Switch to PostgreSQL checkpointing (`langgraph up` or standalone) |
| Thread state lost on container restart | `MemorySaver` used in production | Use `PostgresSaver` or deploy with `langgraph up` / standalone Docker |
| `RemoteGraph` deadlock | Calling a graph within the same deployment | Use local composition instead |
| Streaming breaks in serverless | SSE requires long-lived HTTP connections | Use a persistent server (ECS, Cloud Run with min=1, Fly.io) |
| Checkpoint write overhead at scale | Default `async` mode writes after every superstep | Switch to `durability.mode: "exit"` for short-lived, non-resumable graphs |
| Auth bypass in Lite self-hosting | Standalone Lite has no custom auth support | Use Enterprise tier or wrap in your own auth proxy |
| `thread_id` collisions across deployments | Non-UUID thread IDs | Always use `uuidv4()` for `thread_id` |
| Subgraph per-thread persistence fails inside a tool | Not supported by the SDK | Use per-invocation persistence for subgraphs called as tools |
| Traces not appearing in LangSmith in scripts | Background callback not flushed before process exit | Call `await waitForAllTracers()` at script end |
| Docker Compose start fails with "db not healthy" | `langgraph-postgres` healthcheck takes >10s on first boot | Increase `start_period` in the postgres healthcheck to `30s` |
| High cost on managed cloud at scale | Node execution billed at $0.001/node | Self-host with Docker Compose (MIT, no per-node fees) or use Enterprise self-hosted |
| Safari CORS on LangSmith Studio preview | Safari blocks non-HTTPS localhost connections | Not applicable in production; use `--tunnel` in local dev only |
| `imagePullSecrets` missing in Hybrid K8s | Private registry not authenticated | Set `imagePullSecrets` in `langgraph-dataplane-values.yaml` |
| `LANGCHAIN_CALLBACKS_BACKGROUND=true` missing in long-running servers | Traces dropped because callbacks are not awaited | Set `LANGCHAIN_CALLBACKS_BACKGROUND=true` for servers; `false` for short scripts |
