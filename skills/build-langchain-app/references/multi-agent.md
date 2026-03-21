# Multi-Agent Systems with LangGraph.js

> For `@langchain/langgraph@1.2.5`, `@langchain/langgraph-supervisor@1.0.1`, `@langchain/langgraph-swarm@1.0.1` — TypeScript only.
> Python-only features are explicitly marked. All TypeScript patterns verified against official docs and npm packages (2026-03-21).

---

## 1. Do You Need Multi-Agent?

**Start here.** Most LLM applications do NOT need multi-agent systems.

### Decision Tree

```
How many tools does your agent need?
│
├── ≤10 tools, single domain
│   └─► Single agent is sufficient.
│       Use createAgent or a StateGraph ReAct loop.
│
├── 10-20 tools, mixed domains
│   └─► Consider splitting into 2-3 focused agents.
│       Supervisor pattern is likely the right fit.
│
├── 20+ tools, multiple domains, different expertise
│   └─► Multi-agent is warranted.
│       Choose a pattern below.
│
└── Do agents need to collaborate back-and-forth?
    ├── No (one-directional delegation) → Supervisor pattern
    ├── Yes (peer-to-peer handoffs) → Swarm pattern
    └── Mixed (some sequential, some parallel) → Custom StateGraph
```

### When NOT to Use Multi-Agent

| Scenario | Better Alternative |
|----------|-------------------|
| Simple chatbot with 3-5 tools | Single `createAgent` |
| Linear pipeline (A → B → C) | LCEL chain or functional API |
| One domain, one model | Provider SDK directly |
| Classification + single handler | Conditional routing in one graph |

### When Multi-Agent Adds Value

| Scenario | Why Multi-Agent Helps |
|----------|----------------------|
| Research + writing + review pipeline | Specialized prompts per phase |
| Customer support with escalation tiers | Domain isolation, different tool access |
| Code generation + testing + review | Each agent has focused expertise |
| Dynamic task decomposition | Supervisor can delegate unknown tasks |
| Compliance gates between steps | HITL + isolated agent contexts |

---

## 2. Multi-Agent Patterns Overview

### Pattern Decision Matrix

| Pattern | Control | Agents | Complexity | Best Use Case |
|---------|---------|--------|------------|---------------|
| **Supervisor** | Centralized | 2-10 | Low | Clear hierarchy, delegation |
| **Swarm** | Distributed | 2-5 | Medium | Peer collaboration, dynamic handoffs |
| **Agent-as-Tool** | Caller-controlled | 2-5 | Low | Wrapping agents for ad-hoc use |
| **Custom StateGraph** | Fully custom | Any | High | Bespoke routing and state management |
| **Orchestrator-Worker** | Fan-out/fan-in | 2-20+ | Medium | Parallel independent tasks |

**Default recommendation:** Start with **Supervisor** unless you have a specific need for peer-to-peer handoffs (Swarm) or parallel fan-out (Orchestrator-Worker).

---

## 3. Supervisor Pattern

A central supervisor agent decides which specialized agent handles each step. The supervisor owns the conversation state and delegates tasks.

### Using @langchain/langgraph-supervisor

```bash
npm install @langchain/langgraph-supervisor @langchain/langgraph @langchain/core
```

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { createSupervisor } from "@langchain/langgraph-supervisor";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const model = new ChatOpenAI({ model: "gpt-4o" });

// Define specialized tools
const add = tool(
  async ({ a, b }) => `${a + b}`,
  {
    name: "add",
    description: "Add two numbers",
    schema: z.object({ a: z.number(), b: z.number() }),
  }
);

const webSearch = tool(
  async ({ query }) => `Search results for: ${query}`,
  {
    name: "web_search",
    description: "Search the web for information",
    schema: z.object({ query: z.string() }),
  }
);

// Create specialized agents using createReactAgent
const mathAgent = createReactAgent({
  llm: model,
  tools: [add],
  name: "math_expert",
  prompt: "You are a math expert. Use your tools to solve math problems.",
});

const researchAgent = createReactAgent({
  llm: model,
  tools: [webSearch],
  name: "research_expert",
  prompt: "You are a research expert. Search for information when asked.",
});

// Create supervisor
const workflow = createSupervisor({
  agents: [mathAgent, researchAgent],
  llm: model,
  prompt:
    "You are a team supervisor. " +
    "Route math problems to math_expert. " +
    "Route research questions to research_expert.",
});

const app = workflow.compile();

const result = await app.invoke({
  messages: [{ role: "user", content: "What is 15 * 23?" }],
});
```

### Supervisor with Memory

```typescript
import { MemorySaver, InMemoryStore } from "@langchain/langgraph";

const checkpointer = new MemorySaver();
const store = new InMemoryStore();

const workflow = createSupervisor({
  agents: [mathAgent, researchAgent],
  llm: model,
  prompt: "You are a team supervisor.",
});

const app = workflow.compile({ checkpointer, store });

const config = { configurable: { thread_id: "team-session-1" } };
const result = await app.invoke(
  { messages: [{ role: "user", content: "Research AI trends" }] },
  config
);
```

### Message History Management

Control how much agent conversation history the supervisor sees:

```typescript
// Full history — supervisor sees all agent messages
const workflow = createSupervisor({
  agents: [agent1, agent2],
  llm: model,
  outputMode: "full_history",
});

// Last message only — supervisor sees only each agent's final response
const workflow = createSupervisor({
  agents: [agent1, agent2],
  llm: model,
  outputMode: "last_message",
});
```

**Use `"last_message"` when:** Agent conversations are long and would bloat the supervisor's context.
**Use `"full_history"` when:** The supervisor needs to see intermediate reasoning steps.

### Multi-Level Hierarchies

Nest supervisors for complex organizations:

```typescript
const researchTeam = createSupervisor({
  agents: [researchAgent, mathAgent],
  llm: model,
}).compile({ name: "research_team" });

const writingTeam = createSupervisor({
  agents: [writerAgent, editorAgent],
  llm: model,
}).compile({ name: "writing_team" });

const topLevel = createSupervisor({
  agents: [researchTeam, writingTeam],
  llm: model,
  prompt: "Route research tasks to research_team, writing tasks to writing_team.",
}).compile();
```

---

## 4. Swarm Pattern

Agents dynamically hand off control to each other based on specialization. No central coordinator — agents are peers.

### Using @langchain/langgraph-swarm

```bash
npm install @langchain/langgraph-swarm @langchain/langgraph @langchain/core
```

```typescript
import { createSwarm, createHandoffTool } from "@langchain/langgraph-swarm";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { MemorySaver } from "@langchain/langgraph";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const model = new ChatOpenAI({ model: "gpt-4o" });

const queryDb = tool(
  async ({ sql }) => `Query result: [row1, row2]`,
  {
    name: "query_db",
    description: "Execute a SQL query",
    schema: z.object({ sql: z.string() }),
  }
);

const executeCode = tool(
  async ({ code }) => `Code output: ${code}`,
  {
    name: "execute_code",
    description: "Execute Python code",
    schema: z.object({ code: z.string() }),
  }
);

// Alice: SQL specialist who can hand off to Bob
const alice = createReactAgent({
  llm: model,
  tools: [
    queryDb,
    createHandoffTool({ agentName: "Bob", description: "Hand off to Bob for Python tasks" }),
  ],
  name: "Alice",
  prompt: "You are Alice, a SQL expert. Hand off to Bob for Python tasks.",
});

// Bob: Python specialist who can hand off to Alice
const bob = createReactAgent({
  llm: model,
  tools: [
    executeCode,
    createHandoffTool({ agentName: "Alice", description: "Hand off to Alice for SQL tasks" }),
  ],
  name: "Bob",
  prompt: "You are Bob, a Python expert. Hand off to Alice for SQL tasks.",
});

// Create swarm — Alice starts by default
const checkpointer = new MemorySaver();
const workflow = createSwarm({
  agents: [alice, bob],
  defaultActiveAgent: "Alice",
});

const app = workflow.compile({ checkpointer });

const config = { configurable: { thread_id: "swarm-1" } };

// Alice handles SQL, hands off to Bob for Python
const result = await app.invoke(
  { messages: [{ role: "user", content: "Query the users table then visualize with Python" }] },
  config
);
```

### Swarm Memory

The swarm **remembers which agent was last active** across turns (requires checkpointer):

```typescript
// Turn 1: Routes to Alice (default)
await app.invoke(
  { messages: [{ role: "user", content: "Query the users table" }] },
  config
);

// Turn 2: Alice hands off to Bob
await app.invoke(
  { messages: [{ role: "user", content: "Now visualize that data" }] },
  config
);

// Turn 3: Resumes with Bob (last active agent)
await app.invoke(
  { messages: [{ role: "user", content: "Add a title to the chart" }] },
  config
);
```

### Custom Handoff Tools

Customize what information is passed during handoffs:

```typescript
import { tool } from "@langchain/core/tools";
import { ToolMessage } from "@langchain/core/messages";
import { Command, getCurrentTaskInput } from "@langchain/langgraph";
import { z } from "zod";
import type { BaseMessage } from "@langchain/core/messages";

const createCustomHandoff = ({ agentName }: { agentName: string }) => {
  return tool(
    async (args, config) => {
      const toolMessage = new ToolMessage({
        content: `Transferred to ${agentName}: ${args.taskDescription}`,
        name: `handoff_to_${agentName}`,
        tool_call_id: config.toolCall.id,
      });

      const { messages } = getCurrentTaskInput() as { messages: BaseMessage[] };
      const lastMessage = messages[messages.length - 1];

      return new Command({
        goto: agentName,
        graph: Command.PARENT,
        update: {
          messages: [lastMessage, toolMessage],
          activeAgent: agentName,
        },
      });
    },
    {
      name: `handoff_to_${agentName}`,
      description: `Transfer to ${agentName} with a task description`,
      schema: z.object({
        taskDescription: z.string().describe("What the next agent should do"),
      }),
    }
  );
};
```

### Supervisor vs Swarm: When to Choose Which

| Aspect | Supervisor | Swarm |
|--------|-----------|-------|
| Who decides routing? | Central supervisor LLM | Each agent decides individually |
| Communication | Hub-and-spoke | Peer-to-peer |
| Context isolation | Agents have isolated contexts | Agents share message history |
| Scalability | 2-10 agents | 2-5 agents (n² handoff complexity) |
| Back-and-forth | Supervisor mediates | Direct agent-to-agent |
| Best for | Delegation, pipelines | Collaboration, exploration |

---

## 5. Agent-as-Tool Pattern

Wrap an agent as a tool for another agent. The caller treats the sub-agent like any other tool.

```typescript
import { createAgent } from "langchain";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

// Create a specialized sub-agent
const researchAgent = createAgent({
  model,
  tools: [webSearchTool],
  prompt: "You are a research specialist. Search and summarize findings concisely.",
});

// Wrap the agent as a tool
const researchTool = tool(
  async ({ query }: { query: string }) => {
    const result = await researchAgent.invoke({
      messages: [{ role: "user", content: query }],
    });
    // Extract the final text response
    const lastMessage = result.messages[result.messages.length - 1];
    return String(lastMessage.content);
  },
  {
    name: "research_agent",
    description: "Delegates a research question to a specialist agent that can search the web",
    schema: z.object({
      query: z.string().describe("The research question to investigate"),
    }),
  }
);

// Supervisor agent uses the research agent as a tool
const supervisorAgent = createAgent({
  model,
  tools: [researchTool, calculatorTool, writerTool],
  prompt: "You are a project manager. Use research_agent for research questions.",
});
```

### When to Use Agent-as-Tool

- **Quick integration**: Wrap existing agents without restructuring into a graph.
- **Context isolation**: Sub-agent runs in its own context — no state pollution.
- **Mixed ecosystems**: Call agents from different frameworks as tools.

### Limitations

- No shared state between caller and sub-agent (communication is via tool input/output strings).
- No streaming of sub-agent's intermediate steps.
- Higher latency — full agent execution per tool call.

---

## 6. Agents as Subgraph Nodes (Custom StateGraph)

For maximum control, build multi-agent systems with raw StateGraph:

```typescript
import { StateGraph, MessagesAnnotation, START, END, MemorySaver } from "@langchain/langgraph";
import { createReactAgent } from "@langchain/langgraph/prebuilt";

const researchAgent = createReactAgent({
  llm: model,
  tools: [webSearchTool],
  name: "researcher",
  prompt: "You are a researcher.",
});

const writerAgent = createReactAgent({
  llm: model,
  tools: [],
  name: "writer",
  prompt: "You are a writer. Write based on research findings.",
});

// Router: supervisor decides which agent to call
async function supervisorRouter(state: typeof MessagesAnnotation.State): Promise<string> {
  const lastMessage = state.messages[state.messages.length - 1];
  const response = await model.invoke([
    { role: "system", content: "Route to 'researcher' or 'writer' or 'end'. Reply with one word." },
    ...state.messages,
  ]);
  const route = String(response.content).trim().toLowerCase();
  if (route.includes("researcher")) return "researcher";
  if (route.includes("writer")) return "writer";
  return END;
}

const graph = new StateGraph(MessagesAnnotation)
  .addNode("researcher", researchAgent)
  .addNode("writer", writerAgent)
  .addNode("supervisor", async (state) => {
    const response = await model.invoke([
      { role: "system", content: "Decide next step. Route to researcher, writer, or end." },
      ...state.messages,
    ]);
    return { messages: [response] };
  })
  .addEdge(START, "supervisor")
  .addConditionalEdges("supervisor", supervisorRouter)
  .addEdge("researcher", "supervisor")  // return to supervisor after research
  .addEdge("writer", "supervisor");     // return to supervisor after writing

const app = graph.compile({ checkpointer: new MemorySaver() });
```

---

## 7. Communication Patterns

### Sequential Handoff

Agent A completes, then Agent B receives the result:

```typescript
const graph = new StateGraph(MessagesAnnotation)
  .addNode("researcher", researchAgent)
  .addNode("writer", writerAgent)
  .addEdge(START, "researcher")
  .addEdge("researcher", "writer")
  .addEdge("writer", END);
```

Simple and predictable. No routing decisions needed.

### Parallel Dispatch with Send

Fan out to multiple agents simultaneously:

```typescript
import { Send } from "@langchain/langgraph";

async function fanOut(state: typeof MyState.State) {
  // Return Send objects to dispatch to multiple nodes in parallel
  return [
    new Send("researchAgent", { messages: state.messages, focus: "technical" }),
    new Send("researchAgent", { messages: state.messages, focus: "business" }),
  ];
}

const graph = new StateGraph(MyState)
  .addNode("dispatcher", fanOut)
  .addNode("researchAgent", researchNode)
  .addNode("aggregator", aggregateResults)
  .addEdge(START, "dispatcher")
  .addEdge("researchAgent", "aggregator")
  .addEdge("aggregator", END);
```

**Critical:** When using parallel dispatch, the target state field **must** have a reducer to merge results from parallel executions. Without a reducer, you'll get `INVALID_CONCURRENT_GRAPH_UPDATE`.

### Supervised Round-Robin

Supervisor calls agents in a loop until satisfied:

```typescript
function supervisorRoute(state: typeof State.State): string {
  // Check if we have enough information to finish
  if (state.researchComplete && state.writingComplete) return END;
  if (!state.researchComplete) return "researcher";
  return "writer";
}

graph
  .addEdge(START, "supervisor")
  .addConditionalEdges("supervisor", supervisorRoute)
  .addEdge("researcher", "supervisor")
  .addEdge("writer", "supervisor");
```

---

## 8. Shared State vs Isolated State

### Shared State (Default)

All agents read from and write to the same state. Simple but can cause context bloat.

```typescript
// Both agents share MessagesAnnotation — all messages visible to both
const graph = new StateGraph(MessagesAnnotation)
  .addNode("agentA", agentA)
  .addNode("agentB", agentB);
```

**Pros:** Simple setup, full context visibility.
**Cons:** Agent A sees Agent B's internal reasoning; context window fills up fast.

### Isolated State (Subgraph with Different Schema)

Each agent has its own message history:

```typescript
import { Annotation, messagesStateReducer, StateGraph, START, END } from "@langchain/langgraph";
import { BaseMessage } from "@langchain/core/messages";

// Agent A has its own state schema
const AgentAState = Annotation.Root({
  agent_a_messages: Annotation<BaseMessage[]>({
    reducer: messagesStateReducer,
    default: () => [],
  }),
});

// Parent state
const ParentState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: messagesStateReducer,
    default: () => [],
  }),
  summary: Annotation<string>,
});

// Wrapper transforms parent state ↔ agent state
async function callAgentA(state: typeof ParentState.State) {
  const agentAGraph = buildAgentAGraph(); // uses AgentAState
  const result = await agentAGraph.invoke({
    agent_a_messages: state.messages, // pass relevant messages
  });
  // Only return a summary, not the full internal conversation
  const lastMsg = result.agent_a_messages[result.agent_a_messages.length - 1];
  return { summary: String(lastMsg.content) };
}
```

**Best practice:** Keep subagents stateless. The supervisor/parent owns memory. Pass only the minimum context needed to each agent, and return only the relevant output.

### Handoff Message Hygiene

When handing off between agents, the receiving agent must see a valid tool call → tool result pair:

```typescript
// ✅ Correct: Include both the AIMessage with tool_call and a ToolMessage result
update: {
  messages: [
    lastAIMessageWithToolCall,  // The AIMessage that triggered the handoff
    new ToolMessage({
      content: "Successfully transferred to AgentB",
      tool_call_id: toolCallId,
    }),
  ],
}
```

**Do NOT** forward an agent's entire internal transcript to the next agent. Pass a compact summary instead.

---

## 9. Failure Handling

### Agent Timeout

Wrap agent calls with a timeout to prevent runaway agents:

```typescript
async function callAgentWithTimeout(
  agent: any,
  input: any,
  config: any,
  timeoutMs: number = 30000
) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const result = await agent.invoke(input, {
      ...config,
      signal: controller.signal,
    });
    return result;
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") {
      return { error: "Agent timed out" };
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}
```

### Loop Detection

Prevent agents from calling each other in infinite loops:

```typescript
const State = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: messagesStateReducer,
    default: () => [],
  }),
  iterationCount: Annotation<number>,
});

function supervisorRoute(state: typeof State.State): string {
  if (state.iterationCount >= 10) {
    return END; // Force termination
  }
  // ... normal routing logic
}

async function supervisorNode(state: typeof State.State) {
  // Increment counter each time supervisor runs
  return { iterationCount: state.iterationCount + 1 };
}
```

Also use graph-level `recursionLimit`:

```typescript
const app = graph.compile({
  checkpointer,
  recursionLimit: 50, // hard limit on total node executions
});
```

### Tool Failure Handling

When a sub-agent's tools fail, handle gracefully:

```typescript
async function resilientAgentNode(state: typeof State.State) {
  try {
    const result = await subAgent.invoke({ messages: state.messages });
    return { messages: result.messages };
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Unknown error";
    // Return an error message instead of crashing the graph
    return {
      messages: [new AIMessage(`Agent failed: ${errorMessage}. Skipping to next step.`)],
      agentError: errorMessage,
    };
  }
}
```

### Error Routing in Multi-Agent Graphs

```typescript
function routeAfterAgent(state: typeof State.State): string {
  if (state.agentError) return "errorHandler";
  if (state.needsReview) return "reviewer";
  return "nextAgent";
}

graph
  .addConditionalEdges("agentA", routeAfterAgent)
  .addEdge("errorHandler", "supervisor") // supervisor decides what to do
  .addEdge("reviewer", "supervisor");
```

---

## 10. Production Considerations

### Cost Management

- **Limit tool calls per agent:** Use `toolCallLimitMiddleware({ runLimit: 10 })` with `createAgent`.
- **Use cheaper models for routing:** Supervisor can use a fast/cheap model (e.g., `gpt-4o-mini`) while specialized agents use capable models.
- **Minimize context passing:** Use `outputMode: "last_message"` in supervisor to avoid ballooning token usage.
- **Set recursion limits:** Always `recursionLimit` on compiled graphs with cycles.

```typescript
// Cheap model for supervisor routing
const routerModel = new ChatOpenAI({ model: "gpt-4o-mini" });
// Capable model for specialized work
const workerModel = new ChatOpenAI({ model: "gpt-4o" });

const workflow = createSupervisor({
  agents: [agent1, agent2],
  llm: routerModel, // supervisor uses cheap model
});
```

### Observability Across Agents

Enable LangSmith tracing to see the full execution flow:

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=lsv2_pt_...
export LANGSMITH_PROJECT=my-multi-agent-system
```

LangSmith shows:
- Which agent was invoked at each step
- Token usage per agent
- Tool calls and results within each agent
- Full state at each checkpoint

### The 3-Layer Context Model

Organize data across three layers for scalable multi-agent systems:

| Layer | Scope | Storage | Examples |
|-------|-------|---------|----------|
| **Static runtime context** | Per-run, immutable | Config / env vars | User ID, DB clients, API keys, permissions |
| **Dynamic runtime context** | Per-run, mutable | Graph state (checkpointer) | Messages, routing flags, intermediate results |
| **Cross-conversation context** | Cross-run, persistent | Store (InMemoryStore / DB) | User preferences, learned facts, stable profiles |

```typescript
import { MemorySaver, InMemoryStore } from "@langchain/langgraph";

const checkpointer = new MemorySaver();  // Layer 2: per-thread state
const store = new InMemoryStore();        // Layer 3: cross-thread memory

// Store user preferences (Layer 3)
await store.put(["users", userId], "preferences", { tone: "concise", language: "en" });

// Access in agent via store
const prefs = await store.get(["users", userId], "preferences");

// Layer 1: passed via config
const config = {
  configurable: {
    thread_id: `user-${userId}-session-${sessionId}`,
    // Layer 1 data accessible via config
  },
};
```

### Multi-Agent Memory Strategy

- **Supervisor owns memory.** Subagents should be stateless.
- **Don't pass full conversation history** to every subagent. Pass only relevant messages.
- **Use Store for cross-conversation facts.** Don't rely on checkpointer for long-term memory.
- **Summarize subagent outputs** before adding to supervisor state.

### Testing Multi-Agent Systems

Follow a test pyramid:

```
┌─────────────────────────────────┐
│       E2E Tests (few)           │  Critical paths only, real LLMs
├─────────────────────────────────┤
│   Integration Tests (some)      │  Stub models, verify state flow
├─────────────────────────────────┤
│    Unit Tests (many)            │  Tool schemas, node functions
└─────────────────────────────────┘
```

```typescript
// Unit test: verify tool schema
import { z } from "zod";

test("search tool schema validates correctly", () => {
  const result = searchToolSchema.safeParse({ query: "test" });
  expect(result.success).toBe(true);
});

// Integration test: verify graph routing (stub LLM)
test("supervisor routes math to math agent", async () => {
  // Use a deterministic mock model
  const mockModel = createMockModel({ responses: ["math_expert"] });
  const workflow = createSupervisor({ agents, llm: mockModel });
  const app = workflow.compile();

  const result = await app.invoke({
    messages: [{ role: "user", content: "What is 2+2?" }],
  });
  // Assert math agent was invoked
});
```

---

## 11. Python-Only vs TypeScript Availability

| Feature | Python | TypeScript | Notes |
|---------|--------|-----------|-------|
| `createSupervisor` | `langgraph-supervisor` | `@langchain/langgraph-supervisor@1.0.1` | ✅ Both available |
| `createSwarm` / `createHandoffTool` | `langgraph-swarm` | `@langchain/langgraph-swarm@1.0.1` | ✅ Both available |
| `createReactAgent` (prebuilt) | ✅ | ✅ `@langchain/langgraph/prebuilt` | Same API |
| `Send` for parallel dispatch | ✅ | ✅ `@langchain/langgraph` | Same API |
| `Command` for routing + update | ✅ | ✅ `@langchain/langgraph` | Same API |
| `RetryPolicy` on nodes | ✅ | ❌ Not available | Use try-catch + manual retry in TS |
| `RemainingSteps` managed value | ✅ | ❌ Not available | Track iteration count manually in TS |
| `MultiServerMCPClient` | ✅ `langchain-mcp-adapters` | ❌ Different MCP integration | TS uses different MCP approach |
| `checkpointer=True` on subgraphs | ✅ | ✅ | Same API |
| `addActiveAgentRouter` (swarm internal) | ✅ | ✅ `@langchain/langgraph-swarm` | For custom swarm graphs |

### Key TS Differences

- **No `RetryPolicy`:** Implement retry logic inside node functions with try-catch.
- **No `RemainingSteps`:** Track remaining steps via a counter in state.
- **Swarm uses `createReactAgent`** (not `createAgent` from `langchain`) — per official swarm docs.
- **Node `ends` option:** When building custom swarm graphs with `addNode`, pass `{ ends: ["AgentB"] }` to declare possible handoff targets.

---

## 12. Import Reference

```typescript
// Supervisor
import { createSupervisor } from "@langchain/langgraph-supervisor";

// Swarm
import { createSwarm, createHandoffTool } from "@langchain/langgraph-swarm";
import { addActiveAgentRouter } from "@langchain/langgraph-swarm"; // for custom swarms

// Core graph
import { StateGraph, Annotation, MessagesAnnotation, START, END } from "@langchain/langgraph";
import { MemorySaver, InMemoryStore, Command, Send } from "@langchain/langgraph";
import { messagesStateReducer } from "@langchain/langgraph";

// Prebuilt agents
import { createReactAgent } from "@langchain/langgraph/prebuilt";

// High-level agent (langchain v1)
import { createAgent } from "langchain";

// Tools and messages
import { tool } from "@langchain/core/tools";
import { HumanMessage, AIMessage, ToolMessage } from "@langchain/core/messages";
import { z } from "zod";
```

---

## 13. Quick Reference: Choosing a Pattern

```
Start here:
│
├── Do you need multiple specialized agents?
│   ├── No → Single createAgent or StateGraph ReAct loop
│   └── Yes ↓
│
├── Is there a clear hierarchy (one agent delegates)?
│   ├── Yes → createSupervisor
│   └── No ↓
│
├── Do agents need to hand off to each other dynamically?
│   ├── Yes → createSwarm
│   └── No ↓
│
├── Do you need fully custom routing logic?
│   ├── Yes → Custom StateGraph with agents as nodes
│   └── No ↓
│
└── Do you need parallel independent processing?
    ├── Yes → Orchestrator-Worker with Send API
    └── No → Sequential pipeline with addEdge
```
