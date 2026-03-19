# Elicitation and Sampling

Guide to requesting user input (`ctx.elicit`) and LLM completions (`ctx.sample`) during tool execution with mcp-use TypeScript server library.

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
  { name: "collect-feedback", description: "Collect user feedback." },
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

Use `ctx.client.can()` to check for a specific capability before calling:

```typescript
if (!ctx.client.can("elicitation")) {
  return text("This tool requires a client that supports elicitation.");
}
```

You can also inspect all client capabilities at once:

```typescript
const caps = ctx.client.capabilities();
// e.g. { sampling: {}, roots: { listChanged: true }, elicitation: { form: {}, url: {} } }
```

### Error Handling

Wrap elicitation calls in `try/catch` to handle failures gracefully. Errors can arise from validation failures, unsupported clients, or network issues.

```typescript
try {
  const result = await ctx.elicit("Enter details", schema, { timeout: 30000 });
  if (result.action === "accept") { /* use result.data */ }
} catch (err: unknown) {
  // Client doesn't support elicitation, timeout, or validation error
  return text(`Elicitation failed: ${err instanceof Error ? err.message : String(err)}. Please ensure your client supports elicitation.`);
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
    return text(`Sentiment: ${response.content.text}`);
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
return text(response.content.text);
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
  content: {
    type: "text" | "image";
    text?: string;
    data?: string;
    mimeType?: string;
  };
  model: string;
  stopReason?: "endTurn" | "maxTokens" | "stopSequence";
}
```

> **Note:** `content` is a single object (not an array). Access the text directly via `response.content.text` or guard with optional chaining: `response.content?.text ?? ''`.

### Checking Client Support

Use `ctx.client.can("sampling")` to guard calls before attempting them:

```typescript
if (!ctx.client.can("sampling")) {
  return text("Sampling not supported — returning basic analysis.");
}
```

You can also inspect all client capabilities, or combine capability checks:

```typescript
const caps = ctx.client.capabilities();
// e.g. { sampling: {}, roots: { listChanged: true }, elicitation: { form: {}, url: {} } }

if (ctx.client.can('sampling') && ctx.client.can('elicitation')) {
  // Use both features
}
```

### Identifying the Client

Use `ctx.client.info()` to get the client's name and version from the MCP initialize handshake. Use `ctx.client.extension(id)` to access any MCP extension (SEP-1724). Use `ctx.client.supportsApps()` as a convenience check for MCP Apps support (SEP-1865):

```typescript
// Who is connecting?
const { name, version } = ctx.client.info();
// e.g. { name: "claude-desktop", version: "1.2.0" }

// Access any MCP extension (SEP-1724)
const uiExt = ctx.client.extension('io.modelcontextprotocol/ui');
// { mimeTypes: ['text/html;profile=mcp-app'] } | undefined

// Convenience check for MCP Apps support (SEP-1865)
if (ctx.client.supportsApps()) {
  // Return rich widget responses
}
```

Note: `ctx.client.supportsApps()` is **per-connection** — different clients connecting to the same server may return different values.

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
    const category = classification.content.text.trim().toLowerCase();

    const summary = await ctx.sample(
      `Summarize this ${category} document in 2-3 sentences:\n\n${args.document}`,
      { maxTokens: 150, temperature: 0.3 }
    );

    return object({ category, summary: summary.content.text.trim(), model: summary.model });
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
    return text(report.content.text);
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


---

## Advanced Elicitation Patterns

`ctx.elicit()` shines when the user needs to provide missing information before a tool can continue. The most reliable elicitation flows are **small, explicit, and validated**.

### Form-based elicitation with Zod schemas

```typescript
import { MCPServer, text, object, error } from 'mcp-use/server'
import { z } from 'zod'

const deployForm = z.object({
  environment: z.enum(['staging', 'production']).describe('Target environment'),
  version: z.string().min(1).describe('Version to deploy'),
  changelogSummary: z.string().max(500).describe('Short deployment summary'),
  approved: z.boolean().default(false).describe('I confirm this deployment is approved'),
})

server.tool(
  {
    name: 'deploy-release',
    description: 'Collect deployment information, then start a deployment.',
  },
  async (_args, ctx) => {
    if (!ctx.client.can('elicitation')) return error('Elicitation is not supported by this client.')

    const result = await ctx.elicit('Provide deployment details', deployForm)
    if (result.action !== 'accept') return text('Deployment was not started.')
    if (!result.data.approved) return text('Deployment approval was not confirmed.')

    return object({
      message: 'Deployment queued',
      environment: result.data.environment,
      version: result.data.version,
    })
  }
)
```

### High-signal schema design tips

| Practice | Why |
|---|---|
| Use `.describe()` on every field | Becomes the form label/help text |
| Prefer enums over free text for known options | Prevents ambiguous input |
| Keep forms short | Better completion rates |
| Use validation constraints | Users get immediate feedback |
| Make irreversible actions explicit | Reduces accidental approval |

### Supported schema patterns

| Zod pattern | UI effect |
|---|---|
| `z.enum([...])` | Dropdown, segmented control, or radio list |
| `z.boolean().default(false)` | Checkbox/toggle |
| `z.string().email()` | Email input |
| `z.string().url()` | URL input |
| `z.number().min().max()` | Numeric input with validation |
| `z.array(z.string())` | Multi-value capture when supported by the client |

### SEP-1330 Advanced Enum Patterns

The simplified Zod API covers most cases. When you need advanced enum shapes — titled enum options, legacy `enumNames`, or multi-select arrays — use the verbose API with helpers exported from `mcp-use/server`:

```typescript
import {
  enumSchema,
  legacyEnum,
  titledEnum,
  titledMultiEnum,
  untitledEnum,
  untitledMultiEnum,
} from 'mcp-use/server';

const result = await ctx.elicit({
  message: 'Choose your options',
  requestedSchema: enumSchema({
    untitledSingle: untitledEnum(['option1', 'option2', 'option3']),
    titledSingle: titledEnum([
      { value: 'value1', title: 'First Option' },
      { value: 'value2', title: 'Second Option' },
    ]),
    legacyNamed: legacyEnum([
      { value: 'opt1', name: 'Option One' },
      { value: 'opt2', name: 'Option Two' },
    ]),
    untitledMulti: untitledMultiEnum(['option1', 'option2', 'option3']),
    titledMulti: titledMultiEnum([
      { value: 'value1', title: 'First Choice' },
      { value: 'value2', title: 'Second Choice' },
    ]),
  }),
});

if (result.action === 'accept') {
  return text(`Selected: ${JSON.stringify(result.data)}`);
}
```

| SEP-1330 Variant | Helper | JSON Schema Shape |
|---|---|---|
| Untitled single-select | `untitledEnum` | `type: "string" + enum` |
| Titled single-select | `titledEnum` | `type: "string" + oneOf[{ const, title }]` |
| Legacy named enum | `legacyEnum` | `type: "string" + enum + enumNames` |
| Untitled multi-select | `untitledMultiEnum` | `type: "array" + items.enum` |
| Titled multi-select | `titledMultiEnum` | `type: "array" + items.anyOf[{ const, title }]` |

Use `.default()` for straightforward Zod-based forms. Use the verbose `enumSchema` API when you need titled variants or multi-select arrays.

---

## URL Elicitation Mode

Some flows should happen **outside** the MCP client form UI. The classic examples are OAuth handoffs, SSO consent, device pairing, payment approval, or other sensitive interactions that belong in the browser.

### When to use URL mode

| Use URL mode for... | Why |
|---|---|
| OAuth / SSO | The provider already owns the browser flow |
| Password or sensitive secrets | Avoid collecting them in the client form |
| External approvals | Human action belongs in a trusted web app |
| Complex onboarding | Browser UI can explain more than a compact form |

```typescript
server.tool(
  {
    name: 'connect-github-account',
    description: 'Send the user to a browser-based GitHub connection flow.',
  },
  async (_args, ctx) => {
    if (!ctx.client.can('elicitation')) return error('Elicitation is not supported by this client.')

    const result = await ctx.elicit(
      'Open the secure browser flow to connect GitHub, then return here.',
      'https://app.example.com/connect/github'
    )

    switch (result.action) {
      case 'accept':
        return text('GitHub connection completed.')
      case 'decline':
        return text('GitHub connection was declined.')
      case 'cancel':
        return text('GitHub connection was cancelled.')
    }
  }
)
```

### Result handling language

Docs often describe these outcomes as **accepted, declined, and cancelled**, while the programmatic `action` values are typically `accept`, `decline`, and `cancel`. Treat them as the same three states.

| Human language | Programmatic value | Meaning |
|---|---|---|
| accepted | `accept` | User completed the step |
| declined | `decline` | User refused to continue |
| cancelled | `cancel` | User aborted mid-flow |

❌ **BAD** — Put password collection in a standard elicitation form:

```typescript
z.object({ password: z.string().describe('Your password') })
```

✅ **GOOD** — Send the user to a secure browser flow instead:

```typescript
const result = await ctx.elicit('Complete sign-in in the browser.', 'https://app.example.com/login')
```

---

## Multi-Step Elicitation Workflows

For longer flows, split the conversation into small validated checkpoints instead of presenting a huge one-shot form.

### Two-step example

```typescript
const basicInfo = await ctx.elicit(
  'Step 1 of 2: Tell me which environment you want.',
  z.object({
    environment: z.enum(['staging', 'production']).describe('Target environment'),
  })
)
if (basicInfo.action !== 'accept') return text('Cancelled at step 1.')

const confirmation = await ctx.elicit(
  `Step 2 of 2: Confirm deployment to ${basicInfo.data.environment}.`,
  z.object({
    confirm: z.boolean().default(false).describe('I understand this is irreversible'),
  })
)
if (confirmation.action !== 'accept' || !confirmation.data.confirm) return text('Deployment not confirmed.')
```

### Multi-step rules

1. Carry forward already-known values in the prompt.
2. Validate and exit early after each step.
3. Keep step count low — two or three is usually enough.
4. Use URL mode for any step that needs a browser.

---

## `ctx.sample()` Model Preferences

Sampling lets the server ask the client LLM to help with summarization, classification, rewriting, extraction, or other bounded reasoning tasks. The most important design choice is being explicit about **how much model control** you need.

### Common sampling options

| Option | Use for |
|---|---|
| `messages` | Multi-turn or role-structured prompts |
| `systemPrompt` | Set LLM behavior and persona |
| `maxTokens` | Bound output length |
| `temperature` | Control determinism |
| `modelPreferences` | Hint the kind of model you want |

### Example with model preferences

```typescript
const result = await ctx.sample({
  messages: [
    {
      role: 'user',
      content: { type: 'text', text: 'Summarize this incident report in three bullets.' },
    },
  ],
  maxTokens: 180,
  temperature: 0.2,
  modelPreferences: {
    intelligencePriority: 0.5,
    speedPriority: 0.8,
  },
})
```

### Model preference trade-offs

`modelPreferences` values are numeric between `0.0` and `1.0`. Higher values express stronger preference.

| Preference | Values | Good for |
|---|---|---|
| `speedPriority` | 0.0–1.0 | Lightweight classification, short summaries |
| `intelligencePriority` | 0.0–1.0 | Complex extraction or nuanced rewriting |
| Balanced (both ~0.5) | — | Most production tools |

❌ **BAD** — Leave `maxTokens` unbounded for repetitive or user-provided prompts:

```typescript
const result = await ctx.sample({ messages })
```

✅ **GOOD** — Bound the output and tune the prompt to the task:

```typescript
const result = await ctx.sample({ messages, maxTokens: 200, temperature: 0.1 })
```

---

## Sampling Callbacks and Progress Hooks

Sampling can take time. If the client and library support progress callbacks, use them to keep the user informed without manually streaming every intermediate detail.

### Callback pattern

```typescript
const result = await ctx.sample(
  'Classify this changelog.',
  {
    maxTokens: 64,
    timeout: 120000,
    progressIntervalMs: 2000,
    onProgress: ({ message }) => {
      console.log(`[Sampling] ${message}`)
    },
  }
)
```

### Callback guidance

| Callback | Use for |
|---|---|
| `onProgress` | High-level stage updates during long completions |

### Result handling

After sampling completes, normalize the result before mixing it into business logic.

```typescript
const summaryText = result.content?.text?.trim() ?? ''
if (!summaryText) return error('The model returned an empty summary.')
return object({ summary: summaryText, model: result.model })
```

---

## Elicitation + Sampling Together

A powerful pattern is: **elicit missing user intent first, then sample with that structured input**.

```typescript
server.tool(
  {
    name: 'generate-release-brief',
    description: 'Ask the user for brief settings, then have the client LLM draft it.',
  },
  async (_args, ctx) => {
    const briefRequest = await ctx.elicit(
      'Choose the release brief style.',
      z.object({
        audience: z.enum(['engineering', 'sales', 'customers']).describe('Audience'),
        tone: z.enum(['concise', 'detailed']).describe('Tone'),
      })
    )

    if (briefRequest.action !== 'accept') return text('Release brief cancelled.')

    const sampled = await ctx.sample({
      messages: [
        {
          role: 'user',
          content: {
            type: 'text',
            text: `Write a ${briefRequest.data.tone} release brief for ${briefRequest.data.audience}.`,
          },
        },
      ],
      maxTokens: 250,
      temperature: 0.3,
    })

    return text(sampled.content.text)
  }
)
```

---

## Safety and UX Checklist

| Question | Why |
|---|---|
| Does the client support elicitation/sampling? | Prevents runtime failures |
| Are all form fields described clearly? | Improves completion quality |
| Are sensitive steps moved to URL mode? | Better security posture |
| Is every action state handled? | Avoids hung tools |
| Are model outputs token-bounded? | Controls cost and latency |
| Are callbacks used for longer operations? | Improves user trust |

❌ **BAD** — Ignore `decline` and `cancel` because only success matters:

```typescript
const result = await ctx.elicit('Approve?', schema)
return text(`Approved by ${result.data.name}`)
```

✅ **GOOD** — Handle all three outcome states explicitly:

```typescript
switch (result.action) {
  case 'accept':
    return text('Approved.')
  case 'decline':
    return text('The user declined.')
  case 'cancel':
    return text('The user cancelled.')
}
```

## Recommended defaults

1. Use **small Zod forms** for simple missing data.
2. Use **URL mode** for auth, secrets, and external approvals.
3. Treat `accept` / `decline` / `cancel` as **accepted / declined / cancelled** states.
4. Use **model preferences + `maxTokens`** for predictable sampling.
5. Add **progress callbacks** for longer sample operations.
