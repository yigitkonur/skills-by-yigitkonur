# Memory Management

Memory controls how an MCPAgent retains conversation history across runs, enabling multi‑turn workflows or fully stateless calls.

---

## Scope and goals

Use this guide to build reliable, token‑aware memory behavior with MCPAgent. It covers:

- `memoryEnabled` (default `true`)
- `clearConversationHistory()` and `getConversationHistory()`
- Token and cost implications
- Multi‑turn conversation patterns
- Stateless mode (`memoryEnabled: false`)
- Conversation window and budget strategies

This is not a primer on LLM prompting. It is a production guide for memory control.

---

## Key imports

Always import from `mcp-use` in this skill.

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
```

---

## MCPAgent memory options

### Constructor options

| Option | Type | Default | Purpose | When to use |
|---|---|---|---|---|
| `memoryEnabled` | `boolean` | `true` | Enable internal conversation history | Multi‑turn workflows, follow‑ups |
| `maxSteps` | `number` | `5` | Cap tool‑calling steps per run | Cost control, deterministic runs |
| `autoInitialize` | `boolean` | `false` | Automatically establish MCP server connections on construction | Set `true` for early startup failure detection; set `false` to initialize manually |
| `systemPrompt` | `string \| null` | `null` | Custom system prompt (overrides framework default) | Domain‑specific constraints |
| `additionalInstructions` | `string \| null` | `null` | Extra instructions appended to the system prompt | Lightweight policy tuning |
| `disallowedTools` | `string[]` | `[]` | Tool block list | Safety and policy enforcement |

### Memory methods

| Method | Signature | Return | Purpose |
|---|---|---|---|
| `clearConversationHistory()` | `(): void` | `void` | Clear all stored messages (system message preserved if present) |
| `getConversationHistory()` | `(): Message[]` | `Message[]` | Returns a copy of the current conversation history as an array of message objects |

### `run` method signature

`run` accepts either an options object (preferred) or a plain string (deprecated):

```typescript
// Options object — preferred form
async run<T = string>(options: {
  prompt: string;           // user query
  schema?: ZodSchema<T>;    // optional Zod schema for structured typed output
  maxSteps?: number;        // override constructor maxSteps for this call only
  signal?: AbortSignal;     // cancel the run via AbortController
}): Promise<T>

// Plain string — still works but deprecated
await agent.run("Summarize the project");
```

When `schema` is provided, the return value is typed according to the Zod schema. When omitted, the return is a `string`.

Memory state is controlled by the constructor `memoryEnabled` option, not by a per-call flag. To get a stateless result from a stateful agent, use a separate agent instance with `memoryEnabled: false`.

---

## Structured output

Pass a Zod schema to `run` to receive a typed result instead of raw text. Memory behavior is unchanged.

```typescript
import { z } from "zod";

const result = await agent.run({
  prompt: "Analyze the file structure",
  schema: z.object({
    totalFiles: z.number(),
    fileTypes: z.array(z.string()),
    largestFile: z.string(),
  }),
});

console.log(result.totalFiles); // typed as number
```

Structured output works with both `memoryEnabled: true` and `memoryEnabled: false`.

---

## Quick start: memory on (default)

Use memory to carry context from one run to the next.

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "./"],
    },
  },
});
await client.createAllSessions();

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o-mini" }),
  client,
  memoryEnabled: true,
});

await agent.run("Summarize the repository");
await agent.run("Now list the top 5 risks from that summary");
```

---

## Quick start: stateless mode

Use `memoryEnabled: false` to make every `run` independent.

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4.1" }),
  client: new MCPClient({ mcpServers: {} }),
  memoryEnabled: false,
});

const response = await agent.run("Explain the token budget for this single request only");
```

---

## How conversation memory works

MCPAgent stores a list of conversation messages across runs when `memoryEnabled` is true.

1. `run(prompt)` receives your prompt string.
2. The agent appends a **user message** to its internal history.
3. The agent streams and calls tools as needed.
4. The final **assistant message** is appended to history.
5. On the next `run`, the full history is replayed.

This makes the agent *stateful* by default. You must manage history size and scope.

---

## What counts as “memory”

Memory is the **conversation history** used to build the prompt for every new run. It is not:

- Server‑side state in MCP servers
- External storage (databases, files)
- Tool results that are not embedded into the conversation

If you need durable state across sessions, store it explicitly in your own systems.

---

## Inspecting memory

Use `getConversationHistory()` to view the memory buffer. It returns a copy of the stored `Message[]` array.

```typescript
const history = agent.getConversationHistory();
console.log(`Current history has ${history.length} messages`);
for (const msg of history) {
  console.log(msg.constructor.name, msg.content);
}
```

### Suggested handling

- **Do** log message counts, not full contents, in production
- **Do** redact PII before logging
- **Do** use history inspection during debugging and tuning

---

## Clearing memory

Use `clearConversationHistory()` to reset the agent for a new user, project, or workflow.

> **Note:** If `memoryEnabled` is `true` and a system message exists, it will be preserved after clearing. All other messages are removed.

```typescript
agent.clearConversationHistory();
await agent.run("Start a fresh analysis");
```

When to clear:

- After a workflow completes
- Before switching user contexts
- When a conversation drifts off‑topic
- When you want a deterministic “first run”

---

## Memory and token usage

Memory increases prompt size. More history ⇒ more tokens ⇒ higher cost and latency.

### Example token impact

| History size | Approx messages | Prompt tokens | Typical effect |
|---|---|---|---|
| Small | 4–8 | 800–1,600 | Minimal overhead |
| Medium | 12–20 | 2,000–4,000 | Moderate cost increase |
| Large | 30+ | 6,000+ | Slow and expensive |

Token counts vary by model and message length. Always measure in your environment.

---

## Token budget strategies

Use these strategies to keep memory manageable:

1. **Summarize early**: Replace long discussions with compact summaries.
2. **Trim tool outputs**: Avoid dumping entire logs into the conversation.
3. **Windowed history**: Keep only the last N messages.
4. **Session‑based clearing**: Clear between tasks or users.
5. **Explicit boundaries**: Add “New task begins” markers for the agent.
6. **Stateless runs**: Disable memory when you don’t need continuity.

---

## Memory window management

MCPAgent does not automatically trim history. If your app needs a fixed window, you must do it manually.

### Manual windowing pattern

```typescript
const maxMessages = 12;
const history = agent.getConversationHistory();

if (history.length > maxMessages) {
  const trimmed = history.slice(history.length - maxMessages);
  agent.clearConversationHistory();
  for (const message of trimmed) {
    // Re‑inject messages by running a synthetic prompt
    // or by re‑feeding them through your own logic.
  }
}
```

### Summary‑then‑clear pattern

1. Ask the agent to summarize the conversation so far.
2. Store that summary externally or keep it in memory.
3. Clear the history and re‑seed with the summary.

```typescript
const summary = await agent.run("Summarize the key decisions so far in 8 bullet points");

agent.clearConversationHistory();
await agent.run(`Use this summary as context:\n${summary}`);
```

---

## Multi‑turn conversation patterns

Use memory to coordinate longer flows. Each pattern below assumes `memoryEnabled: true`.

### Pattern 1: Stepwise refinement

- Run an initial draft
- Ask for improvements
- Ask for validation

```typescript
await agent.run("Draft a one‑page migration plan");
await agent.run("Now add rollout phases and rollback criteria");
await agent.run("Review for missing risks");
```

### Pattern 2: Progressive constraints

- Start broad
- Add policy constraints
- Re‑evaluate

```typescript
await agent.run("Propose an API naming scheme");
await agent.run("Conform to our kebab‑case style guide");
await agent.run("Check for conflicts with existing endpoints");
```

### Pattern 3: Tool‑assisted exploration

- Ask agent to scan
- Follow up on results

```typescript
await agent.run("Find all auth middleware files");
await agent.run("Summarize how each middleware handles JWT");
```

### Pattern 4: Decision capture

- Produce options
- Decide
- Persist decision

```typescript
await agent.run("List three storage options and tradeoffs");
await agent.run("Pick the best option for multi‑tenant use");
await agent.run("Write down the final decision");
```

### Pattern 5: Multi‑persona workflow

- Ask for an architect view
- Ask for an operator view
- Ask for a PM view

```typescript
await agent.run("As an architect, identify core risks");
await agent.run("As an operator, suggest monitoring");
await agent.run("As a PM, define launch checklist");
```

### Pattern 6: Iterative spec writing

- Start with requirements
- Add edge cases
- Finalize output

```typescript
await agent.run("Draft requirements for a webhook system");
await agent.run("Add failure modes and retries");
await agent.run("Finalize with a delivery checklist");
```

### Pattern 7: Data extraction

- Ask agent to parse
- Ask to validate

```typescript
await agent.run("Extract all deadlines from this document");
await agent.run("Verify if any deadlines conflict");
```

### Pattern 8: Re‑cap alignment

- Ask for recap
- Ask for next steps

```typescript
await agent.run("Summarize what we agreed on");
await agent.run("List next steps with owners");
```

### Pattern 9: Policy enforcement

- Start with draft
- Apply policy
- Validate compliance

```typescript
await agent.run("Draft user‑visible error messages");
await agent.run("Apply our accessibility language policy");
await agent.run("Check for jargon and simplify");
```

### Pattern 10: Incident investigation

- Gather symptoms
- Identify likely root causes
- Generate mitigation steps

```typescript
await agent.run("Summarize incident timeline from logs");
await agent.run("Identify top three likely root causes");
await agent.run("Propose mitigation steps");
```

---

## Stateless patterns (memory disabled)

Use these when each request must be isolated:

- API endpoints serving user requests
- Multi‑tenant systems with untrusted inputs
- Batch jobs where each item is independent

```typescript
const statelessAgent = new MCPAgent({
  llm,
  client,
  memoryEnabled: false,
});

const response = await statelessAgent.run("Generate a one‑off report for customer 123");
```

### Stateless batch processing

```typescript
for (const item of items) {
  const result = await statelessAgent.run(`Classify this item: ${item}`);
  saveResult(item, result);
}
```

---

## Memory boundaries by user

Never share memory across users unless you explicitly intend to.

### Per‑user agent pattern

```typescript
const agentByUser = new Map<string, MCPAgent>();

function getAgentForUser(userId: string): MCPAgent {
  let agent = agentByUser.get(userId);
  if (!agent) {
    agent = new MCPAgent({ llm, client, memoryEnabled: true });
    agentByUser.set(userId, agent);
  }
  return agent;
}
```

### Session cleanup

```typescript
function closeUserSession(userId: string) {
  const agent = agentByUser.get(userId);
  if (!agent) return;
  agent.clearConversationHistory();
  agentByUser.delete(userId);
}
```

---

## Conversation history structure (conceptual)

Your history is a list of message objects. Treat them as opaque but loggable for debugging.

```typescript
[
  { role: "user", content: "Summarize project risks" },
  { role: "assistant", content: "Here are the top risks..." },
]
```

---

## Memory and tool outputs

Tool outputs can balloon token usage.

**Do:**

- Summarize tool results before re‑injecting them
- Extract only the fields the next step needs
- Use server tools to store data rather than embedding it

**Avoid:**

- Large raw logs
- Full JSON dumps without trimming
- Multi‑MB file contents in a single response

---

## Defining a memory budget

Set budgets for:

- **Max messages** (e.g., 12)
- **Max total tokens** (e.g., 4k)
- **Max tool output size** (e.g., 10 KB)

Then build guardrails in your code.

```typescript
const MAX_TOOL_OUTPUT = 10_000; // chars

function trimToolOutput(text: string) {
  return text.length > MAX_TOOL_OUTPUT ? text.slice(0, MAX_TOOL_OUTPUT) + "…" : text;
}
```

---

## When to clear vs summarize

| Situation | Use clear | Use summary |
|---|---|---|
| New user session | ✅ | ❌ |
| Long running task | ❌ | ✅ |
| Sensitive data surfaced | ✅ | ❌ |
| Memory exceeded budget | ✅ | ✅ |

---

## Memory and determinism

Memory introduces variability because the prompt changes on every run.

To improve determinism:

- Clear history before critical operations
- Limit history window size
- Use explicit instructions to freeze requirements

---

## Memory with streaming

Memory applies equally to `run`, `stream`, `streamEvents`, and `prettyStreamEvents`. Streaming does not bypass memory.

All streaming methods accept the options-object form shown below, and the older plain-string overloads remain for compatibility. Prefer the options object so memory-sensitive code can pass `maxSteps`, `schema`, or `signal` without changing call shape.

```typescript
// Step-by-step tool streaming — yields AgentStep { action: { tool, toolInput, log }, observation }
for await (const step of agent.stream({ prompt: "Analyze the logs", maxSteps: 20 })) {
  console.log(`Tool: ${step.action.tool}`);
}

// Pretty CLI streaming — auto-formatted, suitable for terminal output
for await (const _ of agent.prettyStreamEvents({ prompt: "Analyze the codebase", maxSteps: 20 })) {
  // formatted output printed automatically
}

// Low-level event streaming — yields { event: string; data?: { chunk?: { content?: string } } }
for await (const ev of agent.streamEvents({ prompt: "Generate content" })) {
  if (ev.event === "on_chat_model_stream") {
    process.stdout.write(ev.data?.chunk?.content ?? "");
  }
}
```

---

## Security and compliance

Memory can store secrets. Handle it as you would any sensitive log.

- Redact PII before persistence
- Clear memory after handling secrets
- Avoid cross‑tenant history sharing
- Ensure audit logs do not include raw memory by default

---

## ❌ BAD / ✅ GOOD patterns

### 1) Sharing memory across users

❌ BAD
```typescript
const sharedAgent = new MCPAgent({ llm, client, memoryEnabled: true });

app.post("/ask", async (req, res) => {
  const answer = await sharedAgent.run(req.body.question);
  res.json({ answer });
});
```

✅ GOOD
```typescript
const agentByUser = new Map<string, MCPAgent>();

app.post("/ask", async (req, res) => {
  const userId = req.user.id;
  const agent = agentByUser.get(userId) ?? new MCPAgent({ llm, client, memoryEnabled: true });
  agentByUser.set(userId, agent);
  const answer = await agent.run(req.body.question);
  res.json({ answer });
});
```

### 2) Letting memory grow without bounds

❌ BAD
```typescript
while (true) {
  await agent.run("Continue");
}
```

✅ GOOD
```typescript
const MAX_TURNS = 10;
let turns = 0;

while (turns < MAX_TURNS) {
  await agent.run("Continue");
  turns += 1;
}
agent.clearConversationHistory();
```

### 3) Logging full history in production

❌ BAD
```typescript
console.log(agent.getConversationHistory());
```

✅ GOOD
```typescript
const history = agent.getConversationHistory();
console.log({ count: history.length, lastRole: history.at(-1)?.role });
```

---

## Memory checklist (use before launch)

- [ ] Define whether memory is required for this workflow
- [ ] Set `memoryEnabled` explicitly (avoid ambiguity)
- [ ] Establish history limits (messages, tokens, tool output)
- [ ] Decide when to clear history
- [ ] Decide when to summarize history
- [ ] Prevent cross‑user memory contamination
- [ ] Redact sensitive data in logs
- [ ] Verify token costs under peak load

---

## Frequently asked questions

### Does memory affect tool selection?

Yes. Memory contributes to the prompt, which influences tool selection and reasoning.

### Is memory persisted to disk?

No. MCPAgent memory is in‑process. Persist it yourself if needed.

### Can I pre‑seed memory?

Use a first `run` with a prompt like “Use this context…” or inject a synthetic summary.

### Is memory shared across `stream` and `run` calls?

Yes. Memory is global to the agent instance.

### Can I disable memory temporarily?

`memoryEnabled` is a constructor option, not a per-call option. To get a stateless single call, create a separate agent with `memoryEnabled: false`:

```typescript
const statelessAgent = new MCPAgent({ llm, client, memoryEnabled: false });
const result = await statelessAgent.run({ prompt: "One-off stateless query" });
await statelessAgent.close();
```

If you need both stateful and stateless behavior from the same session, maintain two agent instances pointing to the same `MCPClient`.

---

## Reference: recommended memory policies

### Policy A: Short tasks (stateless)

- `memoryEnabled: false`
- One run per request
- No history inspection

### Policy B: Medium tasks (bounded memory)

- `memoryEnabled: true`
- Window to last 10–15 messages
- Summarize at 10 messages

### Policy C: Long tasks (summary loops)

- `memoryEnabled: true`
- Summarize every 5–8 steps
- Clear and re‑seed with summary

---

## Extended examples

### Example: Document analysis with rolling summary

```typescript
const agent = new MCPAgent({ llm, client, memoryEnabled: true });

const intro = await agent.run("Read the doc and summarize key sections");

const deeper = await agent.run("Add risks and compliance notes");

const summary = await agent.run("Summarize our findings in 6 bullets");

agent.clearConversationHistory();
await agent.run(`Context summary:\n${summary}`);
```

### Example: Multi‑turn Q&A with explicit reset

```typescript
await agent.run("Explain our SLO policy");
await agent.run("Give two examples");
agent.clearConversationHistory();
await agent.run("Now switch to our incident policy");
```

### Example: Dual‑agent strategy (stateful + stateless)

```typescript
const stateful = new MCPAgent({ llm, client, memoryEnabled: true });
const stateless = new MCPAgent({ llm, client, memoryEnabled: false });

await stateful.run("Plan a migration");
await stateful.run("Add risks");

await stateless.run("Summarize the final plan only");
```

---

## Troubleshooting memory issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Responses drift over time | History too long | Summarize or clear |
| High latency | Large token window | Trim tool output, reduce window |
| Conflicting instructions | Old prompt persists | Clear history and re‑seed |
| Sensitive data appears | Memory not cleared | Clear after sensitive steps |

---

## Summary

- Memory is **on by default** (`memoryEnabled: true`).
- It increases token usage and affects determinism.
- Use `clearConversationHistory()` for resets.
- Use `getConversationHistory()` for debugging only.
- Use stateless mode for per‑request isolation.
