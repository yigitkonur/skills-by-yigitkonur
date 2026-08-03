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
  //   content: ContentBlock
  // }
  // content is a single block per message — to send text and an image, use two messages.
}
```

Where `ContentBlock` is one of:
```typescript
{ type: "text", text: string }
| { type: "image", data: string, mimeType: string }       // data is base64
| { type: "audio", data: string, mimeType: string }       // data is base64
| { type: "resource", resource: { uri: string, mimeType?: string, text: string } | { uri: string, mimeType?: string, blob: string } }
| { type: "resource_link", uri: string, name: string, title?: string, mimeType?: string, description?: string }
```

`resource`'s `blob` is a base64-encoded **string**, not `Uint8Array` — the SDK schema serializes binary content as base64 text over the wire.

---

## Notifying changes

`server.prompt()` throws if called after the server has started — registrations are replayed per request from a registry built once at construction time. Register every prompt before `server.listen()` or `server.fetch`; there is no runtime `server.prompt()` call to make later.

To change what clients *see* at runtime (feature flags, per-tenant entitlements), register every possible prompt up front and filter the list with `mcp:prompts/list` middleware instead:

```typescript
server.use("mcp:prompts/list", async (ctx, next) => {
  const prompts = await next();
  return prompts.filter((p) => isEnabledForTenant(p.name, ctx));
});
```

When the filtering criteria change (a flag flips, a tenant's entitlements change), notify clients so they re-fetch:

```typescript
await server.notifyPromptsChanged();
```

Clients re-issue `prompts/list` and refresh their UI.
