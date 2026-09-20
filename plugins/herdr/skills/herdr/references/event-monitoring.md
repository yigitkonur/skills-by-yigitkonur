# Observe tasks and PR candidates

Read this before submitting or supervising a task. The main skill owns the master orchestration lifecycle and container cleanup; this file owns observation mechanics, the bidirectional push-callback protocol, result classification, and PR discovery.

---

## Submission and identity

Record task/attempt, pane/terminal, agent conversation ID, prompt submission time, last observed status/revision, and the host observer handle. These identifiers are not interchangeable.

### The Bidirectional Push-Callback Architecture
Never rely solely on continuous polling or indefinite synchronous blocking. When the orchestrator dispatches a task to a worker agent, the orchestrator **must** provide its own coordinates:

```bash
CALLER_PANE_ID="${HERDR_PANE_ID:-$(herdr pane current --json | jq -r .result.pane_id)}"
CALLER_TAB_ID="${HERDR_TAB_ID:-}"
```

In the task brief, instruct the worker agent to report its completion directly back to the caller's pane:

```bash
herdr agent prompt "$CALLER_PANE_ID" \
  "I'm the herdr agent in pane $WORKER_PANE_ID (tab $WORKER_TAB_ID). Task $TASK_NAME is finished on branch $BRANCH. PR: #$PR_NUM (Draft). Summary: $SUMMARY. You can read my full output with: herdr agent read $WORKER_PANE_ID --source recent-unwrapped --lines 100"
herdr notification show "Task Complete" --body "Worker in $WORKER_PANE_ID finished $BRANCH" --sound done
```

### Submitting to Recognized Agents
For a recognized agent ready for input, deliver prompts using `herdr agent prompt`:

```bash
herdr agent prompt <target> "$(cat /absolute/run/mission.txt)"
```

- **Bracketed Paste**: Herdr wraps text in DEC Mode 2004 (`\x1b[200~...\x1b[201~`), preserving newlines without premature execution.
- **300ms Staged Delay**: Herdr enforces a 300ms silence (`AGENT_PROMPT_SUBMIT_DELAY`) between text write and `\r` (Enter), preventing dropped keystroke race conditions.
- **Activity Guard**: If submitted from a non-working state with `--wait`, Herdr enforces a 5,000ms deadline requiring a transition to `working` or `blocked`. If the agent stalls or does not activate, Herdr returns `agent_prompt_stalled`.

---

## Keep the controller responsive

Modern multi-agent workflows run across different agent runtimes. Tailor your supervision strategy to the runtime environment:

### Runtime Strategy Matrix

| Agent Runtime | Observation Mechanism | Recommended Supervisor Pattern |
|---|---|---|
| **Claude Code** | Native background subshells / streaming monitors | Launch background terminal task with output monitoring; receive streaming updates while keeping caller interactive. |
| **Antigravity CLI / Gemini** | Asynchronous tool calls (`run_command` async + `schedule` watchdog) | Dispatch worker with Push Callback Mandate. Either run bounded `agent wait` or set a 5-minute watchdog timer via `schedule` tool and yield turn. The worker's reverse prompt reactivates the supervisor automatically. |
| **OpenAI Codex CLI** | Synchronous tool turns | Dispatch with Push Callback Mandate; execute bounded `agent wait --timeout 60000`. If timeout occurs, inspect screen with `agent read --source visible` and renew. |
| **Cursor / IDE Terminals** | Persistent terminal panes | Dispatch with Push Callback Mandate. Use non-blocking terminal sessions. |

### Bounded Wait vs. Polling Loops
Do NOT write continuous tight polling loops (`while true; do sleep 1; done`) or custom Unix socket daemons. Instead, use Herdr's native event-driven wait:

```bash
herdr agent wait <target> --until idle --until done --timeout 60000
```

- The default settled set is `[idle, done, blocked]`.
- Background tabs transition to `done` (`seen = false`) upon completing work. Focusing the tab marks it seen, transitioning it to `idle`. **Always wait for both `--until idle --until done`.**

---

## WAIT result → READ → action

The mandatory supervision sequence is:
**WAIT / NOTIFY → READ → CLASSIFY → NEXT ACTION.**

After any wait returns or after receiving a callback prompt, always perform an explicit read to extract verified evidence before deciding the next step:

```bash
# Read uncorrupted, unwrapped transcript lines
herdr agent read <target> --source recent-unwrapped --lines 40

# Read active modal or question state
herdr agent read <target> --source visible --lines 20
```

### Result Classification Matrix

| Observation | Interpretation and Required Next Action |
|---|---|
| **Callback Prompt Received in Caller Pane** | Worker has finished its assignment (or is blocked). Read the worker's pane or report file (`.agent-runs/report.md`), verify the test outcomes and Draft PR URL, and advance to clean-context review. |
| **WAIT returns 0 (Status: `idle` or `done`)** | Agent has finished its turn. Read `recent-unwrapped` to verify the completion claim and handback contract. |
| **WAIT returns `error.code: timeout`** | Deadline expired before status changed. READ current pane. If the agent is compiling or running tests, renew the wait. If the agent is idle, consume the result. If hung, investigate. |
| **Agent is `blocked`** | Target is pausing on an interactive question or modal. READ `visible` viewport to see choices. Use `herdr agent send-keys <target> <keys...>` to navigate and select options. |
| **`error.code: agent_prompt_stalled`** | Prompt did not produce working/blocked state within 5,000ms. Inspect pane with `visible`. If model is reasoning with slow TTFT, wait. Do not resubmit duplicate prompts. |
| **`error.code: agent_blocked`** | Attempted to prompt a blocked agent. Herdr actively protected the PTY from corrupted text. Read `visible` and use `agent send-keys`. |
| **Target missing (`pane_not_found`)** | Inspect `herdr pane list` to check if pane was moved, renamed, or closed. |

---

## Discover PR changes separately

Herdr observes workers; GitHub queries verify pull requests and candidate states. A draft PR may appear while its author is still refining tests.

When checking PRs across a wave, use finite, targeted queries rather than continuous loops:

```bash
# Check PR status for a specific branch
gh pr view <branch-or-number> --json number,title,state,isDraft,mergeable,reviewDecision

# List open PRs for this project
gh pr list --state open --json number,title,headRefName,isDraft,updatedAt
```

### The Clean-Context Review Integration Gate
1. Once a worker opens a **Draft PR**, do NOT review it in the worker's pane.
2. Launch a fresh Reviewer agent in a separate tab or pane with a clean context window.
3. Reviewer inspects `gh pr diff <PR_NUMBER>`.
4. Reviewer submits review comments or approval:
   ```bash
   gh pr review <PR_NUMBER> --approve -b "LGTM: spec requirements and test coverage verified."
   ```
5. Once approved, mark PR ready for review:
   ```bash
   gh pr ready <PR_NUMBER>
   ```
6. Rebase serially on `origin/main`, verify tests, and merge:
   ```bash
   gh pr merge <PR_NUMBER> --squash --delete-branch
   ```
