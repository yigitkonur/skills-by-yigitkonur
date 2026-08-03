# Prompts Overview

*Read this when you need to expose reusable instruction templates that users invoke with optional parameters, producing chat messages.*

## What is a prompt

A prompt is a reusable instruction template the user invokes by name — code review workflows, structured analyses, diagnostic guides. Prompts accept optional arguments and return one or more LLM chat messages.

| You need to expose | Use |
|---|---|
| Reusable LLM instruction with optional parameters | Prompt |
| Read-only data to fetch and display | Resource |
| Action with side effects, driven by LLM | Tool |

Prompts are **user-invoked**, not automatically selected by the LLM. Tools are LLM-driven; prompts are user-driven.

---

## Registration

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });

server.prompt(
  {
    name: "code-review",
    description: "Review code for bugs and improvements",
    schema: z.object({
      code: z.string().describe("Source code to review"),
      language: z.string().default("typescript"),
    }),
  },
  async ({ code, language }, ctx) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: `Review this ${language} code for bugs and improvements:\n\n\`\`\`${language}\n${code}\n\`\`\``,
      },
    }],
  })
);
```

---

## PromptDefinition fields

| Field | Type | Default | Notes |
|---|---|---|---|
| `name` | `string` | (required) | Unique identifier within the server |
| `title` | `string \| undefined` | (inferred from `name`) | Human-readable display name |
| `description` | `string \| undefined` | `undefined` | Shown to users in prompt pickers |
| `schema` | `StandardSchemaWithJSON \| undefined` | `undefined` | Zod v4 / Standard Schema for arguments; fields wrapped with `completable()` gain autocomplete |

---

## Callback signature

```typescript
type PromptCallback<TInput, TUser, HasOAuth, TEnv> = 
  (params: TInput, ctx: RequestContext<TUser, HasOAuth, TEnv>) 
    => GetPromptResult | CallToolResult | Promise<GetPromptResult | CallToolResult>
```

**GetPromptResult (preferred):**
```typescript
{
  messages: PromptMessage[]
  // where PromptMessage = { role: "user" | "assistant", content: ContentBlock }
  // content is a single block, not an array — one message = one content block
}
```

A `CallToolResult` (`{ content: [...] }`) is also accepted and converted at registration time: each content block becomes its own `user`-role message.

---

## Static vs template prompts

| Kind | Has `schema`? | Use when |
|---|---|---|
| Static | No | Fixed instructions, no variation |
| Template | Yes | Behavior depends on user-supplied arguments |

See `02-static-prompts.md` and `03-prompt-templates.md`.

---

## Completable arguments

Fields in the prompt's `schema` can be wrapped with `completable()` to provide autocomplete suggestions:

```typescript
import { completable } from "mcp-use";

schema: z.object({
  language: completable(
    z.string(),
    ["python", "typescript", "go", "rust"]
  ),
})
```

See `04-completable-arguments.md` for static lists and dynamic callbacks.

---

## Wire protocol

| JSON-RPC method | Purpose |
|---|---|
| `prompts/list` | Enumerate available prompts |
| `prompts/get` | Render a prompt with user-supplied arguments |
| `notifications/prompts/list_changed` | Server-pushed notification of registry change |
| `completion/complete` | Argument autocompletion; shipped in beta.66. See `04-completable-arguments.md` |

---

## Cluster map

| File | Topic |
|---|---|
| `02-static-prompts.md` | Fixed-text prompts without arguments |
| `03-prompt-templates.md` | Argument schemas, multi-message construction |
| `04-completable-arguments.md` | `completable()` for argument autocomplete |
| `05-prompt-engineering.md` | Prompt content guidance, prompt vs tool decision |
