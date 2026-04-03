# Deployment: Local Development & Studio Reference

> Verified against @langchain/langgraph-cli latest, @langchain/langgraph@1.2.5, LangSmith Studio (web-based, hosted by LangSmith).
> LangGraph Platform was rebranded to LangSmith Deployment in May 2025. CLI and `langgraph.json` are unchanged.

---

## LangGraph Studio (LangSmith Studio)

The Studio UI is web-based and hosted by LangSmith. It connects to your local or deployed server via a `baseUrl` query parameter — no installation required.

**URL**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

### Core Features

| Feature | Notes |
|---------|-------|
| Graph visualization | Interactive node/edge rendering; shows live execution position |
| Real-time state inspection | Full state at each checkpoint as it runs |
| State editing mid-run | Edit any state field at a checkpoint and re-run from that point |
| Time-travel debugging | Fork from any past checkpoint with modified state; original history preserved |
| Breakpoints | Pause before or after any node; resume manually |
| Hot reload | `langgraph dev` auto-restarts on source changes |
| Thread management | List, select, create threads; view full conversation history |
| Assistant management | Create, version, activate assistants with different configurations |
| Graph mode / Chat mode | Full graph+state view or lightweight conversational UI |
| Interrupt indicators | Visual marker when graph waits at `interrupt()` |

### Studio Modes

**Graph mode** — Full graph visualization with:
- Node execution cards showing status (idle / streaming / complete)
- State panel for inspecting values at each checkpoint
- Fork / re-run / edit-state controls per node
- Raw vs Pretty toggle for state display

**Chat mode** — Conversational interface with:
- Message streaming
- Tool call visibility toggle (Show tool calls)
- Assistant selector dropdown

### Setting a Breakpoint in Studio

1. Click **Interrupt** in the run settings panel.
2. Select a node from the dropdown.
3. Choose **Before** or **After** execution.
4. Click **Submit** — execution pauses at the selected node.
5. Inspect or edit state, then click **Continue** to resume.

### Time-Travel Debugging

Every state change creates a checkpoint. From Studio:

1. In the thread view, each node turn has **Fork** and **Re-run from here** controls.
2. **Edit node state** → modify any field → **Fork** creates a new branch.
3. **Re-run from here** replays without state modification (allows changing the assistant config).
4. Original execution history is preserved; forked threads appear as new threads.

TypeScript time-travel with `MemorySaver`:

```ts
import { StateGraph, MemorySaver, Annotation, START } from "@langchain/langgraph";
import { v4 as uuidv4 } from "uuid";

const StateAnnotation = Annotation.Root({
  topic: Annotation<string>(),
  joke: Annotation<string>(),
});

const checkpointer = new MemorySaver();
const graph = new StateGraph(StateAnnotation)
  .addNode("generateTopic", () => ({ topic: "socks" }))
  .addNode("writeJoke", (s) => ({ joke: `Why do ${s.topic} disappear?` }))
  .addEdge(START, "generateTopic")
  .addEdge("generateTopic", "writeJoke")
  .compile({ checkpointer });

const config = { configurable: { thread_id: uuidv4() } };
await graph.invoke({}, config);

// Get full checkpoint history
const states: any[] = [];
for await (const s of graph.getStateHistory(config)) states.push(s);

// Find checkpoint before writeJoke ran
const beforeJoke = states.find(s => s.next.includes("writeJoke"));

// Fork with modified state
const forkConfig = await graph.updateState(beforeJoke.config, { topic: "chickens" });
const forkResult = await graph.invoke(null, forkConfig);
```

`updateState` options:

| Option | Description |
|--------|-------------|
| `asNode` | Attribute the update to a specific node (useful for parallel branches) |
| Pass `null` as input to `invoke` | Replay from the forked checkpoint without new input |

---

## CLI Reference — All Commands

### Installation (JS/TS)

```bash
npm install --save-dev @langchain/langgraph-cli
# Scaffold a new project:
npm create langgraph
npx @langchain/langgraph-cli new path/to/app --template new-langgraph-project-js
```

### `langgraph dev` — Development Server (No Docker)

Starts an in-memory dev server. Hot reload is on by default. Threads survive reloads.

```bash
npx @langchain/langgraph-cli dev
npx @langchain/langgraph-cli dev --port 3000 --no-browser
npx @langchain/langgraph-cli dev --debug-port 5678 --wait-for-client
npx @langchain/langgraph-cli dev --allow-blocking   # needed for sync I/O in nodes
npx @langchain/langgraph-cli dev --tunnel           # expose via Cloudflare (Safari fix)
```

Server output after start:

```
> Ready!
> - API: http://localhost:2024
> - Docs: http://localhost:2024/docs
> - LangSmith Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

Full flag reference:

| Option | Default | Description |
|--------|---------|-------------|
| `-c, --config FILE` | `langgraph.json` | Path to configuration file |
| `--host TEXT` | `127.0.0.1` | Host to bind |
| `--port INTEGER` | `2024` | Port to bind |
| `--no-reload` | — | Disable auto-reload |
| `--n-jobs-per-worker INTEGER` | `10` | Max concurrent jobs per worker |
| `--debug-port INTEGER` | — | Port for DAP debugger |
| `--wait-for-client` | `false` | Pause startup until debugger connects |
| `--no-browser` | — | Skip auto-opening browser/Studio |
| `--allow-blocking` | `false` | Allow synchronous I/O in nodes |
| `--tunnel` | `false` | Expose via Cloudflare tunnel |

### `langgraph up` — Production-Like Local Stack (Docker Required)

Starts API server + PostgreSQL + Redis containers. Suitable for testing production behavior locally.

```bash
langgraph up                         # start production-like stack
langgraph up --watch                 # with hot reload
langgraph up --port 8123             # custom port (default: 8123)
langgraph up --postgres-uri "postgresql://user:pass@host:5432/db"  # custom DB
```

Full flag reference:

| Option | Default | Description |
|--------|---------|-------------|
| `-p, --port INTEGER` | `8123` | Port to expose |
| `--watch` | — | Restart on file changes |
| `--postgres-uri TEXT` | — | External Postgres URI |
| `--base-image TEXT` | `langchain/langgraph-api` | Base Docker image |
| `--pull / --no-pull` | `pull` | Pull latest images |
| `--recreate / --no-recreate` | `no-recreate` | Force container recreation |
| `--verbose` | — | Show detailed server logs |
| `-c, --config FILE` | `langgraph.json` | Config file path |
| `-d, --docker-compose FILE` | — | Additional compose services |

### `dev` vs `up` Comparison

| Feature | `langgraph dev` | `langgraph up` |
|---------|----------------|---------------|
| Docker required | No | Yes |
| Default port | 2024 | 8123 |
| State persistence | In-memory + pickle | PostgreSQL |
| Hot-reload | Yes (default) | Optional (`--watch`) |
| Resource usage | Light (single process) | Heavy (3 containers) |
| IDE debugging | Built-in DAP | Regular container debugging |
| Custom auth | Basic | Full (requires license key) |
| Cron job support | No | Yes |

### `langgraph build` — Build Docker Image

```bash
npx @langchain/langgraph-cli build -t my-agent:latest
npx @langchain/langgraph-cli build -t my-agent:1.0.0 --platform linux/amd64
npx @langchain/langgraph-cli build -t my-registry.com/app:v1 --platform linux/amd64,linux/arm64
```

| Option | Default | Description |
|--------|---------|-------------|
| `-t, --tag TEXT` | Required | Docker image tag |
| `--platform TEXT` | — | Target platform(s) |
| `--pull / --no-pull` | `--pull` | Pull latest base image |
| `-c, --config FILE` | `langgraph.json` | Config file path |
| `--build-command TEXT` | — | Custom build command (JS/TS) |
| `--install-command TEXT` | — | Custom install command (JS/TS) |

### `langgraph deploy` — Deploy to LangSmith Cloud

```bash
langgraph deploy
langgraph deploy --name "my-agent-prod" --deployment-type prod
langgraph deploy list
langgraph deploy revisions
langgraph deploy logs
langgraph deploy delete --deployment-id <id>
```

### `langgraph dockerfile` — Emit Dockerfile

```bash
npx @langchain/langgraph-cli dockerfile > Dockerfile
```

---

## `langgraph.json` — Complete Schema Reference

Central configuration file used by all CLI commands and all deployment modes.

### Minimal (TypeScript)

```json
{
  "node_version": "20",
  "graphs": {
    "agent": "./src/agent.ts:agent"
  },
  "env": ".env"
}
```

### Full Schema (All Options)

```json
{
  "node_version": "20",
  "graphs": {
    "agent": "./src/agent.ts:agent",
    "worker": "./src/worker.ts:graph"
  },
  "env": ".env",
  "ui": {
    "agent": "./src/agent/ui.tsx",
    "custom-namespace": "./src/other/ui.tsx"
  },
  "auth": {
    "path": "./src/auth.ts:auth",
    "openapi": {
      "securitySchemes": {
        "apiKeyAuth": {
          "type": "apiKey",
          "in": "header",
          "name": "X-API-Key"
        }
      },
      "security": [{ "apiKeyAuth": [] }]
    },
    "disable_studio_auth": false
  },
  "http": {
    "app": "./src/webapp.ts:app",
    "cors": {
      "allow_origins": ["https://example.com"],
      "allow_methods": ["GET", "POST", "PUT", "DELETE"],
      "allow_headers": ["Authorization", "Content-Type"],
      "allow_credentials": true,
      "allow_origin_regex": "^https://.*\\.example\\.com$",
      "expose_headers": ["x-request-id"],
      "max_age": 600
    },
    "configurable_headers": ["x-request-id", "x-session-id"],
    "logging_headers": {
      "includes": ["request-id", "x-purchase-id"],
      "excludes": ["authorization", "x-api-key"]
    },
    "disable_assistants": false,
    "disable_mcp": false,
    "disable_a2a": false,
    "disable_runs": false,
    "disable_store": false,
    "disable_threads": false,
    "disable_ui": false,
    "disable_webhooks": false,
    "mount_prefix": "/api"
  },
  "store": {
    "index": {
      "dims": 1536,
      "embed": "openai:text-embedding-3-small",
      "fields": ["$"]
    },
    "ttl": {
      "refresh_on_read": true,
      "default_ttl": 43200,
      "sweep_interval_minutes": 60
    }
  },
  "checkpointer": {
    "backend": "default",
    "ttl": {
      "strategy": "delete",
      "default_ttl": 10080,
      "sweep_interval_minutes": 60
    }
  },
  "webhooks": {
    "env_prefix": "WEBHOOK_",
    "headers": ["x-custom-header"],
    "url": "https://your-webhook-endpoint.com"
  },
  "api_version": "0.3",
  "base_image": "langchain/langgraphjs-api:20",
  "dockerfile_lines": [
    "RUN apt-get install -y some-native-dep"
  ]
}
```

### Schema Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `node_version` | For JS/TS | Node.js version (e.g., `"20"`, `"24"`) |
| `graphs` | Yes | `graph-id → "file:export"` map |
| `env` | No | Path to `.env` file or `{ "KEY": "value" }` object |
| `ui` | No | Namespace → `.tsx` file for Generative UI |
| `auth.path` | No | Custom auth handler (e.g., `"./src/auth.ts:auth"`) |
| `auth.disable_studio_auth` | No | `true` lets LangSmith Studio bypass custom auth |
| `http.app` | No | Path to Hono app for custom routes |
| `http.cors` | No | CORS configuration object |
| `http.configurable_headers` | No | HTTP headers forwarded to `config.configurable` |
| `http.logging_headers` | No | Headers to include/exclude from server logs |
| `http.disable_*` | No | Boolean flags to disable specific route groups |
| `http.mount_prefix` | No | URL prefix for all routes (e.g., `"/api"`) |
| `store.index` | No | Semantic search index config (dims, embed model, fields) |
| `store.ttl` | No | TTL policy for store items |
| `checkpointer.backend` | No | `"default"`, `"mongo"`, or `"custom"` |
| `checkpointer.ttl` | No | TTL policy for checkpoints (`strategy: "delete"`) |
| `api_version` | No | Pin API version to avoid breaking changes |
| `base_image` | No | Override Docker base image |
| `dockerfile_lines` | No | Extra Dockerfile instructions injected into the build |

### Multi-Graph Configuration

```json
{
  "node_version": "20",
  "graphs": {
    "customer_support": "./src/graphs/support.ts:supportGraph",
    "analytics": "./src/graphs/analytics.ts:analyticsGraph",
    "research": "./src/graphs/research.ts:researchGraph"
  },
  "env": ".env"
}
```

### Graph Entry Point Formats

```json
{
  "graphs": {
    "agent1": "./src/agent.ts:app",
    "agent2": "./src/graphs/agent2.ts:compiledGraph",
    "agent3": "./src/factories/agent3.ts:createAgent"
  }
}
```

`createAgent` is a factory function — LangGraph calls it automatically on startup.

---

## VS Code Debugger Attachment

The TypeScript CLI has built-in DAP (Debug Adapter Protocol) support via `--debug-port`.

```bash
# Start dev server with DAP debug port exposed
npx @langchain/langgraph-cli dev --debug-port 5678 --wait-for-client
```

`launch.json` for VS Code:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Attach to LangGraph",
      "type": "node",
      "request": "attach",
      "port": 5678,
      "address": "localhost",
      "restart": true,
      "sourceMaps": true,
      "remoteRoot": "/app",
      "localRoot": "${workspaceFolder}"
    }
  ]
}
```

For Python graphs using `debugpy`:

```bash
pip install debugpy
langgraph dev --debug-port 5678
```

Python `launch.json`:

```json
{
  "name": "Attach to LangGraph (Python)",
  "type": "debugpy",
  "request": "attach",
  "connect": { "host": "0.0.0.0", "port": 5678 }
}
```

`--wait-for-client` holds server startup until the debugger attaches — useful to catch issues during graph initialization.

---

## Local Dev Server Configuration

### Quick SDK Test Against Dev Server

```ts
import { Client } from "@langchain/langgraph-sdk";

const client = new Client({ apiUrl: "http://localhost:2024" });

const streamResponse = client.runs.stream(
  null,       // threadless run
  "agent",    // assistant/graph ID
  {
    input: {
      messages: [{ role: "user", content: "What is LangGraph?" }]
    },
    streamMode: "messages-tuple",
  }
);

for await (const chunk of streamResponse) {
  console.log(`Event type: ${chunk.event}`);
  console.log(JSON.stringify(chunk.data));
}
```

### Disable Tracing Locally

```env
# .env
LANGSMITH_TRACING=false
```

### Hono Custom Routes (Extend the Dev Server)

```json
// langgraph.json
{ "http": { "app": "./src/webapp.ts:app" } }
```

```ts
// src/webapp.ts
import { Hono } from "hono";

export const app = new Hono();

app.get("/health", (c) => c.json({ status: "ok" }));
app.get("/version", (c) => c.json({ version: "1.0.0" }));

app.post("/login", async (c) => {
  const body = await c.req.json();
  // validate credentials, return JWT
  return c.json({ token: "..." });
});
```

Custom routes take precedence over default LangGraph routes when paths overlap.

---

## Agent Chat UI

Pre-built Next.js application for chatting with any LangGraph agent that exposes a `messages` state key.

- **Hosted version**: `https://agentchat.vercel.app` (no setup required)
- **GitHub repo**: `https://github.com/langchain-ai/agent-chat-ui`

### Local Setup

```bash
npx create-agent-chat-app --project-name my-chat-ui
cd my-chat-ui
pnpm install
pnpm dev
```

### Configuration (Environment Variables)

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | UI's API proxy base URL | `http://localhost:3000/api` |
| `NEXT_PUBLIC_ASSISTANT_ID` | Graph/assistant identifier | `agent` |
| `LANGGRAPH_API_URL` | Direct LangGraph server URL (server-side) | `http://localhost:2024` |
| `LANGSMITH_API_KEY` | Secret key for API Passthrough auth | `lsv2_...` |
| `NEXT_PUBLIC_AUTH_SCHEME` | Set to `langsmith-api-key` for Agent Builder deployments | `langsmith-api-key` |

### `useTypedStream` — Typed Hook with Custom Auth Headers

```ts
import { useTypedStream } from "@langchain/langgraph-sdk/react-ui";

const streamValue = useTypedStream({
  apiUrl: process.env.NEXT_PUBLIC_API_URL,
  assistantId: process.env.NEXT_PUBLIC_ASSISTANT_ID,
  defaultHeaders: {
    Authorization: `Bearer ${token}`,
  },
});
```

### Hide Messages from the Chat UI

```ts
// Suppress live streaming — final result still shown
const model = new ChatAnthropic().withConfig({ tags: ["langsmith:nostream"] });

// Permanently hide from UI entirely
result.id = `do-not-render-${result.id}`;
return { messages: [result] };
```

---

## Hot Reload Behavior

| Mode | Reload Support | Notes |
|------|---------------|-------|
| `langgraph dev` | Yes, default | Threads survive reloads; no Docker required |
| `langgraph up --watch` | Yes, with `--watch` flag | **Known bug**: reloads can delete in-flight threads |

If hot reload stops triggering with `langgraph up`, the most common cause is an outdated Docker base image:

```bash
docker pull langchain/langgraph-api
```

---

## Safari Tunnel Workaround

Safari blocks connections to `localhost` from external pages (including the LangSmith Studio hosted at `smith.langchain.com`).

**Fix**:

```bash
npx @langchain/langgraph-cli dev --tunnel
```

This exposes your dev server via a Cloudflare tunnel and prints a public HTTPS URL. Then:

1. Open `https://smith.langchain.com/studio`.
2. Click **Connect to a local server** in Studio settings.
3. Paste the tunnel URL (e.g., `https://abc123.trycloudflare.com`).

Chrome 130+ also has `Private Network Access` restrictions that can cause CORS errors with localhost. Use Firefox for local development or use `--tunnel`.

---

## Known Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| Hot reload stops triggering with `langgraph up` | Outdated Docker base image | `docker pull langchain/langgraph-api` |
| `langgraph up --watch` deletes in-flight threads | Known CLI bug in hot-reload path | Use `langgraph dev` for iterative development |
| Studio page not loading | `langgraph dev` not running or wrong `baseUrl` | Verify dev server is up; check URL param; clear browser cache |
| Safari blocks localhost in Studio | Browser blocks non-HTTPS localhost | `langgraph dev --tunnel`; add tunnel URL in Studio settings |
| Chrome 130+ CORS error on localhost | `Private Network Access` policy | Use Firefox in dev, or `--tunnel` flag |
| CORS with `undefined` values in Hono middleware | Bug in early Hono versions | Update Hono to latest version |
| `--wait-for-client` hangs server startup | Debugger never attached | Attach VS Code debugger before the timeout expires |
| Factory function graph not loading | `createAgent` not exported as named export | Verify the export name matches `langgraph.json` `file:export` format |
| `langgraph dev` cron jobs never fire | In-memory checkpointer does not support crons | Switch to `langgraph up` (PostgreSQL) for cron testing |
| Traces not appearing in LangSmith locally | Background callback not flushed | Call `await waitForAllTracers()` at script end, or set `LANGCHAIN_CALLBACKS_BACKGROUND=false` |
