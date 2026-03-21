# Lobster Workflow Patterns

Lobster is a typed workflow runtime provided as an OpenClaw plugin. It enables multi-step processes with structured execution, resumable approvals, and typed data flow between steps.

## Core concepts

| Concept | Description |
|---|---|
| Workflow | A named sequence of typed steps that execute in order |
| Step | A single unit of work with typed input and output |
| Approval gate | A step that pauses execution until a human approves or rejects |
| Resume | Continuing a paused workflow from where it left off |
| Typed data flow | Each step receives the previous step's output as typed input |

## When to use Lobster

Use Lobster when:

- The task has 3+ steps that must execute in a defined order
- Steps produce structured data that feeds into subsequent steps
- Destructive or expensive actions need human approval before proceeding
- The workflow may need to be paused, inspected, and resumed later
- You need an audit trail of what happened at each step

Do NOT use Lobster when:

- A single exec call or LLM Task accomplishes the goal
- The task is a one-off command with no data flow between steps
- The workflow is purely browser automation (use the browser tool directly, orchestrated by Lobster only if multiple non-browser steps are involved)

## Workflow structure

A Lobster workflow is defined with steps, each specifying:

1. **Name** -- a descriptive identifier for the step
2. **Action** -- what the step does (exec, llm_task, browser action, or custom logic)
3. **Input type** -- the shape of data this step expects
4. **Output type** -- the shape of data this step produces
5. **Approval** -- whether to pause for human approval before executing

### Simple sequential workflow

```
Workflow: daily-report
  Step 1: gather-data
    Action: exec (query database)
    Output: { rows: [...], count: number }

  Step 2: analyze-data
    Action: llm_task (summarize findings)
    Input: { rows: [...], count: number }
    Output: { summary: string, highlights: string[] }

  Step 3: send-report
    Action: exec (send email)
    Input: { summary: string, highlights: string[] }
    Approval: required (before sending)
    Output: { sent: boolean, recipient: string }
```

### Workflow with approval gates

Place approval gates before any step that:

- Sends data externally (emails, API calls, webhooks)
- Modifies production data (database writes, file deletions)
- Spends money (API calls with cost, deployments)
- Is irreversible (publishing, notifications to users)

When a workflow reaches an approval gate:

1. Execution pauses
2. The pending step and its input data are displayed
3. A human reviews and approves or rejects
4. On approval, execution continues from that step
5. On rejection, the workflow terminates with a rejection record

### Workflow with branching

Lobster steps can include conditional logic based on previous step output:

```
Workflow: deploy-pipeline
  Step 1: run-tests
    Output: { passed: boolean, failures: string[] }

  Step 2 (if passed): build-artifact
    Output: { artifact_url: string }

  Step 2 (if not passed): notify-failure
    Output: { notified: boolean }

  Step 3 (after build): deploy
    Approval: required
    Output: { deployment_id: string }
```

## Data flow patterns

### Passing data between steps

Each step's output becomes the next step's input. Keep data structures flat and focused:

- Prefer `{ count: 42, items: ["a","b"] }` over deeply nested objects
- Include only data the next step needs, not the full context
- Use descriptive field names that make the data self-documenting

### Accumulating context

When later steps need data from non-adjacent earlier steps, aggregate into a context object:

```
Step 1 output: { urls: [...] }
Step 2 input: { urls: [...] }
Step 2 output: { urls: [...], content: [...] }  // carries forward urls
Step 3 input: { urls: [...], content: [...] }   // has access to both
```

### Error data flow

When a step fails, its output should include error information that helps the next step (or the human reviewer) understand what went wrong:

```
Output on success: { status: "ok", data: {...} }
Output on failure: { status: "error", error: "Connection refused", retryable: true }
```

## Combining Lobster with other tools

### Lobster + cron

Use cron to trigger a Lobster workflow on a schedule. The cron job starts the workflow; Lobster handles the typed execution.

**Pattern:** cron triggers workflow start, Lobster manages steps internally. Do not use cron to trigger individual steps -- let Lobster handle sequencing.

### Lobster + LLM Task

Use LLM Task as the action within a Lobster step when you need AI reasoning with structured JSON output.

**Pattern:** The Lobster step defines the input/output types. The LLM Task within that step receives the input and must produce output matching the expected type.

### Lobster + exec

Use exec as the action within a Lobster step for shell commands.

**Pattern:** The Lobster step wraps the exec call, captures stdout/stderr, and structures the output. This is safer than raw exec because Lobster provides the audit trail and can enforce approval gates.

### Lobster + browser

Use browser actions within Lobster steps for web automation that is part of a larger workflow.

**Pattern:** Each browser interaction (navigate, extract, screenshot) is one Lobster step. This gives you typed data between browser actions and approval gates before sensitive browser operations.

## Debugging workflows

When a workflow fails or produces unexpected results:

1. **Check step outputs** -- review the typed output from each completed step
2. **Check the failing step's input** -- ensure the previous step produced the expected data shape
3. **Check approval state** -- a workflow may be paused at an approval gate, not failed
4. **Run the failing step in isolation** -- test the step's action independently with the same input
5. **Check plugin availability** -- Lobster is plugin-provided; verify it is loaded

## Safety considerations

- Always use approval gates before destructive or irreversible actions
- Log workflow execution for audit purposes
- Set timeouts on individual steps to prevent hanging
- Handle step failures gracefully -- a workflow should not leave external systems in an inconsistent state
- When a workflow is rejected at an approval gate, clean up any resources created by earlier steps
