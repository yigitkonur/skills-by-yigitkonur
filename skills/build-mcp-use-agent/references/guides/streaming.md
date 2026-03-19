# Streaming

Complete guide to real-time agent execution using stream(), streamEvents(), and prettyStreamEvents().

---

## 1. Overview

When building agentic applications, you often have a choice between waiting for a final answer or streaming the progress.

**Use `run()` when:**
- The task is short and low-latency (e.g., < 2 seconds).
- You only care about the final answer.
- You are running a background job without a user interface.
- You need a simple Promise-based API.
- You are writing a script where intermediate output is just noise.

**Use streaming when:**
- The task involves multiple tool calls (agents are slow).
- You need to show "thinking" indicators to the user (e.g., "Reading file...", "Searching web...").
- You want to display partial text as it is generated (the "typewriter" effect).
- You are building a chat interface.
- You need to debug the agent's decision-making process in real-time.
- You want to allow the user to interrupt the process if the agent goes down a wrong path.

### The Three Modes

| Mode | Method | Returns | Best For |
|---|---|---|---|
| **Step-by-Step** | `agent.stream()` | `AsyncGenerator<AgentStep, string, void>` | Debugging, logging, custom UIs that update per tool call. High-level logic. |
| **Token-Level** | `agent.streamEvents()` | `AsyncGenerator<StreamEvent, void, void>` | Chat interfaces, real-time text streaming. Low-level control. |
| **CLI Pretty** | `agent.prettyStreamEvents()` | `AsyncGenerator<void, string, void>` | Terminal applications requiring zero-config formatting. Fast prototyping. |

---

## 2. AgentStep Type Reference

The `agent.stream()` method yields `AgentStep` objects. Each step represents one cycle of the agent's loop where a tool is selected and called.

> **Important:** `step.observation` may be populated or empty depending on execution order. The agent tracks tool results internally. When using `for await`, the `observation` field reflects the tool result for that step. When manually calling `.next()`, the `observation` field on yielded steps may be empty; only the generator's return value (when `done === true`) contains the final string result.

### Type Definition

```typescript
export interface AgentStep {
  action: {
    /**
     * The name of the tool selected by the agent.
     * Example: "playwright_navigate", "read_file"
     */
    tool: string;

    /**
     * The input parameters passed to the tool.
     * This is a fully typed object matching the tool's schema.
     *
     * Example: { url: "https://example.com" }
     */
    toolInput: any;

    /**
     * The agent's reasoning log for this step.
     */
    log: string;
  };

  /**
   * The output returned by the tool execution.
   * May be populated when using for-await iteration.
   * When manually calling .next(), only the generator return value
   * (done === true, value = final string) contains the complete result.
   */
  observation: string;
}
```

### Runtime Example

Here is what an actual `AgentStep` object looks like when yielded during streaming:

```json
{
  "action": {
    "tool": "playwright_navigate",
    "toolInput": {
      "url": "https://news.python.org"
    }
  },
  "observation": ""
}
```

### Field Reference

| Field | Type | Description |
|---|---|---|
| `action.tool` | `string` | The identifier of the tool being executed. Matches the tool name from the MCP server. |
| `action.toolInput` | `any` | The arguments passed to the tool. Useful for showing the user what the agent is doing (e.g., which URL is being visited). |
| `observation` | `any` | **Empty at yield time.** Tool results are tracked internally and not populated in the step object during streaming. |

---

## 3. stream() — Step-by-Step Streaming

Use `agent.stream()` when you want to process the agent's execution one step at a time. This is higher level than `streamEvents()` but lower level than `run()`.

This method accepts either a **plain string prompt** (deprecated but supported) or a **`RunOptions` object**.

### Signatures

```typescript
// Options object form (preferred)
agent.stream(options: { prompt: string; maxSteps?: number; schema?: ZodSchema<T>; signal?: AbortSignal }): AsyncGenerator<AgentStep, string | T, void>

// Plain string form (deprecated but still works)
agent.stream(prompt: string): AsyncGenerator<AgentStep, string, void>
```

When the generator completes (`done === true`), the `value` is the final string (or typed value if `schema` was provided).

### Example: Logging each step

```typescript
import { ChatOpenAI } from '@langchain/openai'
import { MCPAgent, MCPClient } from 'mcp-use'

async function stepStreamingExample() {
  const config = {
    mcpServers: {
      playwright: {
        command: 'npx',
        args: ['@playwright/mcp@latest']
      }
    }
  }

  const client = new MCPClient(config)
  const llm = new ChatOpenAI({ model: 'gpt-4o' })
  const agent = new MCPAgent({ llm, client })

  console.log('Agent is working...')
  console.log('-'.repeat(50))

  for await (const step of agent.stream('Search for the latest Python news and summarize it')) {
    console.log(`\nTool: ${step.action.tool}`)
    console.log(`Input: ${JSON.stringify(step.action.toolInput)}`)
    console.log(`Output: ${step.observation}`)
  }

  console.log('\nDone!')
  await client.closeAllSessions()
}

stepStreamingExample().catch(console.error)
```

> **Note:** `stream()` is primarily useful for showing which tool is being called and with what inputs. The generator's return value (when `done === true` via `.next()`) is the final string result. For token-level visibility, use `streamEvents()`.

---

## 4. streamEvents() — Raw Event Stream

Use `agent.streamEvents()` for maximum control. This exposes the underlying LangChain event stream, giving you access to individual tokens as they are generated by the LLM, as well as lifecycle events for tools and chains.

This method accepts either a **plain string prompt** (deprecated but supported) or a **`RunOptions` object**.

### Signatures

```typescript
// Options object form (preferred)
agent.streamEvents(options: { prompt: string; schema?: ZodSchema<T>; maxSteps?: number; signal?: AbortSignal }): AsyncGenerator<StreamEvent, void, void>

// Plain string form (deprecated but still works)
agent.streamEvents(prompt: string): AsyncGenerator<StreamEvent, void, void>
```

### Event Types Reference

The streaming API is based on LangChain's `streamEvents` method. Key event types include:

| Event Name | Description | Key Payload |
|---|---|---|
| `on_chat_model_stream` | Fired for every token generated by the LLM. | `event.data?.chunk?.text` or `event.data?.chunk?.content` |
| `on_tool_start` | Fired when a tool is about to be called. | `event.name`, `event.data.input` |
| `on_tool_end` | Fired when a tool finishes execution. | `event.name`, `event.data.output` |
| `on_chain_start` | Fired when the agent loop starts. | `event.name` |
| `on_chain_end` | Fired when the agent loop finishes. | `event.name`, `event.data.output` |

For the full list of event types and data structures, see the [LangChain JavaScript streaming documentation](https://js.langchain.com/docs/how_to/streaming/).

### Event Chunk Property Compatibility

The chunk property on `on_chat_model_stream` events may be `text` (Anthropic and some providers) or `content` (OpenAI and others) depending on the LangChain version and LLM provider. Always check both:

```typescript
const text = event.data?.chunk?.text || event.data?.chunk?.content
```

### Example: Token-by-Token Streaming

```typescript
import { ChatOpenAI } from '@langchain/openai'
import { MCPAgent, MCPClient } from 'mcp-use'

async function basicStreamingExample() {
  const config = {
    mcpServers: {
      playwright: {
        command: 'npx',
        args: ['@playwright/mcp@latest']
      }
    }
  }

  const client = new MCPClient(config)
  const llm = new ChatOpenAI({ model: 'gpt-4o' })
  const agent = new MCPAgent({ llm, client })

  console.log('Agent is working...')

  for await (const event of agent.streamEvents('Search for the latest Python news and summarize it')) {
    if (event.event === 'on_chat_model_stream') {
      // Stream LLM output token by token
      // Note: chunk property may be 'text' or 'content' depending on LLM provider
      const text = event.data?.chunk?.text || event.data?.chunk?.content
      if (text) {
        process.stdout.write(text)
      }
    }
  }

  console.log('\n\nDone!')
  await client.closeAllSessions()
}

basicStreamingExample().catch(console.error)
```

### Example: Handling Multiple Event Types

```typescript
for await (const event of agent.streamEvents('Analyze the server logs')) {
  switch (event.event) {
    case 'on_chat_model_stream': {
      const token = event.data?.chunk?.text || event.data?.chunk?.content || ''
      if (token) process.stdout.write(token)
      break
    }

    case 'on_tool_start':
      console.log(`\n[Tool Start] ${event.name}`)
      console.log(`Input:`, event.data.input)
      break

    case 'on_tool_end': {
      console.log(`\n[Tool End] ${event.name}`)
      const output = JSON.stringify(event.data.output)
      console.log(`Output:`, output.length > 100 ? output.slice(0, 100) + '...' : output)
      break
    }

    case 'on_chain_end':
      if (event.name === 'AgentExecutor') {
        console.log('\n[System] Agent finished.')
        console.log('Final Answer:', event.data.output)
      }
      break

    default:
      // Ignore other events (prompt generation, model start, etc.)
      break
  }
}
```

### Filtering Events

Filter for only the events you need to reduce noise and improve performance:

```typescript
// Only listen to token events for a text-only stream
for await (const event of agent.streamEvents(prompt)) {
  if (event.event === 'on_chat_model_stream') {
    // process token
  }
}
```

---

## 5. prettyStreamEvents() — CLI Output

For command-line tools, `mcp-use` includes a built-in formatter that pretty-prints the event stream with ANSI colors and syntax highlighting. This is the fastest way to get professional-looking CLI output without writing your own formatter.

This method always accepts an **options object** (unlike `stream()` and `streamEvents()`, there is no plain string form).

### Signature

```typescript
agent.prettyStreamEvents(options: {
  prompt: string
  maxSteps?: number
  schema?: ZodSchema<T>  // Optional: for structured output
}): AsyncGenerator<void, string, void>
```

### Usage

```typescript
import { MCPAgent } from 'mcp-use'

async function prettyStreamExample() {
  const agent = new MCPAgent({
    llm: 'openai/gpt-4o',
    mcpServers: {
      filesystem: {
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-filesystem', './']
      }
    }
  })

  // Pretty streaming with automatic formatting and colors
  for await (const _ of agent.prettyStreamEvents({
    prompt: 'List all TypeScript files and count the total lines of code',
    maxSteps: 20
  })) {
    // Just iterate - all formatting is handled automatically by the library
  }

  await agent.close()
}

prettyStreamExample().catch(console.error)
```

### Features

The `prettyStreamEvents()` method automatically handles:

- **Syntax highlighting**: JSON and code are highlighted with colors.
- **Tool call formatting**: Clear display of tool names and inputs.
- **Progress indicators**: Visual feedback during execution.
- **Token streaming**: Real-time LLM output display.
- **Error formatting**: Clear error messages with context.

> **Terminal Compatibility:** The pretty output uses ANSI color codes and works best in modern terminals. For environments without color support, the output gracefully degrades to plain text.

---

## 6. Streaming Error Handling

Errors can occur mid-stream (e.g., a tool fails, network drops, or context limit is reached). Since streams are asynchronous generators, wrap the consumption loop in a `try/catch` block.

### Handling Errors in the Loop

```typescript
try {
  for await (const step of agent.stream('...')) {
    processStep(step)
  }
} catch (error) {
  // This block catches errors that happen DURING generation
  console.error('Stream interrupted:', error)

  return {
    partial: true,
    steps: collectedSteps,
    error: error.message
  }
}
```

### Handling Tool Errors

By default, if a tool throws an error, the agent catches it, observes the error message, and tries to correct itself. This does not throw an exception in the stream generator. You will see the error surface in the `on_tool_end` event's output when using `streamEvents()`.

---

## 7. BAD / GOOD Patterns

### Pattern 1: Error Handling

**BAD:** Ignoring errors in the async iterator.

```typescript
// BAD: No try/catch - if stream throws, the process may crash
async function run() {
  for await (const step of agent.stream('...')) {
    console.log(step)
  }
}
```

**GOOD:** Wrapping the iteration in try/catch.

```typescript
// GOOD
async function run() {
  try {
    for await (const step of agent.stream('...')) {
      console.log(step)
    }
  } catch (err) {
    console.error('Stream failed, cleaning up resources...', err)
  }
}
```

### Pattern 2: User Interface Feedback

**BAD:** Waiting for the entire stream to finish before showing anything.

```typescript
// BAD: User waits 10s+ for nothing
const steps = []
for await (const step of agent.stream(prompt)) {
  steps.push(step)
}
render(steps)
```

**GOOD:** Updating the UI immediately as each step arrives.

```typescript
// GOOD: Show progress as it happens
for await (const step of agent.stream(prompt)) {
  appendStepToState(step)
  scrollToBottom()
}
```

### Pattern 3: Event Filtering

**BAD:** Logging every single event from `streamEvents()`.

```typescript
// BAD: Creates massive noise and performance overhead
for await (const event of agent.streamEvents(prompt)) {
  console.log(event)
}
```

**GOOD:** Filtering only for the specific events you need.

```typescript
// GOOD: Only process what you care about
for await (const event of agent.streamEvents(prompt)) {
  if (event.event === 'on_chat_model_stream') {
    processText(event.data)
  } else if (event.event === 'on_tool_start') {
    showToolIndicator(event.name)
  }
}
```

### Pattern 4: CLI Formatting

**BAD:** Manually implementing ANSI colors and spinners.

```typescript
// BAD: Brittle, hard to maintain
for await (const step of agent.stream(prompt)) {
  console.log('\x1b[33m' + step.action.tool + '\x1b[0m')
}
```

**GOOD:** Using `prettyStreamEvents` for consistent, maintained CLI formatting.

```typescript
// GOOD: Let the library handle formatting, colors, and spinners
for await (const _ of agent.prettyStreamEvents({ prompt })) {
  // pass
}
```

### Pattern 5: Checking Both Chunk Properties

**BAD:** Only checking one chunk property, which breaks across LLM providers.

```typescript
// BAD: Misses tokens from some providers
const text = event.data?.chunk?.content
```

**GOOD:** Always checking both `text` and `content` for compatibility.

```typescript
// GOOD: Works across LangChain versions and LLM providers
const text = event.data?.chunk?.text || event.data?.chunk?.content
```

---

## Summary

Streaming is essential for creating high-quality, responsive AI experiences.

- Use **`stream(prompt)`** or **`stream({ prompt, ... })`** for step-level visibility — see which tools are called and with what inputs. The generator return value (when `done === true`) is the final string result.
- Use **`streamEvents(prompt)`** or **`streamEvents({ prompt, schema? })`** for token-level streaming and chat interfaces. Always check both `chunk.text` (Anthropic) and `chunk.content` (OpenAI) for compatibility.
- Use **`prettyStreamEvents({ prompt })`** for CLI tools with zero-config formatting. This method only accepts an options object.
- `stream()` and `streamEvents()` accept either a **plain string** (deprecated) or an **options object** `{ prompt, maxSteps?, schema?, signal? }`. `prettyStreamEvents()` always takes an **options object**.
- All three streaming methods return `AsyncGenerator` instances — not `AsyncIterable`. You can use `for await` or call `.next()` manually.
- Always implement **error handling** with try/catch around streaming loops.
- For the full event type reference, see the [LangChain JavaScript streaming documentation](https://js.langchain.com/docs/how_to/streaming/).
