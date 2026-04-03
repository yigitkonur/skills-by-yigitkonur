---
name: build-openclaw-workflow
description: Use skill if you are building OpenClaw automation — Lobster typed workflows, cron scheduled jobs, LLM task chains, and browser automation.
---

# OpenClaw Automation Workflows

Build, schedule, and orchestrate automation workflows using OpenClaw's built-in tools and plugin-provided capabilities.

## Trigger boundary

Use this skill when:

- Building a Lobster workflow with typed steps, approvals, or resumable execution
- Setting up cron jobs to run on a schedule
- Chaining LLM tasks that produce structured JSON output
- Automating browser interactions via OpenClaw's built-in Chromium tool
- Managing the OpenClaw instance via gateway restarts or health checks
- Running shell commands through exec or managing background processes
- Combining multiple automation primitives into a larger pipeline

Do NOT use this skill when:

- Configuring OpenClaw settings, models, or providers (use `configure-openclaw`)
- Building an OpenClaw plugin from scratch (use `build-openclaw-plugin`)
- Building or authoring a Claude skill (use `build-openclaw-skill` or `build-skills`)
- Doing browser automation with `agent-browser` CLI or Playwright (use `run-agent-browser` or `run-playwright`)
- Performing research or web search without active browser control

## Non-negotiable rules

1. **Verify runtime and tool availability before using them.** `openclaw` must exist first. `lobster` and `llm-task` are optional plugin tools, and Lobster also requires the `lobster` CLI on the gateway host.
2. **Respect risk levels.** `exec` is VERY HIGH risk. `browser` is HIGH risk. Never use these without confirming the user understands the implications.
3. **Prefer structured output.** LLM Task forces JSON-only output. Lobster workflows produce typed results. Use these over freeform text whenever possible.
4. **Guard cron jobs.** Every cron job must have a clear disable path and should not run unbounded loops. Read `references/cron-scheduling.md` before creating any scheduled job.
5. **Test workflows incrementally.** Run each step individually before chaining them together.
6. **Use approvals for destructive actions.** Lobster supports resumable approval gates. Use them before any step that modifies external state, deletes data, or spends money.

## Runtime preflight

Before choosing a workflow primitive, verify the runtime boundary:

1. Confirm the runtime exists: `command -v openclaw`
2. Check health and loaded tools: `openclaw doctor` then `openclaw status --all`
3. Match the exact runtime names before choosing a branch:
   - plugin tools: `lobster`, `llm-task`
   - built-in tools: `cron`, `browser`, `canvas`, `gateway`
   - core tools: `exec`, `process`
4. If you choose Lobster, confirm the gateway host also has the Lobster CLI: `command -v lobster`
5. If a required tool or host dependency is missing, draft the workflow/config files only and state the exact blocker instead of claiming execution coverage

Success signal: the runtime is healthy, the chosen primitive is visible in status, and you can run a no-side-effect canary for that primitive. If you cannot run the canary, stop at file authoring and say why.

## Standard confirmation wording for risky tools

Before any side-effecting `exec`, `browser`, `gateway`, or `process` step, use an explicit confirmation message:

`About to run <tool> for <action>. Side effects: <effect>. Verification: <check>. Reply approve to continue.`

Do not replace this with vague warnings.

## Decision tree

```
What automation task are you building?
|
+-- Multi-step workflow with typed data flow
|   +-- Needs approval gates or resumable execution
|   |   \-- Lobster workflow -------- references/lobster-workflows.md
|   +-- Steps run sequentially, no approval needed
|   |   \-- Lobster workflow (simple) -- references/lobster-workflows.md
|   \-- Steps involve LLM reasoning
|       \-- LLM Task chain ---------- references/llm-task-chains.md
|
+-- Scheduled or recurring task
|   +-- Runs on a cron schedule
|   |   \-- cron tool --------------- references/cron-scheduling.md
|   +-- Needs to restart the OpenClaw instance
|   |   \-- gateway tool ------------ references/gateway-and-exec.md
|   \-- Needs background process management
|       \-- process tool ------------ references/gateway-and-exec.md
|
+-- Browser interaction
|   +-- Navigate, click, fill forms, screenshot in Chromium
|   |   \-- browser tool (built-in) - references/browser-automation.md
|   \-- Render visual output to canvas
|       \-- canvas tool ------------- references/browser-automation.md
|
+-- Shell command execution
|   +-- One-off command
|   |   \-- exec tool --------------- references/gateway-and-exec.md
|   +-- Long-running background process
|   |   \-- process tool ------------ references/gateway-and-exec.md
|   \-- Pipeline combining exec + LLM + cron
|       \-- Read all relevant references for the primitives involved
|
\-- Adjusting agent behavior
    +-- Change reasoning depth
    |   \-- Use `/think:<level>` or a primitive's `thinking` field
    \-- Prevent infinite tool loops
        \-- tool-loop detection (built-in)
```

## Tool quick reference

| Tool | Provider | Group | Risk | Purpose |
|---|---|---|---|---|
| `lobster` | Plugin | - | Medium | Typed workflow runtime with resumable approvals |
| `llm-task` | Plugin | - | Low | JSON-only LLM step for structured output |
| `cron` | Built-in | `group:automation` | Medium | Schedule and manage recurring jobs |
| `gateway` | Built-in | `group:automation` | Medium | Restart OpenClaw instance |
| `browser` | Built-in | `group:ui` | HIGH | Chromium automation (navigate, click, screenshot) |
| `canvas` | Built-in | `group:ui` | Low | Node-Canvas visual output |
| `exec` | Core | - | VERY HIGH | Run shell commands |
| `process` | Core | - | High | Manage background processes |

Reasoning depth is not a separate tool. Use `/think:<level>` for interactive turns and the documented `thinking` field on primitives that support it.

## Combining primitives

Most real automation involves multiple tools. Common combinations:

### Cron + Lobster: Scheduled multi-step workflow

Use cron to trigger a Lobster workflow on a schedule. The Lobster workflow handles the typed execution, approvals, and error recovery. Cron handles the timing.

Read `references/cron-scheduling.md` for the cron setup, then `references/lobster-workflows.md` for the workflow definition.

### LLM Task + Exec: AI-driven shell pipeline

Use LLM Task to analyze or generate structured data, then exec to act on it. The LLM Task produces JSON, which can be parsed and piped to shell commands.

Read `references/llm-task-chains.md` for LLM Task patterns, then `references/gateway-and-exec.md` for exec safety.

### Browser + LLM Task: Scrape and analyze

Use browser to navigate and extract page content, then LLM Task to analyze the extracted data into structured output.

Read `references/browser-automation.md` for extraction, then `references/llm-task-chains.md` for analysis.

### Lobster + Browser + LLM Task: Full automation pipeline

A Lobster workflow orchestrates the entire pipeline: browser steps extract data, LLM Task steps analyze it, exec steps act on the results, and approval gates protect destructive actions.

Read `references/lobster-workflows.md` first for the orchestration layer.

## Common pitfalls

| Pitfall | Fix |
|---|---|
| Using exec when a safer built-in tool exists | Check if cron, gateway, or process handles the need first |
| Creating cron jobs without a disable path | Always include how to list, disable, and delete the job |
| Skipping approval gates on destructive Lobster steps | Add explicit approval steps before delete, deploy, or payment actions |
| Assuming Lobster/LLM Task plugins are always present | Check tool availability at workflow start; fall back to exec + manual JSON if missing |
| Guessing whether a tool is loaded or misnaming it | Use `openclaw status --all` and the exact runtime names: `lobster`, `llm-task`, `cron`, `browser`, `gateway`, `exec`, `process` |
| Treating browser actions like CSS-selector commands | Take a fresh browser snapshot and act on refs, not selectors |
| Running browser automation without screenshots for verification | Capture screenshots after key actions to verify state |
| Unbounded loops in cron + exec combinations | Set max iterations, timeout, and failure thresholds |
| Passing secrets through exec command strings | Use environment variables or OpenClaw's secure config instead |

## Community skills for automation

These community skills provide specialized automation knowledge:

| Skill | Focus |
|---|---|
| `cron-mastery` / `cron-creator` | Deep cron expression knowledge |
| `cron-guardrails` / `safe-cron-runner` | Safety constraints for scheduled jobs |
| `lobsterguard` | Lobster workflow validation and safety |

Check if any of these are installed before building automation from scratch.

## Do this, not that

| Do this | Not that |
|---|---|
| Use Lobster for multi-step workflows with typed data | String together raw exec calls with pipes |
| Use LLM Task for structured AI reasoning steps | Parse freeform LLM text output with regex |
| Use cron for scheduled jobs with clear start/stop | Use exec + sleep loops for scheduling |
| Use gateway to restart OpenClaw cleanly | Kill the process with exec and hope it restarts |
| Use approval gates before destructive actions | Auto-execute destructive steps without confirmation |
| Verify tool availability before workflow start | Assume all plugins are loaded |
| Set timeouts and failure limits on all automation | Let automation run unbounded |

## Reference routing

| File | Read when |
|---|---|
| `references/lobster-workflows.md` | Building typed multi-step workflows, defining approval gates, handling workflow resumption, or structuring step-to-step data flow |
| `references/cron-scheduling.md` | Creating, listing, modifying, or deleting scheduled jobs, or combining cron with other tools |
| `references/llm-task-chains.md` | Using LLM Task for structured JSON output, chaining multiple LLM steps, or integrating LLM reasoning into a pipeline |
| `references/browser-automation.md` | Navigating pages, clicking elements, filling forms, taking screenshots, or rendering canvas output via OpenClaw's built-in browser tool |
| `references/gateway-and-exec.md` | Restarting the OpenClaw instance, running shell commands, managing background processes, or understanding risk levels and safety constraints |

## Minimal reading sets

### Scheduled data pipeline

- `references/cron-scheduling.md`
- `references/llm-task-chains.md`
- `references/gateway-and-exec.md`

### Interactive web automation

- `references/browser-automation.md`
- `references/lobster-workflows.md`

### Full orchestration

- `references/lobster-workflows.md`
- `references/llm-task-chains.md`
- `references/cron-scheduling.md`
- `references/gateway-and-exec.md`

## Guardrails

- Do NOT create cron jobs without confirming the user understands they will run automatically
- Do NOT use exec for tasks that have a dedicated built-in tool
- Do NOT skip approval gates on Lobster steps that modify external systems
- Do NOT assume Lobster or LLM Task plugins are loaded without checking
- Do NOT run browser automation on authenticated sessions without the user's explicit consent
- Do NOT chain more than 5 exec calls without an intermediate verification step
- Do NOT store secrets in cron job definitions, exec arguments, or workflow step data
- Always capture evidence (screenshots, logs, output) at each verification point
