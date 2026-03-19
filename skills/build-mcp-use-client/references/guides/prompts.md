# Prompts

Complete reference for using MCP prompts — listing, retrieval, arguments, completions, and LLM integration.

---

## Understanding Prompts

Prompts are reusable, server-defined templates that return structured messages suitable for LLM conversations. Think of them as parameterized message factories — you call them with arguments and receive an array of role-tagged messages back.

Key characteristics:

- **Named and discoverable** — every prompt has a unique name and description.
- **Accept typed arguments** — prompts are invoked with a params object typed as `T extends Record<string, any>`.
- **Return structured messages** — each message carries a `role` string and typed `content`.
- **Support argument completion** — servers can provide autocomplete suggestions for prompt arguments.
- **Change notifications** — servers emit events when their prompt list changes at runtime.

Prompts are read-only from the client perspective. The server defines them; the client discovers, invokes, and consumes them.

---

## Listing Prompts

Use `session.listPrompts()` to discover all prompts a server exposes.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});

await client.createAllSessions();
const session = client.getSession("myServer");

const prompts = await session.listPrompts();

for (const prompt of prompts) {
  console.log(`Prompt: ${prompt.name}`);
  console.log(`Description: ${prompt.description}`);
}
```

Each prompt in the returned array has this shape:

```typescript
interface PromptInfo {
  name: string;
  description: string;
}
```

---

## Getting a Prompt

Call `session.getPrompt(promptName, params)` to invoke a prompt and receive its messages. The method is generic — `params` is typed as `T extends Record<string, any>`, enabling IDE autocompletion for each prompt's argument schema.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    travel: { url: "http://localhost:3000/mcp" }
  }
});

await client.createAllSessions();
const session = client.getSession("travel");

const result = await session.getPrompt("plan_vacation", {
  destination: "Japan",
  duration: "2 weeks",
  budget: "$5000",
  interests: ["culture", "food", "nature"]
});

console.log(`Prompt description: ${result.description}`);

for (const message of result.messages) {
  console.log(`Role: ${message.role}`);
  if (message.content.text) {
    console.log(`Text: ${message.content.text}`);
  }
}
```

Pass arguments as a plain object. The server validates them against its declared schema.

---

## PromptResult Interface

Every `getPrompt()` call returns a `PromptResult`:

```typescript
interface PromptResult {
  description: string;
  messages: Array<{
    role: string;
    content: {
      text?: string;
      image?: any;
      [key: string]: any;
    };
  }>;
}
```

Check the content shape by testing for property presence:

```typescript
for (const message of result.messages) {
  const role = message.role;

  if ("text" in message.content) {
    const textContent = message.content.text;
    console.log(`${role}: ${textContent}`);
  }

  if ("image" in message.content) {
    console.log(`${role}: [Image content]`);
  }
}
```

| Field | Type | Description |
|---|---|---|
| `description` | `string` | Human-readable description of what the prompt produced |
| `messages` | `Array<PromptMessage>` | Ordered list of messages to feed to an LLM |
| `messages[].role` | `string` | The role for the message in conversation context (e.g., `"user"`, `"assistant"`, `"system"`) |
| `messages[].content` | Object | Content payload — check for `text` or `image` property presence |
| `messages[].content.text` | `string \| undefined` | Present when message carries text content |
| `messages[].content.image` | `any \| undefined` | Present when message carries image content (type depends on server implementation) |

---

## Prompt Arguments

Prompts accept arguments as key-value pairs (`T extends Record<string, any>`). When a prompt declares its arguments, pass them as a plain object to `getPrompt`. The server validates the arguments against its declared schema.

### Discovering available prompts

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    codeServer: { url: "http://localhost:3000/mcp" }
  }
});

await client.createAllSessions();
const session = client.getSession("codeServer");

const prompts = await session.listPrompts();
const codeReview = prompts.find((p) => p.name === "code-review");

if (codeReview) {
  console.log(`${codeReview.name}: ${codeReview.description}`);
}
```

### Passing arguments

```typescript
// Simple string arguments
const result = await session.getPrompt("greeting", {
  name: "Alice",
  language: "Spanish"
});

// Arguments can include arrays — the server receives them as-is
const result2 = await session.getPrompt("plan_vacation", {
  destination: "Japan",
  duration: "2 weeks",
  budget: "$5000",
  interests: ["culture", "food", "nature"]
});
```

### Required vs optional arguments

Servers define which arguments are required. Omitting a required argument causes a server-side error. Optional arguments use server-defined defaults when omitted. Consult the server's documentation or prompt description to know which arguments are expected.

```typescript
// ❌ BAD: Omitting a required argument
const result = await session.getPrompt("code-review", {});
// Error: Missing required argument "code"

// ✅ GOOD: Providing all required arguments
const result = await session.getPrompt("code-review", {
  code: "function add(a, b) { return a + b; }",
  language: "typescript" // optional — server uses default if omitted
});
```

---

## Completion for Prompt Arguments

Servers can provide autocomplete suggestions for prompt arguments. Use `session.complete()` to request them.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    codeServer: { url: "http://localhost:3000/mcp" }
  }
});

await client.createAllSessions();
const session = client.getSession("codeServer");

const result = await session.complete({
  ref: { type: "ref/prompt", name: "code-review" },
  argument: { name: "language", value: "py" }
});

console.log("Suggestions:", result.completion.values);
// e.g. ["python", "pypy"]

console.log("Total available:", result.completion.total);
console.log("Has more:", result.completion.hasMore);
```

The MCP spec limits completion responses to **100 values maximum** per request. Use the `hasMore` flag to determine if additional completions exist beyond the returned set.

---

## CompleteRequestParams

The parameter shape for `session.complete()`:

```typescript
type CompleteRequestParams = {
  ref:
    | { type: "ref/prompt"; name: string }
    | { type: "ref/resource"; uri: string };
  argument: {
    name: string;
    value: string;
  };
};
```

| Field | Type | Description |
|---|---|---|
| `ref.type` | `"ref/prompt" \| "ref/resource"` | Whether completing for a prompt argument or a resource URI template |
| `ref.name` | `string` | Prompt name (when `type` is `"ref/prompt"`) |
| `ref.uri` | `string` | Resource URI template (when `type` is `"ref/resource"`) |
| `argument.name` | `string` | The argument to complete |
| `argument.value` | `string` | Current partial value typed by the user |

---

## CompleteResult

The response from `session.complete()`:

```typescript
type CompleteResult = {
  completion: {
    values: string[];
    total?: number;
    hasMore?: boolean;
  };
};
```

| Field | Type | Description |
|---|---|---|
| `values` | `string[]` | Up to 100 completion suggestions |
| `total` | `number \| undefined` | Total number of matching completions (may exceed `values.length`) |
| `hasMore` | `boolean \| undefined` | `true` if more completions exist beyond the returned values |

---

## Using Prompts with LLMs

The primary use case for prompts is generating messages to feed into an LLM API. Map `PromptResult.messages` directly to the message format your LLM expects.

### OpenAI-compatible APIs

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    assistant: { url: "http://localhost:3000/mcp" }
  }
});

await client.createAllSessions();
const session = client.getSession("assistant");

const promptResult = await session.getPrompt("code-review", {
  code: "function add(a: number, b: number) { return a + b; }",
  language: "typescript"
});

// Map prompt messages to OpenAI message format
const messages = promptResult.messages.map((m) => ({
  role: m.role,
  content: m.content.text ?? ""
}));

// Feed to your LLM API
const response = await fetch("https://api.openai.com/v1/chat/completions", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${process.env.OPENAI_API_KEY}`
  },
  body: JSON.stringify({
    model: "gpt-4",
    messages
  })
});

const completion = await response.json();
console.log(completion.choices[0].message.content);
```

### Appending user context after prompt messages

```typescript
const promptResult = await session.getPrompt("code-review", {
  code: sourceCode,
  language: "typescript"
});

const messages = promptResult.messages.map((m) => ({
  role: m.role as "user" | "assistant" | "system",
  content: m.content.text ?? ""
}));

// Append additional user context after prompt-generated messages
messages.push({
  role: "user",
  content: "Focus especially on error handling and edge cases."
});
```

---

## Multi-Message Prompt Patterns

Prompts commonly return multiple messages to set up context before the main request. A typical pattern is a system message for instructions followed by a user message with the actual task.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    writer: { url: "http://localhost:3000/mcp" }
  }
});

await client.createAllSessions();
const session = client.getSession("writer");

const result = await session.getPrompt("technical_writer", {
  topic: "WebSockets",
  audience: "intermediate developers"
});

// Typical multi-message result:
// messages[0]: { role: "system", content: { text: "You are a technical writer..." } }
// messages[1]: { role: "user",   content: { text: "Write a guide about WebSockets for intermediate developers." } }

for (const msg of result.messages) {
  console.log(`[${msg.role}] ${msg.content.text}`);
}
```

### Handling different content types in messages

```typescript
const result = await session.getPrompt("image_analysis", {
  imageUrl: "https://example.com/photo.jpg"
});

for (const msg of result.messages) {
  if ("text" in msg.content) {
    console.log(`Text: ${msg.content.text}`);
  } else if ("image" in msg.content) {
    console.log(`Image: [image content]`);
  } else {
    console.log(`Other content type`);
  }
}
```

---

## CLI Usage

The `mcp-use` CLI provides commands for interacting with prompts without writing code.

### List all prompts

```bash
npx mcp-use client prompts list
```

### Get a prompt without arguments

```bash
npx mcp-use client prompts get daily_summary
```

### Get a prompt with arguments

```bash
npx mcp-use client prompts get greeting '{"name": "Alice"}'
```

### Get a prompt with JSON output

```bash
npx mcp-use client prompts get greeting '{"name": "Alice"}' --json
```

### Get a prompt with multiple arguments

```bash
npx mcp-use client prompts get code-review '{"code": "const x = 1;", "language": "javascript"}'
```

The CLI prints each message with its role prefix (`[system]`, `[user]`, `[assistant]`) for easy reading.

---

## React Hook Usage

### Basic prompt access with `useMcp`

```typescript
import { useMcp } from "mcp-use/react";

function PromptViewer() {
  const mcp = useMcp({ url: "http://localhost:3000/mcp" });

  if (mcp.state !== "ready") return <div>Connecting...</div>;

  const handleGetPrompt = async () => {
    const result = await mcp.getPrompt("greeting", { name: "Alice" });
    for (const msg of result.messages) {
      console.log(`[${msg.role}] ${msg.content.text}`);
    }
  };

  return <button onClick={handleGetPrompt}>Get Prompt</button>;
}
```

### Server-scoped prompt access with `useMcpServer`

```typescript
import { useMcpServer } from "mcp-use/react";
import { useState } from "react";

function PromptExplorer() {
  const server = useMcpServer("my-server");
  const [messages, setMessages] = useState<Array<{ role: string; text: string }>>([]);

  // Access cached prompts list
  const prompts = server.prompts; // PromptInfo[]

  const handleListPrompts = async () => {
    const freshPrompts = await server.listPrompts();
    console.log("Found prompts:", freshPrompts.length);
  };

  const handleGetPrompt = async (name: string) => {
    const result = await server.getPrompt(name, { language: "en" });
    setMessages(
      result.messages.map((m) => ({
        role: m.role,
        text: m.content.text ?? ""
      }))
    );
  };

  const handleComplete = async () => {
    const result = await server.complete({
      ref: { type: "ref/prompt", name: "code-review" },
      argument: { name: "language", value: "py" }
    });
    console.log("Suggestions:", result.completion.values);
  };

  return (
    <div>
      <h2>Available Prompts</h2>
      <ul>
        {prompts.map((p) => (
          <li key={p.name}>
            <button onClick={() => handleGetPrompt(p.name)}>
              {p.name}: {p.description}
            </button>
          </li>
        ))}
      </ul>

      <h2>Messages</h2>
      {messages.map((m, i) => (
        <div key={i}>
          <strong>[{m.role}]</strong> {m.text}
        </div>
      ))}

      <button onClick={handleComplete}>Test Completion</button>
    </div>
  );
}
```

---

## Prompt Change Notifications

Servers emit `notifications/prompts/list_changed` when their prompt list changes at runtime. Listen for these to keep your UI or agent in sync.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    dynamic: { url: "http://localhost:3000/mcp" }
  }
});

await client.createAllSessions();
const session = client.getSession("dynamic");

// Initial load
let currentPrompts = await session.listPrompts();
console.log("Initial prompts:", currentPrompts.length);

// Listen for changes
session.on("notification", async (notification) => {
  if (notification.method === "notifications/prompts/list_changed") {
    currentPrompts = await session.listPrompts();
    console.log("Prompts updated:", currentPrompts.length);

    // Diff and log changes
    const names = currentPrompts.map((p) => p.name);
    console.log("Current prompt names:", names);
  }
});
```

### Re-fetching prompts on change in React

```typescript
import { useMcpServer } from "mcp-use/react";
import { useEffect, useState } from "react";

function LivePromptList() {
  const server = useMcpServer("my-server");
  const [prompts, setPrompts] = useState(server.prompts);

  useEffect(() => {
    // The hook automatically re-renders when prompts change via notifications.
    // Access server.prompts to get the latest list.
    setPrompts(server.prompts);
  }, [server.prompts]);

  return (
    <ul>
      {prompts.map((p) => (
        <li key={p.name}>{p.name}</li>
      ))}
    </ul>
  );
}
```

---

## Error Handling

Handle errors when working with prompts. Common failure modes include missing prompts, invalid arguments, and unsupported capabilities.

### Catching prompt errors

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});

await client.createAllSessions();
const session = client.getSession("myServer");

try {
  const result = await session.getPrompt("nonexistent_prompt", {});
} catch (error) {
  if (error instanceof Error) {
    console.error("Failed to get prompt:", error.message);
  }
}
```

### Checking server capabilities before completing

```typescript
const capabilities = session.serverCapabilities;

if (capabilities?.completions) {
  const result = await session.complete({
    ref: { type: "ref/prompt", name: "code-review" },
    argument: { name: "language", value: "py" }
  });
  console.log("Suggestions:", result.completion.values);
} else {
  console.log("Server does not support completions");
}
```

### Error reference table

| Error | Cause | Solution |
|---|---|---|
| Prompt not found | Calling `getPrompt()` with a name that doesn't exist | List prompts first to verify the name |
| Missing required argument | Omitting an argument the prompt requires | Consult the server's documentation or prompt description for required fields |
| Invalid argument type | Passing a non-string value where a string is expected | Serialize complex values with `JSON.stringify()` |
| Client not ready | Calling `complete()` before the session is connected | Wait for session initialization to finish |
| Method not found (`-32601`) | Server doesn't implement the completions capability | Check `serverCapabilities?.completions` before calling |
| Not completable | Argument exists but the server doesn't provide completions for it | Only request completions for arguments the server supports |

---

## Common Mistakes

### Ignoring message roles

```typescript
// ❌ BAD: Ignoring the role field in prompt messages
const result = await session.getPrompt("code-review", { code: sourceCode });
const flatText = result.messages.map((m) => m.content.text).join("\n");
// Loses role context — LLM won't know which messages are system vs user

// ✅ GOOD: Preserving roles when feeding to LLM
const result = await session.getPrompt("code-review", { code: sourceCode });
const messages = result.messages.map((m) => ({
  role: m.role,
  content: m.content.text ?? ""
}));
// Each message retains its role for proper LLM conversation structure
```

### Not handling empty prompt results

```typescript
// ❌ BAD: Not handling empty prompt results
const result = await session.getPrompt("maybe_empty", {});
const firstMessage = result.messages[0].content.text;
// TypeError if messages array is empty

// ✅ GOOD: Checking messages array length
const result = await session.getPrompt("maybe_empty", {});
if (result.messages.length === 0) {
  console.warn("Prompt returned no messages");
} else {
  const firstMessage = result.messages[0].content.text;
  console.log(firstMessage);
}
```

### Requesting completions without checking capabilities

```typescript
// ❌ BAD: Requesting completion without checking server capabilities
const completions = await session.complete({
  ref: { type: "ref/prompt", name: "code-review" },
  argument: { name: "language", value: "py" }
});
// Throws if server doesn't support completions

// ✅ GOOD: Checking capabilities first
if (session.serverCapabilities?.completions) {
  const completions = await session.complete({
    ref: { type: "ref/prompt", name: "code-review" },
    argument: { name: "language", value: "py" }
  });
  console.log(completions.completion.values);
} else {
  console.log("Completions not supported — skip autocomplete UI");
}
```

### Hardcoding prompt names without discovery

```typescript
// ❌ BAD: Hardcoding prompt names without checking availability
const result = await session.getPrompt("v2_summary", { text: content });

// ✅ GOOD: Discovering prompts first, then using them
const prompts = await session.listPrompts();
const summaryPrompt = prompts.find((p) => p.name.includes("summary"));
if (summaryPrompt) {
  const result = await session.getPrompt(summaryPrompt.name, { text: content });
  console.log(result.messages);
} else {
  console.warn("No summary prompt available on this server");
}
```

---

## Browser Usage

Use `mcp-use/browser` for browser environments. The API surface is identical.

```typescript
import { MCPClient } from "mcp-use/browser";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});

await client.createAllSessions();
const session = client.getSession("myServer");

const prompts = await session.listPrompts();
const result = await session.getPrompt(prompts[0].name, {});
console.log(result.messages);
```

---

## Summary

| Operation | Method | Returns |
|---|---|---|
| List all prompts | `session.listPrompts()` | `PromptInfo[]` |
| Get a prompt | `session.getPrompt<T>(promptName, params)` | `PromptResult` |
| Autocomplete an argument | `session.complete(params)` | `CompleteResult` |
| Listen for changes | `session.on("notification", cb)` | Notification events |
| List prompts (React) | `server.listPrompts()` | `PromptInfo[]` |
| Get prompt (React) | `server.getPrompt<T>(promptName, params)` | `PromptResult` |
| Cached prompts (React) | `server.prompts` | `PromptInfo[]` |
| List prompts (CLI) | `npx mcp-use client prompts list` | Stdout |
| Get prompt (CLI) | `npx mcp-use client prompts get <name> [args]` | Stdout |
