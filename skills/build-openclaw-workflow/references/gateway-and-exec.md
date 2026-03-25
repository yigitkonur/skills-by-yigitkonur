# Gateway, Exec, and Process Management

This reference covers three related tools for system-level operations in OpenClaw: the `gateway` tool for instance management, the `exec` tool for shell command execution, and the `process` tool for background process management.

## Tool overview

| Tool | Provider | Group | Risk | Purpose |
|---|---|---|---|---|
| `gateway` | Built-in | `group:automation` | Medium | Restart the OpenClaw instance |
| `exec` | Core | - | VERY HIGH | Execute shell commands |
| `process` | Core | - | High | Manage background processes |

## Gateway tool

### Purpose

The gateway tool restarts the OpenClaw instance. Use it for:

- Applying changes that do not hot-apply and truly require a restart
- Recovering from a corrupted state
- Refreshing the runtime environment
- Scheduled maintenance restarts (via cron)

### When to use

- After plugin installation or removal
- After environment variable changes that require a restart
- When the instance is in an unhealthy state
- As part of a scheduled maintenance workflow

### Safety

- **Causes downtime.** The instance will be unavailable during restart.
- **Interrupts running workflows.** Any in-progress Lobster workflows, cron jobs, or browser sessions will be terminated.
- **Always warn the user** before triggering a gateway restart.
- **Never automate gateway restarts without explicit approval.** Even in a cron job, an approval gate or confirmation mechanism should exist.

### Pattern: Graceful restart

```
1. Check for running workflows or jobs
2. Warn user about potential interruption
3. Wait for approval
4. Trigger gateway restart
5. Wait for instance to come back online
6. Verify instance health
```

### Confirmation template for risky operations

Use this wording before gateway, exec, browser, or process actions with side effects:

`About to run <tool> for <action>. Side effects: <effect>. Verification: <check>. Reply approve to continue.`

Examples:

- `About to run gateway for a runtime restart. Side effects: active sessions and workflows will be interrupted. Verification: openclaw status returns healthy. Reply approve to continue.`
- `About to run exec for a package install. Side effects: filesystem and dependency changes. Verification: the install command exits 0 and the build passes. Reply approve to continue.`
- `About to run browser against an authenticated session. Side effects: the site may perform real account actions. Verification: screenshot after each critical step. Reply approve to continue.`

## Exec tool

### Purpose

The exec tool runs arbitrary shell commands on the system where OpenClaw is hosted.

### Risk level: VERY HIGH

The exec tool has the highest risk level in OpenClaw because it:

- Runs commands with the OpenClaw process's permissions
- Can read, write, and delete any file the process can access
- Can make network calls
- Can install software
- Can modify system configuration
- Can execute arbitrary code

### Mandatory safety rules

1. **Never use exec when a built-in tool exists.** Check if cron, gateway, browser, or another tool handles the need.
2. **Never include secrets in exec command strings.** Use environment variables.
3. **Always set timeout limits.** Long-running exec commands should have explicit timeouts.
4. **Validate all input before passing to exec.** User-provided data in exec strings is a command injection vector.
5. **Use absolute paths.** Relative paths can break depending on the working directory.
6. **Capture and log output.** Always redirect stdout and stderr for debugging.
7. **Never run exec in an unbounded loop.** Set maximum iteration counts.
8. **Ask for user confirmation** before running exec commands that modify the filesystem, install software, or make network calls.

### Execution boundary

OpenClaw exec is not automatically a host shell. Be explicit about where the command runs:

| Setting | Meaning |
|---|---|
| `host: "sandbox"` | Default. Use this whenever the task can stay inside the sandbox. |
| `host: "gateway"` | Run on the gateway host. Requires approval and policy alignment. |
| `host: "node"` | Run on a paired node host. Requires a configured node target. |
| `security: "deny" \| "allowlist" \| "full"` | Controls what host execution is permitted to do. |
| `ask: "off" \| "on-miss" \| "always"` | Controls approval prompting for host execution. |

Prefer sandbox execution first. Only move to `gateway` or `node` when the workflow truly needs host access and the user has approved that risk.

### Safe exec patterns

#### Read-only operations (lower risk)

```
exec: list directory contents
exec: read file contents
exec: check disk usage
exec: query system information
exec: run diagnostic commands
```

#### Write operations (higher risk, require confirmation)

```
exec: write to file (confirm path and content)
exec: create directory (confirm location)
exec: install package (confirm package name and source)
exec: run build command (confirm build tool and target)
```

#### Dangerous operations (require explicit approval)

```
exec: delete files (always confirm, never delete recursively without review)
exec: modify system configuration
exec: start network services
exec: run arbitrary scripts
exec: modify permissions
```

### Input sanitization

When constructing exec commands from dynamic data (e.g., output from a previous LLM Task step):

- Escape shell metacharacters
- Validate data types and lengths
- Use parameterized commands where possible
- Never interpolate untrusted strings directly into shell commands

## Process tool

### Purpose

The process tool manages background processes -- long-running tasks that continue executing while the agent does other work.

### When to use

- Running a development server in the background
- Starting a file watcher
- Running a long build process
- Managing daemon processes

### Operations

| Operation | Description |
|---|---|
| Start | Launch a new background process |
| List | View all running background processes |
| Stop | Terminate a specific background process |
| Status | Check if a process is still running |
| Output | Read stdout/stderr from a background process |

### Safety rules

1. **Track every process you start.** Maintain awareness of running processes.
2. **Clean up processes when done.** Stop background processes that are no longer needed.
3. **Set resource limits.** Background processes should not consume unbounded CPU or memory.
4. **Monitor output.** Check background process output periodically for errors.
5. **Never start processes that listen on network ports** without explicit user approval.

### Pattern: Managed background process

```
1. Start the process
2. Verify it is running (check status)
3. Do other work
4. Periodically check output for errors
5. Stop the process when the task is complete
6. Verify it has stopped
```

## Combining tools

### Gateway + cron: Scheduled restarts

Use cron to schedule periodic gateway restarts for maintenance:

**Warning:** This combination interrupts running workflows. Only use when:
- No critical workflows run at the scheduled time
- The restart window is documented and communicated
- Users can disable the scheduled restart if needed

### Exec + process: Build and run

Use exec for one-off build commands, then process to run the result:

```
Step 1 (exec): Build the project
Step 2 (process): Start the built application in background
Step 3: Verify the application is running
```

### Exec + LLM Task: Analyze system state

Use exec to gather system information, then LLM Task to analyze it:

```
Step 1 (exec): Run diagnostic commands
Step 2 (LLM Task): Analyze output, classify issues
Step 3 (exec or notification): Act on findings
```

## Thinking control

There is no separate `thinking_level` tool in this workflow. Use the OpenClaw thinking controls that match the primitive:

| Level | When to use |
|---|---|
| `/think:low` or `thinking: "low"` | Simple exec commands, straightforward cron jobs, routine process management |
| `/think:medium` or `thinking: "medium"` | Multi-step workflow planning, structured analysis, bounded troubleshooting |
| `/think:high` | Complex pipeline design, debugging failures with several moving parts |

Set the level before the run you care about. For interactive turns, use `/think:<level>`. For primitives such as cron payloads or `llm-task`, use their documented `thinking` field.

## Tool-loop detection

OpenClaw includes built-in tool-loop detection that prevents infinite tool-calling cycles. This is relevant when:

- An exec command's output triggers another exec call
- A cron job restarts itself
- A Lobster workflow step calls another workflow

If the loop detector fires, it means the automation has a cycle. Fix the cycle in the workflow design rather than trying to bypass detection.

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Exec command fails silently | No error capture | Redirect stderr, check exit code |
| Process starts but immediately stops | Startup error | Check process output for error messages |
| Gateway restart hangs | Instance cannot restart cleanly | Check for blocking processes, try stopping them first |
| Exec + cron runs but produces no result | Output not captured or wrong working directory | Use absolute paths, redirect output to a log file |
| Process consumes excessive resources | No resource limits set | Add memory and CPU limits, or use timeout |
| Exec command has different behavior in cron | Different environment in cron context | Set full PATH and environment variables in the cron action |
