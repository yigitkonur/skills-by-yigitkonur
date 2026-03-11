# Fleet Mode

## What Fleet Mode Does

Fleet mode activates parallel agent execution within a session. Instead of a single agent working sequentially, the CLI spawns multiple sub-agents that tackle parallelizable aspects of the task simultaneously. Use fleet mode when the work can be decomposed into independent tracks — e.g., writing tests while implementing features, or processing multiple independent modules concurrently.

## Activating Fleet Mode

Call `session.rpc.fleet.start()` to enable fleet mode. Returns `{ started: boolean }` indicating whether activation succeeded.

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient();
await client.start();

const session = await client.createSession({
  model: "claude-sonnet-4.5",
  onPermissionRequest: async () => ({ kind: "approved" }),
});

// Activate fleet mode with an optional directing prompt
const result = await session.rpc.fleet.start({
  prompt: "Implement the user authentication module with full test coverage",
});

console.log("Fleet started:", result.started);
// result.started: true if fleet mode activated, false otherwise
```

## Optional Prompt Parameter

The `prompt` parameter is optional. It allows you to direct fleet work at activation time, combining your instructions with the CLI's built-in fleet orchestration instructions.

```typescript
// Without a directing prompt — fleet decides how to parallelize
await session.rpc.fleet.start({});

// With a directing prompt — direct the fleet's focus
await session.rpc.fleet.start({
  prompt: "Focus on the payment processing module. Implement the Stripe integration and write unit tests in parallel.",
});
```

When provided, your prompt is merged with the fleet instructions. The CLI determines the actual parallelization strategy; you provide the task focus.

## Fleet Mode Parameters

From the RPC schema:
- `sessionId` — auto-injected by the SDK, do not pass manually
- `prompt?: string` — optional user prompt to combine with fleet instructions

```typescript
// Type: SessionFleetStartParams (minus sessionId)
interface FleetStartOptions {
  prompt?: string;
}

// Return type
interface FleetStartResult {
  started: boolean;
}
```

## Monitoring Fleet Execution

Listen to session events to track fleet progress. Fleet sub-agents emit the same event types as single-agent sessions.

```typescript
const session = await client.createSession({
  model: "claude-sonnet-4.5",
  onPermissionRequest: async () => ({ kind: "approved" }),
});

// Track tool executions across all fleet sub-agents
session.on((event) => {
  switch (event.type) {
    case "tool.execution_start":
      console.log("Tool executing:", event.data.toolName);
      break;
    case "tool.execution_end":
      console.log("Tool complete:", event.data.toolName);
      break;
    case "assistant.message":
      console.log("Agent message:", event.data.content?.substring(0, 100));
      break;
    case "session.idle":
      console.log("Fleet work complete — all sub-agents finished");
      break;
  }
});

await session.rpc.fleet.start({
  prompt: "Implement the data pipeline with parallel processing stages",
});

// Wait for all fleet work to complete
await session.waitForIdle();
```

## Fleet Mode vs. Single Session

| Aspect | Single Session | Fleet Mode |
|--------|---------------|------------|
| Execution | Sequential | Parallel sub-agents |
| Use case | Linear tasks, step-by-step refactors | Parallelizable work, independent modules |
| Context | Single shared context | Distributed across sub-agents |
| Overhead | None | Orchestration overhead |
| Predictability | High — deterministic ordering | Lower — parallel execution |

Use single sessions when tasks have sequential dependencies (step A must complete before step B) or when you need to observe and steer each step. Use fleet mode when the task has independent tracks that benefit from parallelism.

## Fleet Mode with Plan Mode

Combine plan mode with fleet for complex parallel work: plan first, review, then activate fleet for execution.

```typescript
const session = await client.createSession({
  model: "claude-sonnet-4.5",
  onPermissionRequest: async () => ({ kind: "approved" }),
});

// Phase 1: Plan the work
await session.rpc.mode.set({ mode: "plan" });

const planReady = new Promise<void>((resolve) => {
  session.on((event) => {
    if (event.type === "exit_plan_mode.requested") resolve();
  });
});

await session.send({ prompt: "Implement the complete e-commerce checkout flow" });
await planReady;

// Review the plan
const plan = await session.rpc.plan.read();
console.log(plan.content);

// Phase 2: Execute with fleet parallelism
// Switch to autopilot then activate fleet
await session.rpc.mode.set({ mode: "autopilot" });
const fleetResult = await session.rpc.fleet.start({
  prompt: "Execute the plan with parallel sub-agents for each component",
});

await session.waitForIdle();
```

## Limitations and Requirements

- Fleet mode requires the CLI to support parallel agent orchestration — check `result.started` to confirm activation.
- Fleet sub-agents share the session's permission handler; all sub-agent permission requests route through the same `onPermissionRequest` callback.
- The `prompt` parameter is optional but recommended for complex tasks to guide the parallelization strategy.
- Fleet mode is not appropriate for tasks where sub-tasks must execute in strict sequence — use chained `send()` calls with `waitForIdle()` instead.
- External tools registered via `defineTool` are available to all fleet sub-agents; tool handlers may be called concurrently from multiple sub-agents, so make them thread-safe.
