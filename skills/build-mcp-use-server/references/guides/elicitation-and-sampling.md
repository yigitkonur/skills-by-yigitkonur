# Elicitation and Sampling

Guide to requesting user input (`ctx.elicit`) and LLM completions (`ctx.sample`) during tool execution with mcp-use.

---

## Elicitation

Elicitation lets a tool pause and ask the user for structured input mid-execution. The client renders a form (or directs the user to a URL), collects data, and returns the result. mcp-use then validates the response server-side against your Zod schema before passing it to your handler.

### Basic Usage

Pass a message string and a Zod schema. The return type is inferred automatically.

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });

server.tool(
  { name: "collect-feedback", description: "Collect user feedback.", schema: z.object({}) },
  async (_args, ctx) => {
    const result = await ctx.elicit(
      "Please share your feedback",
      z.object({
        rating: z.number().min(1).max(5).describe("Rating from 1 to 5"),
        comment: z.string().max(500).optional().describe("Optional comment"),
      })
    );

    if (result.action === "accept") {
      return text(`Thanks! You rated us ${result.data.rating}/5.`);
    }
    return text("Feedback skipped.");
  }
);
```

### Field Types

Use standard Zod types. Add `.describe()` for field labels shown to the user.

```typescript
z.object({
  name: z.string().min(1).describe("Your full name"),
  age: z.number().int().min(0).max(150).describe("Your age"),
  subscribe: z.boolean().default(false).describe("Subscribe to newsletter"),
  plan: z.enum(["free", "pro", "enterprise"]).describe("Select a plan"),
})
```

| Zod Type | Rendered As | Notes |
|---|---|---|
| `z.string()` | Text input | Use `.email()`, `.url()`, `.min()`, `.max()` for constraints |
| `z.number()` | Number input | Use `.int()`, `.min()`, `.max()` for constraints |
| `z.boolean()` | Checkbox / toggle | Use `.default()` to pre-check |
| `z.enum([...])` | Dropdown / radio | Values are the selectable options |

### Handling Responses

`ctx.elicit()` returns an object with an `action` field. Always handle all three cases:

```typescript
const result = await ctx.elicit("Confirm deployment?", z.object({
  environment: z.enum(["staging", "production"]).describe("Target environment"),
  confirm: z.boolean().default(false).describe("I understand this is irreversible"),
}));

switch (result.action) {
  case "accept":
    if (!result.data.confirm) return text("Deployment not confirmed.");
    return text(`Deploying to ${result.data.environment}...`);
  case "decline":
    return text("User declined to provide deployment details.");
  case "cancel":
    return text("Deployment cancelled.");
}
```

| Action | Meaning | `result.data` |
|---|---|---|
| `accept` | User submitted the form | Present, validated against schema |
| `decline` | User explicitly refused | `undefined` |
| `cancel` | User dismissed the prompt | `undefined` |

### Validation

mcp-use automatically validates returned data against your Zod schema server-side. Invalid data never reaches your handler.

**What gets validated:** data types, constraints (`.min()`, `.max()`, `.email()`), required fields, enum membership, and custom Zod refinements.

**Default values:** Fields with `.default()` are filled automatically if the user omits them.

```typescript
const result = await ctx.elicit("Preferences", z.object({
  theme: z.enum(["light", "dark"]).default("light"),
  notifications: z.boolean().default(true),
}));
// If user submits {}, result.data = { theme: "light", notifications: true }
```

### URL Mode

For sensitive data (credentials, OAuth tokens, API keys), use URL mode. Pass a URL string instead of a Zod schema — mode is detected automatically.

```typescript
server.tool(
  { name: "connect-github", description: "Authorize GitHub access.", schema: z.object({}) },
  async (_args, ctx) => {
    const authUrl = `https://github.com/login/oauth/authorize?client_id=${CLIENT_ID}`;
    const result = await ctx.elicit("Please authorize GitHub access", authUrl);

    if (result.action === "accept") return text("GitHub authorization successful.");
    return text("Authorization declined or cancelled.");
  }
);
```

> **Security rule:** Never use form mode for passwords, tokens, or payment data. URL mode keeps sensitive information out of the MCP transport.

### Timeout

By default `ctx.elicit()` waits indefinitely. Pass an options object to set a timeout:

```typescript
const result = await ctx.elicit(
  "Quick confirmation needed",
  z.object({ confirm: z.boolean() }),
  { timeout: 60000 } // 60 seconds
);
```

### Checking Client Support

```typescript
if (!ctx.client.can("elicitation")) {
  return text("This tool requires a client that supports elicitation.");
}
```

### Error Types

| Error | When | Extra Property |
|---|---|---|
| `ElicitationDeclinedError` | User explicitly declined | — |
| `ElicitationTimeoutError` | No response within timeout | `.timeoutMs` |
| `ElicitationValidationError` | Data failed Zod validation | `.cause` (Zod error) |

```typescript
import { ElicitationTimeoutError, ElicitationValidationError } from "mcp-use";

// ...inside a tool handler:
try {
  const result = await ctx.elicit("Enter details", schema, { timeout: 30000 });
  if (result.action === "accept") { /* use result.data */ }
} catch (err) {
  if (err instanceof ElicitationTimeoutError) {
    return text(`Timed out after ${err.timeoutMs}ms.`);
  }
  if (err instanceof ElicitationValidationError) {
    return text(`Invalid input: ${err.message}`);
  }
  return text(`Elicitation failed: ${err instanceof Error ? err.message : String(err)}`);
}
```

### Complete Example — Multi-Step Form

```typescript
import { MCPServer, text, error } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "onboarding-server", version: "1.0.0" });

server.tool(
  { name: "onboard-user", description: "Multi-step user onboarding.", schema: z.object({}) },
  async (_args, ctx) => {
    if (!ctx.client.can("elicitation")) {
      return error("Client does not support elicitation.");
    }

    const step1 = await ctx.elicit("Step 1: Basic Information", z.object({
      name: z.string().min(2).describe("Full name"),
      email: z.string().email().describe("Email address"),
    }));
    if (step1.action !== "accept") return text("Onboarding cancelled at step 1.");

    const step2 = await ctx.elicit(`Welcome ${step1.data.name}! Step 2: Preferences`, z.object({
      role: z.enum(["developer", "designer", "manager"]).describe("Your role"),
      experience: z.number().min(0).max(50).describe("Years of experience"),
      newsletter: z.boolean().default(true).describe("Receive weekly updates"),
    }));
    if (step2.action !== "accept") return text("Onboarding cancelled at step 2.");

    return text(
      `Onboarding complete! ${step1.data.name} (${step1.data.email}) — ` +
      `${step2.data.role} with ${step2.data.experience} years experience.`
    );
  }
);
```

---

## Sampling

Sampling lets a tool request LLM completions from the connected client. Your server doesn't need its own LLM — it uses whatever model the client has configured.

### Basic Usage — String API

Pass a prompt string for simple completions:

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "analyzer", version: "1.0.0" });

server.tool(
  {
    name: "analyze-sentiment",
    description: "Analyze sentiment of the provided text.",
    schema: z.object({ content: z.string().describe("Text to analyze") }),
  },
  async (args, ctx) => {
    const response = await ctx.sample(
      `Classify the sentiment as positive, negative, or neutral. Output one word only.\n\nText: ${args.content}`
    );
    return text(`Sentiment: ${response.content[0].text}`);
  }
);
```

### String API with Options

```typescript
const response = await ctx.sample(
  `Summarize in one sentence: ${args.content}`,
  { maxTokens: 100, temperature: 0.3, timeout: 30000 }
);
```

### Extended API — Full Control

Use the object form for system prompts, message arrays, and model preferences:

```typescript
const response = await ctx.sample({
  messages: [
    { role: "user", content: { type: "text", text: `Analyze: ${args.content}` } },
  ],
  systemPrompt: "You are an expert data analyst. Be concise.",
  maxTokens: 200,
  modelPreferences: {
    intelligencePriority: 0.8,
    speedPriority: 0.5,
  },
});
return text(response.content[0].text);
```

### Parameters

| Parameter | Type | Default | Purpose |
|---|---|---|---|
| `maxTokens` | `number` | `1000` | Maximum tokens in the response |
| `temperature` | `number` | — | Sampling temperature (0.0–1.0) |
| `systemPrompt` | `string` | — | System prompt for the LLM |
| `modelPreferences` | `object` | — | Hint at model selection (intelligence, speed priorities) |
| `timeout` | `number` | `Infinity` | Timeout in milliseconds |
| `progressIntervalMs` | `number` | `5000` | Interval for progress callbacks |
| `onProgress` | `function` | — | Custom progress handler |

### Response Shape

```typescript
interface CreateMessageResult {
  role: "assistant";
  content: { type: "text" | "image"; text?: string; data?: string; mimeType?: string };
  model: string;
  stopReason?: "endTurn" | "maxTokens" | "stopSequence";
}
```

### Checking Client Support

```typescript
if (!ctx.client.can("sampling")) {
  return text("Sampling not supported — returning basic analysis.");
}
```

### Progress Reporting

```typescript
const response = await ctx.sample(args.prompt, {
  timeout: 120000,
  progressIntervalMs: 2000,
  onProgress: ({ message }) => console.log(`[Sampling] ${message}`),
});
```

### Complete Example — Tool with LLM Processing

```typescript
import { MCPServer, text, object, error } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "content-processor", version: "1.0.0" });

server.tool(
  {
    name: "classify-and-summarize",
    description: "Classify a document topic and summarize it using the client LLM.",
    schema: z.object({ document: z.string().min(1).describe("Document text") }),
  },
  async (args, ctx) => {
    if (!ctx.client.can("sampling")) return error("Sampling not supported.");

    const classification = await ctx.sample({
      messages: [
        { role: "user", content: { type: "text",
          text: `Classify into: technology, business, science, health, politics. One word.\n\n${args.document}` } },
      ],
      maxTokens: 10, temperature: 0.0,
    });
    const category = classification.content[0].text.trim().toLowerCase();

    const summary = await ctx.sample(
      `Summarize this ${category} document in 2-3 sentences:\n\n${args.document}`,
      { maxTokens: 150, temperature: 0.3 }
    );

    return object({ category, summary: summary.content[0].text.trim(), model: summary.model });
  }
);
```

---

## Combining Elicitation and Sampling

Both features compose naturally inside a single tool:

```typescript
server.tool(
  {
    name: "smart-report",
    description: "Ask the user what report they want, then use LLM to generate it.",
    schema: z.object({ data: z.string().describe("Raw data to report on") }),
  },
  async (args, ctx) => {
    const prefs = await ctx.elicit("What kind of report?", z.object({
      format: z.enum(["summary", "detailed", "bullet-points"]).describe("Report format"),
      focusArea: z.string().optional().describe("Specific area to focus on"),
    }));
    if (prefs.action !== "accept") return text("Report cancelled.");

    const prompt = `Generate a ${prefs.data.format} report` +
      (prefs.data.focusArea ? ` focusing on ${prefs.data.focusArea}` : "") +
      `:\n\n${args.data}`;

    const report = await ctx.sample(prompt, { maxTokens: 1000, temperature: 0.4 });
    return text(report.content[0].text);
  }
);
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Not checking `ctx.client.can()` | Crashes on clients without support | Guard with capability check before calling |
| Ignoring `decline` / `cancel` actions | Tool hangs or errors on non-accept | Always handle all three action values |
| Using form mode for passwords | Credentials pass through MCP client | Use URL mode for all sensitive data |
| No `try/catch` around elicit/sample | Timeouts and validation errors crash handler | Wrap in try/catch, return `error()` |
| Unbounded sampling without `maxTokens` | Excessively long LLM responses | Always set `maxTokens` to a reasonable limit |
| Calling `ctx.sample()` in a loop | Runaway LLM costs and latency | Cap iterations; consider batch prompts |
