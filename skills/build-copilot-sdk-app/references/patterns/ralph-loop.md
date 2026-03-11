# Ralph Loop: Autonomous Development Pattern

## What Is a Ralph Loop

A Ralph loop is an autonomous development workflow where each iteration runs in a fresh session context. State lives on disk (files), not in the model's context window. Each iteration: reads current state from disk, picks and implements one task, validates against backpressure (tests, builds, lints), commits, and exits. The next iteration starts with a clean context.

Core insight: **context accumulation causes hallucination drift**. By destroying the session after each iteration and creating a new one, the agent always operates in the high-quality zone of its context window, never in the degraded-performance tail end.

Reference implementation: `/Users/yigitkonur/dev/copilot-sdk/cookbook/copilot-sdk/nodejs/recipe/ralph-loop.ts`

## Minimal Implementation

```typescript
import { readFile } from "fs/promises";
import { CopilotClient } from "@github/copilot-sdk";

async function ralphLoop(promptFile: string, maxIterations = 50): Promise<void> {
  const client = new CopilotClient();
  await client.start();

  try {
    const prompt = await readFile(promptFile, "utf-8");

    for (let i = 1; i <= maxIterations; i++) {
      console.log(`\n=== Iteration ${i}/${maxIterations} ===`);

      // Fresh session — context isolation is the point
      const session = await client.createSession({
        model: "gpt-5.1-codex-mini",
      });

      try {
        // 10-minute timeout per iteration
        await session.sendAndWait({ prompt }, 600_000);
      } finally {
        // Disconnect — releases in-memory resources, preserves disk state.
        // Since Ralph loops create fresh sessions each iteration,
        // disk state from prior iterations is not reused.
        await session.disconnect();
      }

      console.log(`Iteration ${i} complete.`);
    }
  } finally {
    await client.stop();
  }
}

ralphLoop("PROMPT.md", 20);
```

Use `session.disconnect()` to release in-memory resources after each iteration. Each iteration creates a fresh session, so prior session state is not needed.

## Full Implementation with Plan/Build Modes

```typescript
import { readFile } from "fs/promises";
import { CopilotClient } from "@github/copilot-sdk";

type Mode = "plan" | "build";

async function ralphLoop(mode: Mode, maxIterations: number): Promise<void> {
  const promptFile = mode === "plan" ? "PROMPT_plan.md" : "PROMPT_build.md";

  const client = new CopilotClient();
  await client.start();

  console.log(`Mode: ${mode} | Prompt: ${promptFile} | Max: ${maxIterations}`);

  try {
    const prompt = await readFile(promptFile, "utf-8");

    for (let i = 1; i <= maxIterations; i++) {
      console.log(`\n=== Iteration ${i}/${maxIterations} ===`);

      const session = await client.createSession({
        model: "gpt-5.1-codex-mini",
        workingDirectory: process.cwd(),        // Pin to project root
        onPermissionRequest: async () => ({ kind: "approved" }), // Auto-approve
      });

      // Log tool usage for observability
      session.on((event) => {
        if (event.type === "tool.execution_start") {
          console.log(`  Tool: ${event.data.toolName}`);
        }
      });

      try {
        await session.sendAndWait({ prompt }, 600_000);
      } finally {
        await session.disconnect();
      }

      console.log(`Iteration ${i} complete.`);
    }

    console.log(`\nReached max iterations: ${maxIterations}`);
  } finally {
    await client.stop();
  }
}

// CLI: npx tsx ralph-loop.ts [plan] [max_iterations]
const args = process.argv.slice(2);
const mode: Mode = args.includes("plan") ? "plan" : "build";
const maxArg = args.find((a) => /^\d+$/.test(a));
const maxIterations = maxArg ? parseInt(maxArg) : 50;

ralphLoop(mode, maxIterations).catch(console.error);
```

## Required Project File Structure

```
project-root/
├── PROMPT_plan.md         # Instructions for planning mode
├── PROMPT_build.md        # Instructions for building mode
├── AGENTS.md              # Build/test commands (keep under 60 lines)
├── IMPLEMENTATION_PLAN.md # Shared state: task list (updated each iteration)
├── specs/                 # Requirement specs
│   ├── feature-auth.md
│   └── feature-payments.md
└── src/                   # Source code
```

`IMPLEMENTATION_PLAN.md` is the coordination mechanism between iterations. Planning mode creates/updates it. Build mode reads it, picks one task, implements it, updates it, and commits.

## PROMPT_plan.md Template

```markdown
0a. Study `specs/*` to learn the application specifications.
0b. Study IMPLEMENTATION_PLAN.md (if present) to understand the plan so far.
0c. Study `src/` to understand existing code and shared utilities.

1. Compare specs against code (gap analysis). Create or update
   IMPLEMENTATION_PLAN.md as a prioritized bullet-point list of tasks
   yet to be implemented. Do NOT implement anything.

IMPORTANT: Do NOT assume functionality is missing — search the
codebase first to confirm. Prefer updating existing utilities over
creating new copies.
```

## PROMPT_build.md Template

```markdown
0a. Study `specs/*` to learn the application specifications.
0b. Study IMPLEMENTATION_PLAN.md.
0c. Study `src/` for context.

1. Choose the highest-priority incomplete item from IMPLEMENTATION_PLAN.md.
2. Before making changes, search the codebase — don't assume it isn't there.
3. Implement completely. No placeholders or stubs.
4. Run tests (`npm test`). If tests fail, fix them before committing.
5. When tests pass, update IMPLEMENTATION_PLAN.md to mark the item done.
6. Run `git add -A && git commit -m "descriptive message"`.
7. Exit after one task. Future iterations will pick the next task.

Keep IMPLEMENTATION_PLAN.md current — every future iteration depends on it.
```

## Why Fresh Context Prevents Hallucination Drift

LLMs degrade in quality as context fills. Long sessions accumulate tool outputs, intermediate reasoning, error messages, and redundant observations. The model starts hallucinating patterns from earlier in the context, loses track of the current state, and makes mistakes it would not make fresh.

The Ralph loop solves this structurally: each iteration starts with a small, focused prompt and a clean context. The agent reads the current state of the codebase and plan directly from disk, so it always has accurate ground truth. There is no "memory" of prior iterations to corrupt the current one.

## Iteration State Tracking

Track progress externally, not in the session. Use the file system:

```typescript
import { readFile, writeFile } from "fs/promises";

interface LoopState {
  iteration: number;
  completedTasks: string[];
  lastError?: string;
  startedAt: string;
}

async function saveLoopState(state: LoopState): Promise<void> {
  await writeFile(".ralph-state.json", JSON.stringify(state, null, 2));
}

async function loadLoopState(): Promise<LoopState | null> {
  try {
    const raw = await readFile(".ralph-state.json", "utf-8");
    return JSON.parse(raw);
  } catch {
    return null;
  }
}
```

## Error Recovery Between Iterations

Wrap each iteration in try/catch. Log the error, continue to the next iteration. Do not abort the loop on a single iteration failure — the agent may have partially completed work that the next iteration can build on.

```typescript
for (let i = 1; i <= maxIterations; i++) {
  const session = await client.createSession({
    model: "gpt-5.1-codex-mini",
    workingDirectory: process.cwd(),
    onPermissionRequest: async () => ({ kind: "approved" }),
  });

  try {
    await session.sendAndWait({ prompt }, 600_000);
  } catch (err) {
    console.error(`Iteration ${i} failed:`, err);
    // Log but continue — next iteration starts fresh
  } finally {
    // Always disconnect, even on error
    await session.disconnect().catch(() => {});
  }
}
```

## When to Use Ralph Loop vs. Persistent Sessions

| Use Ralph Loop | Use Persistent Session |
|---|---|
| Implementing many tasks from a spec | Interactive coding assistance |
| Large refactors split into small tasks | Multi-turn conversations requiring memory |
| Unattended overnight development runs | Exploratory prototyping |
| Clear backpressure (tests/CI) to validate work | When you need session history |
| Risk of context drift over many steps | Short-duration tasks (under 30 min) |

Never use Ralph loops for one-shot operations — the overhead of create/destroy is unnecessary. Never use persistent sessions for long autonomous runs — context drift will degrade quality.

## Settings

- `workingDirectory`: Always set to `process.cwd()` or your project root. Without it, the agent's file operations resolve relative to the CLI's working directory, not your project.
- `onPermissionRequest`: Use `async () => ({ kind: "approved" })` for unattended operation. Never use this in interactive contexts.
- Timeout on `sendAndWait`: Set to 600_000 (10 minutes) or longer for complex builds. The default may be too short for tasks with many tool calls.
- Model: `gpt-5.1-codex-mini` is the canonical choice for build tasks — strong coding performance, efficient for repeated use.
