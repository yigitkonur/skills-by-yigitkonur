# Universal Harness Protocols (Claude Code, Gemini, Cursor & Others)

This reference defines general operational conventions, shell readiness rules, startup recovery, and provider safeguards across other AI coding agent harnesses supported by Herdr (Claude Code, Gemini CLI, Cursor, OpenCode, Amp, Devin, etc.).

---

## 1. Universal Interaction Baseline

For any agent harness lacking specialized queue semantics:
1. **Input-Ready Single-Send**:
   Submit prompts only when the pane is verified to be in an input-ready state (`idle` or `done`). Send exactly ONE prompt at a time.
2. **Inspect Consumption Before Re-Sending**:
   Do NOT assume transport submission equals execution. Verify that the agent has started processing the prompt before issuing follow-up commands.
3. **No Unsolicited Input Flooding**:
   Injecting rapid keystrokes into an unclassified agent harness while it is rendering output or running tools can cause terminal buffer corruption.

---

## 2. Shell Readiness Gate

Before invoking `herdr agent start`:
1. **Interactive Shell Prompt Required**:
   The target pane MUST be resting cleanly at an interactive shell prompt (e.g. `$ `, `% `).
   ```bash
   herdr pane read --source visible --lines 5 "$PANE_ID"
   ```
2. **No Foreground Process**:
   Verify no background jobs, previous agent instances, editors, or compilers are holding the foreground PTY:
   ```bash
   herdr pane process-info --pane "$PANE_ID"
   ```
   **Never run `herdr agent start` over a running agent or active process.**

---

## 3. Startup Timeout vs. Live Agent Recovery

When `herdr agent start` times out (default 30,000ms):

> [!IMPORTANT]
> **A startup timeout is NOT proof of launch failure.**
> In many cases, the agent process booted successfully, registered its session, and is already executing tools, but took longer than 30s to satisfy Herdr's regex readiness heuristic.

### Recovery Sequence:
1. **Query Process Tree**:
   ```bash
   herdr pane process-info --pane "$PANE_ID"
   ```
   If the expected agent binary is running as the foreground process, the agent is alive.
2. **Read Visible Terminal Buffer**:
   ```bash
   herdr agent read "$PANE_ID" --source visible --lines 20
   ```
   - If the agent is displaying its banner, model info, or active tool turns, **do NOT kill or relaunch it**.
   - If the agent is waiting at a confirmation dialog, resolve the dialog (see modal rules in [event-monitoring.md](event-monitoring.md)).
   - Only if the process is completely absent or terminated with a shell prompt should a restart be attempted.

---

## 4. Provider & Infrastructure Safeguards

1. **Two-Failure Rule**:
   If an agent encounters two consecutive infrastructure failures (e.g. connection drops, provider API errors, socket timeouts), **stop automated retries**. Document the failure and escalate.
2. **Model & Effort Fidelity**:
   Never guess unsupported model names or silently downgrade model reasoning tiers. If a requested model is unavailable, report the constraint to the user or supervisor.
3. **Shared Server Invariant**:
   Never execute `killall herdr` or `herdr server stop` to unblock a single hung agent. The Herdr server multiplexes all active sessions, workspaces, and user terminals. Terminate only the specific offending process within its own pane.
