# Cron Scheduling Guide

The `cron` tool is a built-in OpenClaw tool in the `group:automation` group. It manages scheduled jobs that run automatically at specified intervals.

## Core operations

| Operation | Description |
|---|---|
| Create | Define a new cron job with a schedule and action |
| List | View all active cron jobs |
| Disable | Temporarily stop a cron job without deleting it |
| Enable | Re-activate a disabled cron job |
| Delete | Permanently remove a cron job |
| View | Inspect a specific cron job's configuration and history |

## Cron expression format

Standard cron expressions use 5 fields:

```
*  *  *  *  *
|  |  |  |  |
|  |  |  |  +-- Day of week (0-7, 0 and 7 = Sunday)
|  |  |  +----- Month (1-12)
|  |  +-------- Day of month (1-31)
|  +----------- Hour (0-23)
+-------------- Minute (0-59)
```

### Common schedules

| Schedule | Expression | Description |
|---|---|---|
| Every minute | `* * * * *` | Use sparingly -- high resource usage |
| Every 5 minutes | `*/5 * * * *` | Good for frequent checks |
| Every hour | `0 * * * *` | At the top of each hour |
| Every day at midnight | `0 0 * * *` | Daily maintenance tasks |
| Every Monday at 9am | `0 9 * * 1` | Weekly reports |
| First of month at noon | `0 12 1 * *` | Monthly summaries |
| Weekdays at 8am | `0 8 * * 1-5` | Business-hour automation |

## Safety rules for cron jobs

### Before creating any cron job

1. **Confirm the user wants automated execution.** Never create a cron job without explicit consent.
2. **Define the disable path.** Tell the user exactly how to stop the job.
3. **Set reasonable frequency.** Do not create jobs that run every minute unless there is a clear justification.
4. **Define failure behavior.** What happens when the job fails? Does it retry? Alert? Stop?
5. **Check for existing jobs.** List current cron jobs to avoid duplicates or conflicts.

### Mandatory safety constraints

- Every cron job MUST have a corresponding disable/delete instruction provided to the user
- Jobs that call exec MUST have timeout limits
- Jobs that call external APIs MUST have rate limiting awareness
- Jobs that modify data MUST log what they changed
- Jobs MUST NOT run unbounded loops (set max iterations)
- Jobs MUST NOT contain secrets in their definition (use environment variables)

## Creating a cron job

### Step-by-step

1. List existing jobs to check for conflicts
2. Define the schedule expression
3. Define the action (what the job does)
4. Set failure and timeout behavior
5. Create the job
6. Verify it appears in the job list
7. Provide the user with disable/delete instructions

### Action types

Cron jobs can trigger various actions:

| Action type | When to use | Safety |
|---|---|---|
| Exec command | Shell operations, scripts | VERY HIGH risk -- validate thoroughly |
| Lobster workflow start | Multi-step typed processes | Medium risk -- Lobster handles safety |
| LLM Task | AI analysis on schedule | Low risk -- produces JSON only |
| Gateway restart | Scheduled instance refresh | Medium risk -- causes downtime |

## Managing existing jobs

### Listing jobs

Always list existing jobs before creating new ones. Check for:

- Duplicate schedules doing similar work
- Jobs that may conflict with the new one
- Disabled jobs that should be cleaned up

### Modifying jobs

To change a cron job's schedule or action:

1. Note the current configuration
2. Delete the existing job
3. Create a new job with the updated configuration
4. Verify the new job is active

There is no in-place edit -- always delete and recreate.

### Monitoring job health

Check job execution history to identify:

- Jobs that consistently fail (investigate root cause)
- Jobs that take longer than expected (add timeouts)
- Jobs that overlap with the next scheduled run (increase interval)
- Jobs producing unexpected output (review the action logic)

## Combining cron with other tools

### Cron + Lobster

Use cron to trigger a Lobster workflow on a schedule. The cron job starts the workflow; Lobster manages the multi-step execution.

**Warning:** If the Lobster workflow includes approval gates, the cron-triggered instance will pause at the gate and wait for human approval. Design cron-triggered workflows to either skip approval (for trusted automated actions) or alert the human that approval is needed.

### Cron + exec

Use cron to run shell commands on a schedule.

**Warning:** This is the highest-risk combination. The exec command runs with the OpenClaw instance's permissions. Always:

- Use absolute paths
- Set timeout limits
- Redirect output to logs
- Handle errors explicitly
- Never include secrets in the command string

### Cron + LLM Task

Use cron to trigger LLM analysis on a schedule. Good for periodic report generation, data summarization, or anomaly detection.

**Pattern:** Cron triggers the LLM Task, which produces structured JSON output. A subsequent exec step can act on the results (send email, write file, call API).

## Community skills

Check if these are available for specialized cron guidance:

| Skill | Focus |
|---|---|
| `cron-mastery` | Advanced cron expression patterns |
| `cron-creator` | Interactive cron expression builder |
| `cron-guardrails` | Safety validation for cron jobs |
| `safe-cron-runner` | Sandboxed cron execution |

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Job does not run | Wrong cron expression | Verify expression with a cron expression tester |
| Job runs too often | Wildcard in wrong position | Review all 5 fields of the expression |
| Job fails silently | No error handling in action | Add explicit error capture and logging |
| Job conflicts with another | Overlapping schedules | List all jobs, stagger schedules |
| Job runs but produces no output | Action succeeds but output is not captured | Redirect stdout/stderr to a log |
| Cannot find a job to delete | Job was already deleted or name changed | List all jobs to verify current state |
