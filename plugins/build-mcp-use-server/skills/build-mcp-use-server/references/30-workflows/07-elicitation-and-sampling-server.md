# Workflow: Elicitation and Sampling Server

**Goal:** demonstrate two interactive primitives — `ctx.elicit` (ask the *user* via the client UI) and `ctx.sample` (ask the *client's LLM*). Capability-gate every call so older clients get a clean error rather than a 500.

## Prerequisites

- A client that supports elicitation and/or sampling. The Inspector (`mcp-use dev`) supports both.
- mcp-use ≥ 1.21.5.

## Layout

```
interactive-mcp/
├── package.json
└── index.ts
```

## `index.ts`

```typescript
import { MCPServer, text, error, object } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "interactive-mcp",
  version: "1.0.0",
  description: "Elicitation + sampling demo",
});

// ── Elicitation: ask the user a structured question ─────────────────────────

server.tool(
  {
    name: "deploy-production",
    description: "Deploy a build to production. Asks the user to confirm.",
    schema: z.object({
      version: z.string().min(1),
    }),
  },
  async ({ version }, ctx) => {
    if (!ctx.client.can("elicitation")) {
      return error("This client does not support user prompts (elicitation)");
    }

    const response = await ctx.elicit(
      `You are about to deploy **${version}** to production. Continue?`,
      z.object({
        confirmed: z.boolean().describe("Tick to confirm deployment"),
        reason: z.string().min(3).describe("Reason for this deploy"),
      })
    );

    if (response.action === "cancel" || !response.data?.confirmed) {
      return text(`Deployment of ${version} cancelled.`);
    }

    // Real implementation would invoke the deploy here.
    return text(
      `Deployed ${version}. Reason: ${response.data.reason}`
    );
  }
);

// ── Sampling: ask the client's LLM to generate text ─────────────────────────

server.tool(
  {
    name: "summarize",
    description: "Summarize the supplied text using the client's LLM",
    schema: z.object({
      content: z.string().min(1).describe("Text to summarize"),
      style: z.enum(["brief", "detailed"]).default("brief"),
    }),
  },
  async ({ content, style }, ctx) => {
    if (!ctx.client.can("sampling")) {
      return error("This client does not support sampling");
    }

    try {
      const result = await ctx.sample({
        messages: [
          {
            role: "user",
            content: {
              type: "text",
              text: `Summarize the following in a ${style} style:\n\n${content}`,
            },
          },
        ],
        maxTokens: style === "brief" ? 200 : 800,
        temperature: 0.4,
      });

      const out =
        result.content?.type === "text"
          ? result.content.text
          : "(no text returned)";
      return text(out);
    } catch (e) {
      return error(`Sampling failed: ${(e as Error).message}`);
    }
  }
);

// ── Combined: elicit a topic, then sample a story about it ──────────────────

server.tool(
  {
    name: "story-from-topic",
    description: "Ask the user for a topic, then sample a short story",
    schema: z.object({}),
  },
  async (_, ctx) => {
    if (!ctx.client.can("elicitation") || !ctx.client.can("sampling")) {
      return error(
        "This tool requires both elicitation and sampling. Available: " +
          JSON.stringify({
            elicitation: ctx.client.can("elicitation"),
            sampling: ctx.client.can("sampling"),
          })
      );
    }

    const ask = await ctx.elicit(
      "What topic should the story be about?",
      z.object({
        topic: z.string().min(2),
        length: z.enum(["short", "medium"]).default("short"),
      })
    );

    if (ask.action === "cancel" || !ask.data) {
      return text("Cancelled.");
    }

    const result = await ctx.sample({
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `Write a ${ask.data.length} story about: ${ask.data.topic}`,
          },
        },
      ],
      maxTokens: ask.data.length === "short" ? 300 : 800,
    });

    return object({
      topic: ask.data.topic,
      story: result.content?.type === "text" ? result.content.text : "",
    });
  }
);

await server.listen();
```

## Run

```bash
npm install && npm run dev
```

## Test in the Inspector

1. Open http://localhost:3000/inspector and connect.
2. Call `deploy-production` with `{ "version": "1.2.3" }`. The Inspector renders a form. Submit.
3. Call `summarize` with `{ "content": "...long text...", "style": "brief" }`. The Inspector forwards the sampling request to its configured LLM.
4. Call `story-from-topic`. The Inspector elicits, then samples.

## Capability matrix

Always check before invoking:

| Method | Capability key | Behaviour if missing |
|---|---|---|
| `ctx.elicit(...)` | `elicitation` | Throws — return `error("...")` instead |
| `ctx.sample(...)` | `sampling` | Throws — return `error("...")` instead |

`ctx.client.can(name)` returns a boolean from the client's declared capabilities at handshake time. It does not roundtrip to the client.

## Notes

- The user can cancel an elicit prompt. `response.action === "cancel"` is normal — handle it as a clean exit, not an error.
- Sampling charges the *client's* LLM budget, not the server's. There is no provider key in the server.
- Combined elicit-then-sample flows can take many seconds. They run on the same SSE session — the client receives the tool result when both finish.

## See also

- Elicitation reference: `../12-elicitation/`
- Sampling reference: `../13-sampling/`
- Full example: `../31-canonical-examples/05-mcp-progress-demo.md`
