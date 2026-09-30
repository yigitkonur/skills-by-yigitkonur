# Event monitoring and recovery

Read when waiting, inspecting an ambiguous state, handling modals or recovering
an interrupted agent. Work one target at a time at short tool boundaries.

## Observe the right surface

| Need | Command |
|---|---|
| Logical transcript and check output | `herdr agent read TARGET --source recent-unwrapped --lines 60` |
| Current composer, modal or spinner | `herdr agent read TARGET --source visible --lines 30` |
| Column-aligned terminal evidence | `herdr agent read TARGET --source recent --lines 60` |
| Agent registry/state | `herdr agent get TARGET` |
| Foreground and child-process evidence | `herdr pane process-info --pane PANE_ID` |
| Classifier's input | `herdr agent read TARGET --source detection` |

Raw reads are terminal text; state/creation responses are JSON. Do not parse a
transcript as structured state. Use pane-level reads when agent detection fails;
consult installed help for their argument order.
On the tested Codex alternate screen, a large recent read while blocked returned
`agent_not_idle` because history capture required scrolling. Use a short
`--source visible` read for the current dialog; do not wait for idle just to
learn which approval is blocking it.

## Bounded wait and next action

```bash
herdr agent wait "$TARGET" --timeout 30000
```

Default settle matches idle, done or blocked. Use `--until` only when a specific
transition matters; `--until done` can miss an idle ready-state. Without a timeout
this command waits indefinitely. There is no top-level `herdr wait` command.

Use the caller's native shell/session monitor: if exec returns a session handle,
join that handle and read its exit/output instead of launching another wait.
Keep tool wait windows short enough to inspect progress and communicate.
No detached polling, minute-long blocking scripts or artificial heartbeat loop.

| Result | Next action |
|---|---|
| idle/done | Read the job's result; readiness alone is not completion |
| blocked | Read the visible dialog and resolve only an authorized choice |
| timeout | Read recent + visible output and process-info; do not resubmit |
| unknown | Verify foreground identity before any injection or restart |
| transport error | Reconcile process and pending message before retrying |

`agent prompt --wait` has an activity gate when starting from a ready state.
Use it for a controller's single submission to a verified ready target, with a
bounded timeout. Worker callbacks remain waitless. If work was already submitted,
observe it without resending. A timeout before activity can still leave delivery
uncertain. Waiting on an already busy target is not proof that your particular
message was consumed.
A separate settle wait immediately after submission can return the pre-existing
`done` state before the new turn starts; this happened in the live Codex pilot.
Compare the pre-submit state/change sequence, observe activity and read the exact
job's output. A later `working → done` transition still does not prove success:
the tested Codex model returned an unsupported-model HTTP 400 and then `done`.

`pane wait-output` can match text already in scrollback: use a unique job marker,
and still verify producer/result identity rather than trusting a generic “done”.

## First-folder trust and other modals

A newly created checkout can open a folder trust screen before the normal
composer. On live Herdr 0.9.1, both AGY 1.2.14 and Codex 0.159.2 returned
`idle` / `interactive_ready: true` while that trust screen was visible. Treat
startup success as detection, then inspect the visible screen before a brief.
Claude 2.1.285 instead returned `agent_not_ready`/blocked and initially selected
“No, exit”. The owned-folder test navigated to the visible “Yes” choice and
verified it before Enter. Startup classification and default selection vary by
harness; neither success nor a shared key sequence proves the composer is ready.

1. Read `agent read TARGET --source visible --lines 30` after startup.
2. Compare the displayed folder to the assigned absolute checkout. Resolve
   symlinks: `/tmp` can display as `/private/tmp` on macOS. A different or unknown
   folder is a routing blocker; do not accept trust there.
3. If this is the task's known, inspected checkout and trust is within authority,
   use the visible selected choice. In the observed AGY and Codex trust screens,
   the selected option was trust/continue, so one `pane send-keys PANE enter`
   completed it. Do not reuse that key for login, billing or permission dialogs.
4. Read the screen again at the next tool boundary. The first immediate read can
   still show the old frame; do not press Enter again. Confirm the actual native
   composer and model/status header before sending the task. Codex’s inspected
   `/model` picker also reported `done` / `interactive_ready`; check for a menu
   before sending even when the semantic state looks settled.
5. Reconcile `agent get` and the visible screen if they disagree. A quota screen
   can expose an input-ready composer while semantic status remains `blocked`.
   A new task via `agent prompt` is rejected with `agent_blocked` in that state.

Read every unfamiliar dialog before keys. A startup timeout can leave a running
agent at a modal; inspect it rather than launch over it. When the required choice
exceeds the assignment's authority, report the concrete dialog and await input.

## Catch and answer asynchronous questions

A controller expecting a question can capture its first blocked transition:

```bash
herdr agent prompt "$TARGET" "$BRIEF" --wait --until blocked --timeout 30000
herdr agent read "$TARGET" --source recent-unwrapped --lines 40
```

Run the capture and read consecutively so another model turn does not delay the
feedback. Record the actual question/options and notify the user promptly.
A timeout is not proof that no question was asked: inspect the exact job's
transcript before any retry. This state-specific wait is for controllers, never
worker callbacks. Normal work uses the default settled states.

The live Codex tool call was `request_user_input_async`; `accepted: true` meant
the question was registered, not answered. In a standalone question turn Herdr
reported working → blocked → done without a reply. In the HTML/CSS writer pilot,
Herdr remained blocked while the TUI showed Working and the agent created and
checked files. A pending question does not prove the process has stopped. Do not
interrupt, relaunch, or block independent work just to clear that badge.

Track each unanswered question separately from execution and quality status.
The worker can continue independent work with explicit provisional placeholders;
only work depending on the answer must wait. Do not treat a provisional choice
as the user's choice, and do not declare the full task complete while required
preferences remain unresolved.

### Native Codex question panel

When the visible footer says `shift+← to answer`, the tested native command is:

```bash
herdr agent send-keys "$TARGET" shift+left
herdr agent read "$TARGET" --source visible --lines 35
```

Read the current question and selected option before deciding any key.
`shift+right` returned to the main composer without answering. Only submit an
authorized reply: navigate to its visible option, confirm selection, then Enter.
The live test consumed a non-default name and a non-default accent through this
panel while independent edits continued. Enter submits that question; the next
panel can show only the remaining question, without a “2 of 2” counter. Match
question identity/text and selected option, never a fixed page count.

A short `pane wait-output ... --source visible --timeout 3000` can confirm the
selected row before Enter. A match alone is not sufficient: it must be the known
current question panel, not a transcript or an old screen. If the expected row
is absent, read the current screen and stop that key sequence; do not submit.
After answering, the TUI may say the reply will be submitted at the next tool
call. Leave it queued; do not Escape or resend to make it faster. Verify the
correlated reply and resulting files after consumption.

### When the turn ends before an answer

In the tested build, the panel disappeared when the worker finished its turn;
Shift+Left did not reopen it then. Preserve the unanswered item in the controller
ledger even if Herdr now reports done. This observation does not prove a question
timeout. Send the authorized answer through the normal ready composer with the
job/question identity, or explicitly arrange a native-UI retest. Do not silently
re-ask or infer an answer from disappearance. The pilot separately verified text
reply consumption; that is different from a native menu selection.

## Unknown detection and stopped agents

1. Query registry, visible screen and process-info for the exact owned pane.
2. If the expected TUI is running and its composer is visibly input-ready,
   use that harness's documented pane-level fallback. Unknown detection is not
   permission to inject into a shell, editor or modal.
3. If genuinely stopped, preserve conversation/session ID and pending effects.
   Confirm the old process is dead and a clean shell prompt exists before restart.
4. Resume the exact session through installed native syntax when available;
   restore the same scope/model/effort and live callback. Do not rerun a submitted
   Git operation or message until its actual effects are reconciled.
5. If state is ambiguous, report it; do not invent a successful resume.

Interruption keys can leave child processes alive. Inspect after targeted
interruption; never blanket-kill or stop the Herdr server. A Git lock is not proof
of a dead process: inspect its exact repository lock path with
`git rev-parse --path-format=absolute --git-path index.lock` and process ownership.
Do not delete an active or ambiguously owned lock.

## Quota, pause and retry budget

Count equivalent failures across retries and replacement sessions. After two,
stop automatic recovery and report the diagnostic, preserved work and next
required decision. Do not rotate accounts, modify proxies/billing, downgrade
models, or expand scope. Inspect wrappers without printing credentials; a wrapper
preflight can have account side effects even for help/model listing.

User pause stops new dispatch, keys and mutations until resumed. Already-running
work may continue; describe its state honestly rather than claim it was stopped.
When unpaused, reconcile existing sessions before creating anything new.

## Socket observation when CLI waits are insufficient

Ordinary operations keep using CLI wrappers. For a scoped state-transition trace,
the live socket test used newline-delimited JSON over `HERDR_SOCKET_PATH`:

```json
{"id":"observe-job","method":"events.subscribe","params":{"subscriptions":[{"type":"pane.agent_status_changed","pane_id":"VERIFIED_PANE"}]}}
```

Read and validate the `subscription_started` acknowledgement before dispatch.
Keep reading that same connection for events; another connection can perform
`agent.get` or dispatch. The observed events used `event` and `data`, including
pane/workspace/agent/status. Limit the observation duration and close the socket
when finished. A subscription does not establish current state: also query the
target. Terminal output still determines why it is blocked or whether it failed.
Do not send `pane.report_agent` to overwrite a real harness's state as a repair.

Use `herdr api schema --output ABSOLUTE_PATH` and raw `ping` to discover the
installed protocol before implementing a client. The website may describe a
newer build. On the tested 0.9.1 server, mixed valid/invalid subscription targets
rejected with `pane_not_found` and a derived request ID; an unsupported method
returned `invalid_request` with an empty ID. Preserve the raw response and
correlation mismatch as diagnostics. Neither is an accepted subscription or task.
Do not assume successful delivery from socket writes, or latest-doc error fields
from an older running server. Refresh live identities before a corrected request.
