# Static Prompts

*Read this when you need a fixed-text prompt without user-supplied arguments.*

A static prompt has **no arguments** — register it without a `schema`. The handler returns the same content every time.

---

## Registration

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({ name: "example", version: "1.0.0" });

server.prompt(
  {
    name: "summarize-logs",
    description: "Summarize recent application logs",
  },
  async (params, ctx) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: "Retrieve the recent logs and summarize errors, warnings, and unusual patterns.",
      },
    }],
  })
);
```

---

## When to use static

| Use static when | Use a template instead |
|---|---|
| Instructions are fixed | Behavior varies per call |
| No per-user/per-request context to inject | User picks language, focus area, or sets constraints |
| Canned workflow — always the same prompt | Arguments toggle behavior or set parameters |

If you find yourself branching logic inside a static prompt, you need a template — see `03-prompt-templates.md`.

---

## Embedding resource references

Prompts often reference resource URIs by name in the text. Smart clients (Claude, Cursor) resolve these and provide the content to the LLM:

```typescript
server.prompt(
  {
    name: "review-config",
    description: "Review the current application configuration",
  },
  async (params, ctx) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: "Review the configuration at config://app. Flag any non-default values, deprecated keys, or insecure settings.",
      },
    }],
  })
);
```

The user invokes the prompt; the client fetches `config://app` via `resources/read` and includes it in the LLM context.

---

## Multi-message static prompts

Use multiple messages to seed a system + user pair:

```typescript
server.prompt(
  {
    name: "incident-triage",
    description: "Open a structured incident triage",
  },
  async (params, ctx) => ({
    messages: [
      {
        role: "user",
        content: {
          type: "text",
          text: "You are an on-call SRE. Be concise; lead with severity. Open a triage. List the questions you need answered first.",
        },
      },
    ],
  })
);
```

See `03-prompt-templates.md` for the full message and content block structure.

---

## Return shape

Prefer `GetPromptResult`:

```typescript
{
  messages: PromptMessage[]
  // where PromptMessage = {
  //   role: "user" | "assistant"
  //   content: ContentBlock | ContentBlock[]
  // }
}
```

Where `ContentBlock` is:
```typescript
{ type: "text", text: string } 
| { type: "image", data: string, mimeType: string }
| { type: "resource", uri: string, mimeType?: string, text?: string, blob?: Uint8Array }
```

---

## Notifying changes

If you register or remove a static prompt at runtime, notify clients to refresh:

```typescript
server.prompt(
  {
    name: "new-workflow",
    description: "Newly added",
  },
  async (params, ctx) => ({
    messages: [{
      role: "user",
      content: { type: "text", text: "..." },
    }],
  })
);

await server.notifyPromptsChanged();
```

Clients re-issue `prompts/list` and refresh their UI.
