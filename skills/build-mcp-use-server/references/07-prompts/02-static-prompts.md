# Static Prompts

A static prompt has **no arguments** — register it without a `schema`. The handler returns the same content every time.

## Registration

```typescript
import { text } from "mcp-use/server";

server.prompt(
  { name: "summarize-logs", description: "Summarize recent application logs" },
  async () => text("Retrieve the recent logs and summarize errors, warnings, and unusual patterns."),
);
```

## When to use

| Use static when | Use a template instead when |
|---|---|
| Instructions are fixed | Behavior varies per call |
| There is no per-user context to inject | The user picks language, dialect, focus area |
| The prompt is a canned workflow | Arguments toggle behavior or set constraints |

If you find yourself writing branching logic inside a static prompt, you actually want a template — see `03-prompt-templates.md`.

## Embedding resource references

Prompts often reference resource URIs by name in the prompt text. Smart clients (Claude, Cursor) resolve these and provide the content to the LLM:

```typescript
server.prompt(
  { name: "review-config", description: "Review the current application configuration" },
  async () =>
    text(
      "Review the configuration at config://app. Flag any non-default values, deprecated keys, or insecure settings."
    ),
);
```

The user invokes the prompt; the client fetches `config://app` via `resources/read` and includes it in the LLM context.

## Multi-message static prompts

Use the `{ messages: [] }` return shape to seed a system + user pair:

```typescript
server.prompt(
  { name: "incident-triage", description: "Open a structured incident triage" },
  async () => ({
    messages: [
      { role: "system", content: "You are an on-call SRE. Be concise; lead with severity." },
      { role: "user", content: "Open a triage. List the questions you need answered first." },
    ],
  }),
);
```

The shape is the same as the template version — see `03-prompt-templates.md` for the full message format.

## Notifying changes

If you register or remove a static prompt at runtime, notify clients:

```typescript
server.prompt(
  { name: "new-canned-workflow", description: "Newly added" },
  async () => text("..."),
);
await server.sendPromptsListChanged();
```

Clients re-issue `prompts/list` and refresh their UI.
