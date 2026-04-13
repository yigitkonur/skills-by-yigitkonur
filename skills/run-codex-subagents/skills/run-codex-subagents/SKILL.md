---
name: run-codex-subagents
description: Use skill if you are orchestrating Codex coding agents with the cli-codex-subagent CLI and need to start file-backed tasks, follow live runs, answer blocked requests, reuse sessions, materialize prompt bundles for handoff, or coordinate multi-wave coding work. Do NOT use for MCP server setup, mcpc testing, or general Codex documentation.
---

# Orchestrate Codex Tasks with cli-codex-subagent

Use this skill when you are delegating coding, research, verification, or follow-up work to Codex workers through the `cli-codex-subagent` shell interface.

This is a CLI skill, not an MCP skill. Use CLI commands, local artifact paths, and shell-native control flow.

## Trigger Boundaries

Use this skill for:
- launching Codex work from Markdown prompt files
- monitoring async Codex runs with `task follow` or `task wait`
- handling blocked runtime requests with `request list`, `request read`, and `request answer`
- reusing sessions, steering finished tasks, and coordinating multi-wave task batches
- materializing prompt bundles or handoff manifests for another coding agent
- recovering failed runs from `task read`, `task events`, timeline logs, stderr logs, and `doctor`

Do not use this skill for:
- MCP server setup, `mcpc` validation, or resource/tool schema testing
- changing `cli-codex-subagent` source code itself unless the user explicitly wants CLI development
- general Codex/OpenAI documentation questions
- built-in Codex `spawn_agent` delegation that does not involve this CLI

## Prerequisites

Before dispatching work:

1. Verify the CLI path you will use:
   - Preferred: `cli-codex-subagent --help`
   - Local-dev fallback: `node --import tsx src/cli.ts --help`
2. If neither command works, stop and tell the user the CLI is unavailable.
3. Assume prompts are file-backed. If the user gave inline instructions only, write or request a task file before dispatching.

## Non-Negotiable Operating Rules

1. File-backed prompts only. Start work from `task.md`, `followup.md`, or another Markdown file. Do not invent inline prompt text when the CLI expects files.
2. Inspect before dispatch when context is complex. Use `prompt inspect` or `prompt lint` before `run` or `task start` if prompt resolution, `AGENTS.md`, or context files matter.
3. Choose execution mode deliberately. Default async mode returns quickly; `--wait` blocks without streaming; `--follow` blocks and streams events.
4. Treat `waiting_request` as blocked, not failed. When a task pauses, switch immediately to the `request` command family.
5. Reuse sessions intentionally. Use a session only when the same workspace, runtime context, and follow-up thread continuity are useful.
6. Prefer machine-readable output for automation. Use `--json`, `--stream-json`, `--field`, and `--quiet` instead of parsing prose.
7. Recover before retrying. A failed task may already have useful files or a good rendered prompt. Read the artifacts first.
8. Handoff through files, not memory. Use `prompt inspect --write-bundle` or `task read --field artifacts.handoffManifestPath` when another agent should take over.

## Default Loop

### 1. Shape the task input

- Write the task as a Markdown file.
- If the task depends on repo instructions or supporting notes, pass them with `--context-file` or `--base-instructions-file`.
- If you need to verify the fully resolved prompt first, run `prompt inspect`.

### 2. Start the right command

- Use `run <taskFile>` for the common one-shot path.
- Use `task start <taskFile>` when you want the explicit task noun.
- Use `task start --session <sessionId>` when continuing a prepared session.
- Use `task steer <taskId> <messageFile>` only after the earlier task has completed, failed, or been interrupted.

### 3. Monitor the task

- Default async start: capture `task_id`, `session_id`, and `actions`.
- Live view: `task follow <taskId>`
- Blocking no-stream wait: `task wait <taskId>`
- Quick artifact read: `task read <taskId>`

### 4. Unblock requests

If the task status becomes `waiting_request` or the command exits `2`:

1. `cli-codex-subagent request list --status pending --json`
2. `cli-codex-subagent request read <requestId> --json`
3. Answer with `request answer --choice`, `--decision`, `--text-file`, `--custom-file`, or `--json-file`
4. Resume with `task follow` or `task wait`

### 5. Recover or continue

- Failed run: inspect `task read`, `task events`, task timeline, summary, and stderr before retrying.
- Completed run with follow-up work: use `task steer` or create a new prompt file in the same session/workspace flow.
- Need a new agent to take over: materialize a prompt bundle or handoff manifest and pass the path forward.

## Quick Route by Need

| Need | Command path |
|---|---|
| Fast one-shot execution | `run task.md --wait --json` |
| Async launch plus later monitoring | `task start task.md --json` then `task follow <taskId>` |
| Live streaming from the start | `task start task.md --follow --stream-json` |
| Pre-create a reusable workspace/model context | `session create --cwd ... --model ...` |
| Continue the same thread later | `task start task.md --session ses_123` or `task steer tsk_123 followup.md` |
| Handle a blocked approval or question | `request list` → `request read` → `request answer` |
| Build a portable handoff for another agent | `prompt inspect task.md --write-bundle ./bundle --json` |
| Retrieve a finished task's handoff artifact | `task read tsk_123 --field artifacts.handoffManifestPath` |
| Diagnose a failure | `task read` + `task events` + `doctor` |
| Batch several independent tasks | separate prompt files + `task start --label ...` for each wave |

## Choosing Execution Mode

| Mode | Use when | Command shape |
|---|---|---|
| Async (default) | You want task ids immediately and will follow up later | `task start task.md --json` |
| `--wait` | You want one blocking result without streamed events | `task start task.md --wait --json` |
| `--follow` | You want streamed normalized events plus the final result | `task start task.md --follow --stream-json` |

## Choosing Effort

`task start` and `run` accept `--effort none|minimal|low|medium|high|xhigh`.

Default guidance:
- `minimal` or `low` for narrow edits, command runners, and deterministic file work
- `medium` for multi-step implementation or refactors
- `high` or `xhigh` only when the task truly needs deeper synthesis and the prompt is already precise

Do not compensate for a vague task by raising effort. Tighten the task file first.

## Prompt Writing Standard

Every task file should say:
- what to do
- which files or directories matter
- what not to touch
- what success looks like
- which verification commands prove success

For exact structures and copy-ready starters, read `references/prompt-writing.md` and the routed templates.

## Handling Results

| Status | Meaning | Next move |
|---|---|---|
| `running` | task is active | `task follow`, `task wait`, or `task read` |
| `waiting_request` | task is blocked on runtime input | use the `request` commands |
| `completed` | task finished successfully | inspect artifacts or continue with `task steer` |
| `failed` | task ended with an error | inspect artifacts and recover before retrying |
| `interrupted` | task was cancelled or stopped mid-run | inspect artifacts, then retry or steer |

For shell automation, use the CLI exit-code contract from `references/composability-and-exit-codes.md`.

## Do This, Not That

| Do this | Not that |
|---|---|
| `prompt inspect` when context resolution matters | fire a task blindly and hope `AGENTS.md` was loaded correctly |
| `task start --follow` when you need live visibility | parse generic prose output after the fact |
| `request answer` for blocked runs | assume the runtime auto-answered a question |
| `task read --json` before retrying a failed task | immediately rerun the same prompt without inspecting artifacts |
| `prompt inspect --write-bundle` for handoff | paste a long ad hoc summary and lose the original prompt structure |
| `--json`, `--stream-json`, `--field`, `--quiet` for scripts | scrape text tables or decorative output |
| `session create` when continuity is intentional | reuse sessions casually across unrelated tasks |

## Minimal Reading Sets

### "I need to dispatch one good worker task"
- `references/command-reference.md`
- `references/prompt-writing.md`
- `references/templates/coder-mission.md`

### "I need to monitor async work or coordinate a wave"
- `references/command-reference.md`
- `references/orchestration-patterns.md`
- `references/templates/batch-wave.md`

### "I need to unblock a paused task"
- `references/request-handling.md`
- `references/composability-and-exit-codes.md`

### "I need to hand off context to another agent"
- `references/prompt-bundles.md`
- `references/templates/research-mission.md`

### "I need to recover from a failure"
- `references/recovery-and-diagnostics.md`
- `references/composability-and-exit-codes.md`

## Reference Files

| File | When to read |
|---|---|
| `references/command-reference.md` | Exact command families, flags, and output modes. |
| `references/orchestration-patterns.md` | Single-task, async, session, batch, continuation, and handoff loops. |
| `references/request-handling.md` | Handling `waiting_request`, reading request payloads, and answering them correctly. |
| `references/prompt-bundles.md` | Prompt resolution, `AGENTS.md`, `--context-file`, `--write-bundle`, and handoff manifests. |
| `references/recovery-and-diagnostics.md` | Reading task artifacts, timelines, events, stderr, and doctor output. |
| `references/runtime-config.md` | How the CLI inherits runtime config from `~/.codex/config.toml` and when flags override it. |
| `references/composability-and-exit-codes.md` | `--json`, `--stream-json`, `--field`, `--quiet`, and shell-safe exit semantics. |
| `references/prompt-writing.md` | Writing precise Markdown task files for Codex workers. |
| `references/templates/coder-mission.md` | Copy-ready coding task file template. |
| `references/templates/research-mission.md` | Copy-ready repo exploration template. |
| `references/templates/batch-wave.md` | Copy-ready multi-wave orchestration template. |
| `references/templates/test-runner.md` | Copy-ready verification and test execution template. |

## Guardrails

- Do not mention MCP tools, MCP resources, or `task:///...` URIs in this skill.
- Do not assume blocked requests are auto-answered.
- Do not invent unsupported CLI flags. Recheck `--help` before documenting or using a command.
- Do not reuse stale task ids, request ids, or sessions without reading their current state first.
- Do not hand off work without a prompt bundle, rendered prompt, or handoff manifest path.
- Do not claim a task is irrecoverable until you have inspected `task read`, task artifacts, and `doctor` where relevant.
