# MCP Deployment Platform Patterns

Platform-specific patterns for remote MCP server deployment on Cloudflare Workers, Vercel, Smithery, Modal, Fly.io, Railway, Render, AWS Lambda, Azure Container Apps, GCP Cloud Run, Deno Deploy, Koyeb, and Northflank. Each platform has unique quirks for session state, Streamable HTTP, timeouts, response caps, auth primitives, and cold-start behavior that determine whether a given MCP workload can run on it at all.

This file does **not** re-cover generic transport choice, stdout purity, rate limiting, caching, K8s deployment, or lazy-auth — those live in `transport-and-ops.md`. This file is strictly about platform-shaped decisions.

---

## 1. On Cloudflare Workers, Use `McpAgent` for Stateful, `createMcpHandler` for Stateless

The Cloudflare MCP stack has two distinct primitives. Pick based on whether each client needs durable per-session state.

- **`McpAgent`** (in `agents` package) — binds every MCP client to a dedicated Durable Object instance. State survives across requests, across hibernation, and across region failovers. Use when you need per-user memory, long-running conversations, or resumable tool calls.
- **`createMcpHandler`** (in `@modelcontextprotocol/cloudflare`) — plain Workers handler. No DO, no session memory, no hibernation. Use for tools that are fully idempotent and stateless.

```typescript
import { McpAgent } from "agents/mcp";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

export class MyMCP extends McpAgent<Env, State> {
  server = new McpServer({ name: "my-mcp", version: "1.0.0" });

  async init() {
    this.server.tool("ping", {}, async () => ({
      content: [{ type: "text", text: `pong ${this.state.counter ?? 0}` }],
    }));
  }
}

export default {
  fetch(req: Request, env: Env, ctx: ExecutionContext) {
    return MyMCP.serve("/mcp").fetch(req, env, ctx);
  },
};
```

`MyMCP.serve("/mcp")` serves Streamable HTTP. `MyMCP.serveSSE("/sse")` exists for legacy clients but is deprecated. DO NOT mount both unless you explicitly need backward compatibility.

**Source:** [developers.cloudflare.com/agents/guides/remote-mcp-server/](https://developers.cloudflare.com/agents/guides/remote-mcp-server/) (accessed 2026-04); [developers.cloudflare.com/agents/api-reference/mcp-agent-api/](https://developers.cloudflare.com/agents/api-reference/mcp-agent-api/) (accessed 2026-04)

---

## 2. Use Durable Object WebSocket Hibernation to Stop Paying for Idle MCP Sessions

Durable Objects charge per GB-second of wall-clock time they are in memory. A chatty MCP session that waits 10 minutes between tool calls bills for those 10 minutes unless you hibernate.

Hibernation evicts the DO from memory while keeping the WebSocket connection open. When the next message arrives, the runtime rehydrates the DO and calls `deserializeAttachment()` to restore per-connection state. Billing pauses during the idle window.

```typescript
export class MyMCP extends McpAgent<Env, State> {
  async init() {
    // Opt the WS into hibernation instead of using addEventListener("message")
    this.ctx.acceptWebSocket(ws, ["session-tag"]);
    ws.serializeAttachment({ clientId: "abc", scopes: ["read", "write"] });
  }

  async webSocketMessage(ws: WebSocket, msg: string) {
    const state = ws.deserializeAttachment(); // Restored after rehydration
    // handle MCP frame...
  }
}
```

**Footgun:** `serializeAttachment()` has a **2,048-byte hard cap**. Anything larger goes in SQLite storage (`this.ctx.storage.sql`), not the attachment.

**Billing delta:** A session with 60s of active work and 10min of idle per hour on a non-hibernating DO bills ~11× the compute of the same session on a hibernating DO.

**Source:** [developers.cloudflare.com/durable-objects/best-practices/websockets/](https://developers.cloudflare.com/durable-objects/best-practices/websockets/) (compatibility date 2026-04-07); [developers.cloudflare.com/durable-objects/platform/pricing/](https://developers.cloudflare.com/durable-objects/platform/pricing/) (accessed 2026-04)

---

## 3. Cloudflare Workers CPU Time is 30s by Default — Opt Into 5 Minutes for Long Tools

Workers measure **CPU time**, not wall-clock time. I/O waits (fetch, DO storage, D1 queries) do not count. But a synchronous hot loop or CPU-bound tool burns the budget fast.

- **Default:** 30,000 ms CPU per invocation.
- **Maximum:** 300,000 ms (5 min) — requires explicit opt-in in `wrangler.toml`.
- **There is no wall-clock limit.** A Worker can sit in `await fetch()` for hours if the upstream supports it.

```toml
# wrangler.toml
name = "my-mcp-server"
main = "src/index.ts"
compatibility_date = "2026-04-07"

[limits]
cpu_ms = 300000   # opt into 5 min CPU
```

Set the lowest value your real tools need. Lower `cpu_ms` caps your bill against runaway loops.

**Source:** [developers.cloudflare.com/changelog/post/2025-03-25-higher-cpu-limits/](https://developers.cloudflare.com/changelog/post/2025-03-25-higher-cpu-limits/) (2025-03-25); [developers.cloudflare.com/workers/platform/limits/](https://developers.cloudflare.com/workers/platform/limits/) (accessed 2026-04)

---

## 4. For Regulated Workloads on Cloudflare, Bind the McpAgent to the FedRAMP Jurisdiction

Cloudflare DOs support jurisdictional binding. `jurisdiction: "fedramp"` pins the DO — and every byte of SQLite state it owns — to Cloudflare's FedRAMP Moderate data plane. `jurisdiction: "eu"` pins to EU for GDPR residency.

```typescript
// wrangler.toml
[[durable_objects.bindings]]
name = "MCP_OBJECT"
class_name = "MyMCP"
jurisdiction = "fedramp"

// Code — FedRAMP namespaces never cross into non-FedRAMP regions
const id = env.MCP_OBJECT.jurisdiction("fedramp").idFromName(userId);
```

**Source:** [developers.cloudflare.com/durable-objects/reference/data-location/](https://developers.cloudflare.com/durable-objects/reference/data-location/) (accessed 2026-04)

---

## 5. Wrap McpAgent in `workers-oauth-provider` for Full OAuth 2.1 Without a Separate Auth Server

Cloudflare's `workers-oauth-provider` is a first-party library that gives you a conforming OAuth 2.1 authorization server inside the same Worker — Dynamic Client Registration (RFC 7591), PKCE, token introspection, and `tokenExchangeCallback` for upstream federation — so you do not need Auth0/WorkOS/Stytch/Clerk to ship a remote MCP with auth.

```typescript
import OAuthProvider from "@cloudflare/workers-oauth-provider";

export default new OAuthProvider({
  apiRoute: "/mcp",
  apiHandler: MyMCP.serve("/mcp"),
  defaultHandler: authUiHandler,        // login page, consent screen
  authorizeEndpoint: "/authorize",
  tokenEndpoint: "/token",
  clientRegistrationEndpoint: "/register",
  tokenExchangeCallback: async (token, ctx) => {
    // Federate to GitHub/Google/Slack/Stytch/Auth0/WorkOS/Cloudflare Access
    return { accessToken: await exchangeWithUpstream(token), ...token };
  },
});
```

Integrates natively with GitHub, Google, Slack, Stytch, Auth0, WorkOS, and Cloudflare Access.

**Source:** [github.com/cloudflare/workers-oauth-provider](https://github.com/cloudflare/workers-oauth-provider) v0.4.0 (2026-03-31); [blog.cloudflare.com/building-ai-agents-with-mcp-authn-authz-and-durable-objects](https://blog.cloudflare.com/building-ai-agents-with-mcp-authn-authz-and-durable-objects) (accessed 2026-04)

---

## 6. On Vercel, Enable Fluid Compute Explicitly — Otherwise You Get 300s Max

The `@vercel/mcp-adapter` supports both stateless and stateful (Redis-backed) MCP servers, but hits a hard wall on execution duration. The cap depends on plan **and** whether Fluid Compute is enabled.

| Plan | Default max | Fluid Compute max |
|---|---|---|
| Hobby | 60s (quickstart default) | 300s |
| Pro | 60s | **800s** |
| Enterprise | 60s | **800s** |

The `@vercel/mcp-adapter` quickstart sets `maxDuration: 60`. Long-running MCP tools (migrations, batch jobs, AI inference chains) silently 504 with `FUNCTION_INVOCATION_TIMEOUT` unless you override.

```typescript
// app/api/[transport]/route.ts
import { createMcpHandler } from "@vercel/mcp-adapter";

const handler = createMcpHandler(/* ... */);

export const maxDuration = 800; // Override quickstart default — requires Fluid Compute ON
export { handler as GET, handler as POST };
```

Enable Fluid Compute in **Project Settings → Functions → Fluid Compute**. Without it, `maxDuration: 800` silently caps at 300s.

**Source:** [vercel.com/blog/building-efficient-mcp-servers](https://vercel.com/blog/building-efficient-mcp-servers) (2025-06-12); [vercel.com/docs/functions/limitations](https://vercel.com/docs/functions/limitations) (2026-02-24); [github.com/vercel/mcp-adapter](https://github.com/vercel/mcp-adapter) v1.1.0 (2026-03-24)

---

## 7. Vercel Caps Response Bodies at 4.5 MB — Offload Large Blobs to R2/S3/Blob

Vercel enforces a **4.5 MB hard cap** on function response bodies. Exceeding it returns `413 FUNCTION_PAYLOAD_TOO_LARGE`. This kills any MCP tool that returns screenshots, PDF exports, parsed CSVs, or embeddings over ~300k tokens.

**Fix:** Stream the artifact to external storage inside the tool, return a short-lived signed URL in the MCP response.

```typescript
server.tool("export_report", { format: z.enum(["pdf", "csv"]) }, async ({ format }) => {
  const blob = await renderReport(format);             // could be 50 MB
  const { url } = await put(`reports/${nanoid()}.${format}`, blob, {
    access: "public",
    token: process.env.BLOB_READ_WRITE_TOKEN,
  });
  return {
    content: [{ type: "text", text: `Report ready: ${url} (expires in 1 hour)` }],
  };
});
```

Use Vercel Blob, Cloudflare R2, or S3 with 1-hour presigned URLs. Never try to chunk a 4.5+ MB response through MCP content blocks — the cap applies at the HTTP layer before MCP framing.

**Source:** [vercel.com/docs/functions/limitations](https://vercel.com/docs/functions/limitations) (2026-02-24)

---

## 8. Smithery Requires `startCommand.type: http` for Container Deployments

Smithery is a registry + hosted gateway + CLI for MCP servers. Its `smithery.yaml` manifest distinguishes two runtimes, and mismatching `runtime` with `startCommand.type` silently fails at deploy time.

```yaml
# smithery.yaml — container runtime
runtime: container
build:
  dockerfile: Dockerfile
  dockerBuildPath: .
startCommand:
  type: http            # REQUIRED for container runtime
  configSchema:
    type: object
    required: ["TAVILY_API_KEY"]
    properties:
      TAVILY_API_KEY:
        type: string
        description: "Tavily API key from https://tavily.com"
  exampleConfig:
    TAVILY_API_KEY: "tvly-..."
```

```yaml
# smithery.yaml — stdio runtime (JS bundle only)
runtime: stdio
startCommand:
  type: stdio
  commandFunction: |-
    (config) => ({
      command: "node",
      args: ["dist/index.js"],
      env: { TAVILY_API_KEY: config.TAVILY_API_KEY }
    })
```

- `runtime: container` → must use `type: http`.
- `runtime: stdio` → must use `type: stdio` with a JS `commandFunction` — no Docker, no Python, no Go.

**Source:** [smithery.ai/docs/build](https://smithery.ai/docs/build) (accessed 2026-04); [github.com/tavily-ai/tavily-mcp/blob/main/smithery.yaml](https://github.com/tavily-ai/tavily-mcp/blob/main/smithery.yaml); [github.com/blockscout/mcp-server/blob/main/smithery.yaml](https://github.com/blockscout/mcp-server/blob/main/smithery.yaml)

---

## 9. Smithery `configSchema` Auto-Renders the Connect UI — Make Required Fields Explicit

Smithery Connect reads your `configSchema` (JSON Schema Draft-7) and builds the user-facing form from it. `required` becomes required inputs, `description` becomes help text, `format: password` masks the field.

```yaml
configSchema:
  type: object
  required: ["API_KEY", "WORKSPACE_ID"]
  properties:
    API_KEY: { type: string, format: password, description: "Get your key at https://app.example.com/settings/api" }
    WORKSPACE_ID: { type: string, description: "UUID of the workspace" }
    DEBUG: { type: boolean, default: false }
```

Optional fields without `default` arrive as `undefined` — your server must tolerate missing config. Publish with `smithery mcp publish <url> -n myorg/my-server` after `smithery auth login`.

**Source:** [smithery.ai/docs/build](https://smithery.ai/docs/build) (accessed 2026-04); [github.com/smithery-ai/cli](https://github.com/smithery-ai/cli) v4.8.0 (2026-04-12)

---

## 10. AWS Lambda: Set `AWS_LWA_INVOKE_MODE=response_stream` for Streamable HTTP

MCP's Streamable HTTP transport requires the server to stream responses. Plain Lambda function URLs buffer the full response — incompatible. The fix is the **Lambda Web Adapter (LWA)** with response streaming enabled.

```dockerfile
FROM public.ecr.aws/lambda/nodejs:20
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter
ENV AWS_LWA_INVOKE_MODE=response_stream
ENV AWS_LWA_ASYNC_INIT=true
ENV PORT=8080
COPY dist/ ${LAMBDA_TASK_ROOT}/
CMD ["index.handler"]
```

Runtime constraints to internalize:

| Limit | Value | Consequence |
|---|---|---|
| Lambda timeout | 15 min (900s) **hard** | No override exists |
| Streamed response | 200 MB max | 6 MB buffered fallback |
| Bandwidth | Uncapped first 6 MB, then **2 MB/s** | Large blobs throttle hard |
| Init timeout | 10s default | `AWS_LWA_ASYNC_INIT=true` defers blocking work |

Node.js **managed** runtime gained response streaming support on **2025-04-22**. Python still requires the container-image workaround.

**Source:** [github.com/aws/aws-lambda-web-adapter](https://github.com/aws/aws-lambda-web-adapter) (accessed 2026-04); [docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html](https://docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html) (accessed 2026-04); [github.com/aarora79/streamable-mcp-serverless](https://github.com/aarora79/streamable-mcp-serverless)

---

## 11. Lambda's 15-Minute Wall Forces SQS + Webhook for Long-Running MCP Tools

A tool that might take longer than 15 min (full-repo indexing, transcoding, multi-agent batch jobs) cannot run inline on Lambda. The pattern: Lambda receives the `tool_call`, enqueues to SQS with a `jobId`, and returns **immediately** with `{ jobId, status: "queued" }`. A separate SQS-triggered worker (Fargate/ECS/another Lambda) does the work and POSTs completion via webhook — or the agent polls a `get_job_status({ jobId })` tool.

```typescript
server.tool("index_repository", { repo_url: z.string() }, async ({ repo_url }) => {
  const jobId = crypto.randomUUID();
  await sqs.send(new SendMessageCommand({
    QueueUrl: process.env.INDEX_QUEUE,
    MessageBody: JSON.stringify({ jobId, repo_url }),
  }));
  return { content: [{ type: "text", text: JSON.stringify({
    jobId, status: "queued", poll_tool: "get_index_status", estimated_seconds: 180,
  })}] };
});
```

The MCP session never blocks on the long job. Mandatory on Lambda, useful everywhere else.

**Source:** [docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html](https://docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html) (accessed 2026-04); [github.com/aarora79/streamable-mcp-serverless](https://github.com/aarora79/streamable-mcp-serverless)

---

## 12. GCP Cloud Run Has the Longest HTTP Timeout of Any Managed Platform — 60 Minutes

Cloud Run caps request duration at 3,600 seconds (60 min), default 300s. This is **double** Vercel Enterprise's 800s and **4× Lambda's** 900s. When you need one managed platform that can run a single MCP tool call for close to an hour, Cloud Run is the answer.

```bash
gcloud run deploy my-mcp \
  --source . \
  --region us-central1 \
  --timeout 3600 \
  --no-allow-unauthenticated \
  --port 8080
```

Cloud Run is also stateless by default; sticky sessions require `--session-affinity` and externalized state (Firestore or Memorystore for Redis). GPU is GA for Cloud Run as of mid-2025 — viable for Python/ML MCP servers that need sub-60-min wall-clock bursts.

**Source:** [cloud.google.com/blog/topics/developers-practitioners/build-and-deploy-a-remote-mcp-server-to-google-cloud-run-in-under-10-minutes](https://cloud.google.com/blog/topics/developers-practitioners/build-and-deploy-a-remote-mcp-server-to-google-cloud-run-in-under-10-minutes) (2025-06-17); [cloud.google.com/run/docs/configuring/request-timeout](https://cloud.google.com/run/docs/configuring/request-timeout) (accessed 2026-04)

---

## 13. Cloud Run MCP Servers Must Bind `host="0.0.0.0"` and Use `--no-allow-unauthenticated`

Two Cloud Run footguns kill first-time MCP deploys:

1. **Binding to `127.0.0.1`** — Cloud Run routes external traffic to the container; localhost is invisible to the proxy. Bind `0.0.0.0:${PORT}` with `PORT` from env (default 8080).
2. **Leaving auth off** — `--allow-unauthenticated` exposes MCP to the public internet. Use `--no-allow-unauthenticated` + `roles/run.invoker` IAM grants.

```python
import os
from fastmcp import FastMCP
mcp = FastMCP("my-mcp")
mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
```

Local testing against a protected deployment: `gcloud run services proxy my-mcp --port=8080` — MCP client hits `localhost:8080` with local gcloud credentials.

**Source:** [cloud.google.com/blog/topics/developers-practitioners/build-and-deploy-a-remote-mcp-server-to-google-cloud-run-in-under-10-minutes](https://cloud.google.com/blog/topics/developers-practitioners/build-and-deploy-a-remote-mcp-server-to-google-cloud-run-in-under-10-minutes) (2025-06-17)

---

## 14. Azure Container Apps Offers Two MCP Modes — Standalone and Dynamic Sessions

Azure Container Apps (ACA) has a unique second mode: **dynamic sessions**. Instead of hosting *your* MCP server, Azure runs the *tool code* inside Hyper-V isolated per-session sandboxes. Pattern applies when tools need to execute untrusted or user-supplied code.

| Mode | You deploy | Per-session isolation | Use for |
|---|---|---|---|
| Standalone | Your MCP server container | No (standard ACA replicas) | Normal remote MCP |
| Dynamic sessions | The tool *code* | Yes — Hyper-V sandbox per session | Code-execution-as-a-service, untrusted workloads, multi-tenant with hard isolation |

Standalone mode uses Entra ID built-in auth. Dynamic sessions use API keys scoped per session pool.

ACA docs **explicitly recommend `min-replica: 1`** for interactive MCP servers — scale-to-zero cold starts (5-15s) break interactive agent loops. The `ingress.transport: auto` default upgrades to HTTP/2 when clients negotiate.

```bash
az containerapp create \
  --name my-mcp --resource-group rg \
  --image myregistry/my-mcp:latest \
  --ingress external --target-port 8080 \
  --min-replicas 1 --max-replicas 10
```

**Source:** [learn.microsoft.com/en-us/azure/container-apps/mcp-overview](https://learn.microsoft.com/en-us/azure/container-apps/mcp-overview) (2026-02-27)

---

## 15. Fly.io `fly mcp launch` Wires Bearer Tokens to Both Server and Client

`flyctl` 0.3.125+ ships a launcher that provisions a Fly Machine, sets a random bearer token as a secret, and patches the local MCP client config (Claude Desktop or Cursor) to send that token.

```bash
fly mcp launch --claude --server myapp --secret API_KEY=sk-...
```

Server gets `FLY_MCP_TOKEN` in env with the adapter enforcing `Authorization: Bearer ${FLY_MCP_TOKEN}`. Claude Desktop config is patched with `{"headers": {"Authorization": "Bearer ..."}}`.

**Footgun:** scale-to-zero (`auto_stop_machines = true`) + in-memory sessions are incompatible — first request after sleep gets a fresh Machine and loses session state. Externalize to Redis, Fly Postgres, or LiteFS. Pricing floor: `shared-cpu-1x @ 256MB` $2.02/mo; `performance-1x @ 2GB` $32.19/mo.

**Source:** [fly.io/docs/blueprints/remote-mcp-servers/](https://fly.io/docs/blueprints/remote-mcp-servers/); [fly.io/blog/mcp-launch/](https://fly.io/blog/mcp-launch/); [fly.io/docs/about/pricing/](https://fly.io/docs/about/pricing/) (all accessed 2026-04)

---

## 16. Deno Deploy Blocks `Deno.connect` to Port 443 — Use `Deno.connectTls`

Deno Deploy's sandbox blocks raw TCP connections to port 443 to prevent unencrypted writes to what should be a TLS port. If your MCP server opens its own sockets (e.g., to speak a custom wire protocol to a backend on 443), this fails at runtime.

```typescript
// ❌ Fails on Deno Deploy
const conn = await Deno.connect({ hostname: "api.example.com", port: 443 });

// ✅ Works
const conn = await Deno.connectTls({ hostname: "api.example.com", port: 443 });
```

Other Deno Deploy quirks for MCP:

- **Memory cap:** 512 MB per deployment, 1 GB total across deployments on free tier.
- **Binding `0.0.0.0`** requires `--dnsRebinding` plus an `MCP_ALLOWED_HOSTS` allowlist; wildcard `*` is rejected.
- **SSRF guard:** `Deno.connect` and `fetch()` default-block private IPs (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), localhost, and `.internal` TLDs.
- **SSE vs HTTP:** Set `MCP_JSON_RESPONSE=true` to force JSON-only responses and disable SSE framing.
- **Auth:** `MCP_HTTP_BEARER_TOKEN` configures the bearer check. Set `MCP_REQUIRE_HTTP_AUTH=true` and the server refuses to start if the token env is unset — prevents accidental public deployments.

**Source:** [github.com/phughesmcr/deno-mcp-template](https://github.com/phughesmcr/deno-mcp-template) v0.7.0 (2026-03-29); [docs.deno.com/deploy/pricing_and_limits](https://docs.deno.com/deploy/pricing_and_limits) (2025-10-07)

---

## 17. Modal MCP Servers Must Set `stateless_http=True`

Modal's serverless functions are ephemeral — containers scale to zero, scale cold, and move between hosts. Per-session DO-style state is not supported. FastMCP must run in stateless mode.

```python
import modal
from fastmcp import FastMCP
from fastapi import FastAPI

app = modal.App("mcp-server")
image = modal.Image.debian_slim().pip_install("fastmcp", "fastapi")
mcp = FastMCP("my-mcp", stateless_http=True)

@mcp.tool()
async def analyze(code: str) -> str: return f"lines: {len(code.splitlines())}"

web_app = FastAPI()
web_app.mount("/mcp", mcp.streamable_http_app())

@app.function(image=image, gpu="H100", timeout=600)
@modal.asgi_app()
def fastapi_app(): return web_app
```

Modal's edge is GPU economics: H100 $0.001097/sec, A10 $0.000306/sec, CPU $0.0000131/core-sec, Sandbox (code-exec) $0.00003942/core-sec. Starter tier: $30/mo free credits, 100 container / 10 GPU concurrency.

**Source:** [modal.com/docs/examples/mcp_server_stateless](https://modal.com/docs/examples/mcp_server_stateless) (accessed 2026-04); [modal.com/pricing](https://modal.com/pricing) (accessed 2026-04)

---

## 18. Render's MCP API Key is Account-Wide — Treat It Like a Root Token

Render's own MCP server (for managing Render infrastructure via an agent) uses an API key that is **broadly scoped across every workspace the key owner belongs to**. There is no per-workspace or per-service scoping primitive. A single leaked key = full account compromise.

Rules of engagement:

- Never commit the Render MCP key to any repo or pass it to an untrusted agent.
- Rotate the key when moving between workspaces or organizations.
- Prefer short-lived, human-in-the-loop agent sessions for Render MCP; do not run it in unattended CI.

For your *own* MCP servers hosted on Render (not Render's MCP API), use the standard Render web service + persistent disk pattern. Render gives you a managed HTTPS endpoint, auto-scaling, and a free tier; no MCP-specific quirks apply.

**Source:** [render.com/docs/mcp-server](https://render.com/docs/mcp-server) (accessed 2026-04); [github.com/render-oss/render-mcp-server](https://github.com/render-oss/render-mcp-server) v0.3.0 (2026-01-14)

---

## 19. Koyeb & Northflank: Scale-to-Zero Remote MCP with `sessionIdGenerator: undefined`

Both platforms offer scale-to-zero container hosting and published Streamable HTTP MCP recipes. Run the transport in **stateless mode** so cold starts don't strand sessions.

```typescript
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: undefined,   // Stateless — no server-issued session IDs
});
await server.connect(transport);
```

```bash
koyeb deploy . my-mcp/main --git github.com/me/my-mcp-server \
  --ports 8080:http --routes /:8080 --min-scale 0 --max-scale 5 --instance-type free
```

Northflank uses a Combined Service with HTTP port 8080, optional `/health`, runtime env vars. Both give `.koyeb.app` / `.northflank.app` hostnames. If you need state, either set min-scale 1 or back with Redis/Upstash.

**Source:** [koyeb.com/tutorials/deploy-remote-mcp-servers-to-koyeb-using-streamable-http-transport](https://www.koyeb.com/tutorials/deploy-remote-mcp-servers-to-koyeb-using-streamable-http-transport) (2025-05-05); [northflank.com/blog/how-to-build-and-deploy-a-model-context-protocol-mcp-server](https://northflank.com/blog/how-to-build-and-deploy-a-model-context-protocol-mcp-server) (2025-08-26)

---

## 20. Composio Isn't Free Infrastructure — Price Against the Auth Value, Not the Compute

Composio bundles OAuth catalog + auth server + tool proxy for ~250 SaaS APIs. Pricing is per-call: Free 20K/mo, Starter $29/mo for 200K, Pro $229/mo for 2M.

For 100K calls/mo, Composio is $29/mo; the same traffic on raw Lambda is ~$1/mo — **~29× more on pure compute math**. The delta buys managed OAuth for Gmail/Slack/Notion/Linear/GitHub, tool catalog + schemas, token rotation, request logging, shared auth UI.

Decision rule: Composio pays off when you need ≥5 third-party OAuth integrations; raw Lambda + `workers-oauth-provider` wins for 1-2 integrations or custom auth.

**Source:** [composio.dev/pricing](https://composio.dev/pricing) (accessed 2026-04)

---

## Platform Profiles (Compact Reference)

| Platform | Session primitive | Streamable HTTP | Max duration | Response cap | Auth | Best for |
|---|---|---|---|---|---|---|
| **Cloudflare Workers + McpAgent** | Durable Object per session + SQLite + hibernation | Native via `MyMCP.serve()` | 5 min CPU opt-in; no wall-clock limit | 100 MB (Free/Pro), 500 MB (Ent) | `workers-oauth-provider` (OAuth 2.1 + DCR) | Multi-tenant SaaS, personal CLI |
| **Vercel Fluid Compute** | BYO (Redis for resumability) | Native via `@vercel/mcp-adapter` | 300s Hobby / 800s Pro+Ent (Fluid on) | **4.5 MB hard** | BYO middleware | Team B2B, serverless-first |
| **Smithery.ai** | Managed per-server | Native when `type: http` | Container runtime limits | Container runtime limits | `configSchema` + Smithery Connect | Marketplace / public servers |
| **Modal** | None (stateless only) | Via FastMCP `streamable_http_app()` + FastAPI | Function `timeout` param | Function memory | BYO | Python/ML, GPU workloads |
| **Fly.io Machines** | Machine-local volumes | Native; machine-level | No enforced HTTP timeout | No enforced cap | `fly mcp launch` bearer token | Stateful team-internal |
| **Railway** | Service volume, 1 replica default | Native | No hard HTTP cap | Build 10 min Free / 20 min Trial | BYO | Prototypes, budget-constrained |
| **Render** | Persistent disk per service | Native | No hard cap | No hard cap | BYO (Render MCP key = account-wide) | Simple web-service MCP |
| **AWS Lambda + LWA** | None inline; SQS + webhook for long | `AWS_LWA_INVOKE_MODE=response_stream` | **15 min hard** | 200 MB streamed / 6 MB buffered; 2 MB/s past 6 MB | Cognito + JWT authorizer | Enterprise VPC, event-driven |
| **Azure Container Apps** | Standalone + Dynamic Sessions (Hyper-V) | Native (ingress `transport: auto`) | No hard cap | No hard cap | Entra ID built-in | Regulated enterprise, code-exec tools |
| **GCP Cloud Run** | Session affinity flag; state externalized | Native | **60 min (3600s)** | No hard cap | `--no-allow-unauthenticated` + IAM | Long-running single-call tools |
| **Deno Deploy** | Deno KV + event store | Via `MCP_JSON_RESPONSE=true` | Deploy-tier dependent | 512 MB mem / 1 GB deploy | `MCP_HTTP_BEARER_TOKEN` | TypeScript-native, KV-backed |
| **Koyeb / Northflank** | Scale-to-zero stateless | Native; `sessionIdGenerator: undefined` | No hard cap | No hard cap | BYO | Scale-to-zero remote MCP |

---

## Picker Rubric: Workload → Platform

Scores are 0-10 for the specified workload. **Bold** = top pick(s) for the row.

| Workload | CF Workers | Vercel | Smithery | Modal | Fly | Railway | Render | Lambda | ACA | Cloud Run | Deno |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Personal CLI tool | **10** | 7 | 8 | 6 | 7 | 7 | 7 | 5 | 5 | 7 | 8 |
| Team B2B internal | **9** | 8 | 7 | 6 | **9** | 8 | 7 | 7 | 8 | 8 | 7 |
| Multi-tenant SaaS | **10** | 8 | 6 | 5 | 8 | 6 | 6 | 8 | **9** | 8 | 6 |
| Marketplace / public | 8 | 7 | **10** | 6 | 7 | 6 | 6 | 6 | 6 | 7 | 6 |
| Regulated enterprise | **9** (FedRAMP DO) | 7 | 4 | 5 | 7 | 5 | 5 | **9** (VPC) | **10** (Entra + Hyper-V) | 8 | 5 |
| GPU / ML-heavy | 4 | 5 | 3 | **10** | 7 | 6 | 6 | 7 | 7 | 8 | 3 |
| Long-running (>5 min) | 7 | 7 | 4 | 8 | **9** (no cap) | 7 | 7 | 6 | 8 | **10** (60 min) | 5 |

**Headline recommendations:**

| Workload | Primary | Why | Backup |
|---|---|---|---|
| Personal CLI | Cloudflare Workers + McpAgent | Free DO tier (100K req/day), built-in OAuth, hibernation ≈ $0 idle | Deno Deploy |
| Team B2B internal | Cloudflare Workers **or** Fly Machines | Workers for stateless/light; Fly for stateful/container-heavy | Railway |
| Multi-tenant SaaS | Cloudflare Workers McpAgent | Per-session DO + SQLite + hibernation maps 1:1 to MCP session | Azure ACA |
| Marketplace / public | Smithery.ai container runtime | Purpose-built hosting + discovery + OAuth/configSchema | CF Workers + custom domain |
| Regulated enterprise | Azure ACA **or** CF Workers `jurisdiction: "fedramp"` | Entra ID + Hyper-V isolation; CF has FedRAMP DOs | AWS Lambda in VPC |
| Python / ML GPU | Modal | Serverless GPU at $0.001097/sec H100; native FastMCP example | Cloud Run GPU |
| Long-running (>5 min) | GCP Cloud Run | 60-minute HTTP timeout — highest of any managed platform | Fly Machines (no enforced cap) |

---

## Cross-Cutting Decision Heuristics

- **Scale-to-zero + in-memory sessions is always broken.** If you want scale-to-zero (Fly, Koyeb, Cloud Run, ACA), externalize session state to Redis/KV/DO/Firestore, or set min-replica ≥ 1.
- **4.5 MB response caps and 15-min timeouts are platform constants, not bugs.** Design tools to either fit the envelope or offload via signed URL + polling. See `error-handling.md` for the polling-tool pattern.
- **Session state = per-session DO or external store.** Do not reach for "sticky load balancer" on Cloud Run / ACA / Fly if you also want autoscaling — session affinity and HPA fight each other.
- **OAuth 2.1 is cheap on Cloudflare, expensive everywhere else.** `workers-oauth-provider` is the only first-party, DCR-capable, PKCE-capable OAuth server bundled with the runtime. On Vercel/Lambda/Cloud Run, you're wiring Clerk/Auth0/Stytch/WorkOS by hand.
- **Price by dominant axis.** GPU workloads: Modal wins by a wide margin. Always-on stateful: Fly. Bursty stateless: Cloudflare/Vercel. Long single tool calls: Cloud Run. Regulated: ACA or CF FedRAMP.
