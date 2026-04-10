# Workflow Engine Architecture

The workflow engine manages the lifecycle of workflow-driven agent sessions.

## Core Types

### WorkflowConfig

```typescript
type WorkflowConfig = {
  name: string;
  description?: string;
  version?: string;
  plugins: PluginSpec[];
  promptTemplate: string;
  loop?: LoopConfig;
  isolation?: string;
  model?: string;
  env?: Record<string, string>;
  systemPromptFile?: string;
  examplePrompts?: string[];
};
```

### LoopConfig

```typescript
type LoopConfig = {
  enabled: boolean;
  completionMarker: string;
  maxIterations: number;
  blockedMarker?: string;
  trackerPath?: string;
  continuePrompt?: string;
};
```

### PluginSpec

```typescript
type PluginSpec = string | { ref: string; version: string };
```

## Execution Flow

### 1. Workflow Compilation (`plan.ts`)

`WorkflowPlan` compilation:
1. Load workflow config from registry
2. Resolve all `PluginSpec` entries to local directories
3. Deduplicate plugins across workflow, config, and CLI sources
4. Build `WorkflowPlan` with resolved plugin paths

### 2. Session Lifecycle (`sessionPlan.ts`)

`WorkflowRunState` lifecycle stages:

1. **Create** — `createWorkflowRunState()` builds initial state with LoopManager
2. **Prepare Turn** — `prepareWorkflowTurn()` builds the prompt:
   - First iteration: uses `promptTemplate` with `{input}` substitution
   - Subsequent iterations: uses `continuePrompt` with `{trackerPath}` interpolation
3. **Execute** — Turn runs via the harness (Claude or Codex process)
4. **Check** — `shouldContinueWorkflowRun()` evaluates loop conditions
5. **Cleanup** — `cleanupWorkflowRun()` removes tracker file, deactivates loop

### 3. Loop Management (`loopManager.ts`)

The `LoopManager` class:

```
iteration 1: promptTemplate → agent runs → check tracker for markers
iteration 2: continuePrompt → agent runs → check tracker for markers
...
iteration N: stop (completion marker, blocked marker, or max iterations)
```

Operations:
- `readTracker()` — Reads tracker file content
- `checkCompletion()` — Scans agent output for completion/blocked markers
- `buildContinuePrompt()` — Interpolates `{trackerPath}` into continue prompt
- `incrementIteration()` — Advances iteration counter
- `shouldContinue()` — Returns true if loop should proceed

### 4. Prompt Application (`applyWorkflow.ts`)

Template substitution:
- `{input}` in `promptTemplate` is replaced with the user's prompt
- `{trackerPath}` in `continuePrompt` is replaced with the tracker file path

## Workflow Registry (`registry.ts`)

CRUD operations on `~/.config/athena/workflows/`:

| Operation | Method |
|-----------|--------|
| List | Read all workflow.json files in registry |
| Get | Read specific workflow by name |
| Install | Copy workflow.json to registry with source.json |
| Remove | Delete workflow directory |
| Upgrade | Re-fetch from marketplace and overwrite |

## Plugin Resolution (`installer.ts`)

Resolves `PluginSpec` entries to local directories:

1. **Local path** — Use directly
2. **Marketplace ref** (`name@owner/repo`) — Clone/update marketplace repo, resolve via manifest
3. **Versioned ref** — Try npm (`@athenaflow/plugin-<name>@version`), fall back to marketplace

Resolved paths are cached at:
- Marketplace repos: `~/.config/athena/marketplaces/<owner>/<repo>/`
- npm packages: `~/.config/athena/plugin-packages/`

## Workflow Discovery

Plugins can contain a `workflow.json` at their root. Athena auto-discovers these:

- If exactly one workflow discovered and no `--workflow` flag → auto-activate
- If multiple workflows discovered → require explicit `--workflow` selection

## Built-in Default Workflow

Located at `src/core/workflows/builtins/`:
- General-purpose long-horizon task workflow
- Uses tracker file system prompt
- Agent maintains `task-tracker.md` with checkboxes and completion markers

## React Hook Integration

`useWorkflowSessionController.ts` wraps the HarnessProcess with loop logic:
1. Starts the first turn with the prompt template
2. After each turn, checks loop conditions
3. If continuing, sends the continue prompt
4. On completion, cleans up and reports results
