# Resume a Stopped Worker

Use this procedure only after READ confirms that a worker stopped unexpectedly with unfinished authorized work. A normal wait timeout or an `unknown` classification belongs first to [event-monitoring.md](event-monitoring.md), not immediate worker restart.

---

## 1. Inspect and Classify First

Read the current pane before intervening:

```bash
herdr agent read <target> --source visible --lines 25
herdr agent read <target> --source recent-unwrapped --lines 50
```

Determine the exact operating state:
- **Still Working**: Thinking or tool call is executing. Do not inject another prompt; renew the bounded wait.
- **Finished Turn**: The prompt is at rest. Consume the report or deliverable.
- **Interactive Question / Modal**: The agent is paused on `ask_question` or a confirmation menu (`[y/N]`). Do NOT send text! Use the modal bridge:
  ```bash
  herdr agent send-keys <target> down enter
  ```
- **CLI / Session Crash**: The agent process aborted or crashed back to the shell prompt.

---

## 2. Recovery Strategies

### Strategy A: The Interactive Continuation Prompt
If the agent CLI is still alive and resting at its interactive prompt after an error or interruption, submit a single targeted continuation prompt:

```bash
herdr agent prompt <target> \
  "Your previous command encountered an error. Review the error in your terminal history, inspect git status, and resume the task from the last valid checkpoint."
```

### Strategy B: Restarting Crashed Agent Session
If the agent process exited back to the shell prompt:
1. Verify the pane is sitting at a shell prompt (`$` or `%`).
2. Identify the active model used by the orchestrator (`$CURRENT_MODEL`).
3. Re-launch the agent CLI using the same model:
   ```bash
   herdr agent start <name> --kind <kind> --pane <pane_id> -- --model "$CURRENT_MODEL"
   ```
4. Re-submit the mission brief pointing to existing progress in the worktree:
   ```bash
   herdr agent prompt <target> \
     "Resuming task on feature/<task>. Previous changes exist in .worktrees/<task>. Check git status and tests, then complete remaining acceptance criteria."
   ```

### Strategy C: Interrupted Tool Call Recovery
If an agent CLI is permanently hung on a frozen subprocess or deadlocked tool call:
1. Send `ctrl+c` to cancel the hung command:
   ```bash
   herdr agent send-keys <target> ctrl+c
   ```
2. Read the visible screen to confirm return to prompt:
   ```bash
   herdr agent read <target> --source visible --lines 10
   ```
3. Once back at prompt, issue continuation instructions.

---

## 3. Bounded Recovery Rule

After **two consecutive failed recovery attempts** for the same failure mode:
1. Stop automated retries.
2. Capture the full terminal transcript to a debug file:
   ```bash
   herdr agent read <target> --source recent-unwrapped --lines 200 > /tmp/worker-crash-dump.log
   ```
3. Report the blocker to the orchestrator/user with the exact failure evidence.
