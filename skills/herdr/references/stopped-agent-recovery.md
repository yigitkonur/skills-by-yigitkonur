# Resume a stopped worker

Use this branch only after READ confirms that a worker stopped with unfinished
authorized work. A lost observer, WAIT deadline or `unknown` classification
belongs first to [event-monitoring.md](event-monitoring.md), not worker restart.
Keep the existing scope, checkout, ownership, model and permission mode. The
controller still owns completion; continuation does not override user stops,
real quota limits or required decisions.

## Read and classify first

Read the current pane and task ledger. Save the exact conversation ID from Herdr's `agent_session.value` (when its kind is `id`) or the CLI's printed resume command, plus the checkout, last outcome, pending background jobs, and error. Conversation ID, pane ID, and host WAIT session ID are different identifiers.

- **Already resumed by the user or still working:** do not inject another prompt. Keep/renew its single WAIT subscription.
- **Finished:** consume evidence and close the completed container under the main skill's lifecycle rule.
- **Transient network/provider error, interactive input available:** submit the continuation message below once, then WAIT → READ.
- **CLI/session limit or unusable CLI:** preserve its conversation ID and actual resume command; interrupt only that worker with Ctrl+C, READ to confirm its state, and resume the same conversation once a shell is available. A first Ctrl+C may only cancel generation; do not type a shell command into an agent prompt. Read before deciding whether another interrupt is needed.
- **Account quota/rate limit with a reset time:** restarting does not replenish quota. Respect the reported retry time and record a blocker if unavailable; continue independent ready work. Never churn accounts/models or relaunch repeatedly to evade a limit.
- **Genuine permission, ownership, product decision, or user pause:** preserve and surface the actual blocker. Do not send a generic continuation to override it.
- **Failed test or disproved implementation:** keep the failed evidence and assign a bounded diagnosis/correction; an upstream-error continuation is not an explanation or a fix.

Before a recovery input, confirm the composer is empty and preserve any user
text. After a material correction, confirm acknowledgment or observed compliance;
a queued submission does not prove the next action follows it.

## Check specific causes before relaunch

- **Worktree startup/hook failure:** compare foreground cwd with the assigned
  checkout and inspect the actual startup error. Provision missing runtime
  files only through the repository's authorized setup; do not copy arbitrary
  executable hooks from another checkout.
- **Context drift:** verify current Git/artifact state, then send a compact
  re-anchor with completed work, remaining acceptance and live constraints.
  Use the agent's supported compaction/resume path if that fails.
- **Suspected wedge:** require task-appropriate evidence over time, such as
  repeated errors plus unchanged process/artifact progress. Quiet output, a
  spinner, one timeout or unchanged files alone do not prove a stuck worker.
  Interrupt only the identified task when evidence and authority support it.
- **Repeated stale review results:** confirm the writer has stopped editing,
  freeze the candidate and use one bounded review. Do not add reviewer fanout
  against a moving head.

## Continuation prompt

Use the user's requested wording, followed by the task's concrete remaining outcome and current constraints when needed:

```text
Continue from where you left off (if subagents/workflows failed, try to resume, if not possible, respawn them again) to complete execution and never stop before reaching %100 completion!
```

For a controller-owned topology, append: `Report failed child workflows to the controller; do not spawn duplicate workers yourself. Preserve existing work, report real blockers, and verify the assigned completion criteria before claiming completion.`

For an unrecognized interactive agent, `pane run` submits text and Enter:

```bash
herdr pane run <pane-id> 'Continue from where you left off (if subagents/workflows failed, try to resume, if not possible, respawn them again) to complete execution and never stop before reaching %100 completion! Report failed child workflows to the controller; do not spawn duplicate workers yourself. Preserve existing work and report real blockers.'
```

For recognized agents prefer `agent prompt`. If text was already queued, wait for that submission instead of adding another copy.

## Resume a limited or interrupted agy session

Check `agy --help` and the actual printed resume command. The installed CLI at this writing supports `--conversation <id>`; `--continue` selects the most recent conversation and is ambiguous with parallel tasks. Prefer the exact ID.

```bash
# Only after observing a stopped/unusable worker and preserving its session ID:
herdr pane send-keys <pane-id> ctrl+c
herdr pane read <pane-id> --source visible --lines 60

# Only after READ confirms a shell, using the saved actual ID and original cwd:
herdr pane run <pane-id> 'agy --conversation <saved-conversation-id> --model gemini-3.8-flash-high --effort high --mode accept-edits --prompt-interactive "Continue from where you left off (if subagents/workflows failed, try to resume, if not possible, respawn them again) to complete execution and never stop before reaching %100 completion!"'
```

The model/mode above illustrate the user's configured Gemini mission; preserve the task's actual settings and never broaden permissions during recovery. Inspect/copy the CLI's emitted resume command when its syntax differs. Do not assume restart clears a context limit; if the CLI requires compaction or a fresh conversation, use its supported flow or the fresh-agent handoff below.

Attach a bounded native WAIT with a short host yield; record its handle, then explicitly READ when it settles. Confirm new work belongs to the resumed task and no duplicate background writer survived the interruption. Retire the obsolete observer before attaching a replacement; never run custom recovery/polling scripts.

## Bounded recovery and fresh-agent fallback

After two consecutive equivalent recovery failures (operation + provider + error class), change approach or report the blocker before a third attempt. A WAIT timeout alone is not a failed recovery: READ and renew if work is progressing.

If the session cannot be resumed but the task remains authorized and executable, the controller may create a fresh agent. Preserve/read the previous artifacts and Git state first; confirm the former writer and its background jobs are no longer active. Give the replacement a standalone brief with the original acceptance criteria, exact checkout/base/head, completed work, remaining work, evidence paths, and failure history. Use a related pane in the existing task tab; close the stopped pane after its handoff is preserved. Do not restart the task from scratch or overwrite existing work.

Record the attempt number, conversation identity, error class, preserved
artifacts, observer handle and next owner/action in the existing task table.
If the user already resumed the worker, reconcile that attempt instead of
submitting another continuation. Recovery ends when work demonstrably advances
under observation or an exact blocker remains; mission completion still needs
the delivery evidence. A replacement may inherit a saved draft/check gap, but
must not count that artifact as a completed implementation.
