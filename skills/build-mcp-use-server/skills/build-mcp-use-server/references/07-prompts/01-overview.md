# Prompts Overview

A **prompt** is a reusable instruction template the user invokes — code review workflows, debug sessions, structured analyses. Prompts produce one or more chat messages, optionally seeded by user-supplied arguments.

## When to use a prompt

| You expose | Primitive |
|---|---|
| A reusable LLM instruction with optional parameters | Prompt |
| Read-only data | Resource |
| An action with side effects | Tool |

Prompts are **invoked by the user**, not selected autonomously by the LLM. Tools are LLM-driven; prompts are user-driven.

## API

```typescript
import { z } from "zod";
import { text } from "mcp-use/server";

server.prompt(
  {
    name: "code-review",
    description: "Review code for bugs and improvements",
    schema: z.object({
      code: z.string().describe("Source code to review"),
      language: z.string().default("typescript").describe("Programming language"),
    }),
  },
  async ({ code, language }) =>
    text(`Review this ${language} code for bugs and improvements:\n\n\`\`\`${language}\n${code}\n\`\`\``),
);
```

## Wire protocol

| JSON-RPC method | Purpose |
|---|---|
| `prompts/list` | Enumerate available prompts |
| `prompts/get` | Render a prompt with the user-supplied arguments |
| `notifications/prompts/list_changed` | Server-pushed notification of registry change |
| `completion/complete` | Argument autocompletion (see `04-completable-arguments.md`) |

## Definition fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | `string` | yes | Unique identifier within the server |
| `title` | `string` | no | Human display label; falls back to `name` |
| `description` | `string` | no | Shown to users in prompt pickers |
| `schema` | `z.ZodObject` | no | Zod schema for argument validation |
| `args` | `InputDefinition[]` | no | **Deprecated.** Use `schema` instead |
| `cb` | `PromptCallback` | no | Inline handler (alternative to second argument) |

A prompt without a `schema` takes no arguments — fixed text:

```typescript
server.prompt(
  { name: "summarize-logs", description: "Summarize recent logs" },
  async () => text("Retrieve the recent logs and summarize errors, warnings, and unusual patterns."),
);
```

A prompt with a `schema` accepts validated arguments — the server rejects bad input before your handler runs.

## Static vs template

| Kind | Definition | Use when |
|---|---|---|
| Static | No `schema` | Fixed instructions, no variation |
| Template | `schema: z.object({...})` | Behavior depends on user-supplied arguments |

See `02-static-prompts.md` and `03-prompt-templates.md`.

## Cluster map

| File | Topic |
|---|---|
| `02-static-prompts.md` | Fixed-text prompts |
| `03-prompt-templates.md` | Argument schemas, multi-message construction, response helpers |
| `04-completable-arguments.md` | `completable()` for prompt arguments — single canonical home |
| `05-prompt-engineering.md` | Anti-patterns, few-shot, prompt vs tool decision |

**Canonical doc:** https://manufact.com/docs/typescript/server/prompts
