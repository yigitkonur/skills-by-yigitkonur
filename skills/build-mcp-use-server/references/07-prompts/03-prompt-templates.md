# Prompt Templates

*Read this when you need a prompt that accepts user-supplied arguments.*

A prompt template accepts user-supplied arguments validated by a schema (Zod v4, ArkType, Valibot, etc.). The server validates arguments before the handler runs — invalid input returns an error before any code executes.

---

## Registration

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "example", version: "1.0.0" });

server.prompt(
  {
    name: "code-review",
    description: "Review code for bugs and improvements",
    schema: z.object({
      code: z.string().describe("Source code to review"),
      language: z.string().default("typescript").describe("Programming language"),
    }),
  },
  async ({ code, language }, ctx) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: `Review this ${language} code:\n\n\`\`\`${language}\n${code}\n\`\`\``,
      },
    }],
  })
);
```

Use the full Standard Schema vocabulary — enums, defaults, optionals, refinements. Each field's `.describe()` becomes the user-facing argument hint.

---

## Argument schema patterns

```typescript
schema: z.object({
  // Free-form string
  code: z.string().describe("Source code"),

  // Enum — constrain user choice
  dialect: z.enum(["postgres", "mysql", "sqlite"]).describe("SQL dialect"),

  // Default value
  language: z.string().default("typescript"),

  // Optional field
  context: z.string().optional().describe("Additional context"),

  // Numeric with range
  depth: z.number().int().min(1).max(5).default(2),

  // Boolean flag
  verbose: z.boolean().default(false),
})
```

For autocomplete on enum/string values, wrap the field with `completable()` — see `04-completable-arguments.md`.

---

## GetPromptResult (return shape)

Always prefer the v2 standard `GetPromptResult`:

```typescript
{
  messages: PromptMessage[]
}
```

Where `PromptMessage` is:
```typescript
{
  role: "user" | "assistant" | "system"
  content: ContentBlock | ContentBlock[]
}
```

And `ContentBlock` is one of:
```typescript
{ type: "text", text: string }
| { type: "image", data: string, mimeType: string }
| { type: "resource", uri: string, mimeType?: string, text?: string, blob?: Uint8Array }
```

---

## Single-message template

```typescript
server.prompt(
  {
    name: "code-review",
    schema: z.object({ code: z.string() }),
  },
  async ({ code }, ctx) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: `Review this code:\n\`\`\`\n${code}\n\`\`\``,
      },
    }],
  })
);
```

---

## Multi-message prompts (conversation seed)

Seed multi-turn conversations with system + user messages:

```typescript
server.prompt(
  {
    name: "debug-session",
    description: "Start a debugging session",
    schema: z.object({
      error: z.string().describe("Error message"),
      context: z.string().optional(),
    }),
  },
  async ({ error, context }, ctx) => ({
    messages: [
      {
        role: "user",
        content: {
          type: "text",
          text: `I'm seeing this error: ${error}${context ? `\n\nContext: ${context}` : ""}`,
        },
      },
    ],
  })
);
```

---

## Using enums as configuration

Use enums to constrain output style:

```typescript
server.prompt(
  {
    name: "write-sql",
    description: "Generate SQL with configurable style",
    schema: z.object({
      dialect: z.enum(["postgres", "mysql", "sqlite"]),
      complexity: z.enum(["simple", "optimized", "explained"]),
      task: z.string().describe("What SQL do you need?"),
    }),
  },
  async ({ dialect, complexity, task }, ctx) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: `
Generate a ${complexity} SQL query.

Task: ${task}
Dialect: ${dialect}

Style:
- simple: Just the query
- optimized: Query with performance comments
- explained: Query plus execution-plan explanation
`,
      },
    }],
  })
);
```

---

## Referencing resources in text

Mention resource URIs in prompt text — smart clients (Claude, Cursor) resolve them and include the content in the LLM context:

```typescript
server.prompt(
  {
    name: "analyze-user",
    schema: z.object({ userId: z.string() }),
  },
  async ({ userId }, ctx) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: `Analyze the user profile at users://${userId}.\nCross-check against logs://${userId}/recent.\nApply rules from config://marketing-rules.`,
      },
    }],
  })
);
```

---

## Using context

The `ctx` parameter carries auth, request, and client capability information. Use it to tailor prompts per caller:

```typescript
server.prompt(
  {
    name: "personalized-analysis",
    schema: z.object({ data: z.string() }),
  },
  async ({ data }, ctx) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: `Analyze this data: ${data}${
          ctx.auth ? `\n\nAs: ${ctx.auth.user.id}` : ""
        }`,
      },
    }],
  })
);
```

---

## Notifying changes

When you register or remove prompts at runtime:

```typescript
await server.notifyPromptsChanged();
```

Clients re-issue `prompts/list` and refresh their UI.
