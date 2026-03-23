# Multi-Agent Reference

> Covers `langchain@1.x`, `@langchain/langgraph@1.2.5`, `@langchain/langgraph-supervisor@1.0.1`, `@langchain/langgraph-swarm@1.0.1`. TypeScript only. All API shapes sourced from official LangChain docs and research as of 2026-03-23.

---

## 1. The Four Core Patterns

All LangChain multi-agent architectures are built from four foundational patterns. They can be mixed.

### Pattern Overview Table

| Pattern | Control | Parallelism | Direct User Interaction | Context Isolation | Multi-Hop | Stateful |
|---------|---------|:-----------:|:-----------------------:|:-----------------:|:---------:|:--------:|
| **Subagents** | Supervisor calls subagents as tools | ✅ (5/5) | Low (1/5) | ✅ (5/5) | ✅ (5/5) | Partial |
| **Handoffs** | Tool call transfers active agent | None | ✅ (5/5) | Low (1/5) | ✅ (5/5) | ✅ |
| **Skills** | Single agent loads context on demand | Partial (3/5) | ✅ (5/5) | Partial (3/5) | ✅ (5/5) | ✅ |
| **Router** | Classify input → dispatch to agents | ✅ (5/5) | Partial (3/5) | ✅ (5/5) | None | None |

### Decision Guide: When to Use Each Pattern

| Scenario | Best Pattern | Reason |
|----------|-------------|--------|
| Multiple distinct domains (calendar, email, CRM) | **Subagents** | Context isolation per domain; parallel execution |
| Sequential data collection (form-like workflow) | **Handoffs** | Enforces step ordering; state persists naturally |
| Single agent with many optional specializations | **Skills** | Progressive disclosure; no subagent overhead |
| Parallel knowledge retrieval across verticals | **Router** | Fan-out + synthesis; ~9K tokens vs ~14K for Handoffs |
| Peer-to-peer dynamic routing between specialists | **Swarm** | Agents answer users directly; no central gatekeeper |
| Mixed orchestration with hierarchy | **Hierarchical** | Nested supervisor teams; independent scaling |
| Repeat users (same domain, second turn) | **Handoffs** or **Skills** | ~40% fewer model calls on second turn |
| Multi-domain query, parallel results needed | **Router** | `Send` API for concurrent execution |

### When NOT to Use Multi-Agent

| Scenario | Better Alternative |
|----------|-------------------|
| Simple chatbot with ≤10 tools, one domain | Single `createAgent` or `createReactAgent` |
| Linear A → B → C pipeline | LCEL chain or functional API |
| Classification + single handler | Conditional routing in one graph |
| Agent has poor routing but few tools | Better prompting, not more agents |

**Concrete triggers that justify multi-agent:**
1. Agent consistently picks wrong tools (>20 tools in context — the "dumb zone")
2. Task requires domain-specific context that would overflow a single window
3. Workflow benefits from parallel execution of independent subtasks
4. Multiple teams need clear ownership of distinct capabilities
5. Task is so long-horizon it needs fresh agents spawned for subtasks

---

## 2. Performance Benchmarks (τ-bench)

Data from official LangChain benchmarks — τ-bench retail test, 100 examples.

### Model Calls Per Scenario

| Pattern | One-Shot | Repeat (Turn 2) | Total (2 Turns) | Multi-Domain |
|---------|:--------:|:---------------:|:---------------:|:------------:|
| **Subagents** | 4 | 4 | 8 | 5 calls, ~9K tokens |
| **Handoffs** | 3 | 2 | 5 | 7+ calls, ~14K tokens |
| **Skills** | 3 | 2 | 5 | 3 calls, ~15K tokens |
| **Router** | 3 | 3 | 6 | 5 calls, ~9K tokens |

### τ-bench Architecture Benchmark (with Distractor Domains)

| Architecture | Score Trend | Token Cost | Best For |
|--------------|-------------|:----------:|----------|
| **Single Agent** | Sharp decline at ≥2 distractors | Grows with distractors | <10 tools, no third-party agents |
| **Swarm** | Best performance at many distractors | Flat (lowest) | Internal agents, direct user replies |
| **Supervisor** | Flat but below Swarm; better than single at scale | Flat (10-20% > Swarm) | Mixed ecosystems, third-party agents |

**Key insight:** Stateful patterns (Handoffs, Skills) reduce model calls by ~40% on repeat interactions. Parallel patterns (Subagents, Router) reduce token usage by ~30-40% on multi-domain tasks versus Skills.

---

## 3. Subagents Pattern (Supervisor)

A supervisor agent wraps specialized subagents as tool functions. All routing passes through the supervisor. Subagents have isolated context windows.

```
User → [Supervisor] → [tool: calendar_agent] → result
                    → [tool: email_agent]    → result   (parallel possible)
                    ← synthesized answer
```

### Using `@langchain/langgraph-supervisor`

```bash
npm install @langchain/langgraph-supervisor @langchain/langgraph @langchain/core
```

```typescript
import { createSupervisor } from "@langchain/langgraph-supervisor";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { ChatOpenAI } from "@langchain/openai";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const model = new ChatOpenAI({ model: "gpt-4o" });

const add = tool(
  async ({ a, b }) => `${a + b}`,
  { name: "add", description: "Add two numbers", schema: z.object({ a: z.number(), b: z.number() }) }
);

const webSearch = tool(
  async ({ query }) => `Search results for: ${query}`,
  { name: "web_search", description: "Search the web", schema: z.object({ query: z.string() }) }
);

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

const workflow = createSupervisor({
  agents: [mathAgent, researchAgent],
  llm: model,
  prompt:
    "You are a team supervisor. " +
    "Route math problems to math_expert. " +
    "Route research questions to research_expert.",
  // outputMode: "last_message" | "full_history"  (default: "last_message")
});

const app = workflow.compile();

const result = await app.invoke({
  messages: [{ role: "user", content: "What is 15 * 23?" }],
});
```

### `createSupervisor` API Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `agents` | `CompiledGraph[]` | required | Compiled subagraph nodes to supervise |
| `llm` | `BaseChatModel` | required | Model that makes routing decisions |
| `prompt` | `string` | optional | System prompt guiding the supervisor |
| `outputMode` | `"last_message" \| "full_history"` | `"last_message"` | How much agent history the supervisor sees |

Use `"last_message"` when agent conversations are long and would bloat the supervisor's context. Use `"full_history"` when the supervisor needs intermediate reasoning steps.

### Supervisor with Memory

```typescript
import { MemorySaver, InMemoryStore } from "@langchain/langgraph";

const app = createSupervisor({
  agents: [mathAgent, researchAgent],
  llm: model,
  prompt: "You are a team supervisor.",
}).compile({
  checkpointer: new MemorySaver(),
  store: new InMemoryStore(),
});

const result = await app.invoke(
  { messages: [{ role: "user", content: "Research AI trends" }] },
  { configurable: { thread_id: "team-session-1" } }
);
```

### Subagent-as-Tool Pattern (langchain v1)

When using `createAgent` from the `langchain` package (v1), wrap subagents as tools manually:

```typescript
import { createAgent, tool } from "langchain";
import { ChatAnthropic } from "@langchain/anthropic";
import { MemorySaver } from "@langchain/langgraph";
import { z } from "zod";

const llm = new ChatAnthropic({ model: "claude-sonnet-4-5" });

// Specialized subagent
const calendarAgent = createAgent({
  model: llm,
  tools: [createCalendarEvent, getAvailableTimeSlots],
  systemPrompt: `You are a calendar management specialist.
1. Check available slots with get_available_time_slots.
2. Create the event with create_calendar_event.
Always confirm event details before creating.`,
});

// Wrap as tool for supervisor
const scheduleEvent = tool(
  async ({ request }) => {
    const result = await calendarAgent.invoke({
      messages: [{ role: "user", content: request }],
    });
    return result.messages.at(-1)!.content as string;
  },
  {
    name: "schedule_event",
    description: "Schedule calendar events. Use when user wants to create or check appointments.",
    schema: z.object({
      request: z.string().describe("Natural language scheduling request"),
    }),
  }
);

// Supervisor uses subagent tools
const supervisorAgent = createAgent({
  model: llm,
  tools: [scheduleEvent, manageEmail],
  systemPrompt: `You are a personal assistant. Break down requests into tool calls and coordinate results.`,
  checkpointer: new MemorySaver(),
});

const result = await supervisorAgent.invoke(
  { messages: [{ role: "user", content: "Schedule a team meeting tomorrow at 2pm with alice and bob" }] },
  { configurable: { thread_id: "user-session-1" } }
);
```

### `SubAgent` Interface (DeepAgents)

For `createDeepAgent` from the `deepagents` package:

```typescript
import { createDeepAgent, SubAgent, CompiledSubAgent } from "deepagents";

// SubAgent configuration
interface SubAgent {
  name: string;               // Identifier used by main agent for routing
  description: string;        // Guides the main agent's routing decisions
  systemPrompt: string;       // System prompt for this subagent
  tools: StructuredTool[];    // Tools available to the subagent
  model?: BaseChatModel;      // Optional model override; inherits parent if omitted
  middleware?: AgentMiddleware[];
  interruptOn?: InterruptOnConfig;
}

// CompiledSubAgent — when wrapping a pre-built LangGraph
interface CompiledSubAgent {
  name: string;
  description: string;
  runnable: Runnable;         // Pre-compiled LangGraph graph used as a subagent
}

// Usage
const researchSubagent: SubAgent = {
  name: "research-agent",
  description: "Used to research in-depth questions with web search",
  systemPrompt: "You are a great researcher. Search thoroughly, cite sources, return structured findings.",
  tools: [internetSearch],
  model: new ChatOpenAI({ model: "gpt-4o" }),
};

const agent = createDeepAgent({
  model: new ChatAnthropic({ model: "claude-sonnet-4-20250514" }),
  subagents: [researchSubagent, writerSubagent],
});
```

### Hierarchical Supervisor Teams

Nest supervisors for complex organizations. In TypeScript, build hierarchical teams with nested `StateGraph` compilation.

```typescript
import { StateGraph, MessagesAnnotation, Annotation, END, START } from "@langchain/langgraph";
import { createReactAgent } from "@langchain/langgraph/prebuilt";

const llm = new ChatOpenAI({ model: "gpt-4o" });

// Level 2: Research team members
const webResearcher = createReactAgent({ llm, tools: [webSearchTool], name: "web_researcher" });
const dbResearcher  = createReactAgent({ llm, tools: [dbQueryTool],   name: "db_researcher"  });

const researchTeamState = Annotation.Root({
  ...MessagesAnnotation.spec,
  next: Annotation<string>({ reducer: (_, b) => b }),
});

const researchWorkflow = new StateGraph(researchTeamState)
  .addNode("supervisor", async (state) => {
    const response = await llm.invoke([
      { role: "system", content: "Route to: web_researcher | db_researcher | FINISH" },
      ...state.messages,
    ]);
    return { next: response.content as string };
  })
  .addNode("web_researcher", async (state) => ({ messages: (await webResearcher.invoke(state)).messages }))
  .addNode("db_researcher",  async (state) => ({ messages: (await dbResearcher.invoke(state)).messages  }))
  .addEdge(START, "supervisor")
  .addConditionalEdges("supervisor", (s) => s.next, {
    web_researcher: "web_researcher",
    db_researcher: "db_researcher",
    FINISH: END,
  })
  .addEdge("web_researcher", "supervisor")
  .addEdge("db_researcher", "supervisor");

// Compile research team as a reusable subgraph node
const researchTeam = researchWorkflow.compile({ name: "research_team" });

// Top-level supervisor references the compiled team as a node
const topLevel = new StateGraph(Annotation.Root({
  ...MessagesAnnotation.spec,
  next: Annotation<string>({ reducer: (_, b) => b }),
}))
  .addNode("supervisor", async (state) => {
    const r = await llm.invoke([
      { role: "system", content: "Route to: research_team | writer | FINISH" },
      ...state.messages,
    ]);
    return { next: r.content as string };
  })
  .addNode("research_team", async (state) => ({ messages: (await researchTeam.invoke(state)).messages }))
  .addNode("writer", async (state) => ({ messages: (await writerAgent.invoke(state)).messages }))
  .addEdge(START, "supervisor")
  .addConditionalEdges("supervisor", (s) => s.next, {
    research_team: "research_team",
    writer: "writer",
    FINISH: END,
  })
  .addEdge("research_team", "supervisor")
  .addEdge("writer", "supervisor");

const app = topLevel.compile();
```

---

## 4. Swarm Pattern

Agents dynamically hand off control to each other. No central coordinator — agents are peers. Best when all agents are known ahead of time and agents need to answer users directly.

```bash
npm install @langchain/langgraph-swarm @langchain/langgraph @langchain/core
```

### `createSwarm` Full API

```typescript
import { createSwarm, createHandoffTool } from "@langchain/langgraph-swarm";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { ChatOpenAI } from "@langchain/openai";
import { MemorySaver } from "@langchain/langgraph";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const llm = new ChatOpenAI({ model: "gpt-4o" });

const flightAgent = createReactAgent({
  llm,
  tools: [
    searchFlightsTool,
    createHandoffTool({ agentName: "hotel_agent", description: "Hand off to hotel_agent for accommodation" }),
    createHandoffTool({ agentName: "car_agent",   description: "Hand off to car_agent for rentals" }),
  ],
  name: "flight_agent",
  prompt: "You are a flight booking specialist. Hand off to hotel_agent or car_agent as needed.",
});

const hotelAgent = createReactAgent({
  llm,
  tools: [
    searchHotelsTool,
    createHandoffTool({ agentName: "flight_agent" }),
    createHandoffTool({ agentName: "car_agent" }),
  ],
  name: "hotel_agent",
  prompt: "You are a hotel booking specialist.",
});

const carAgent = createReactAgent({
  llm,
  tools: [
    searchCarsTool,
    createHandoffTool({ agentName: "flight_agent" }),
    createHandoffTool({ agentName: "hotel_agent" }),
  ],
  name: "car_agent",
  prompt: "You are a car rental specialist.",
});

const checkpointer = new MemorySaver();

const swarm = createSwarm({
  agents: [flightAgent, hotelAgent, carAgent],
  defaultActiveAgent: "flight_agent",  // entry point on new conversations
}).compile({ checkpointer });

// The swarm remembers which agent was last active across turns
const config = { configurable: { thread_id: "trip-booking-1" } };

const result = await swarm.invoke(
  { messages: [{ role: "user", content: "Book me a trip to Paris next week" }] },
  config
);
```

### `createHandoffTool` Options

| Option | Type | Description |
|--------|------|-------------|
| `agentName` | `string` | Target agent name (must match `name` in `createReactAgent`) |
| `description` | `string` | Optional; guides LLM decision on when to hand off |

### Swarm vs Supervisor

| Aspect | Supervisor | Swarm |
|--------|-----------|-------|
| Who decides routing? | Central supervisor LLM | Each agent decides individually |
| Communication | Hub-and-spoke | Peer-to-peer |
| User interaction | All responses via supervisor | Agents answer users directly |
| Context sharing | Agents have isolated contexts | Agents share message history |
| Best for | Mixed ecosystems, third-party agents | Internal agents, known registry |
| τ-bench (many distractors) | Below Swarm | Best performance (flat score) |
| Token cost | 10-20% > Swarm | Lowest |

---

## 5. Handoffs Pattern

Agents transfer conversation control via tool calls that return `Command` objects. State (including the active agent) persists across turns via a checkpointer.

### Two Implementation Modes

**Mode 1: Single-agent with middleware** — one agent instance, its system prompt and toolset change per turn based on `currentStep`. Choose when: linear workflows, <5 steps, direct user-facing conversation.

**Mode 2: Multi-agent subgraphs** — multiple distinct agent nodes in a `StateGraph`. Handoff tools use `Command({ goto, graph: Command.PARENT })`. Choose when: agents need different models, per-agent LangSmith traces, or wholly different toolsets.

### Core TypeScript API

#### `Command`

```typescript
import { Command } from "@langchain/langgraph";

new Command({
  update?: {
    messages?: Message[];        // Must include ToolMessage with matching tool_call_id
    [stateKey: string]: any;     // Any state field updates (currentStep, activeAgent, etc.)
  };
  goto?: string;                  // Target node name (multi-agent mode only)
  graph?: typeof Command.PARENT;  // Required when navigating parent graph from inside a subgraph
})
```

#### `ToolRuntime<S>`

Second argument to every tool function. Gives access to current state and tool call ID.

```typescript
import type { ToolRuntime } from "langchain";

async function myHandoffTool(
  args: MyArgsType,
  runtime: ToolRuntime<typeof MyState.State>
) {
  runtime.toolCallId  // string — MUST be echoed in ToolMessage.tool_call_id
  runtime.state       // current state snapshot (read-only)
}
```

#### `StateSchema`

```typescript
import { StateSchema, MessagesValue } from "@langchain/langgraph";
import { z } from "zod";

const SupportState = new StateSchema({
  currentStep:     z.enum(["triage", "classify", "resolve"]).optional(),
  warrantyStatus:  z.enum(["in_warranty", "out_of_warranty"]).optional(),
  issueType:       z.enum(["hardware", "software"]).optional(),
  activeAgent:     z.string().optional(),
  messages:        MessagesValue,
});
```

#### Handoff Tool Construction

```typescript
import { tool, ToolMessage, type ToolRuntime } from "langchain";
import { Command } from "@langchain/langgraph";
import { z } from "zod";

const recordWarrantyStatus = tool(
  async (
    input: { status: "in_warranty" | "out_of_warranty" },
    runtime: ToolRuntime<typeof SupportState.State>
  ) =>
    new Command({
      update: {
        messages: [
          new ToolMessage({
            content: `Warranty status recorded: ${input.status}`,
            tool_call_id: runtime.toolCallId,  // REQUIRED — must match AIMessage.tool_calls[n].id
          }),
        ],
        warrantyStatus: input.status,
        currentStep: "issue_classifier",       // triggers next configuration
      },
    }),
  {
    name: "record_warranty_status",
    description: "Record warranty status and advance to issue classification.",
    schema: z.object({ status: z.enum(["in_warranty", "out_of_warranty"]) }),
  }
);
```

#### Multi-Agent Subgraph Transfer

Use `goto` + `graph: Command.PARENT` when the tool is inside a subgraph and needs to route to a parent graph node:

```typescript
import { Command } from "@langchain/langgraph";
import { tool, ToolMessage, AIMessage, type ToolRuntime } from "langchain";

const transferToSales = tool(
  async (_args: {}, rt: ToolRuntime<typeof MultiAgentState.State>) => {
    const lastAI = [...rt.state.messages].reverse().find(AIMessage.isInstance);
    const handoffMsg = new ToolMessage({
      content: "Transferred to sales agent",
      tool_call_id: rt.toolCallId,
    });
    return new Command({
      goto: "sales_agent",           // target node in the parent graph
      update: {
        activeAgent: "sales_agent",
        messages: [lastAI, handoffMsg].filter(Boolean),  // handoff pair only — not full history
      },
      graph: Command.PARENT,         // REQUIRED when inside a subgraph
    });
  },
  { name: "transfer_to_sales", description: "Transfer to sales for pricing questions.", schema: z.object({}) }
);
```

**Why both `activeAgent` AND `goto`?** `Command.goto` routes within a single turn. `activeAgent` state variable persists across turns — it tells `routeInitial` (called at `START`) which node to enter on the next conversation turn. Without `activeAgent`, a resumed conversation always starts at the default node.

---

## 6. Customer Support Example (Full Working Code)

The canonical three-step state machine from official LangChain.js docs.

```typescript
import { createMiddleware, createAgent, tool, ToolMessage, type ToolRuntime, HumanMessage } from "langchain";
import { Command, MemorySaver, StateSchema } from "@langchain/langgraph";
import { ChatOpenAI } from "@langchain/openai";
import { z } from "zod";
import { v4 as uuidv4 } from "uuid";

// ── State ─────────────────────────────────────────────────────────────────────
const SupportState = new StateSchema({
  currentStep:    z.enum(["warranty_collector", "issue_classifier", "resolution_specialist"]).optional(),
  warrantyStatus: z.enum(["in_warranty", "out_of_warranty"]).optional(),
  issueType:      z.enum(["hardware", "software"]).optional(),
});

// ── Handoff Tools ─────────────────────────────────────────────────────────────
const recordWarrantyStatus = tool(
  async (
    input: { status: "in_warranty" | "out_of_warranty" },
    cfg: ToolRuntime<typeof SupportState.State>
  ) =>
    new Command({
      update: {
        messages: [new ToolMessage({ content: `Warranty: ${input.status}`, tool_call_id: cfg.toolCallId })],
        warrantyStatus: input.status,
        currentStep: "issue_classifier",
      },
    }),
  { name: "record_warranty_status", description: "Save warranty status and advance.", schema: z.object({ status: z.enum(["in_warranty", "out_of_warranty"]) }) }
);

const recordIssueType = tool(
  async (
    input: { issueType: "hardware" | "software" },
    cfg: ToolRuntime<typeof SupportState.State>
  ) =>
    new Command({
      update: {
        messages: [new ToolMessage({ content: `Issue: ${input.issueType}`, tool_call_id: cfg.toolCallId })],
        issueType: input.issueType,
        currentStep: "resolution_specialist",
      },
    }),
  { name: "record_issue_type", description: "Record issue type and advance to resolution.", schema: z.object({ issueType: z.enum(["hardware", "software"]) }) }
);

const provideSolution = tool(
  async (input: { solution: string }) => `Solution: ${input.solution}`,
  { name: "provide_solution", description: "Deliver a solution.", schema: z.object({ solution: z.string() }) }
);

const escalateToHuman = tool(
  async (input: { reason: string }) => `Escalating to human. Reason: ${input.reason}`,
  { name: "escalate_to_human", description: "Hand off to human agent.", schema: z.object({ reason: z.string() }) }
);

// Backtracking tools — allow users to correct earlier inputs
const goBackToWarranty = tool(
  async () => new Command({ update: { currentStep: "warranty_collector", warrantyStatus: undefined } }),
  { name: "go_back_to_warranty", description: "Return to warranty step.", schema: z.object({}) }
);

const goBackToClassification = tool(
  async () => new Command({ update: { currentStep: "issue_classifier", issueType: undefined } }),
  { name: "go_back_to_classification", description: "Return to issue classification.", schema: z.object({}) }
);

// ── Step Config ────────────────────────────────────────────────────────────────
const STEP_CONFIG = {
  warranty_collector: {
    prompt: `You are a support agent in warranty verification.
Ask the customer for their warranty status (in_warranty or out_of_warranty).
Once known, call record_warranty_status.`,
    tools: [recordWarrantyStatus],
    requires: [] as string[],
  },
  issue_classifier: {
    prompt: `You are in issue classification stage.
Customer warranty: {warrantyStatus}
Ask what type of issue (hardware or software) and call record_issue_type.`,
    tools: [recordIssueType],
    requires: ["warrantyStatus"],
  },
  resolution_specialist: {
    prompt: `You are in resolution stage.
Warranty: {warrantyStatus}, Issue type: {issueType}
- Software issue → use provide_solution
- Hardware + in_warranty → use provide_solution
- Hardware + out_of_warranty → use escalate_to_human
- If user corrects info → use go_back_to_warranty or go_back_to_classification`,
    tools: [provideSolution, escalateToHuman, goBackToWarranty, goBackToClassification],
    requires: ["warrantyStatus", "issueType"],
  },
} as const;

// ── Middleware ─────────────────────────────────────────────────────────────────
const applyStepMiddleware = createMiddleware({
  name: "applyStep",
  stateSchema: SupportState,
  wrapModelCall: async (req, next) => {
    const step = (req.state.currentStep ?? "warranty_collector") as keyof typeof STEP_CONFIG;
    const cfg = STEP_CONFIG[step];

    for (const key of cfg.requires) {
      if (req.state[key as keyof typeof req.state] === undefined) {
        throw new Error(`State field '${key}' required before step '${step}'`);
      }
    }

    let prompt = cfg.prompt;
    for (const [k, v] of Object.entries(req.state)) {
      if (v !== undefined) prompt = prompt.replace(`{${k}}`, String(v));
    }

    return next({ ...req, systemPrompt: prompt, tools: [...cfg.tools] });
  },
});

// ── Agent ──────────────────────────────────────────────────────────────────────
const allTools = [
  recordWarrantyStatus, recordIssueType, provideSolution,
  escalateToHuman, goBackToWarranty, goBackToClassification,
];

const supportAgent = createAgent({
  model: new ChatOpenAI({ model: "gpt-4.1-mini", temperature: 0.7 }),
  tools: allTools,
  middleware: [applyStepMiddleware],
  checkpointer: new MemorySaver(),
});

// ── Conversation ───────────────────────────────────────────────────────────────
const threadId = uuidv4();
const runConfig = { configurable: { thread_id: threadId } };

async function turn(message: string) {
  const result = await supportAgent.invoke(
    { messages: [new HumanMessage(message)] },
    runConfig
  );
  const lastMsg = result.messages[result.messages.length - 1];
  console.log(`[step=${result.currentStep}] Agent: ${lastMsg.content}`);
  return result;
}

await turn("My phone screen stopped working");           // → warranty_collector
await turn("It's still under warranty");                 // → issue_classifier
await turn("The screen is completely black");            // → resolution_specialist
await turn("Actually, I dropped it — it's hardware");    // → provide_solution (hardware + in_warranty)
```

---

## 7. Router Pattern and 5 Routing Strategies

The router classifies input and dispatches to one or more agents. Results are synthesized.

### Five Routing Strategies

| Strategy | Mechanism | TypeScript API | Best For |
|----------|-----------|---------------|----------|
| **LLM-based** | LLM with structured output classifies intent | `llm.withStructuredOutput(zodSchema)` | Intent-driven routing to named agents |
| **Rule-based** | `if/else` or switch on state keys | `(state) => state.type === "code" ? "coder" : "writer"` | Known, deterministic routing |
| **Semantic** | Vector similarity against agent descriptions | Embeddings retriever → route | Large agent registries, discovery |
| **Hybrid** | LLM classification + rule-based fallback | LLM first, rules handle errors/edge cases | Production robustness |
| **Parallel fan-out** | Array of `Send` objects | `new Send(name, payload)[]` from routing function | Multi-source queries |

### `Command` vs `Send`

```typescript
import { Command, Send } from "@langchain/langgraph";

// Command — single-agent routing (sequential)
function routeQuery(state: RouterState): Command {
  const agentName = classifyQuery(state.query); // "github" | "notion" | "slack"
  return new Command({ goto: agentName });
}

// Send — parallel fan-out routing
function routeToAgents(state: RouterState): Send[] {
  return state.classifications.map(
    (c) => new Send(c.source, { query: c.query })
  );
}
```

| Aspect | `Command` | `Send` |
|--------|-----------|--------|
| Dispatch | Sequential (1 node) | Parallel (N nodes) |
| Aggregation needed | No | Yes — use `ReducedValue` reducer |
| When to use | Clear single intent | Decomposable multi-source query |

### Full Knowledge-Base Router (Parallel Fan-Out)

```typescript
import { z } from "zod/v4";
import { StateGraph, START, END, Send, StateSchema, ReducedValue } from "@langchain/langgraph";
import { createAgent, tool } from "langchain";
import { ChatOpenAI } from "@langchain/openai";

// ── State ─────────────────────────────────────────────────────────────────────
const AgentOutput = z.object({ source: z.string(), result: z.string() });

const RouterState = new StateSchema({
  query: z.string(),
  classifications: z.array(
    z.object({ source: z.enum(["github", "notion", "slack"]), query: z.string() })
  ),
  results: new ReducedValue(
    z.array(AgentOutput).default(() => []),
    { reducer: (current, update) => current.concat(update) }
  ),
  finalAnswer: z.string(),
});

// ── LLM-based classifier ──────────────────────────────────────────────────────
const ClassificationSchema = z.object({
  classifications: z.array(z.object({
    source: z.enum(["github", "notion", "slack"]),
    query: z.string(),
  })),
});

async function classifyQuery(state: typeof RouterState.State) {
  const structured = new ChatOpenAI({ model: "gpt-4.1-mini" })
    .withStructuredOutput(ClassificationSchema);
  const out = await structured.invoke([
    {
      role: "system",
      content: "Classify the query. For each relevant source (github/notion/slack), produce a targeted sub-question.",
    },
    { role: "user", content: state.query },
  ]);
  return { classifications: out.classifications };
}

// ── Routing function ──────────────────────────────────────────────────────────
function routeToAgents(state: typeof RouterState.State): Send[] {
  return state.classifications.map((c) => new Send(c.source, { query: c.query }));
}

// ── Specialized agents ────────────────────────────────────────────────────────
const llm = new ChatOpenAI({ model: "gpt-4.1" });
const githubAgent = createAgent({ model: llm, tools: [searchCode, searchIssues], systemPrompt: "You are a GitHub expert." });
const notionAgent = createAgent({ model: llm, tools: [searchNotion],             systemPrompt: "You are a Notion expert."  });
const slackAgent  = createAgent({ model: llm, tools: [searchSlack],              systemPrompt: "You are a Slack expert."   });

async function queryGithub(state: { query: string }) {
  const r = await githubAgent.invoke({ messages: [{ role: "user", content: state.query }] });
  return { results: [{ source: "github", result: r.messages.at(-1)?.content ?? "" }] };
}
async function queryNotion(state: { query: string }) {
  const r = await notionAgent.invoke({ messages: [{ role: "user", content: state.query }] });
  return { results: [{ source: "notion", result: r.messages.at(-1)?.content ?? "" }] };
}
async function querySlack(state: { query: string }) {
  const r = await slackAgent.invoke({ messages: [{ role: "user", content: state.query }] });
  return { results: [{ source: "slack",  result: r.messages.at(-1)?.content ?? "" }] };
}

// ── Synthesis ─────────────────────────────────────────────────────────────────
async function synthesizeResults(state: typeof RouterState.State) {
  if (state.results.length === 0) return { finalAnswer: "No results found." };
  const formatted = state.results
    .map((r) => `**${r.source}:**\n${r.result}`)
    .join("\n\n");
  const resp = await new ChatOpenAI({ model: "gpt-4.1" }).invoke([
    { role: "system", content: `Synthesize into a single answer for: "${state.query}"` },
    { role: "user", content: formatted },
  ]);
  return { finalAnswer: resp.content };
}

// ── Graph assembly ────────────────────────────────────────────────────────────
const workflow = new StateGraph(RouterState)
  .addNode("classify", classifyQuery)
  .addNode("github", queryGithub)
  .addNode("notion", queryNotion)
  .addNode("slack", querySlack)
  .addNode("synthesize", synthesizeResults)
  .addEdge(START, "classify")
  .addConditionalEdges("classify", routeToAgents, ["github", "notion", "slack"])
  .addEdge("github", "synthesize")
  .addEdge("notion", "synthesize")
  .addEdge("slack",  "synthesize")
  .addEdge("synthesize", END)
  .compile();

const result = await workflow.invoke({ query: "How do I authenticate API requests?" });
```

---

## 8. Skills Pattern

A single agent dynamically loads specialized prompts ("skills") on demand. The agent maintains control throughout; it only loads skill content when relevant.

```
User query → Agent sees skill descriptions (lightweight) → Agent identifies relevant skill
→ Calls load_skill(name) → Receives full skill context → Executes task
```

### Skill Discovery Methods

| Method | Token Cost | Scale |
|--------|:----------:|:-----:|
| System-prompt listing (`name + description` injected) | Paid upfront (constant) | Up to ~50 skills |
| File-system scanning (`./skills/*.md`) | I/O at startup | ~1K skills |
| Registry API | Network call per request | Unlimited, centralized |
| Dynamic `load_skill_list()` tool | Per-request tool call | Unlimited |

**Size-based strategy:** Embed content < 1K tokens in system prompt directly. Use on-demand `load_skill` for 1–10K token skills. Use paginated/search-based retrieval for > 10K token skills.

### Skills Pattern Implementation

```typescript
import { createAgent, createMiddleware, tool } from "langchain";
import { ChatOpenAI } from "@langchain/openai";
import { MemorySaver } from "@langchain/langgraph";
import { z } from "zod";

// ── Skill definitions ─────────────────────────────────────────────────────────
const SKILLS = [
  {
    name: "sales_analytics",
    description: "Sales data analysis (customers, orders, revenue)",
    content: `
Tables: customers(id, name, email, tier), orders(id, customer_id, total, status, created_at)
Rules: High-value = lifetime spend > $10K. Active = order in last 90 days.
Pattern: SELECT c.name, SUM(o.total) FROM customers c JOIN orders o ON c.id=o.customer_id WHERE o.status='completed' GROUP BY c.id;
    `.trim(),
  },
  {
    name: "inventory_management",
    description: "Inventory tracking (products, warehouses, stock levels)",
    content: `
Tables: products(id, name, sku, unit_price, reorder_point), inventory(product_id, warehouse_id, quantity)
Rules: Low stock = quantity < reorder_point. Stock value = quantity * unit_price.
Pattern: SELECT p.name, i.quantity FROM products p JOIN inventory i ON p.id=i.product_id WHERE i.quantity < p.reorder_point;
    `.trim(),
  },
];

// ── load_skill tool ───────────────────────────────────────────────────────────
const SKILL_REGISTRY = new Map(SKILLS.map((s) => [s.name, s]));

const loadSkill = tool(
  async ({ skillName }) => {
    const skill = SKILL_REGISTRY.get(skillName);
    if (!skill) {
      const available = Array.from(SKILL_REGISTRY.keys()).join(", ");
      return `Skill '${skillName}' not found. Available: ${available}`;
    }
    return `Loaded skill: ${skillName}\n\n${skill.content}`;
  },
  {
    name: "load_skill",
    description: `Load a specialized skill's full context and instructions.
Available skills:
${SKILLS.map((s) => `- **${s.name}**: ${s.description}`).join("\n")}`,
    schema: z.object({
      skillName: z.string().describe("Exact skill name to load"),
    }),
  }
);

// ── Skill middleware ──────────────────────────────────────────────────────────
const skillsPrompt = SKILLS.map((s) => `- **${s.name}**: ${s.description}`).join("\n");

const skillMiddleware = createMiddleware({
  name: "skillMiddleware",
  tools: [loadSkill],
  wrapModelCall: async (req, handler) =>
    handler({
      ...req,
      systemPrompt:
        (req.systemPrompt ?? "") +
        `\n\n## Available Skills\n${skillsPrompt}\n\nUse load_skill before writing any domain-specific query. Never guess schemas.`,
    }),
});

// ── Agent ─────────────────────────────────────────────────────────────────────
const agent = createAgent({
  model: new ChatOpenAI({ model: "gpt-4.1" }),
  systemPrompt: `You are a SQL query assistant.
1. Identify which skill covers the user's question.
2. Call load_skill to get exact schemas and business rules.
3. Write a correct, read-only SQL query using only the loaded schema.`,
  middleware: [skillMiddleware],
  checkpointer: new MemorySaver(),
});
```

---

## 9. Parallel Execution and the Cancel Bug

### Parallel Execution via `Send`

The `Send` API fans out to multiple nodes concurrently. The target state field **must** have a reducer — without one you get `INVALID_CONCURRENT_GRAPH_UPDATE`.

```typescript
import { Send, StateGraph, START, END, Annotation } from "@langchain/langgraph";

const ReportState = Annotation.Root({
  topic:            Annotation<string>({ reducer: (_, b) => b }),
  completedSections: Annotation<string[]>({
    reducer: (existing, incoming) => [...existing, ...incoming],  // merge from parallel nodes
    default: () => [],
  }),
});

async function orchestratorNode(state: typeof ReportState.State) {
  const sections = ["introduction", "methodology", "results", "conclusion"];
  return sections.map(section => new Send("worker", { section, topic: state.topic }));
}

async function workerNode(state: { section: string; topic: string }) {
  const result = await writerAgent.invoke({
    messages: [{ role: "user", content: `Write the ${state.section} for: ${state.topic}` }],
  });
  return { completedSections: [result.messages.at(-1)?.content as string] };
}

const reportGraph = new StateGraph(ReportState)
  .addNode("orchestrator", orchestratorNode)
  .addNode("worker", workerNode)
  .addNode("synthesizer", synthesizerNode)
  .addEdge(START, "orchestrator")
  .addEdge("orchestrator", "worker")
  .addEdge("worker", "synthesizer")
  .addEdge("synthesizer", END);
```

### The Cancel Bug (GitHub: langchain-ai/deepagents#694)

**Issue:** When parallel subagent calls are used with `createDeepAgent`, a failure in one subagent cancels ALL other running subagents.

**Root cause:** Uses `asyncio.gather(task1(), task2(), ...)` without `return_exceptions=True`.

**Mitigation:**

```typescript
// 1. Wrap individual subagent tool calls in try/catch
const robustSubagentCall = tool(
  async ({ query }) => {
    try {
      const result = await subagent.invoke({ messages: [{ role: "user", content: query }] });
      return result.messages.at(-1)?.content;
    } catch (error) {
      // Return error as string result instead of throwing
      return `Subagent failed: ${error instanceof Error ? error.message : String(error)}`;
    }
  },
  { name: "robust_subagent", description: "...", schema: z.object({ query: z.string() }) }
);

// 2. Use createAsyncSubagentMiddleware with returnExceptions: true
import { createAsyncSubagentMiddleware } from "deepagents/middleware";

const asyncMiddleware = createAsyncSubagentMiddleware({
  returnExceptions: true,  // prevents all-cancel on failure
  maxParallel: 5,
});
```

---

## 10. Context Engineering During Handoffs

### The Message Pairing Invariant

Every tool call creates an `AIMessage` with `tool_calls`. The tool **must** return a `ToolMessage` with the same `tool_call_id`. Failing to pair them causes LLM errors on subsequent turns.

```typescript
// AIMessage from LLM:
{ content: "", tool_calls: [{ id: "call_abc", name: "record_warranty_status", args: { status: "in_warranty" } }] }

// ToolMessage must follow with matching tool_call_id:
new ToolMessage({ content: "Warranty status recorded: in_warranty", tool_call_id: "call_abc" })
```

### Pass Only the Handoff Pair

```typescript
// CORRECT — pass only the handoff pair (last AIMessage + ToolMessage)
const lastAI = [...rt.state.messages].reverse().find(AIMessage.isInstance)!;
return new Command({
  goto: "tech_agent",
  update: { messages: [lastAI, handoffMsg] },  // only the pair
  graph: Command.PARENT,
});

// WRONG — forwarding entire history causes token bloat and context confusion
update: { messages: rt.state.messages }  // DO NOT DO THIS
```

### The `add_messages` Reducer Problem

By default, LangGraph's `messages` field uses the `add_messages` reducer which **appends** to existing messages. When you update `messages` in a `Command`, the receiving agent still sees full history.

**Fix: custom reducer that replaces on handoff**

```typescript
import { Annotation } from "@langchain/langgraph";
import { BaseMessage, ToolMessage } from "@langchain/core/messages";

function handoffAwareReducer(existing: BaseMessage[], incoming: BaseMessage[]): BaseMessage[] {
  const isHandoff = incoming.some(
    m => m instanceof ToolMessage && m.content.toString().startsWith("Transferred")
  );
  if (isHandoff) return incoming;           // replace with just the handoff pair
  return [...existing, ...incoming];         // normal append
}

const MultiAgentState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: handoffAwareReducer,
    default: () => [],
  }),
  activeAgent: Annotation<string>({ default: () => "default" }),
});
```

---

## 11. Import Reference

```typescript
// Supervisor (npm package)
import { createSupervisor } from "@langchain/langgraph-supervisor";

// Swarm (npm package)
import { createSwarm, createHandoffTool, addActiveAgentRouter } from "@langchain/langgraph-swarm";

// Core graph
import { StateGraph, Annotation, MessagesAnnotation, START, END } from "@langchain/langgraph";
import { MemorySaver, InMemoryStore, Command, Send } from "@langchain/langgraph";
import { StateSchema, MessagesValue, ReducedValue } from "@langchain/langgraph";
import { messagesStateReducer } from "@langchain/langgraph";

// Prebuilt agents
import { createReactAgent } from "@langchain/langgraph/prebuilt";

// LangChain v1 high-level API
import { createAgent, createMiddleware, tool } from "langchain";
import { ToolMessage, AIMessage, HumanMessage } from "langchain";
import type { ToolRuntime } from "langchain";

// DeepAgents
import { createDeepAgent, SubAgent, CompiledSubAgent } from "deepagents";
import { createAsyncSubagentMiddleware } from "deepagents/middleware";

// Tools and messages (low-level)
import { tool } from "@langchain/core/tools";
import { HumanMessage, AIMessage, ToolMessage } from "@langchain/core/messages";

// Models
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";

// Zod
import { z } from "zod";
import { z } from "zod/v4";  // use zod/v4 with StateSchema
```

---

## 12. Known Pitfalls

| # | Pitfall | Symptom | Fix |
|---|---------|---------|-----|
| 1 | **Missing ToolMessage in Command** | "tool call not followed by tool result"; LLM errors on next turn | Always include `new ToolMessage({ tool_call_id: runtime.toolCallId })` in `Command.update.messages` |
| 2 | **Mismatched `tool_call_id`** | Runtime error or malformed state | Always use `runtime.toolCallId` — never hardcode or generate a new ID |
| 3 | **Forgetting `graph: Command.PARENT`** | Handoff tool runs but `goto` is ignored; conversation stays in subgraph | Set `graph: Command.PARENT` whenever routing from inside a subgraph to a parent node |
| 4 | **No checkpointer** | `currentStep` resets to default on every `invoke()`; workflow starts over | Always pass `checkpointer: new MemorySaver()` (or production equivalent) to `createAgent` |
| 5 | **Ping-pong loop** | Agent A transfers to B; B immediately transfers back to A; infinite loop | Give each agent an exclusive domain in its prompt; track `activeAgent` to block transferring back to the source |
| 6 | **Handoffs for parallel queries** | 3× slower when query spans multiple domains | Use Router pattern with `Send` for parallel fan-out across domains |
| 7 | **Full history passed on handoff** | Receiving agent confused by irrelevant conversation; high token usage | Pass only the handoff pair `[lastAIMessage, toolMessage]`, not `rt.state.messages` |
| 8 | **`add_messages` reducer accumulates across handoffs** | Receiving agent sees all prior history despite isolated intent | Use a custom `handoffAwareReducer` that replaces messages on handoff events |
| 9 | **God supervisor** | Supervisor with 20+ tools makes poor routing decisions | Split into domain-specific subagents with ≤5 tools each |
| 10 | **Context leaking to subagents** | Subagent is confused; token usage grows per delegation | Pass only the specific task; return only the final result |
| 11 | **Permanent skill loading** | All skill bodies loaded at agent start; context window exhausted | Use progressive disclosure — load skill body only when `load_skill` is called |
| 12 | **Unbounded loops** | Agent calls tools until token limit is hit | Set `recursionLimit` on compiled graph; add iteration counter in state; use circuit breaker |
| 13 | **Parallel cancel bug** (`deepagents#694`) | One subagent failure cancels all parallel subagents | Wrap subagent tool calls in `try/catch`; use `createAsyncSubagentMiddleware({ returnExceptions: true })` |
| 14 | **Vague subagent descriptions** | Supervisor routes to wrong agent | Write specific, distinctive descriptions; test with adversarial queries |
| 15 | **No timeout on subagent calls** | Single stuck subagent blocks entire workflow | Wrap calls with `Promise.race` + timeout rejection |
| 16 | **Missing Zod schema on tool inputs** | Runtime parse errors in LangGraph | Always define `schema: z.object({...})` on every tool |
| 17 | **No `thread_id` in stateful workflows** | Multi-turn state not preserved | Always pass `{ configurable: { thread_id: "..." } }` to `invoke()` |
| 18 | **Streaming across subagents** | Subagent token streams don't propagate to parent (known issue, March 2026) | Collect final results and re-emit; use `streamMode: "updates"` and filter by node name |
