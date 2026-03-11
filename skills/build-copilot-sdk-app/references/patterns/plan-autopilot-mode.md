# Plan and Autopilot Mode

## Three Session Modes

Every session operates in one of three modes. Get and set via `session.rpc.mode.get()` and `session.rpc.mode.set({ mode })`.

```typescript
const { mode } = await session.rpc.mode.get();
// Returns: "interactive" | "plan" | "autopilot"

await session.rpc.mode.set({ mode: "plan" });
await session.rpc.mode.set({ mode: "autopilot" });
await session.rpc.mode.set({ mode: "interactive" });
```

### Mode Behaviors

- **`"interactive"`** (default) — agent executes immediately, applies changes directly, no planning phase. Use for conversational coding assistance, quick fixes, direct file edits.
- **`"plan"`** — agent creates a structured plan before executing. Agent writes a plan file, then emits `exit_plan_mode.requested` waiting for approval before proceeding. Use when you need human review of approach before the agent touches files.
- **`"autopilot"`** — agent executes autonomously with no confirmation prompts. Requires explicit mode switch. Use for unattended batch operations once the plan is approved.

## Plan Mode Workflow

Set plan mode before sending the task. The agent creates a plan and halts, waiting for approval.

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient();
await client.start();

const session = await client.createSession({
  model: "claude-sonnet-4.5",
  onPermissionRequest: async () => ({ kind: "approved" }),
});

// 1. Switch to plan mode before sending the task
await session.rpc.mode.set({ mode: "plan" });

// 2. Register handler for exit_plan_mode.requested BEFORE sending prompt
const planApprovalPromise = new Promise<void>((resolve) => {
  session.on((event) => {
    if (event.type === "exit_plan_mode.requested") {
      console.log("Agent summary:", event.data.summary);
      resolve();
    }
  });
});

// 3. Send the task — agent writes a plan and pauses
await session.send({ prompt: "Refactor the auth module to use JWT tokens" });

// 4. Wait for the agent to finish planning
await planApprovalPromise;
```

## Reading and Inspecting the Plan

After `exit_plan_mode.requested` fires, read the plan content before approving.

```typescript
const planResult = await session.rpc.plan.read();
// planResult.exists: boolean
// planResult.content: string | null
// planResult.path: string | null (absolute path, null if workspace not enabled)

if (planResult.exists && planResult.content) {
  console.log("Plan content:\n", planResult.content);
  // Inspect, validate, or display to the user
}
```

## Modifying the Plan Before Approval

Override the plan content programmatically before switching to autopilot.

```typescript
// Update plan with modifications (full content replacement)
await session.rpc.plan.update({
  content: modifiedPlanContent,
});

// Or delete the plan to force re-planning
await session.rpc.plan.delete();
await session.send({ prompt: "Re-plan with the additional constraint: maintain backward compatibility" });
```

## Switching to Autopilot After Plan Approval

After reviewing the plan, switch to autopilot and let the agent execute.

```typescript
// 5. Approve: switch to autopilot — agent begins execution
await session.rpc.mode.set({ mode: "autopilot" });

// 6. Wait for execution to complete
await session.waitForIdle();

// Optionally monitor progress
session.on((event) => {
  if (event.type === "tool.execution_start") {
    console.log("Executing:", event.data.toolName);
  }
  if (event.type === "session.idle") {
    console.log("Execution complete");
  }
});
```

## Complete Plan-then-Execute Example

```typescript
import { CopilotClient } from "@github/copilot-sdk";

async function planAndExecute(task: string): Promise<void> {
  const client = new CopilotClient();
  await client.start();

  const session = await client.createSession({
    model: "claude-sonnet-4.5",
    workingDirectory: process.cwd(),
    onPermissionRequest: async () => ({ kind: "approved" }),
  });

  try {
    // Phase 1: Plan
    await session.rpc.mode.set({ mode: "plan" });

    let planSummary = "";
    const planReady = new Promise<void>((resolve) => {
      session.on((event) => {
        if (event.type === "exit_plan_mode.requested") {
          planSummary = event.data.summary ?? "";
          resolve();
        }
      });
    });

    await session.send({ prompt: task });
    await planReady;

    // Read and display the plan
    const plan = await session.rpc.plan.read();
    console.log("=== PLAN ===");
    console.log(plan.content);
    console.log("Summary:", planSummary);

    // Phase 2: Execute (switch to autopilot)
    await session.rpc.mode.set({ mode: "autopilot" });

    // Wait for full execution
    await new Promise<void>((resolve) => {
      session.on((event) => {
        if (event.type === "session.idle") resolve();
      });
    });

    console.log("Execution complete");
  } finally {
    await session.destroy();
    await client.stop();
  }
}

await planAndExecute("Add input validation to all API endpoints");
```

## `exit_plan_mode.requested` Event

The event fires when the agent finishes planning and waits for approval.

```typescript
session.on((event) => {
  if (event.type === "exit_plan_mode.requested") {
    // event.data.summary: string | undefined
    // Human-readable summary of what the agent plans to do
    console.log(event.data.summary);
  }
});
```

The `summary` field is a brief description the agent generates. It is optional — always fall back to reading the plan file with `session.rpc.plan.read()` for the full content.

## When to Use Each Mode

| Mode | Use When |
|------|----------|
| `interactive` | Direct coding assistance, quick edits, exploratory conversations |
| `plan` | Large refactors, risky changes, when you need human sign-off on approach |
| `autopilot` | Unattended execution after plan approval, batch processing, CI pipelines |

Set plan mode by default for any task that touches more than 3 files or involves architectural decisions. Reserve autopilot for cases where you have reviewed the plan and trust the execution path.
