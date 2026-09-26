# Event Monitoring & Terminal Physics

This reference details the mechanics of monitoring pane states, reading terminal buffers, tracking agent lifecycles, and managing communication timing across Herdr sessions.

---

## 1. Terminal Screen Snapshot Sources

Select the snapshot source that matches the inspection objective:

| Source | Command Syntax | When to Use |
|---|---|---|
| `recent-unwrapped` | `herdr agent read <T> --source recent-unwrapped --lines <N>` | **Default**: Code blocks, tool output, test logs, and transcripts. Joins soft-wrapped lines into continuous text. |
| `visible` | `herdr agent read <T> --source visible --lines <N>` | **Modals & Spinners**: Approval dialogs, questionnaires, active spinners, interactive menus, and confirmation prompts. |
| `recent` | `herdr agent read <T> --source recent --lines <N>` | **Columnar Data**: Aligned tables, ASCII diagrams, diff grids, and fixed-width formatting. Preserves rendered soft wraps. |
| `detection` | `herdr agent read <T> --source detection` | **Heuristics**: Raw bottom-buffer snapshot used by Herdr's regex classifier to detect agent lifecycle states. |

### Formatting:
- Pass `--format ansi` when color coding, terminal styling, or syntax highlighting are essential evidence. Otherwise, use default plain text.

---

## 2. Agent State Tracking & Settle-Waits

Track agent lifecycle progression with `herdr agent wait`:

```bash
herdr agent wait <TARGET> [--until <STATUS>] [--timeout <MS>]
```

1. **Default Settlement Gate**:
   - Omitting `--until` matches `idle`, `done`, or `blocked`.
   - `blocked` is included because an agent paused at an interactive modal is stable and awaiting human/supervisor input.
2. **Server-Side Seen State vs. TUI Badges**:
   - `idle` and `done` both indicate the agent is ready for input.
   - The Herdr server marks an agent `done` upon completion of a turn; explicit focus transitions mark it `idle`.
   - Each TUI client tracks viewed completions independently, so a badge on one screen may differ from CLI query output.
3. **Timeout Interpretation**:
   - An expired wait timeout does NOT prove agent failure. It indicates the agent is still running a long turn, executing heavy tests, or waiting at an unhandled prompt. Inspect `process-info` and visible output before acting.

---

## 3. Communication & Prompt Delivery Timing

```bash
herdr agent prompt <TARGET> "<PROMPT_TEXT>"
```

### Critical PTY Constraints:
1. **Bracketed Paste Mechanics**:
   Herdr wraps text in DEC Mode 2004 bracketed paste escapes (`\x1b[200~...\x1b[201~`) with an internal pacing delay (~300ms) before the trailing Enter.
2. **Never Pass `--wait` on Worker Notices**:
   When a worker or reviewer notifies an orchestrator or peer, **omit `--wait`**. Passing `--wait` blocks the sender's own process and creates callback deadlocks.
3. **Targeted Waits vs. Whole-Fleet Blocking Deadlock**:
   Never run an unbounded blocking wait across an entire fleet. Wait on specific individual targets using short, bounded timeouts (e.g. 5000ms–15000ms), allowing the supervisor to observe progress and stream reviews without stalling.

---

## 4. Modal Bridge & Resolution

When an agent enters an interactive menu, question, or confirmation prompt, Herdr flags it as `blocked` and rejects new prompt submissions with `error.code: agent_blocked`.

### Resolution Sequence:
1. **Inspect First**:
   ```bash
   herdr agent read <TARGET> --source visible --lines 20
   ```
2. **Select Targeted Keystrokes Based on Visible Choice**:
   ```bash
   herdr agent send-keys <TARGET> <KEYS...>
   ```
   Valid logical tokens: `esc`, `enter`, `up`, `down`, `tab`, `ctrl+c`.
   **Never guess**: Read the visible dialog to determine the authorized selection (e.g. navigating to "Trust this directory" or "Allow once") before sending keys.

---

## 5. Degraded AGY Mode (`herdr pane run`)

When Herdr detection reports `unknown` for an active Antigravity process:
1. **Verify Foreground Program**:
   ```bash
   herdr pane process-info --pane "$PANE_ID"
   ```
2. **Confirm Clean Input State**:
   Inspect the visible screen to verify an input-ready composer with no open modal or alternate-screen buffer:
   ```bash
   herdr pane read --source visible --lines 10 "$PANE_ID"
   ```
3. **Execute Fallback Keystroke Injection**:
   ```bash
   herdr pane run "$PANE_ID" "<TEXT>"
   ```
   *Caution*: `herdr pane run` injects literal text followed by Enter into the PTY. It is keystroke injection, not shell command execution. Never use on unverified foreground programs.

---

## 6. Targeted Intervention

- **`esc`**: Interrupts stuck prompts or turns under explicit pre-inspection safety rules. May leave background child processes running. Inspect process inventory and visible composer state afterwards.
- **`ctrl+c`**: In raw-mode TUIs the terminal passes raw byte 0x03 to the application; in cooked mode it sends SIGINT. The actual effect depends on the foreground application. Verify resulting state by reading the visible screen before assuming prompt returned.
- **No Blind Kills**: Never use blanket `kill -9` or `pkill`. Reconcile state before restart.

---

## 7. Discovery, Bootstrap & Model Verification

All panes identify live topology via `herdr pane current --current` before registering. Verify both runtime binary and model/effort tier through the runtime's own identity method (e.g. inspect the TUI header or query the process). Report mismatches before starting engineering work.

### The 10-Minute Silent Boundary:
If an agent executes for ten minutes without visible output or external notification:
- Perform **ONE status check** (`herdr agent read <TARGET> --source recent-unwrapped --lines 30`) at the next safe tool boundary.
- Do NOT enter tight polling loops.
- Do NOT generate artificial heartbeat messages or timer schedules.
