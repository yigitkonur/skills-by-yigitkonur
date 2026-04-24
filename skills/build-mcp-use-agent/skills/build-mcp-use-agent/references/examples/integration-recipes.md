# Integration Recipes

Examples of integrating MCPAgent with external frameworks and services. Each recipe is fully runnable with all imports included.

---

## 1. Vercel AI SDK — Next.js API Route with Streaming

Stream MCPAgent responses through a Next.js App Router API route using the Vercel AI SDK. This recipe shows the pattern used in mcp-use's own examples (see the `examples/` directory under `libraries/typescript/packages/mcp-use/` in the canonical [`mcp-use/mcp-use`](https://github.com/mcp-use/mcp-use) repo) — `streamEventsToAISDK` and `createReadableStreamFromGenerator` are exported directly from `mcp-use`. The frontend uses `useChat` from `@ai-sdk/react` (the legacy `'ai/react'` subpath was removed in AI SDK v5+).

> **AI SDK version note:** mcp-use's `examples/client/ai_sdk_example.ts` uses `LangChainAdapter.toDataStreamResponse(...)` imported from the `ai` package — that path works on AI SDK `4.x`. In AI SDK `5.x` and `6.x` (current), `LangChainAdapter` was removed; the equivalent is `toUIMessageStream` (from `@ai-sdk/langchain@^2`) wrapped in `createUIMessageStreamResponse` (from `ai@^6`). Both variants are shown below — pick the one matching your installed `ai` version.

---

### Variant A — AI SDK v6 + `@ai-sdk/langchain@^2` (current as of 2026)

```typescript
// Install: npm install ai@^6 @ai-sdk/react@^3 @ai-sdk/langchain@^2 mcp-use
// app/api/chat/route.ts
import { createUIMessageStreamResponse } from "ai";
import { toUIMessageStream } from "@ai-sdk/langchain";
import { MCPAgent, MCPClient } from "mcp-use";

export async function POST(req: Request) {
  const { messages } = await req.json();
  const lastMessage = messages[messages.length - 1]?.content ?? "";

  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp/data"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    client,
    maxSteps: 20,
  });

  try {
    // streamEvents() yields LangChain StreamEvent objects.
    // toUIMessageStream auto-converts them into the UI-message-chunk
    // protocol that @ai-sdk/react's useChat consumes.
    const events = agent.streamEvents({ prompt: lastMessage });
    return createUIMessageStreamResponse({ stream: toUIMessageStream(events) });
  } catch (error) {
    return new Response(
      JSON.stringify({ error: "Agent execution failed" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  } finally {
    await agent.close();
  }
}
```

### Variant B — AI SDK v4 + `LangChainAdapter` from `ai` (matches mcp-use's official example verbatim)

```typescript
// Install: npm install ai@^4 mcp-use
// app/api/chat/route.ts
import { LangChainAdapter } from "ai";
// streamEventsToAISDK and createReadableStreamFromGenerator are exported
// directly from mcp-use (see packages/mcp-use/src/agents/utils/ai_sdk.ts).
import {
  MCPAgent,
  MCPClient,
  streamEventsToAISDK,
  createReadableStreamFromGenerator,
} from "mcp-use";

export async function POST(req: Request) {
  const { messages } = await req.json();
  const lastMessage = messages[messages.length - 1]?.content ?? "";

  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp/data"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    client,
    maxSteps: 20,
  });

  try {
    const events = agent.streamEvents({ prompt: lastMessage });
    const textStream = streamEventsToAISDK(events);
    const readable = createReadableStreamFromGenerator(textStream);
    // Returns a Response in the data-stream protocol useChat understands.
    return LangChainAdapter.toDataStreamResponse(readable);
  } catch (error) {
    return new Response(
      JSON.stringify({ error: "Agent execution failed" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  } finally {
    await agent.close();
  }
}
```

> **About the text-stream path** — the `createTextStreamResponse({ textStream })` helper from `ai` is still exported in v6 and accepts a `ReadableStream<string>`, but it produces plain text suitable only for `useCompletion`. It is NOT consumed correctly by `useChat`, which expects the UI-message-chunk protocol. Use Variant A or B above for `useChat`-paired backends.

**Frontend usage with `useChat` (AI SDK v5+):**

```typescript
// Install: npm install @ai-sdk/react ai
// app/page.tsx
"use client";
import { useChat } from "@ai-sdk/react";

export default function ChatPage() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } =
    useChat({ api: "/api/chat" });

  return (
    <div>
      {messages.map((m) => (
        <div key={m.id}>
          <strong>{m.role}:</strong> {m.content}
        </div>
      ))}
      <form onSubmit={handleSubmit}>
        <input value={input} onChange={handleInputChange} />
        <button type="submit" disabled={isLoading}>
          Send
        </button>
      </form>
    </div>
  );
}
```

---

## 2. Langfuse Observability

Attach Langfuse tracing to every MCPAgent run for cost tracking, latency monitoring, and per-request filtering.

> **mcp-use auto-initializes a Langfuse handler from environment variables.** When `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are set (and `MCP_USE_LANGFUSE` is not `"false"`), mcp-use dynamically loads `langfuse-langchain` and registers a `LoggingCallbackHandler` through its internal `ObservabilityManager`. You do NOT need to pass `callbacks: [...]` manually for the common case. The recommended pattern is env vars + `agent.setMetadata()` + `agent.setTags()`. Pass a manual `CallbackHandler` only when you need per-request `traceId`/`userId` binding — and disable the auto-init first to avoid duplicate traces.

---

### Sub-recipe A — Zero-config auto-init (recommended default)

This matches the observability pattern shipped in mcp-use's own examples (canonical [`mcp-use/mcp-use`](https://github.com/mcp-use/mcp-use) repo, `libraries/typescript/packages/mcp-use/examples/`).

```typescript
// .env:
//   LANGFUSE_PUBLIC_KEY=pk-...
//   LANGFUSE_SECRET_KEY=sk-...
//   LANGFUSE_HOST=https://cloud.langfuse.com   # or your self-hosted URL
//   MCP_USE_LANGFUSE=true                       # optional; auto-init is on by default

import { config } from "dotenv";
import { Logger, MCPAgent, MCPClient } from "mcp-use";

config();

// Optional — see what env vars Langfuse will pick up.
Logger.setDebug(true);

async function main() {
  const client = new MCPClient({
    mcpServers: {
      everything: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-everything"],
      },
    },
  });

  // No callbacks needed — mcp-use auto-detects env vars and registers the handler.
  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    client,
    maxSteps: 15,
  });

  // Enrich every trace this agent emits.
  agent.setMetadata({
    feature: "web-search",
    costCenter: "product-team",
    environment: process.env.NODE_ENV ?? "development",
  });
  agent.setTags(["production", "web-search"]);

  try {
    const result = await agent.run({
      prompt: "Search for the latest TypeScript 5.6 features and summarize them",
      maxSteps: 15,
    });
    console.log("Result:", result);
  } finally {
    // In serverless, flush traces before the function exits.
    await agent.flush();
    await agent.close();
  }
}

main().catch(console.error);
```

### Sub-recipe B — Per-request manual handler (when you need `traceId`/`userId` binding)

Use this only when you need a deterministic `traceId` or `userId` scoped to a single run (e.g. correlating a trace with a specific HTTP request). To prevent double-tracing, you MUST disable the auto-init by setting `MCP_USE_LANGFUSE=false`.

```typescript
// Required env:
//   LANGFUSE_PUBLIC_KEY=pk-...
//   LANGFUSE_SECRET_KEY=sk-...
//   LANGFUSE_HOST=https://cloud.langfuse.com   # or your self-hosted URL
//   MCP_USE_LANGFUSE=false                      # disable ambient auto-init

import { CallbackHandler as LangfuseHandler } from "langfuse-langchain";
import { MCPAgent, MCPClient } from "mcp-use";
import { randomUUID } from "node:crypto";

function createLangfuseHandler(traceId: string, userId?: string) {
  return new LangfuseHandler({
    publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
    secretKey: process.env.LANGFUSE_SECRET_KEY!,
    // mcp-use reads LANGFUSE_HOST (with LANGFUSE_BASEURL — note: no underscore
    // between BASE and URL — as the only documented fallback). LANGFUSE_BASE_URL
    // is NOT a recognized env var.
    baseUrl: process.env.LANGFUSE_HOST ?? "https://cloud.langfuse.com",
    traceId,
    userId,
    sessionId: traceId,
    metadata: { environment: process.env.NODE_ENV ?? "development" },
  });
}

async function runTracedAgent(prompt: string, userId?: string) {
  const traceId = randomUUID();
  const langfuseHandler = createLangfuseHandler(traceId, userId);

  const client = new MCPClient({
    mcpServers: {
      // The Brave Search reference server lives under @modelcontextprotocol.
      // Note: as of late 2024 it is marked deprecated on npm — replace with
      // a community-maintained or self-hosted equivalent if it stops working.
      brave: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-brave-search"],
        env: { BRAVE_API_KEY: process.env.BRAVE_API_KEY! },
      },
    },
  });

  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    client,
    maxSteps: 15,
    callbacks: [langfuseHandler],   // explicit per-request handler
  });

  // Per-run metadata + tags for filtering.
  agent.setMetadata({
    traceId,
    userId: userId ?? "anonymous",
    feature: "web-search",
    costCenter: "product-team",
  });
  agent.setTags([
    "production",
    "web-search",
    `user:${userId ?? "anonymous"}`,
  ]);

  try {
    const result = await agent.run({ prompt, maxSteps: 15 });
    console.log(`[trace:${traceId}] Agent completed successfully`);
    return { result, traceId };
  } catch (error) {
    console.error(`[trace:${traceId}] Agent failed:`, error);
    throw error;
  } finally {
    await langfuseHandler.flushAsync();
    await agent.close();
  }
}

async function main() {
  const { result, traceId } = await runTracedAgent(
    "Search for the latest TypeScript 5.6 features and summarize them",
    "user-42"
  );
  console.log("Result:", result);
  console.log(`View trace: ${process.env.LANGFUSE_HOST ?? "https://cloud.langfuse.com"}/trace/${traceId}`);
}

main().catch(console.error);
```

**Dashboard tips:**

- Filter by tag `production` to see only live traffic.
- Use the `costCenter` metadata field to attribute spend.
- The `userId` on the handler links every span to a user timeline.
- Latency breakdown per tool call is automatic — each MCP tool invocation appears as a child span under the agent trace.
- Set `LANGFUSE_HOST` (not `LANGFUSE_BASE_URL`) to point at a self-hosted instance — e.g. `export LANGFUSE_HOST=https://langfuse.internal.example.com`. mcp-use reads `LANGFUSE_HOST` first and falls back to `LANGFUSE_BASEURL` (no underscore between `BASE` and `URL`).
- Set `MCP_USE_LANGFUSE=false` if you want only the manual per-request handler to run, with no ambient auto-init.

---

## 3. Express.js API Wrapper

A production-ready Express server that exposes MCPAgent behind a REST API. Includes request validation with Zod, SSE streaming, health checks, error middleware, and graceful shutdown.

---

```typescript
// server.ts
import express, { Request, Response, NextFunction } from "express";
import { z } from "zod";
import { MCPAgent, MCPClient } from "mcp-use";

const app = express();
app.use(express.json({ limit: "1mb" }));

// ---------- Request schemas ----------

const AgentRequestSchema = z.object({
  prompt: z.string().min(1).max(4000),
  maxSteps: z.number().int().min(1).max(50).optional().default(20),
  stream: z.boolean().optional().default(false),
});

type AgentRequest = z.infer<typeof AgentRequestSchema>;

// ---------- Shared MCP server config ----------

const MCP_SERVERS = {
  filesystem: {
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp/workspace"],
  },
};

// ---------- Health check ----------

app.get("/health", (_req, res) => {
  res.json({ status: "ok", uptime: process.uptime() });
});

// ---------- POST /api/agent — synchronous run ----------

app.post("/api/agent", async (req: Request, res: Response, next: NextFunction) => {
  const parsed = AgentRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.flatten() });
    return;
  }

  const { prompt, maxSteps, stream } = parsed.data;

  if (stream) {
    return handleStream(prompt, maxSteps, res, next);
  }

  const client = new MCPClient({ mcpServers: MCP_SERVERS });
  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    client,
    maxSteps,
    memoryEnabled: false,
  });

  try {
    const result = await agent.run({ prompt, maxSteps });
    res.json({ result });
  } catch (error) {
    next(error);
  } finally {
    await agent.close();
  }
});

// ---------- SSE streaming handler ----------

async function handleStream(
  prompt: string,
  maxSteps: number,
  res: Response,
  next: NextFunction
) {
  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
  });

  const client = new MCPClient({ mcpServers: MCP_SERVERS });
  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    client,
    maxSteps,
    memoryEnabled: false,
  });

  try {
    const events = agent.streamEvents({ prompt });

    for await (const event of events) {
      if (event.event === "on_chat_model_stream") {
        // chunk property may be 'text' or 'content' depending on LLM provider
        const text = event.data?.chunk?.text || event.data?.chunk?.content;
        if (typeof text === "string" && text.length > 0) {
          res.write(`data: ${JSON.stringify({ type: "token", text })}\n\n`);
        }
      }
      if (event.event === "on_tool_start") {
        res.write(
          `data: ${JSON.stringify({ type: "tool_start", name: event.name })}\n\n`
        );
      }
      if (event.event === "on_tool_end") {
        res.write(
          `data: ${JSON.stringify({ type: "tool_end", output: event.data?.output })}\n\n`
        );
      }
    }

    res.write(`data: ${JSON.stringify({ type: "done" })}\n\n`);
    res.end();
  } catch (error) {
    res.write(
      `data: ${JSON.stringify({ type: "error", message: String(error) })}\n\n`
    );
    res.end();
  } finally {
    await agent.close();
  }
}

// ---------- Error middleware ----------

app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  console.error("Unhandled error:", err);
  res.status(500).json({ error: "Internal server error" });
});

// ---------- Start server + graceful shutdown ----------

const PORT = parseInt(process.env.PORT ?? "3000", 10);
const server = app.listen(PORT, () => {
  console.log(`Agent API listening on :${PORT}`);
});

function shutdown(signal: string) {
  console.log(`\n${signal} received — shutting down gracefully`);
  server.close(() => {
    console.log("HTTP server closed");
    process.exit(0);
  });
  setTimeout(() => {
    console.error("Forced shutdown after timeout");
    process.exit(1);
  }, 10_000);
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
```

**Usage:**

```bash
# Synchronous call
curl -X POST http://localhost:3000/api/agent \
  -H "Content-Type: application/json" \
  -d '{"prompt": "List files in /tmp/workspace"}'

# Streaming call
curl -N -X POST http://localhost:3000/api/agent \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Summarize all markdown files", "stream": true}'
```

---

## 4. React Frontend + Agent Backend

A full-stack integration: an Express API route that streams agent responses via SSE, paired with a React component that consumes the stream and renders messages in real time.

---

**Shared types:**

```typescript
// types.ts
export interface SSEEvent {
  type: "token" | "tool_start" | "tool_end" | "done" | "error";
  text?: string;
  name?: string;
  output?: unknown;
  message?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolCalls?: { name: string; output: unknown }[];
}
```

**Backend — Express SSE endpoint:**

```typescript
// api/agent-stream.ts
import express, { Request, Response } from "express";
import { MCPAgent, MCPClient } from "mcp-use";
import type { SSEEvent } from "./types";

const router = express.Router();

router.post("/agent/stream", async (req: Request, res: Response) => {
  const { prompt } = req.body as { prompt?: string };
  if (!prompt || typeof prompt !== "string") {
    res.status(400).json({ error: "prompt is required" });
    return;
  }

  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
    "Access-Control-Allow-Origin": "*",
  });

  const client = new MCPClient({
    mcpServers: {
      // The Everything reference server is actively maintained and ships
      // a broad sample of tools, resources, and prompts — useful for demos.
      everything: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-everything"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    client,
    maxSteps: 15,
    memoryEnabled: false,
  });

  const send = (event: SSEEvent) => {
    res.write(`data: ${JSON.stringify(event)}\n\n`);
  };

  try {
    const events = agent.streamEvents({ prompt });

    for await (const event of events) {
      if (event.event === "on_chat_model_stream") {
        // chunk property may be 'text' or 'content' depending on LLM provider
        const text = event.data?.chunk?.text || event.data?.chunk?.content;
        if (typeof text === "string" && text.length > 0) {
          send({ type: "token", text });
        }
      }
      if (event.event === "on_tool_start") {
        send({ type: "tool_start", name: event.name });
      }
      if (event.event === "on_tool_end") {
        send({ type: "tool_end", output: event.data?.output });
      }
    }

    send({ type: "done" });
  } catch (error) {
    send({ type: "error", message: String(error) });
  } finally {
    res.end();
    await agent.close();
  }
});

export default router;
```

**Frontend — React component:**

```typescript
// components/AgentChat.tsx
"use client";
import { useState, useCallback, useRef, useEffect } from "react";
import type { SSEEvent, ChatMessage } from "../types";

function generateId() {
  return Math.random().toString(36).slice(2, 10);
}

export function AgentChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!input.trim() || isLoading) return;

      const userMessage: ChatMessage = {
        id: generateId(),
        role: "user",
        content: input.trim(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setInput("");
      setIsLoading(true);
      setError(null);

      const assistantId = generateId();
      setMessages((prev) => [
        ...prev,
        { id: assistantId, role: "assistant", content: "", toolCalls: [] },
      ]);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const res = await fetch("/api/agent/stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: userMessage.content }),
          signal: controller.signal,
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const reader = res.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const event: SSEEvent = JSON.parse(line.slice(6));

            if (event.type === "token" && event.text) {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, content: m.content + event.text }
                    : m
                )
              );
            }

            if (event.type === "tool_end" && event.name) {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? {
                        ...m,
                        toolCalls: [
                          ...(m.toolCalls ?? []),
                          { name: event.name!, output: event.output },
                        ],
                      }
                    : m
                )
              );
            }

            if (event.type === "error") {
              setError(event.message ?? "Unknown error");
            }
          }
        }
      } catch (err: any) {
        if (err.name !== "AbortError") {
          setError(err.message);
        }
      } finally {
        setIsLoading(false);
        abortRef.current = null;
      }
    },
    [input, isLoading]
  );

  // Auto-scroll to bottom
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div style={{ maxWidth: 640, margin: "0 auto", padding: 16 }}>
      <div style={{ minHeight: 400, overflowY: "auto" }}>
        {messages.map((m) => (
          <div key={m.id} style={{ marginBottom: 12 }}>
            <strong>{m.role === "user" ? "You" : "Agent"}:</strong>
            <p style={{ whiteSpace: "pre-wrap" }}>{m.content}</p>
            {m.toolCalls?.map((tc, i) => (
              <details key={i} style={{ fontSize: 12, color: "#666" }}>
                <summary>Tool: {tc.name}</summary>
                <pre>{JSON.stringify(tc.output, null, 2)}</pre>
              </details>
            ))}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <form onSubmit={handleSubmit} style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask the agent..."
          style={{ flex: 1, padding: 8 }}
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}
```

---

## 5. Multi-Provider Fallback

Try OpenAI first, then Anthropic, then Groq — automatically falling back through providers on failure. Includes configurable retries, delay, health checking, and cost-aware ordering.

---

```typescript
// multi-provider-fallback.ts
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";
import { ChatGroq } from "@langchain/groq";
import type { BaseChatModel } from "@langchain/core/language_models/chat_models";

interface ProviderConfig {
  name: string;
  createLLM: () => BaseChatModel;
  maxRetries: number;
  retryDelayMs: number;
  costPer1kTokens: number;
}

// Providers ordered by preference. The fallback loop tries them
// in array order. You can re-sort by cost at runtime if needed.
const PROVIDERS: ProviderConfig[] = [
  {
    name: "openai",
    createLLM: () =>
      new ChatOpenAI({
        model: "gpt-4o",
        apiKey: process.env.OPENAI_API_KEY,
      }),
    maxRetries: 2,
    retryDelayMs: 1000,
    costPer1kTokens: 0.005,
  },
  {
    name: "anthropic",
    createLLM: () =>
      new ChatAnthropic({
        model: "claude-3-5-sonnet-20241022",
        apiKey: process.env.ANTHROPIC_API_KEY,
      }),
    maxRetries: 1,
    retryDelayMs: 2000,
    costPer1kTokens: 0.003,
  },
  {
    name: "groq",
    createLLM: () =>
      new ChatGroq({
        model: "llama-3.3-70b-versatile",
        apiKey: process.env.GROQ_API_KEY,
      }),
    maxRetries: 1,
    retryDelayMs: 500,
    costPer1kTokens: 0.0007,
  },
];

// Optional: sort by cheapest first for cost-aware fallback
function sortByCost(providers: ProviderConfig[]): ProviderConfig[] {
  return [...providers].sort((a, b) => a.costPer1kTokens - b.costPer1kTokens);
}

// Quick health check: send a trivial prompt and expect a response.
async function isProviderHealthy(provider: ProviderConfig): Promise<boolean> {
  try {
    const llm = provider.createLLM();
    const response = await llm.invoke("Say OK");
    return !!response?.content;
  } catch {
    console.warn(`[health] ${provider.name} is unreachable`);
    return false;
  }
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function runWithFallback(prompt: string): Promise<string> {
  // Use env var to control cost-aware ordering:
  // PROVIDER_ORDER=cost-first | default
  const ordered =
    process.env.PROVIDER_ORDER === "cost-first"
      ? sortByCost(PROVIDERS)
      : PROVIDERS;

  const mcpServers = {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
  };

  for (const provider of ordered) {
    // Pre-flight health check
    const healthy = await isProviderHealthy(provider);
    if (!healthy) {
      console.log(`[fallback] Skipping ${provider.name} (unhealthy)`);
      continue;
    }

    for (let attempt = 1; attempt <= provider.maxRetries; attempt++) {
      const client = new MCPClient({ mcpServers });
      const agent = new MCPAgent({
        llm: provider.createLLM(),
        client,
        maxSteps: 20,
      });

      try {
        console.log(
          `[fallback] Trying ${provider.name} (attempt ${attempt}/${provider.maxRetries})`
        );
        const result = await agent.run({ prompt, maxSteps: 20 });
        console.log(`[fallback] ${provider.name} succeeded`);
        return result;
      } catch (error) {
        console.warn(
          `[fallback] ${provider.name} attempt ${attempt} failed:`,
          error
        );
        if (attempt < provider.maxRetries) {
          await sleep(provider.retryDelayMs);
        }
      } finally {
        await agent.close();
      }
    }
  }

  throw new Error("All providers exhausted — no successful response");
}

// Example usage
async function main() {
  const answer = await runWithFallback(
    "List all .ts files in /tmp and summarize the largest one"
  );
  console.log("Answer:", answer);
}

main().catch(console.error);
```

---

## 6. Code Execution Mode Integration

Use MCPClient's `codeMode` option with the `PROMPTS.CODE_MODE` system prompt on the agent. The agent writes and runs code via the filesystem MCP server to accomplish tasks, then cleans up after itself.

Note: `codeMode` is an MCPClient option (second constructor argument), not an MCPAgent option.

---

```typescript
// code-mode.ts
import { MCPAgent, MCPClient, PROMPTS } from "mcp-use";
import { mkdtempSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";

async function runCodeMode() {
  // Create an isolated temp directory for the agent to work in.
  const workDir = mkdtempSync(join(tmpdir(), "mcp-code-"));
  console.log(`[code-mode] Working directory: ${workDir}`);

  // codeMode belongs on MCPClient, not MCPAgent
  const client = new MCPClient(
    {
      mcpServers: {
        filesystem: {
          command: "npx",
          args: ["-y", "@modelcontextprotocol/server-filesystem", workDir],
        },
      },
    },
    { codeMode: true }
  );

  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    client,
    maxSteps: 30,
    systemPrompt: PROMPTS.CODE_MODE,
  });

  try {
    const result = await agent.run({
      prompt: [
        "Create a Node.js script that:",
        "1. Generates 100 random numbers between 1 and 1000",
        "2. Writes them to a file called numbers.json",
        "3. Reads the file back and calculates mean, median, and mode",
        "4. Writes the statistics to stats.json",
        "5. Prints the final statistics",
      ].join("\n"),
      maxSteps: 30,
    });

    console.log("\n--- Code Mode Result ---");
    console.log(result);
  } catch (error) {
    console.error("[code-mode] Execution failed:", error);
  } finally {
    await agent.close();

    // Clean up temp directory
    try {
      rmSync(workDir, { recursive: true, force: true });
      console.log(`[code-mode] Cleaned up ${workDir}`);
    } catch {
      console.warn(`[code-mode] Could not clean up ${workDir}`);
    }
  }
}

runCodeMode().catch(console.error);
```

**Code mode output format:**

When `codeMode: true` is set, the agent's responses tend to follow this pattern:

```
1. The agent writes a script file to the filesystem server.
2. It executes the script using available tools.
3. It reads stdout/stderr and iterates if there are errors.
4. The final response includes the script output and a summary.
```

This is useful for data processing pipelines, file transformations, and any task where the agent benefits from writing structured code rather than making ad-hoc tool calls.

---

## 7. Dynamic Server Addition at Runtime

Use `ServerManager` with `AddMCPServerFromConfigTool` so the agent can connect to new MCP servers during a conversation — without restarting.

---

```typescript
// dynamic-servers.ts
import { MCPAgent, MCPClient } from "mcp-use";

async function dynamicServerDemo() {
  // Start with a minimal set of servers.
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    client,
    maxSteps: 25,
    // Enable the server manager — this gives the agent access to
    // the AddMCPServerFromConfigTool so it can add new MCP servers
    // at runtime by name and configuration.
    useServerManager: true,
  });

  try {
    // The agent can now add new servers mid-conversation.
    // For example, it could decide it needs a web search server
    // and add it dynamically.
    const result = await agent.run({
      prompt: [
        "I need you to do the following:",
        "1. First, list the files in /tmp using the filesystem server.",
        "2. Then, call add_mcp_server_from_config for a web search server with:",
        '   serverName: "brave-search"',
        '   serverConfig: {',
        '     command: "npx",',
        // The official Brave Search reference server lives under
        // @modelcontextprotocol — there is NO @anthropic/mcp-server-* npm scope.
        // Note: this package is marked deprecated on npm as of late 2024;
        // substitute a community-maintained equivalent if it stops working.
        '     args: ["-y", "@modelcontextprotocol/server-brave-search"],',
        `     env: { "BRAVE_API_KEY": "${process.env.BRAVE_API_KEY}" }`,
        "   }",
        "3. Use the newly added brave-search server to look up",
        '   "latest Node.js release notes".',
        "4. Save a summary of the search results to /tmp/node-news.md",
        "   using the filesystem server.",
      ].join("\n"),
      maxSteps: 25,
    });

    console.log("Result:", result);
  } catch (error) {
    console.error("Dynamic server demo failed:", error);
  } finally {
    await agent.close();
  }
}

dynamicServerDemo().catch(console.error);
```

**How `useServerManager` works:**

1. When `useServerManager: true` is set, the agent receives access to the following Server Manager tools:
   - `list_mcp_servers` — returns all configured servers and their available tools.
   - `connect_to_mcp_server` — activates a server and loads its tools.
   - `get_active_mcp_server` — retrieves the currently active server identifier.
   - `disconnect_from_mcp_server` — deactivates the current server.
   - `add_mcp_server_from_config` — adds a new server at runtime via `{ serverName, serverConfig }`, where `serverConfig` matches one `mcpServers` entry.
2. The agent can invoke any of these tools to dynamically orchestrate which servers and tools it uses.
3. The `ServerManager` spins up new MCP server processes on demand and registers their tools with the agent.
4. From that point forward, the agent can use the new server's tools alongside the original ones.
5. All dynamically added servers are cleaned up when `agent.close()` is called.

This pattern is useful when:
- The required servers depend on user input or task context.
- You want a single long-running agent that adapts its capabilities.
- You're building a meta-agent that orchestrates other MCP services.

---

## 8. Structured Output Streaming

Stream a typed, Zod-validated response using `agent.streamEvents()` with a `schema`. The agent emits three structured-output-specific events — `on_structured_output_progress`, `on_structured_output`, and `on_structured_output_error` — in addition to the standard token and tool events.

---

```typescript
// structured-output-streaming.ts
import { z } from "zod";
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

// Define the expected output shape
const WeatherSchema = z.object({
  city: z.string().describe("City name"),
  temperature: z.number().describe("Temperature in Celsius"),
  condition: z.string().describe("Weather condition"),
  humidity: z.number().describe("Humidity percentage"),
});

type Weather = z.infer<typeof WeatherSchema>;

async function streamStructuredOutput(): Promise<void> {
  const client = new MCPClient({
    mcpServers: {
      everything: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-everything"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    client,
    maxSteps: 15,
  });

  try {
    let finalWeather: Weather | null = null;

    // Pass both prompt and schema to streamEvents
    for await (const event of agent.streamEvents({
      prompt: "Get the current weather conditions in San Francisco",
      schema: WeatherSchema,
    })) {
      // Standard token streaming
      if (event.event === "on_chat_model_stream") {
        const text = event.data?.chunk?.text || event.data?.chunk?.content;
        if (typeof text === "string" && text.length > 0) {
          process.stdout.write(text);
        }
      }

      // Structured output in progress (fires approx every 2 seconds)
      if (event.event === "on_structured_output_progress") {
        console.log("\n[progress] Converting to structured format...");
      }

      // Structured output successfully produced and validated
      if (event.event === "on_structured_output") {
        finalWeather = WeatherSchema.parse(event.data?.output);
        console.log("\n[structured] Output ready:", finalWeather);
      }

      // Structured output failed after retries (default: 3 retries)
      if (event.event === "on_structured_output_error") {
        console.error("\n[error] Structured output failed:", event.data?.error);
      }
    }

    if (finalWeather) {
      console.log("\n--- Typed Result ---");
      console.log(`City:        ${finalWeather.city}`);
      console.log(`Temperature: ${finalWeather.temperature}°C`);
      console.log(`Condition:   ${finalWeather.condition}`);
      console.log(`Humidity:    ${finalWeather.humidity}%`);
    }
  } finally {
    await client.closeAllSessions();
  }
}

streamStructuredOutput().catch((err) => {
  console.error("Structured streaming failed:", err);
  process.exit(1);
});
```

**Key takeaways:**

- `agent.streamEvents({ prompt, schema })` — preferred `RunOptions` object form. Pass a Zod `schema` to enable structured output streaming. The plain-string form `agent.streamEvents(prompt)` is deprecated; always use the `{ prompt, ... }` object form.
- `on_structured_output_progress` — fires approximately every 2 seconds while the LLM response is being converted and validated.
- `on_structured_output` — fires once when the output is successfully produced; the validated object is available at `event.data.output`.
- `on_structured_output_error` — fires if conversion/validation fails after the retry limit (default: 3 retries).
- Standard token events (`on_chat_model_stream`) continue to fire alongside the structured output events.
