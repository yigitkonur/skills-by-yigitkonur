# Human-in-the-Loop (HITL) — LangGraph.js TypeScript Reference

> LangGraph.js v0.2+. All examples are TypeScript.

---

## Core Mechanisms

| Mechanism | API | Use when |
|---|---|---|
| Dynamic interrupt | `interrupt()` inside a node or tool | Conditional, production HITL |
| Static pre-node pause | `interruptBefore: ["nodeName"]` at compile | Debugging, deterministic pre-node review |
| Static post-node pause | `interruptAfter: ["nodeName"]` at compile | Debugging, post-node inspection |

**Key invariants:**
1. A **checkpointer** is mandatory — without it state cannot survive the pause.
2. `thread_id` in `configurable` identifies which conversation thread to resume.
3. Resuming always uses `new Command({ resume: value })` passed to `graph.invoke()` or `graph.stream()`.
4. On resume the **node restarts from its beginning** — all code before `interrupt()` runs again.

---

## interrupt() Function

```typescript
import { interrupt } from "@langchain/langgraph";

const humanResponse = interrupt(payload);
// payload: any JSON-serializable value
// returns: the value passed as Command({ resume: value }) by the caller
// throws: GraphInterrupt — DO NOT catch
```

**Under the hood:** saves graph state to checkpointer → throws `GraphInterrupt` → caller receives `{ __interrupt__: [{ id, value: payload, resumable: true, when: "during" }] }` → `Command({ resume })` with same `thread_id` restarts the node and `interrupt()` returns the value.

```typescript
import { StateGraph, MessagesAnnotation, interrupt, Command, MemorySaver } from "@langchain/langgraph";

function humanApprovalNode(state: typeof MessagesAnnotation.State) {
  const decision = interrupt({
    message: "Do you approve this action?",
    context: state.messages.at(-1)?.content,
  });
  if (decision === "approve") {
    return { messages: [{ role: "assistant", content: "Approved. Proceeding." }] };
  }
  return { messages: [{ role: "assistant", content: "Action rejected by human." }] };
}

const graph = new StateGraph(MessagesAnnotation)
  .addNode("humanApproval", humanApprovalNode)
  .addEdge("__start__", "humanApproval")
  .addEdge("humanApproval", "__end__")
  .compile({ checkpointer: new MemorySaver() });

const config = { configurable: { thread_id: "thread-001" } };

// First call — pauses at interrupt
const result1 = await graph.invoke(
  { messages: [{ role: "user", content: "Execute dangerous action" }] },
  config
);
// result1.__interrupt__ = [{ id: "...", value: { message: "...", context: "..." } }]

// Resume with human decision
const result2 = await graph.invoke(new Command({ resume: "approve" }), config);
```

---

## Static Breakpoints: interruptBefore / interruptAfter

```typescript
const graph = new StateGraph(MessagesAnnotation)
  .addNode("planNode", planNode)
  .addNode("executeNode", executeNode)
  .addEdge("__start__", "planNode")
  .addEdge("planNode", "executeNode")
  .addEdge("executeNode", "__end__")
  .compile({
    checkpointer: new MemorySaver(),
    interruptBefore: ["executeNode"],  // pause before executeNode runs
    interruptAfter: ["planNode"],      // pause after planNode completes
    // interruptBefore: ["*"]          // pause before every node (step-through debugging)
  });

const config = { configurable: { thread_id: "debug-001" } };
await graph.invoke({ messages: [...] }, config);

const state = await graph.getState(config);
console.log(state.values);  // what planNode produced
console.log(state.next);    // ["executeNode"]

// Edit state before resuming
await graph.updateState(config, {
  messages: [...state.values.messages, { role: "human", content: "Use approach B." }],
});
await graph.invoke(null, config);  // resume with modified state
```

---

## Dynamic Breakpoints

Conditional interrupts — recommended for production:

```typescript
function executeActionNode(state) {
  const action = state.pendingAction;

  if (action.isDestructive || action.affectsProduction) {
    const decision = interrupt({
      question: `This action will ${action.description}. Approve?`,
      action,
      riskLevel: action.riskLevel,
    });

    if (decision === "reject") return new Command({ goto: "cancelAction" });
    if (decision?.type === "edit") {
      return new Command({ update: { pendingAction: decision.editedAction }, goto: "executeAction" });
    }
  }
  return executeDirectly(action);
}

// Loop until valid input
function collectInfoNode(state) {
  let prompt = "Please provide your customer ID (8-digit number):";
  while (true) {
    const answer = interrupt(prompt);
    if (/^\d{8}$/.test(answer)) return { customerId: answer };
    prompt = `'${answer}' is invalid. Must be 8 digits. Try again:`;
  }
}
```

---

## Command({ resume }): Simple, Structured, Routing

```typescript
import { Command } from "@langchain/langgraph";

await graph.invoke(new Command({ resume: "approve" }), config);                // simple value

await graph.invoke(new Command({                                                // structured data
  resume: { action: "approve", editedArgs: { to: "team@example.com" } },
}), config);

await graph.invoke(new Command({ resume: "confirmed", goto: "processConfirmation" }), config);  // route

// Inside a node: route after interrupt
function approvalNode(state) {
  const decision = interrupt({ question: "Proceed with deployment?" });
  return new Command({
    goto: decision === "yes" ? "deploy" : "cancel",
    update: { approvedBy: "human", approvalTime: Date.now() },
  });
}
```

---

## State Persistence During Interrupts

```typescript
import { MemorySaver } from "@langchain/langgraph";
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";

const checkpointer = new MemorySaver();                                       // dev only
const checkpointer = PostgresSaver.fromConnString(process.env.DATABASE_URL!); // production
await checkpointer.setup();                                                    // creates tables once

// thread_id — one stable UUID per user session, never regenerate per request
const config = { configurable: { thread_id: `user-${userId}-session-${sessionId}` } };

// Inspect paused state
const state = await graph.getState(config);
console.log(state.values);    // current graph state
console.log(state.next);      // pending nodes — non-empty means interrupted
const interrupt = state.tasks?.[0]?.interrupts?.[0];
if (interrupt) console.log(interrupt.value);  // payload passed to interrupt()

// Server pattern: detect pending interrupt vs. fresh start
app.post("/chat", async (req, res) => {
  const { message, sessionId } = req.body;
  const config = { configurable: { thread_id: sessionId } };
  const preState = await graph.getState(config);

  const result = preState.next.length > 0
    ? await graph.invoke(new Command({ resume: message }), config)
    : await graph.invoke({ messages: [new HumanMessage(message)] }, config);

  const postState = await graph.getState(config);
  const pending = postState.tasks?.[0]?.interrupts?.[0];

  res.json(pending?.value
    ? { type: "interrupt", payload: pending.value }
    : { type: "response", message: result.messages.at(-1)?.content }
  );
});
```

---

## Tool Approval Patterns

### interrupt() Inside a Tool

```typescript
import { tool } from "@langchain/core/tools";
import { interrupt } from "@langchain/langgraph";
import { z } from "zod";

const sendEmailTool = tool(
  async ({ to, subject, body }) => {
    const response = interrupt({
      actionType: "send_email",
      preview: { to, subject, body: body.slice(0, 200) },
      message: "Review email. Approve, edit, or reject?",
    });

    if (response?.action === "reject") return "Email cancelled.";
    const finalTo      = response?.editedArgs?.to      ?? to;
    const finalSubject = response?.editedArgs?.subject  ?? subject;
    const finalBody    = response?.editedArgs?.body     ?? body;
    await emailClient.send({ to: finalTo, subject: finalSubject, body: finalBody });
    return `Email sent to ${finalTo}.`;
  },
  { name: "send_email", description: "Send an email", schema: z.object({ to: z.string().email(), subject: z.string(), body: z.string() }) }
);
```

### Custom ToolNode with Per-Tool HITL

```typescript
import { ToolNode } from "@langchain/langgraph/prebuilt";
import { AIMessage, ToolMessage } from "@langchain/core/messages";

const SENSITIVE_TOOLS = new Set(["send_email", "delete_record", "deploy_service"]);

async function customToolNode(state) {
  const lastMessage = state.messages.at(-1) as AIMessage;

  for (const toolCall of lastMessage.tool_calls ?? []) {
    if (SENSITIVE_TOOLS.has(toolCall.name)) {
      const decision = interrupt({ tool: toolCall.name, args: toolCall.args });
      if (decision !== "approve") {
        return {
          messages: [new ToolMessage({ tool_call_id: toolCall.id, content: `${toolCall.name} rejected.` })],
        };
      }
    }
  }
  return new ToolNode(tools)(state);
}
```

### interruptBefore: ["tools"] Pattern

```typescript
const graph = builder.compile({ checkpointer, interruptBefore: ["tools"] });

const state = await graph.getState(config);
const toolCalls = state.values.messages.at(-1)?.tool_calls;

// Optionally edit tool call arguments before resuming
await graph.updateState(config, {
  messages: [{
    ...state.values.messages.at(-1),
    tool_calls: toolCalls.map(tc =>
      tc.name === "send_email" ? { ...tc, args: { ...tc.args, to: "reviewed@example.com" } } : tc
    ),
  }],
}, { asNode: "agent" });

await graph.invoke(null, config);
```

---

## HITL Middleware: interruptOn Config

```typescript
import { createReactAgent } from "@langchain/langgraph/prebuilt";

const agent = createReactAgent({
  llm, tools, checkpointer: new MemorySaver(),
  interruptOn: {
    send_email:     true,                                                        // approve | edit | reject
    execute_sql:    { allowedDecisions: ["approve", "reject"], description: "Requires DBA" },
    read_data:      false,                                                        // never interrupt
    deploy_service: { allowedDecisions: ["approve"], description: "Engineer only" },
  },
});
```

**HITLRequest payload shape:**

```typescript
interface HITLRequest {
  action_requests: { name: string; arguments: Record<string, unknown>; description?: string }[];
  review_configs:  { action_name: string; allowed_decisions: ("approve" | "edit" | "reject")[] }[];
}
```

**Resume with decisions — order must match `action_requests` order:**

```typescript
// Approve
await agent.invoke(new Command({ resume: { decisions: [{ type: "approve" }] } }), config);

// Edit args
await agent.invoke(new Command({
  resume: { decisions: [{ type: "edit", editedAction: { name: "send_email", args: { to: "fixed@example.com" } } }] },
}), config);

// Reject
await agent.invoke(new Command({
  resume: { decisions: [{ type: "reject", message: "Route to internal team instead." }] },
}), config);

// Batch — one decision per tool call in order
await agent.invoke(new Command({
  resume: { decisions: [{ type: "approve" }, { type: "reject", message: "Not now." }] },
}), config);
```

---

## Multiple Interrupts in One Node

Each call to `interrupt()` in a node sequence resumes one at a time — the node restarts each time until all interrupts have been resolved:

```typescript
function multiQuestionNode(state) {
  const name = interrupt("What is your name?");
  const age  = interrupt("What is your age?");
  const city = interrupt("What is your city?");
  return { userProfile: { name, age: parseInt(age), city } };
}

const r1 = await graph.invoke(input, config);                               // pauses: "name?"
const r2 = await graph.invoke(new Command({ resume: "Alice" }), config);   // pauses: "age?"
const r3 = await graph.invoke(new Command({ resume: "30" }), config);      // pauses: "city?"
const r4 = await graph.invoke(new Command({ resume: "Berlin" }), config);  // done
// r4.userProfile = { name: "Alice", age: 30, city: "Berlin" }
```

---

## Streaming with HITL

```typescript
// __interrupt__ appears in "updates" streamMode chunks
for await (const chunk of graph.stream(input, config, { streamMode: ["updates", "messages"] })) {
  if (chunk.__interrupt__) {
    const humanResponse = await collectHumanInput(chunk.__interrupt__[0].value);
    for await (const rc of graph.stream(new Command({ resume: humanResponse }), config, { streamMode: "updates" })) {
      // process resumed chunks
    }
    break;
  }
  if (chunk.messages) {
    for (const msg of chunk.messages)
      process.stdout.write(typeof msg.content === "string" ? msg.content : "");
  }
}
```

### WebSocket streaming with HITL

```typescript
import { WebSocketServer } from "ws";

const wss = new WebSocketServer({ port: 8080 });

wss.on("connection", (ws) => {
  ws.on("message", async (data) => {
    const { type, message, sessionId, resumeValue } = JSON.parse(data.toString());
    const config = { configurable: { thread_id: sessionId } };

    const input = type === "resume"
      ? new Command({ resume: resumeValue })
      : { messages: [{ role: "user", content: message }] };

    for await (const chunk of graph.stream(input, config, { streamMode: "updates" })) {
      if (chunk.__interrupt__) {
        ws.send(JSON.stringify({ type: "interrupt", payload: chunk.__interrupt__[0].value }));
        return; // wait for next ws message to resume
      }
      ws.send(JSON.stringify({ type: "chunk", data: chunk }));
    }

    ws.send(JSON.stringify({ type: "done" }));
  });
});
```

---

## Time Travel: getStateHistory, Replay, Fork

```typescript
// Get full checkpoint history — most recent first
const snapshots: StateSnapshot[] = [];
for await (const s of graph.getStateHistory(config)) snapshots.push(s);
// s.values, s.next, s.config (has checkpoint_id), s.metadata

// Replay from a specific checkpoint
const beforeExecute = snapshots.find(s => s.next.includes("executeNode"));
await graph.invoke(null, beforeExecute!.config);

// Fork: alter timeline without touching original
const pastState = snapshots.find(s => s.values.plan !== undefined);
const forkConfig = await graph.updateState(
  pastState!.config,
  { plan: "Use approach B" },
  { asNode: "planner" }  // attribute update as if planner produced it
);
await graph.invoke(null, forkConfig);

// Edit state during a HITL pause, then resume
await graph.updateState(config, { plan: "Corrected: use read-only DB", humanNotes: "Reviewed" });
await graph.invoke(new Command({ resume: "approved" }), config);
```

---

## Frontend UI: useStream Hook and ApprovalCard

```typescript
import { useStream } from "@langchain/langgraph-sdk/react";

const stream = useStream<AgentState>({
  apiUrl: process.env.NEXT_PUBLIC_LANGGRAPH_URL!,
  assistantId: "my-agent",
  threadId,
  onThreadId: setThreadId,
});
// stream.messages, stream.interrupt (HITLRequest|null), stream.isLoading
// stream.submit(input, { command?: { resume: unknown } })
```

```tsx
function ApprovalCard({ interrupt, onRespond }: { interrupt: HITLRequest; onRespond: (d: Decision[]) => void }) {
  const [editedArgs, setEditedArgs] = useState<Record<string, unknown>>({});
  return (
    <div>
      {interrupt.action_requests.map((req, i) => {
        const cfg = interrupt.review_configs[i];
        return (
          <div key={i}>
            <h3>Review: {req.name}</h3>
            <pre>{JSON.stringify(req.arguments, null, 2)}</pre>
            {cfg.allowed_decisions.includes("approve") && (
              <button onClick={() => onRespond([{ type: "approve" }])}>Approve</button>
            )}
            {cfg.allowed_decisions.includes("edit") && (
              <button onClick={() => onRespond([{ type: "edit", editedAction: { name: req.name, args: editedArgs } }])}>
                Approve with Edits
              </button>
            )}
            {cfg.allowed_decisions.includes("reject") && (
              <button onClick={() => onRespond([{ type: "reject", message: "Rejected." }])}>Reject</button>
            )}
          </div>
        );
      })}
    </div>
  );
}

// In ChatWithHITL component:
{stream.interrupt && (
  <ApprovalCard
    interrupt={stream.interrupt}
    onRespond={(decisions) => stream.submit(null, { command: { resume: { decisions } } })}
  />
)}
```

---

## Async Approval: Slack, Email, Webhook

For approvals spanning minutes/hours, state must survive restarts — use `PostgresSaver`.

```
Agent hits interrupt → state persisted in PostgreSQL → Slack/email notification sent
Reviewer clicks link → POST /resume { thread_id, decision }
  → graph.invoke(Command({ resume }), config) → execution continues
```

**Slack (@slack/bolt):**

```typescript
async function notifySlack(threadId: string, payload: unknown) {
  await slackClient.chat.postMessage({
    channel: process.env.APPROVAL_CHANNEL!,
    text: "Agent requires approval",
    blocks: [
      { type: "section", text: { type: "mrkdwn", text: `*Action:* ${JSON.stringify(payload)}` } },
      {
        type: "actions", block_id: `approval_${threadId}`,
        elements: [
          { type: "button", text: { type: "plain_text", text: "Approve" }, value: `approve:${threadId}`, action_id: "approve_action", style: "primary" },
          { type: "button", text: { type: "plain_text", text: "Reject" },  value: `reject:${threadId}`,  action_id: "reject_action",  style: "danger"  },
        ],
      },
    ],
  });
}

slackApp.action(/^(approve|reject)_action$/, async ({ action, ack }) => {
  await ack();
  const [decision, threadId] = (action as { value: string }).value.split(":");
  await graph.invoke(new Command({ resume: decision }), { configurable: { thread_id: threadId } });
});
```

**Email (Resend) with callback URL:**

```typescript
import { Resend } from "resend";
const resend = new Resend(process.env.RESEND_API_KEY);

async function sendApprovalEmail(threadId: string, payload: unknown, to: string) {
  const base = process.env.APP_URL;
  await resend.emails.send({
    from: "agent@yourapp.com", to,
    subject: "Agent Action Requires Your Approval",
    html: `<pre>${JSON.stringify(payload, null, 2)}</pre>
      <a href="${base}/api/approve?thread=${threadId}&decision=approve">APPROVE</a>
      <a href="${base}/api/approve?thread=${threadId}&decision=reject">REJECT</a>`,
  });
}

app.get("/api/approve", async (req, res) => {
  const { thread, decision } = req.query as { thread: string; decision: string };
  const state = await graph.getState({ configurable: { thread_id: thread } });
  if (state.next.length === 0) return res.send("Already processed.");
  await graph.invoke(new Command({ resume: decision }), { configurable: { thread_id: thread } });
  res.send(`Decision recorded: ${decision}.`);
});
```

**Timeout escalation (node-cron):**

```typescript
import cron from "node-cron";
cron.schedule("*/30 * * * *", async () => {
  const stale = await db.query(
    `SELECT thread_id FROM checkpoints WHERE status = 'interrupted' AND created_at < NOW() - INTERVAL '4 hours'`
  );
  for (const { thread_id } of stale.rows) {
    await graph.updateState({ configurable: { thread_id } }, { escalated: true });
    await graph.invoke(new Command({ resume: "escalate" }), { configurable: { thread_id } });
  }
});
```

---

## RBAC: Role Hierarchy and Multi-Level Approval

```typescript
const ROLE_HIERARCHY = ["editor", "publisher", "admin"];

function canApprove(approverRole: string, requiredRole: string) {
  return ROLE_HIERARCHY.indexOf(approverRole) >= ROLE_HIERARCHY.indexOf(requiredRole);
}

const approvalPolicies = {
  publish_blog_post: { minRole: "publisher" },
  delete_content:    { minRole: "admin" },
};

// Multi-level: initial → escalate to senior
function initialReviewNode(state) {
  const decision = interrupt({ level: "initial", context: state.pendingAction });
  if (decision === "escalate") return new Command({ goto: "seniorReview", update: { reviewLevel: "senior" } });
  return new Command({ goto: "execute", update: { approvedBy: "reviewer" } });
}

function seniorReviewNode(state) {
  const decision = interrupt({ level: "senior", context: state.pendingAction });
  if (decision !== "approve") return new Command({ goto: "reject" });
  return new Command({ goto: "execute", update: { approvedBy: "senior" } });
}
```

---

## Confidence / Cost Thresholds

```typescript
const AUTO_APPROVE_THRESHOLD = 0.92;
const COST_REVIEW_THRESHOLD  = 10.00; // USD

function qualityGateNode(state: { messages: BaseMessage[]; confidenceScore?: number; estimatedCost?: number }) {
  const confidence = state.confidenceScore ?? 0;
  const cost       = state.estimatedCost   ?? 0;

  if (confidence >= AUTO_APPROVE_THRESHOLD && cost < COST_REVIEW_THRESHOLD) {
    return { requiresHumanApproval: false };
  }

  const decision = interrupt({
    reason:    confidence < AUTO_APPROVE_THRESHOLD ? "low_confidence" : "high_cost",
    message:   confidence < AUTO_APPROVE_THRESHOLD
      ? `Confidence ${(confidence * 100).toFixed(0)}% below threshold. Review?`
      : `Estimated cost $${cost.toFixed(2)} exceeds threshold. Approve?`,
  });
  return { requiresHumanApproval: true, humanDecision: decision };
}
```

---

## Multi-Step Approval Chains

Use a linear pipeline of nodes, each with its own `interrupt()`, to route content through multiple reviewers in sequence (e.g., content team → legal → final sign-off).

```typescript
const multiStepApprovalGraph = new StateGraph(approvalState)
  .addNode("generateContent",  generateContentNode)
  .addNode("contentReview",    contentReviewNode)    // interrupt 1 — content team
  .addNode("complianceCheck",  complianceCheckNode)  // interrupt 2 — legal
  .addNode("finalApproval",    finalApprovalNode)    // interrupt 3 — senior sign-off
  .addNode("publish",          publishNode)
  .addEdge("__start__",       "generateContent")
  .addEdge("generateContent", "contentReview")
  .addEdge("contentReview",   "complianceCheck")
  .addEdge("complianceCheck", "finalApproval")
  .addEdge("finalApproval",   "publish")
  .compile({ checkpointer });

function contentReviewNode(state) {
  const edits = interrupt({
    stage:    "content_review",
    content:  state.draft,
    reviewer: "content_team",
    message:  "Review generated content",
  });
  return { draft: edits?.revised ?? state.draft };
}

function complianceCheckNode(state) {
  const approval = interrupt({
    stage:    "compliance",
    content:  state.draft,
    reviewer: "legal_team",
    message:  "Compliance review required",
  });
  return { complianceApproved: approval === "approved" };
}

function finalApprovalNode(state) {
  const decision = interrupt({
    stage:   "final_approval",
    draft:   state.draft,
    message: "Final sign-off before publish",
  });
  if (decision !== "approve") return new Command({ goto: "__end__", update: { status: "rejected" } });
  return { finalApproved: true };
}
```

Each stage is a separate `invoke` + `Command({ resume })` cycle on the same `thread_id`. Three reviewers, three separate HTTP requests, all tracked by a single checkpoint.

### Supervisor pattern with HITL gating

Gate which sub-agent the supervisor is allowed to invoke:

```typescript
function supervisorWithHITL(state) {
  const nextAgent = state.nextAction;

  if (nextAgent === "deploy_agent" || nextAgent === "database_agent") {
    const approval = interrupt({
      message:         `Supervisor wants to invoke ${nextAgent}. Approve?`,
      plannedActions:  state.plan,
      subAgent:        nextAgent,
    });

    if (approval !== "approve") {
      return new Command({ goto: "__end__", update: { status: "halted_by_human" } });
    }
  }

  return new Command({ goto: nextAgent });
}
```

### Subgraph interrupt propagation

Interrupts inside a compiled subgraph surface in the parent — parent handles them via the same `thread_id`:

```typescript
const subgraph = new StateGraph(SubState)
  .addNode("sensitiveOp", (state) => {
    const ok = interrupt("Approve sub-operation?");
    return { subResult: ok === "yes" ? "done" : "skipped" };
  })
  .compile({ checkpointer });  // subgraph must have its own checkpointer

const parentGraph = new StateGraph(ParentState)
  .addNode("runSubgraph", subgraph)  // add as named node, not as function call
  .compile({ checkpointer });

// Interrupt from subgraph propagates to parent result
const r1 = await parentGraph.invoke(input, config);
// r1.__interrupt__ set — parent receives subgraph interrupt

const r2 = await parentGraph.invoke(new Command({ resume: "yes" }), config);
```

### Tool action decision table

| Tool / Action | Allowed Decisions | Rationale |
|---|---|---|
| `send_email` | approve, edit, reject | Review recipient and content |
| `update_database` | approve, reject | No editing — approve exact query or reject |
| `transfer_funds` | approve, reject | Financial actions must not be edited |
| `delete_files` | approve, reject | Destructive — no ambiguity |
| `call_external_api` | approve, edit, reject | May need parameter adjustment |
| `deploy_service` | approve | Senior approval only, no editing |

---

## Testing HITL Workflows

```typescript
import { describe, it, expect } from "vitest";
import { MemorySaver, Command } from "@langchain/langgraph";

describe("HITL approval", () => {
  it("pauses and returns interrupt payload", async () => {
    const config = { configurable: { thread_id: `test-${Date.now()}` } };
    const result = await graph.invoke({ messages: [new HumanMessage("Send email")] }, config);
    expect(result.__interrupt__[0].value).toMatchObject({ actionType: "send_email" });
  });

  it("resumes and approves", async () => {
    const config = { configurable: { thread_id: `test-approve-${Date.now()}` } };
    await graph.invoke({ messages: [new HumanMessage("Send email")] }, config);
    const result = await graph.invoke(new Command({ resume: { action: "approve" } }), config);
    expect(result.messages.at(-1)?.content).toContain("Email sent");
  });

  it("allows state editing before resume (time-travel)", async () => {
    const config = { configurable: { thread_id: `test-edit-${Date.now()}` } };
    await graph.invoke({ messages: [...] }, config);
    await graph.updateState(config, { correctedPlan: "Use read-only DB" }, { asNode: "humanApproval" });
    const result = await graph.invoke(new Command({ resume: "approved" }), config);
    expect(result.correctedPlan).toBe("Use read-only DB");
  });

  it("supports time-travel replay from checkpoint", async () => {
    const config = { configurable: { thread_id: `test-replay-${Date.now()}` } };
    await graph.invoke(input, config);
    const snapshots: StateSnapshot[] = [];
    for await (const s of graph.getStateHistory(config)) snapshots.push(s);
    const beforeFailure = snapshots.find(s => s.next.includes("problematicNode"));
    const replayResult = await graph.invoke(null, beforeFailure!.config);
    expect(replayResult).toBeDefined();
  });
});
```

---

## Production Checklist

- [ ] `MemorySaver` in dev, `PostgresSaver` (with `checkpointer.setup()`) in production
- [ ] `thread_id` is stable per user session — never regenerate per request
- [ ] Side effects before `interrupt()` use idempotency keys (code runs twice on resume)
- [ ] Interrupt payloads are plain JSON-serializable objects — no classes, no functions
- [ ] `interrupt()` is never wrapped in `try/catch`
- [ ] Interrupt call order inside a node is deterministic — no conditional ordering
- [ ] `getState().next.length > 0` checked before sending `Command` vs. fresh input
- [ ] `decisions` array order matches `action_requests` order (HITL middleware)
- [ ] All decisions written to audit log with `userId`, `toolName`, `decision`, timestamp
- [ ] Subgraphs added via `.addNode()`, not called as functions

**Idempotency + audit log:**

```typescript
// Idempotency for side effects that run before interrupt()
async function sendEmailSafely(args: EmailArgs, idempotencyKey: string) {
  const existing = await db.query("SELECT id FROM sent_emails WHERE idempotency_key = $1", [idempotencyKey]);
  if (existing.rows.length > 0) return `Already sent (key: ${idempotencyKey})`;
  await emailClient.send(args);
  await db.query("INSERT INTO sent_emails (idempotency_key) VALUES ($1)", [idempotencyKey]);
  return "Email sent";
}

// Audit log
function logHITLDecision(threadId: string, toolName: string, decision: string, userId: string) {
  return db.query(
    `INSERT INTO hitl_audit_log (thread_id, tool_name, decision, decided_by, decided_at) VALUES ($1, $2, $3, $4, NOW())`,
    [threadId, toolName, decision, userId]
  );
}
```

---

## 9 Anti-Patterns

| Anti-Pattern | Why It Breaks | Fix |
|---|---|---|
| `try { interrupt(...) } catch(e) {}` | Swallows `GraphInterrupt`, prevents pause | Never catch around `interrupt()` |
| New `thread_id` per request | Creates new execution, loses paused state | One stable UUID per user session |
| No checkpointer on compile | State lost on process restart | Always provide checkpointer |
| Non-idempotent code before `interrupt()` | Runs twice on resume | Use idempotency keys or separate into a prior node |
| Conditional `interrupt()` call order | Interrupt IDs mismatched on resume | Keep call order deterministic |
| Class instances in interrupt payload | Cannot serialize to checkpoint | Use plain JSON objects only |
| `interruptBefore` for production HITL | No runtime condition, no resume value | Use dynamic `interrupt()` |
| Not checking `getState().next` before re-invoke | Starts new run instead of resuming | Check `preState.next.length > 0` first |
| Wrong order in `decisions` array | Wrong tool gets wrong decision | Order matches `action_requests` index |

**Subgraph interrupt gotcha:**

```typescript
// WRONG: subgraph called as a function — on resume both parent and subgraph restart
async function parentNode(state) { return await subgraph.invoke(state, config); }

// CORRECT: add as a named node — only the subgraph node restarts on resume
const parentGraph = new StateGraph(ParentState)
  .addNode("subgraphNode", compiledSubgraph)
  .compile({ checkpointer });
```

**Concurrent thread trap:**

```typescript
// A single thread_id cannot be in two interrupt states simultaneously
// Use separate thread_ids for concurrent interactions
const userThreadId     = `user:${userId}:chat`;
const approvalThreadId = `user:${userId}:approval:${Date.now()}`;
// When approved, inject result back via graph.updateState(userThreadConfig, ...)
```

---

## API Quick Reference

```typescript
import { interrupt, Command, StateGraph, MessagesAnnotation, START, END } from "@langchain/langgraph";
import { MemorySaver } from "@langchain/langgraph";
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";
import { HumanMessage, AIMessage, ToolMessage } from "@langchain/core/messages";
import { tool } from "@langchain/core/tools";
import { ToolNode, createReactAgent } from "@langchain/langgraph/prebuilt";
import { useStream } from "@langchain/langgraph-sdk/react";

// interrupt(payload) — inside any node or tool
// throws GraphInterrupt · returns Command({ resume }) value on next invoke

// Command — resume or route
new Command({ resume: value })
new Command({ update: Partial<State>, goto: string | string[], graph?: "parent" })
new Command({ resume: value, goto: "nextNode" })

// compile options: { checkpointer, interruptBefore: string[]|"*", interruptAfter: string[]|"*" }

// StateSnapshot (from getState / getStateHistory)
// { values, next: string[], tasks (with .interrupts), config, metadata, createdAt }

// graph.updateState(config, values, { asNode? }) → RunnableConfig (new fork checkpoint)

// graph.getStateHistory(config, { limit?, before?, filter? }) → AsyncGenerator<StateSnapshot>

// streamMode: "values" | "updates" | "messages" | "debug" | string[]
// __interrupt__ appears in "updates" mode · subgraphs: true includes subgraph events

// useStream hook
// stream.messages | stream.interrupt (HITLRequest|null) | stream.isLoading
// stream.submit(input, { command?: { resume: unknown } })
```
