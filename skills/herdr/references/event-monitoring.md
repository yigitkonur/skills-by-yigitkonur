# Event Monitoring & Communication

## 1. Live Coordinates
Always use live native records via `herdr pane current`. Do NOT trust static startup environment variables (e.g., `HERDR_TAB_ID`) for topology decisions, as panes may move.

## 2. Reading Pane State
Use `herdr agent wait <TARGET> --until idle --until done --timeout 60000` to block until the agent reaches a stable state.
Do not use tight polling loops.

## 3. Communication & Prompt Delivery
To submit a prompt or notification to a recognized agent, use `herdr agent prompt`:

```bash
herdr agent prompt <TARGET> "<PROMPT_TEXT>"
```
- **Enter is Default**: `herdr agent prompt` uses Enter.
- **Worker Notices Omit `--wait`**: Workers must NEVER pass `--wait` when notifying the manager. Passing `--wait` blocks the worker process.

### Runtime-Aware Notification Rules
- **Codex**: Buffers incoming text during tool execution. You MAY send `herdr agent prompt` even if it is currently busy (e.g., has a spinner).
- **AGY**: Interrupting an active AGY writer during synthesis can corrupt state. Wait for `idle` before sending prompts.

## 4. Modal Bridge
When an agent encounters a blocking modal (`ask_question`, `[y/N]`), Herdr rejects `prompt` with `error.code: agent_blocked`.
Resolve it mechanically:
1. `herdr agent read <target> --source visible --lines 20`
2. `herdr agent send-keys <target> down enter`

## 5. Degraded Mode: `herdr pane run`
If Herdr detection reports `unknown` but a foreground agent is visible:
1. Verify: `herdr pane read --source visible --lines 10 <PANE_ID>`
2. Fallback: `herdr pane run <PANE_ID> <COMMAND>...`
Never use `pane run` on an unverified shell prompt.
