# System Messages and Steering

## systemMessage in SessionConfig

Control how the system prompt is constructed via the `systemMessage` field in `SessionConfig`. Two modes are available: `"append"` (default) and `"replace"`.

```typescript
// Mode omitted — defaults to "append" with no extra content
const session = await client.createSession({
  onPermissionRequest: approveAll,
});

// Explicit append with custom content
const session2 = await client.createSession({
  onPermissionRequest: approveAll,
  systemMessage: {
    mode: "append",
    content: "Always respond in British English. Prefer concise answers.",
  },
});

// Full replacement
const session3 = await client.createSession({
  onPermissionRequest: approveAll,
  systemMessage: {
    mode: "replace",
    content: "You are a specialized SQL assistant. Only answer database-related questions.",
  },
});
```

## systemMessageMode: "append" vs "replace"

### Append Mode (Default)

The SDK manages a foundation system prompt that includes tool definitions, safety guardrails, and Copilot-specific instructions. In `"append"` mode your `content` is appended after these SDK-managed sections.

```typescript
systemMessage: {
  mode: "append",
  content: `
You are helping with the ACME Corp internal tooling project.
- Prefer TypeScript over JavaScript
- Always add JSDoc comments to public APIs
- Follow the existing code style in each file
`,
}
```

Use append mode when:
- You want the standard Copilot tool suite to remain active
- You are adding persona, tone, or project-specific constraints
- You want safety guardrails preserved
- You are extending rather than replacing agent behavior

### Replace Mode

Your `content` becomes the entire system message. All SDK-managed content is removed, including tool definitions, safety restrictions, and Copilot persona.

```typescript
systemMessage: {
  mode: "replace",
  content: `You are a triage bot for GitHub issues.
When given an issue title and body, respond with a JSON object:
{
  "priority": "critical" | "high" | "medium" | "low",
  "labels": string[],
  "assignee": string | null,
  "summary": string
}
Respond with JSON only. No prose.`,
}
```

Use replace mode when:
- You need complete control over the system prompt (LLM-as-API usage)
- The Copilot tool suite is irrelevant (e.g., pure text classification)
- You are building a narrowly scoped system with no agentic capabilities
- You explicitly do not want safety guardrails (accept the risk)

Replace mode removes all SDK guardrails. Test thoroughly before using in production.

## Steering Prompts for Agent Behavior

Steering is injecting a new message into the agent's current turn using `mode: "immediate"`. Use it to redirect the agent mid-work without aborting:

```typescript
// Start a long task
await session.send({ prompt: "Refactor the authentication module to use sessions" });

// Agent is mid-turn — redirect it
await session.send({
  prompt: "Actually, use JWT tokens instead of sessions. Keep the existing interface.",
  mode: "immediate",
});
```

Steering is best-effort within the current turn:
- If the agent is between LLM calls, the steering message is injected before the next call
- If the agent has already committed to a tool call, steering takes effect after that call returns but still within the same turn
- If the turn completes before the steering message is processed, the message is automatically moved to the regular queue for the next turn

Keep steering messages concise and directive. The agent incorporates them into its current reasoning context. Long or ambiguous steering messages reduce effectiveness.

## Queueing Prompts with send() While Session Is Busy

`mode: "enqueue"` (the default) buffers messages for sequential processing after the current turn completes. Each queued message triggers its own full agentic turn. Messages are processed FIFO:

```typescript
// Fire-and-forget pipeline
await session.send({ prompt: "Step 1: set up the project structure" });
await session.send({ prompt: "Step 2: add unit tests for the auth module", mode: "enqueue" });
await session.send({ prompt: "Step 3: update the README with setup instructions", mode: "enqueue" });
// The session processes each step sequentially without further input
```

When the session is idle (not actively processing), both `"immediate"` and `"enqueue"` behave identically — the message starts a new turn immediately. The distinction only matters when the session is busy.

Mode comparison:

| Mode | When session busy | When session idle |
|---|---|---|
| `"enqueue"` (default) | Buffered, processed after current turn | Starts new turn immediately |
| `"immediate"` | Injected into current turn | Starts new turn immediately |

## Multi-Turn Conversation Management

### Monitoring Turn Completion

Use `session.idle` to detect when all queued work is done:

```typescript
session.on("session.idle", () => {
  console.log("All turns complete, session is idle");
});
```

### Building a Sequential Pipeline

Queue all steps upfront and wait for the final response:

```typescript
const session = await client.createSession({
  model: "gpt-4.1",
  onPermissionRequest: approveAll,
});

// Queue all steps before any of them run
await session.send({ prompt: "Audit the codebase for security vulnerabilities" });
await session.send({ prompt: "Fix the critical vulnerabilities found", mode: "enqueue" });
await session.send({ prompt: "Write tests for the fixed code", mode: "enqueue" });

// sendAndWait on the final step — blocks until the whole pipeline finishes
const finalResponse = await session.sendAndWait(
  { prompt: "Generate a security report summarizing all changes" },
  600_000  // 10 minute timeout
);
console.log(finalResponse?.data.content);
```

### Handling Abort Mid-Pipeline

If the agent goes off-track, abort and restart the queue:

```typescript
let aborted = false;

session.on("assistant.message_delta", (event) => {
  if (event.data.deltaContent?.includes("deleting production")) {
    aborted = true;
    session.abort();
  }
});

if (aborted) {
  // Session is still valid after abort
  await session.sendAndWait({
    prompt: "Stop. Do not delete anything. Read-only analysis only.",
    mode: "immediate",
  });
}
```

## System Message vs Custom Agent Prompt Interaction

Custom agents defined via `customAgents` in `SessionConfig` each carry their own `prompt` field. This interacts with `systemMessage` as follows:

- In **append mode**: the agent's prompt is layered on top of the SDK foundation and your `systemMessage.content`
- In **replace mode**: the agent's prompt interacts with only your replacement content

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  systemMessage: {
    mode: "append",
    content: "Project context: ACME internal tooling, TypeScript monorepo.",
  },
  customAgents: [
    {
      name: "security-reviewer",
      prompt: "You are a security expert. Review all code changes for OWASP Top 10 vulnerabilities.",
      tools: ["read_file", "list_directory"],
    },
    {
      name: "test-writer",
      prompt: "You write comprehensive unit and integration tests. Aim for 90%+ coverage.",
      tools: ["read_file", "write_file", "run_terminal_command"],
    },
  ],
  agent: "security-reviewer",  // activate security-reviewer at session start
});
```

Switch agents at runtime:

```typescript
// Switch to test-writer mid-session
await session.rpc.agent.select({ name: "test-writer" });
await session.sendAndWait({ prompt: "Write tests for the changes we just reviewed" });
```

## Best Practices for Prompt Engineering with the SDK

### Write the system message for the agent, not the user

The agent reads the system message on every turn. Keep it directive and stable. Avoid including volatile information (current date, file names, user IDs) in the system message; put that in user messages instead.

```typescript
// Good — stable agent persona
systemMessage: {
  mode: "append",
  content: "You are a backend engineer specializing in Node.js. Always add error handling. Prefer async/await over callbacks.",
}

// Bad — volatile info in system message
systemMessage: {
  mode: "append",
  content: `Today is ${new Date().toDateString()}. Current user: ${userId}.`,
}
```

### Use append mode for behavioral constraints

```typescript
systemMessage: {
  mode: "append",
  content: `
CONSTRAINTS:
- Never delete files without explicit confirmation
- Always create a backup before modifying large files
- Log every tool call to the session timeline with session.log()
- Prefer small, reversible changes over large rewrites
`,
}
```

### Use replace mode only for pure LLM usage

```typescript
// Appropriate: no tools, no agent behavior needed
systemMessage: {
  mode: "replace",
  content: "You are a JSON formatter. Accept arbitrary text and return valid, pretty-printed JSON. Respond with JSON only.",
}
```

### Separate concerns between systemMessage and user prompts

- `systemMessage`: persistent agent identity, behavioral rules, project context
- User messages via `send()`/`sendAndWait()`: specific tasks, inputs, feedback

```typescript
// System message: who the agent is
systemMessage: {
  mode: "append",
  content: "You are an expert at reviewing GitHub pull requests. Be direct and constructive.",
}

// User message: what to do right now
await session.sendAndWait({
  prompt: `Review this PR diff:\n\n${prDiff}`,
  attachments: [{ type: "file", path: "./src/auth.ts" }],
});
```

### Use attachments for large context instead of embedding in prompts

```typescript
// Prefer attachments over string interpolation for files
await session.sendAndWait({
  prompt: "Refactor this file to reduce complexity",
  attachments: [
    { type: "file", path: "./src/complex-module.ts" },
    { type: "directory", path: "./src/utils" },
  ],
});

// Avoid — large strings in prompts consume context faster
await session.sendAndWait({
  prompt: `Refactor this:\n\n${fs.readFileSync("./src/complex-module.ts", "utf-8")}`,
});
```

### Steering message guidelines

- Keep steering messages under 2–3 sentences
- Be explicit about what to change, not just what is wrong
- Avoid multiple steering messages in rapid succession; they can degrade turn quality
- If steering is insufficient, abort and start a new turn with a revised prompt

```typescript
// Good steering — specific correction
await session.send({
  prompt: "Use `const` instead of `let` for all variables that are not reassigned.",
  mode: "immediate",
});

// Poor steering — vague
await session.send({
  prompt: "That doesn't look right.",
  mode: "immediate",
});
```

### Reserve queueing for independent follow-up tasks

Queue tasks that each stand alone as a complete turn, not sub-steps of the current task. Sub-steps should be part of the agent's own plan, not separate queued messages.

```typescript
// Good — each queued message is an independent task
await session.send({ prompt: "Write the authentication module" });
await session.send({ prompt: "Write the authorization module", mode: "enqueue" });
await session.send({ prompt: "Write integration tests for both modules", mode: "enqueue" });

// Avoid — micro-management that the agent should handle internally
await session.send({ prompt: "Write the auth module" });
await session.send({ prompt: "Now add the login function", mode: "enqueue" });
await session.send({ prompt: "Now add the logout function", mode: "enqueue" });
await session.send({ prompt: "Now add password hashing", mode: "enqueue" });
```
