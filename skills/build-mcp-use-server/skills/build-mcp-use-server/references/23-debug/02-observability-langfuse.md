# Observability — Langfuse Integration

Langfuse is the recommended observability backend for production mcp-use servers. It captures structured traces of every tool call — inputs, outputs, latency, errors, token costs (for sampling tools) — in a queryable UI.

mcp-use ships first-class Langfuse wiring via `mcp-use/observability`.

---

## What gets exported

| Trace surface | Contents |
|---|---|
| Session traces | Session ID, start/end timestamps, total tool calls, duration |
| Tool call spans | Tool name, args, result, duration, error (if any) |
| Sampling spans | Model, prompt, completion, token usage, cost |
| Elicitation spans | Schema, user response, latency |
| HTTP transport spans | Method, path, status, duration |
| User identity (when available) | OAuth `sub` claim, session metadata |

Argument and result payloads are exported to Langfuse — be deliberate about what enters tool args. Use `_meta` (not `structuredContent`) for client-only fields you don't want surfaced in observability.

---

## Wiring

### 1. Set env vars

```bash
export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_SECRET_KEY=sk-lf-...
export LANGFUSE_HOST=https://cloud.langfuse.com   # or self-hosted URL
```

### 2. Enable observability on the server

```typescript
import { MCPServer } from "mcp-use/server";
import { langfuseHandler } from "mcp-use/observability";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  observability: {
    handler: langfuseHandler(),  // returns BaseCallbackHandler | null
  },
});
```

If `LANGFUSE_*` env vars are missing, `langfuseHandler()` returns `null` and observability silently no-ops. This makes the same code safe in dev (no creds, no traces) and prod (creds present, traces flow).

### 3. Use the manager directly for custom spans

```typescript
import { createManager, getDefaultManager } from "mcp-use/observability";

const manager = createManager({ observe: true });   // explicit instance
const defaultManager = getDefaultManager();          // process-wide singleton

// Inside a handler, add custom spans
server.tool({ name: "fetch-user", schema }, async ({ id }, ctx) => {
  const span = defaultManager.startSpan("db.query", { userId: id });
  const user = await db.users.findById(id);
  span.end({ found: !!user });
  return object(user);
});
```

### 4. Direct Langfuse client (for one-off events)

```typescript
import { langfuseClient } from "mcp-use/observability";

const client = langfuseClient();
if (client) {
  client.event({
    name: "custom-business-event",
    metadata: { plan: "pro", action: "upgrade" },
  });
}
```

---

## Trace shape in Langfuse UI

Each MCP session produces one trace. Each tool call is a span inside that trace.

```
Trace: session-abc123
├─ Span: tools/call greet (12ms)
│  ├─ Input: { name: "World" }
│  └─ Output: { content: [{ type: "text", text: "Hello, World!" }] }
├─ Span: tools/call get-weather (340ms)
│  ├─ Input: { city: "Tokyo" }
│  ├─ Span: db.query (45ms)
│  └─ Output: { content: [...], structuredContent: {...} }
└─ Span: sampling.create (1.2s)
   ├─ Model: claude-3-5-sonnet
   ├─ Tokens: { input: 240, output: 180 }
   └─ Cost: $0.0045
```

---

## Filtering noise

Langfuse will trace everything by default. Two knobs to dial it back:

```typescript
import { createManager } from "mcp-use/observability";

const manager = createManager({
  observe: true,
  filters: {
    // Skip ping/pong and other low-value methods
    skipMethods: ["ping", "tools/list"],
    // Sample only 10% of traces in high-traffic prod
    sampleRate: 0.1,
  },
});
```

---

## Self-hosted vs cloud

| Setup | `LANGFUSE_HOST` |
|---|---|
| Langfuse Cloud (US) | `https://us.cloud.langfuse.com` |
| Langfuse Cloud (EU) | `https://cloud.langfuse.com` |
| Self-hosted | `https://langfuse.your-domain.com` |

For self-hosted, the wire protocol is identical — only the host URL changes. Self-host docs: [https://langfuse.com/docs/deployment/self-host](https://langfuse.com/docs/deployment/self-host).

---

## Verifying traces flow

1. Start the server with `LANGFUSE_*` env vars set.
2. Hit a tool from Inspector or curl.
3. Open Langfuse UI → **Traces** → newest trace should appear within ~10 seconds.
4. If it doesn't:

| Symptom | Fix |
|---|---|
| No trace in Langfuse UI | Verify keys; check server logs for `langfuse: failed to send` |
| Traces show but no spans | `observability.handler` not wired into MCPServer config |
| Sensitive data in traces | Move secrets out of tool args; use `_meta` for client-only fields |
| Cost showing $0 for sampling spans | Model not on Langfuse's pricing list — set custom price in project settings |

---

## Production checklist

- [ ] `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` in production secrets manager
- [ ] `LANGFUSE_HOST` set if self-hosted
- [ ] No PII in tool argument schemas (or PII redaction middleware in front)
- [ ] Sample rate set if traffic is high (`createManager({ filters: { sampleRate: 0.1 } })`)
- [ ] User identity propagated via OAuth `sub` for per-user filtering
- [ ] Dashboard saved for top tools by error rate + p95 latency

---

## Alternatives

mcp-use ships a `BaseCallbackHandler` interface compatible with LangChain — you can plug in any observability backend that implements it (LangSmith, OpenTelemetry exporters, custom). Langfuse is the recommended default; the interface is open.
