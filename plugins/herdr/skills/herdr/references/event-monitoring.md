# Event Monitoring & Communication

## 1. Live Coordinates
Always resolve live coordinates via `herdr pane current` (returns JSON). Do NOT rely on static startup env vars (e.g. `HERDR_TAB_ID`) for topology decisions — they freeze at process creation and become stale when panes move.

`herdr pane current` gives physical pane/tab/terminal IDs. It does NOT prove the active model, effort tier, or that a composer is ready to receive input. Verify identity separately via the runtime's own identity query.

## 2. Reading Pane State

| Source | Syntax | Use |
|---|---|---|
| `recent-unwrapped` | `herdr agent read <T> --source recent-unwrapped --lines <N>` | **Default**: transcripts, code, LLM output. Merges soft wraps. |
| `visible` | `herdr agent read <T> --source visible --lines <N>` | **Modals**: questionnaires, spinners, confirmation prompts. |
| `recent` | `herdr agent read <T> --source recent --lines <N>` | **Columnar**: ASCII diagrams, tables, aligned grids. |
| `detection` | `herdr agent read <T> --source detection` | **Heuristic**: regex rule introspection only. |

`herdr agent wait <TARGET> --until idle --until done --until blocked --timeout 60000` blocks until a stable state. A wait timeout is not itself evidence of worker failure. `blocked` state is included because a worker waiting on a modal is stable.

## 3. Communication & Prompt Delivery

```bash
herdr agent prompt <TARGET> "<PROMPT_TEXT>"
```

- **Bracketed Paste Mechanics**: Wraps text in DEC Mode 2004 (`\x1b[200~...\x1b[201~`). Staged pacing delay (~300ms) before Enter; does not eliminate all PTY race conditions under heavy load.
- **Worker Notices Omit `--wait`**: Passing `--wait` blocks the worker and risks deadlock.

### Runtime-Aware Notice Qualification
- **Codex**: Buffers incoming PTY text during tool execution and reads it at the next turn boundary. Short operational notices to a busy Codex manager may be queued safely, **but busy delivery is not a guaranteed, loss-free synchronization mechanism** under rapid PTY churn. Where timing matters, wait for `idle` first or use the report sweep as fallback.
- **AGY**: Injecting prompt text into an active AGY writer while it is synthesizing code or generating tool calls can disrupt the turn, corrupt composer state, or collide with file writes. **Wait for `idle`** before sending prompts to an active AGY writer. This is a qualified operational constraint, not an invented corruption guarantee; the reviewer's claim that any busy notice corrupts file reads is not established.

## 4. Modal Bridge
When an agent is `blocked`, Herdr rejects `herdr agent prompt` with `error.code: agent_blocked`. Resolve mechanically:
1. Inspect first: `herdr agent read <target> --source visible --lines 20`
2. Choose keystrokes based on what you read: `herdr agent send-keys <target> <keys...>`
   Valid tokens: `up`, `down`, `enter`, `esc`, `tab`, `ctrl+c`. Read the modal before choosing; do not default to `down enter` without confirming the option.

## 5. Degraded AGY Mode (`herdr pane run`)
When Herdr detection reports `unknown` for a known AGY process:
1. Verify foreground process: `herdr pane process-info --pane <PANE_ID>`
2. Confirm visible input-ready composer with no modal: `herdr pane read --source visible --lines 10 <PANE_ID>`
   Foreground process alone is insufficient — a modal or alt-screen can be open.
3. If confirmed, use fallback: `herdr pane run <PANE_ID> <TEXT>...`
   This injects literal text followed by Enter into the pane (keystroke injection, not OS shell execution). Never use on an unverified foreground program or relaunch over a live TUI.

## 6. Targeted Intervention
- **`esc`**: Interrupts stuck prompts. May leave background work running. Inspect process inventory and owned effects afterwards.
- **`ctrl+c`**: In raw-mode TUIs the terminal passes raw byte 0x03 to the application. In cooked mode it sends SIGINT. The actual effect depends on the foreground application. Verify the resulting state by reading the visible screen before assuming the prompt returned.
- **No blind kills**: Never use blanket `kill -9` or `pkill`. Reconcile state before restart.

## 7. Discovery, Bootstrap & Model Verification
All panes identify live topology via `herdr pane current` before registering. Verify both runtime binary and model/effort tier through the runtime's own identity method (e.g. inspect the TUI header or query the process). Report mismatches before starting engineering work.

The 10-Minute Silent Boundary: If an agent operates without an external notification for ten minutes, the supervisor or agent performs ONE status check at the next safe tool boundary—not a mandatory checkpoint report, timer, heartbeat loop, or endless wait.
