# Prompt Templates

A prompt template accepts user-supplied arguments validated by a Zod schema. The server validates arguments before the handler runs — invalid input returns an error before any code executes.

## Registration

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
    text(`Review this ${language} code:\n\n\`\`\`${language}\n${code}\n\`\`\``),
);
```

Use Zod's full vocabulary — enums, defaults, optionals, refinements. Each field's `.describe()` becomes the user-facing argument hint.

## Argument schema patterns

```typescript
schema: z.object({
  // Free-form string with description
  code: z.string().describe("Source code"),

  // Enum — narrow user choice
  dialect: z.enum(["postgres", "mysql", "sqlite"]).describe("SQL dialect"),

  // Default value
  language: z.string().default("typescript"),

  // Optional
  context: z.string().optional().describe("Additional context"),

  // Numeric with range
  depth: z.number().int().min(1).max(5).default(2),
})
```

For autocomplete on argument values, see `04-completable-arguments.md`.

## Response shapes

Handlers can return a response helper or a manual `{ messages: [...] }` object.

### Response helpers — single message

```typescript
import { text, object, mix } from "mcp-use/server";

server.prompt(
  { name: "greeting", schema: z.object({ name: z.string() }) },
  async ({ name }) => text(`Hello, ${name}.`),
);
```

The helper's content becomes a single user message.

### Manual messages — full control

```typescript
server.prompt(
  {
    name: "debug-assistant",
    description: "Help debug an error",
    schema: z.object({
      error: z.string().describe("Error message"),
      context: z.string().optional().describe("Additional context"),
    }),
  },
  async ({ error, context }) => ({
    messages: [
      { role: "system", content: "You are an expert debugger." },
      { role: "user", content: `Debug this error: ${error}` },
      ...(context ? [{ role: "user", content: `Context: ${context}` }] : []),
    ],
  }),
);
```

Roles: `system`, `user`, `assistant`. Content can be a string or a structured content block.

## Multi-message conversation seed

Prompts can seed a multi-turn conversation:

```typescript
server.prompt(
  {
    name: "debug-session",
    description: "Start a debugging session with context",
    schema: z.object({ error: z.string() }),
  },
  async ({ error }) => ({
    messages: [
      { role: "system", content: "You are a senior reliability engineer. Focus on root cause." },
      { role: "user", content: `I'm seeing this error: ${error}` },
      { role: "assistant", content: "Let's check the system logs first." },
      { role: "user", content: "Please query the logs for the last 15 minutes." },
    ],
  }),
);
```

## Arguments as configuration

Use enums to constrain output style:

```typescript
server.prompt(
  {
    name: "write-sql",
    schema: z.object({
      dialect: z.enum(["postgres", "mysql", "sqlite"]),
      complexity: z.enum(["simple", "optimized", "explained"]),
    }),
  },
  async ({ dialect, complexity }) =>
    text(`
Write a SQL query.
Dialect: ${dialect}
Output Style: ${complexity}
- simple: Just the query
- optimized: Query plus performance comments
- explained: Query plus execution-plan explanation
`),
);
```

## Embedding resource URIs

Mention resource URIs in prompt text — clients can resolve them:

```typescript
server.prompt(
  {
    name: "analyze-user",
    schema: z.object({ userId: z.string() }),
  },
  async ({ userId }) =>
    text(`
Analyze the user profile at users://${userId}.
Cross-check against logs://${userId}/recent.
Apply rules from config://marketing-rules.
`),
);
```

## Notifying changes

When you register or remove prompts at runtime:

```typescript
await server.sendPromptsListChanged();
```

Clients re-issue `prompts/list`.

## Handler signatures

```typescript
async (args) => Response | { messages: PromptMessage[] }
async (args, ctx) => Response | { messages: PromptMessage[] }
```

`ctx` exposes auth and request metadata when available — useful for tailoring prompts to the calling user.
