---
name: herdr
description: "Use skill if you are explicitly asked to control Herdr panes, tabs, workspaces, worktrees, commands, or coding agents."
---

# herdr

Control a live Herdr session without stealing focus or guessing terminal state. Herdr supplies the terminals and lifecycle signals; you remain the decision-maker. Inspect, choose the smallest correct primitive, act once, read the result, and verify the intended state.

## Scope and prerequisite

Use this skill only when the user explicitly mentions Herdr or asks to inspect or control a Herdr pane, tab, workspace, worktree, command, or agent. Do not invoke it merely because another pane, delegation, or parallel work might be useful.

Before any control command:

```bash
test "${HERDR_ENV:-}" = 1
```

If this fails, do not inspect or control the user's focused Herdr session from outside it. Explain that the agent must run inside a Herdr-managed pane. You may help with installation or startup, but do not run bare `herdr` as an automated discovery command: it launches or attaches the interactive TUI.

## Let the installed CLI lead

Herdr evolves quickly. The installed binary is the authority:

```bash
herdr --version
herdr --help
herdr agent
herdr pane
herdr workspace
herdr tab
herdr worktree
```

Print only the command group relevant to the task. Do not probe a mutating nested command by omitting arguments; commands such as `workspace create` can execute with defaults. When the CLI and this skill disagree, follow current help and report the drift.

Most commands return JSON. Parse IDs and state from the response instead of predicting them. For deeper protocol questions, inspect `herdr api schema --json` before inventing a socket request.

## Mental model

- **Session** — an independent Herdr server namespace.
- **Workspace** — a project or task boundary.
- **Tab** — one terminal layout within a workspace.
- **Pane** — one persistent terminal process.
- **Agent** — a recognized coding-agent process occupying a pane.

Choose the surface that matches the job:

| Need | Use |
|---|---|
| Create, move, resize, focus, or close terminal layout | `workspace`, `tab`, or `pane` |
| Run or inspect an ordinary shell command | `pane` |
| Prompt, wait for, read, or send keys to a recognized coding agent | `agent` |
| Create or open isolated Git checkouts | `worktree` |
| Inspect protocol capabilities or stream long-running events | `api` / socket API |

`agent start` needs an existing available shell pane. It starts an agent; it does not create layout.

## The control loop

### 1. Orient

Read caller context and the smallest useful live snapshot:

```bash
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
herdr pane current --current
herdr pane layout --pane "$HERDR_PANE_ID"
herdr agent list
```

Add `workspace list`, `tab list`, or `pane list` only when the task spans them. Prefer `--current`, an explicit opaque ID, or a unique agent name. Omitting a target can act on another client's focused pane.

### 2. Decide the topology

Default to a sibling pane in the current tab and current working directory. Preserve focus with `--no-focus`. Create a workspace, tab, worktree, or different cwd only when the request needs that boundary.

For an unspecified split direction, inspect the current rectangle: split a wide pane right; split a narrow or tall pane down. Avoid repeated splits that leave unusable columns or rows.

### 3. Act through the highest-level surface

Create a background pane and capture its returned ID:

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
```

For an ordinary command:

```bash
herdr pane run <pane-id> "just test"
herdr pane wait-output <pane-id> --match "test result" --timeout 120000
herdr pane read <pane-id> --source recent-unwrapped --lines 120
```

For a coding agent:

```bash
herdr agent start reviewer --kind claude --pane <pane-id>
herdr agent prompt reviewer "Review the current diff and report actionable findings only."
```

Use the kind the user requested. Run `herdr agent` to see currently supported kinds and exact options. Pass native agent arguments only after `--`.

Prefer `agent prompt` over raw pane text: it validates the target and submits text with Enter using the pane's live bracketed-paste mode. Use pane input only when raw terminal control is intentional.

### 4. Wait for state, then read evidence

For a submitted turn, wait as part of the prompt:

```bash
herdr agent prompt reviewer "Run the focused review." --wait --timeout 120000
```

If the prompt was submitted separately and you specifically need the next approval/question state, wait for that state instead:

```bash
herdr agent wait reviewer --until blocked --timeout 120000
```

These are alternatives, not a sequence. Without `--until`, `agent wait` settles on `idle`, `done`, or `blocked`.

- `idle` — ready for input after its tab has been seen.
- `done` — background work settled before the tab was seen.
- `blocked` — approval or question UI detected.
- `working` — active.
- `unknown` — classification is uncertain; it does not prove completion.

For long-running agents or multiple transitions, use the push-event workflow in `references/event-monitoring.md`, not an `agent get` polling loop.

Read the actual output after a transition:

```bash
herdr agent get reviewer
herdr agent read reviewer --source recent-unwrapped --lines 120
```

A lifecycle event proves state changed, not that the task succeeded. An agent report is still a claim; verify the evidence the task requires.

### 5. Recover from what Herdr actually reports

| Signal | Response |
|---|---|
| `blocked` | Read the visible pane; surface the exact approval or question. |
| `unknown` | Use `agent explain <target> --json`, inspect output, and check integrations. |
| Wait timed out | Read current state/output; distinguish a long command from a stalled agent. |
| `agent_prompt_stalled` | Confirm the agent was ready and the prompt produced lifecycle activity. |
| Command or flag rejected | Re-open that command group's help; do not retry a guess. |
| Output is missing from large reads | The agent may use the terminal alternate screen; ask it to save its full report to a temporary Markdown file and return only the path. |
| Socket/event shape rejected | Re-read `herdr api schema --json`; wire enums may differ from CLI spellings. |

## Ownership and safety

- Use `--no-focus` for background work unless the user asked to switch context.
- Save IDs from creation responses; never rely on sidebar order, "latest pane," or guessed IDs.
- After moving a pane, continue with `.result.move_result.pane.pane_id`; cross-workspace moves can change the ID.
- Close only panes, tabs, worktrees, or workspaces created for this task unless the user explicitly authorizes otherwise.
- Do not run `herdr server stop` unless the user explicitly intends to stop the server and its pane processes.
- Do not kill the main Herdr process. Use a named session for experiments that require isolation.
- CLI server failures are JSON on stderr with exit status 1; CLI syntax errors exit 2.

## Finish

Report the workspace/tab/pane or agent IDs used, commands or prompts submitted, final lifecycle state, evidence read back, resources created, and cleanup performed. Mention anything intentionally left running.
