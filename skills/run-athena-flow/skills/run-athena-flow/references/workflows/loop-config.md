# Loop Configuration

Loops enable iterative workflow execution — the agent runs, reports progress, and Athena re-prompts it until the task is complete.

## How Loops Work

1. **First iteration** — Athena sends the `promptTemplate` to the agent
2. **Agent runs** — performs work, writes progress to the tracker file
3. **Completion check** — Athena reads the agent's output for `completionMarker` or `blockedMarker`
4. **Continue or stop** — If neither marker found and `maxIterations` not reached, send `continuePrompt`
5. **Next iteration** — Agent receives the continue prompt with tracker file path, picks up where it left off

## LoopConfig Schema

```json
{
  "loop": {
    "enabled": true,
    "completionMarker": "ATHENA_COMPLETE",
    "maxIterations": 10,
    "blockedMarker": "ATHENA_BLOCKED",
    "trackerPath": ".athena-tracker.json",
    "continuePrompt": "Continue from where you left off. Tracker: {trackerPath}"
  }
}
```

## Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `enabled` | boolean | Yes | — | Master switch for looping |
| `completionMarker` | string | Yes | — | Agent outputs this when done |
| `maxIterations` | number | Yes | — | Hard cap on iterations |
| `blockedMarker` | string | No | — | Agent outputs this when stuck |
| `trackerPath` | string | No | — | Relative path to state file |
| `continuePrompt` | string | No | — | Template for iterations 2+, `{trackerPath}` interpolated |

## Tracker Files

The tracker file persists state across loop iterations. The agent writes its progress to this file, and subsequent iterations read it to resume.

Example tracker file content:

```json
{
  "testsGenerated": ["homepage.spec.ts", "login.spec.ts"],
  "testsRemaining": ["checkout.spec.ts"],
  "failures": []
}
```

The `LoopManager` class manages the loop lifecycle:
1. Reads the tracker file at each iteration boundary
2. Checks agent output for completion/blocked markers
3. Decides whether to continue or stop
4. Builds the continue prompt with `{trackerPath}` interpolation

## Exit Conditions

The loop stops when ANY of these conditions is met:

1. **Completion marker** — Agent output contains `completionMarker` string
2. **Blocked marker** — Agent output contains `blockedMarker` string
3. **Max iterations** — `maxIterations` count reached
4. **Process error** — The agent process exits with an error

## Built-in Default Workflow

Athena includes a built-in workflow that uses a tracker system prompt. The agent is instructed to create/update a `task-tracker.md` with:

- Checkbox items for each sub-task
- Status updates as work progresses
- Completion markers when all work is done

## Cleanup

When a workflow run ends, `cleanupWorkflowRun()`:
- Removes the tracker file from the project directory
- Deactivates the loop state
- Records final iteration count in the session
