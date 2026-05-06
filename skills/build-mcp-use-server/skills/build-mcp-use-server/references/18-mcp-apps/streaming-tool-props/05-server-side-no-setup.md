# Server-Side: No Setup Required

Streaming tool props is a **client-side** feature. The server tool handler does **not** need any special configuration, opt-in, or modification. Write a normal `widget(...)` response.

## How it actually works

1. The MCP client connects to your server over Streamable HTTP.
2. The LLM begins generating a tool call. As it produces JSON tokens, the client emits `ui/notifications/tool-input-partial` notifications carrying the growing partial JSON.
3. The mcp-use runtime in the widget's iframe intercepts those notifications and exposes them as `partialToolInput` on `useWidget()`.
4. When the LLM finishes generating arguments, a final `tool-input` notification arrives and `toolInput` becomes the complete args. In `mcp-use@1.26.0`, `partialToolInput` is not cleared here.
5. The server now receives the complete `tools/call` request with the full arguments. Your handler runs normally.
6. Your handler returns a `widget(...)` response. The client receives `tool-result`, clears `partialToolInput`, and `props` includes the server-computed `structuredContent`.

The server handler never sees partials. Everything that powers `partialToolInput` happens at the protocol layer between the LLM and the client — your server is not in that loop.

## A normal tool handler — that's it

```typescript
import { MCPServer, widget } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "summarize-server",
  version: "1.0.0",
});

server.tool(
  {
    name: "summarize",
    description: "Summarize a topic",
    schema: z.object({
      title: z.string(),
      body: z.string(),
      tags: z.array(z.string()),
    }),
    widget: {
      name: "summary-card",
      invoking: "Generating summary...",
      invoked: "Summary ready",
    },
  },
  async ({ title, body, tags }) => {
    // No streaming setup. The client already received partialToolInput
    // for { title, body, tags } while the LLM was generating them.
    return widget({
      props: { title, body, tags },
      message: `Summary: ${title}`,
    });
  }
);
```

There is no `streaming: true` flag, no event-emitter hookup, no progress-reporting requirement. The streaming UX is fully handled by the protocol and the runtime.

## What this means

| Question | Answer |
|---|---|
| Do I add a flag in `server.tool({...})`? | No. |
| Do I emit progress events? | Not for streaming preview. (Progress events exist for tool execution, see `../../04-tools/05-the-ctx-object.md`, but they are unrelated.) |
| Do I split the tool into a streaming and non-streaming version? | No. Same handler. |
| Does my handler get partial args? | No. It runs once, after the full args are assembled. |

## When *would* you change the server?

The only server-side design concern relevant to streaming widgets is making the `widget()` response shape compatible with the partial values the user already saw. If `partialToolInput.title` showed "Hello W…" and your server-computed `props.title` is suddenly "Greetings, World", the user sees a jarring jump.

Best practice: keep final `props` compatible with the preview fields you read from `partialToolInput`, so the transition from preview to complete render is coherent.

## Confirm the wiring

Run `mcp-use dev` and call your tool from MCP Inspector. The Inspector exposes `tool-input-partial` notifications in its event log — you should see them stream in even though your handler did nothing special.
