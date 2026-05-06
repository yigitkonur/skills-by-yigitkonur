# `text()` and `markdown()`

Two text helpers. Both accept a single `string` and return a `CallToolResult`. They differ only in MIME type, which controls how the client renders the content.

## `text(content)` — `text/plain`

Use for plain-language summaries, confirmations, status messages, and short answers that don't need formatting.

```typescript
import { text } from "mcp-use/server";

server.tool(
  { name: "greet", schema: z.object({ name: z.string() }) },
  async ({ name }) => text(`Hello, ${name}!`)
);

return text("Deployment queued successfully.");
return text("Order ORD-1234 created.");
```

Signature: `text(content: string): CallToolResult`. MIME: `text/plain`.

## `markdown(content)` — `text/markdown`

Use when headings, lists, code fences, links, or emphasis improve readability.

```typescript
import { markdown } from "mcp-use/server";

return markdown(`## Deployment

- Status: queued
- Region: us-east-1
- ETA: 2 minutes`);

return markdown(`Found **3 tickets** matching "auth":

1. TKT-101 — Login fails with SSO
2. TKT-102 — Password reset broken
3. TKT-104 — 2FA prompt missing`);
```

Signature: `markdown(content: string): CallToolResult`. MIME: `text/markdown`.

## When to use which

| Need | Helper |
|---|---|
| One-line confirmation or status | `text()` |
| Short factual answer | `text()` |
| Multi-section response with headings | `markdown()` |
| Lists of items | `markdown()` |
| Embedded code snippets | `markdown()` |
| Strict prose for downstream NLP | `text()` (avoid markdown control chars) |

## Default to text/markdown for the conversational answer

For broad client compatibility, `text()` or `markdown()` is the right default. Reach for `object()` only when a typed consumer (widget, Code Mode, agent bridge, parser) actually needs structured fields — see `03-object-and-mix.md` and `../04-tools/07-input-schema-vs-output-schema.md`.

## Anti-pattern: stringify-then-text

Do not serialize JSON into `text()` and hope clients parse it.

```typescript
// Bad — clients have to guess this is JSON
return text(JSON.stringify({ total: 42 }));

// Good — proper structured surface
return object({ total: 42 });
```

## Anti-pattern: html-as-markdown

Markdown clients render HTML inconsistently. If you need HTML, use `html()` — see `04-html-css-javascript-xml.md`.

## Examples

```typescript
// Read tool
server.tool(
  { name: "get-status", description: "Get build status." },
  async () => text("Build green. 187s.")
);

// Search result with structure
server.tool(
  { name: "search-tickets", schema: z.object({ q: z.string() }) },
  async ({ q }) => {
    const tickets = await db.search(q);
    return markdown(
      `Found **${tickets.length}** tickets matching "${q}":\n\n` +
      tickets.map(t => `- ${t.id} — ${t.title}`).join("\n")
    );
  }
);
```
