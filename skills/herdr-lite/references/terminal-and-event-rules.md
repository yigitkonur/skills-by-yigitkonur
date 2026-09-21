# Terminal & Event Monitoring Rules

This reference defines the PTY and terminal interaction physics for Herdr-Lite. Following these rules prevents race conditions, composer corruption, and deadlock.

---

## 1. Live Coordinates

Always resolve live coordinates dynamically using `herdr pane current`. Do NOT trust static startup environment variables (e.g. `HERDR_TAB_ID`), as panes can be moved across tabs or workspaces:

```bash
SELF_PANE_ID="$(herdr pane current | jq -r .result.pane.pane_id)"
SELF_TAB_ID="$(herdr pane current | jq -r .result.pane.tab_id)"
SELF_TERM_ID="$(herdr pane current | jq -r .result.pane.terminal_id)"
SELF_CWD="$(herdr pane current | jq -r .result.pane.cwd)"
```

> [!NOTE]
> `herdr pane current` outputs JSON natively. Do not pass `--json`.

---

## 2. Reading Pane State

| Source | Command Syntax | When to Use |
|---|---|---|
| `recent-unwrapped` | `herdr agent read <TARGET> --source recent-unwrapped --lines <N>` | **Default**: code, tool outputs, transcripts. Merges soft wraps. |
| `visible` | `herdr agent read <TARGET> --source visible --lines <N>` | **Modals**: spinners, questions, interactive menus. |
| `recent` | `herdr agent read <TARGET> --source recent --lines <N>` | **Columnar**: ASCII tables, aligned grids, test matrices. |

Use `herdr agent wait <TARGET> --until idle --timeout 60000` to wait for an agent to finish its active turn. A timeout does not necessarily imply failure; it indicates the agent is still working or blocked on a modal.

---

## 3. Communication & PTY Delivery Rules

```bash
herdr agent prompt <TARGET> "<PROMPT_TEXT>"
```

### Critical PTY Constraints:
1. **Mandatory `idle` Wait for AGY Writers**:
   Injecting prompt text into an active Antigravity (AGY) agent while it is synthesizing code or invoking tools disrupts the turn, corrupts composer state, and can collide with active file writes. **Always wait for `idle`** before sending prompt text to an AGY pane:
   ```bash
   herdr agent wait "$TARGET_PANE_ID" --until idle --timeout 60000
   ```
2. **Bracketed Paste Mechanics**:
   Herdr wraps prompt text in DEC Mode 2004 bracketed paste escapes (`\x1b[200~...\x1b[201~`) with a staged ~300ms delay before Enter.
3. **Never Pass `--wait` on Worker Notices**:
   Passing `--wait` when an implementer or reviewer notifies an orchestrator blocks the worker's own process and risks callback deadlocks.

---

## 4. Modal Bridge

When an agent encounters an interactive confirmation prompt, Herdr flags the agent as `blocked` and rejects prompt attempts with `error.code: agent_blocked`.

Resolve modals systematically:
1. **Inspect First**:
   ```bash
   herdr agent read "$TARGET_PANE_ID" --source visible --lines 20
   ```
2. **Send Targeted Keystrokes**:
   ```bash
   herdr agent send-keys "$TARGET_PANE_ID" <keys...>
   ```
   Valid key tokens: `up`, `down`, `enter`, `esc`, `tab`, `ctrl+c`. Always read the visible prompt before choosing keys; never guess or default to `down enter` blindly.

---

## 5. Degraded AGY Mode (`herdr pane run`)

If Herdr detection reports `unknown` for an active AGY process:
1. Verify the foreground process:
   ```bash
   herdr pane process-info --pane "$PANE_ID"
   ```
2. Inspect the visible screen to confirm an input-ready composer with no open modal:
   ```bash
   herdr pane read --source visible --lines 10 "$PANE_ID"
   ```
3. Use the fallback run command:
   ```bash
   herdr pane run "$PANE_ID" "<TEXT>"
   ```
   *Caution*: `herdr pane run` injects literal keystrokes into the PTY; it is not shell command execution. Never use on unverified foreground programs.

---

## 6. The 10-Minute Silent Boundary

If an agent runs without visible progress or output for 10 minutes, the orchestrator performs **ONE status check** (`herdr agent read <TARGET> --source visible --lines 10`) at the next safe tool boundary. Avoid tight polling loops or artificial heartbeat timers.
