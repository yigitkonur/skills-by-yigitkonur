# Observe tasks and PR candidates

Read this before submitting or supervising a task. The main skill owns the
mission table and terminal cleanup; this file owns observation, result
classification and PR discovery. Worker recovery is a separate branch.

## Submission and identity

Record task/attempt, pane/terminal, agent conversation, prompt submission time,
last observed status/revision and the host observer handle. These identifiers
are not interchangeable. A pane revision or status sequence is useful context,
not an invented per-turn correlation guarantee.

Keep the worker interactive and its progress visible in the Herdr pane. A
controller-side asynchronous WAIT does not require a headless worker. Capture
final reports separately; do not replace live output with stdout redirection.

For a recognized agent that is ready for input, prefer a combined submission:

```bash
herdr agent prompt <target> "$(cat /absolute/run/mission.txt)" \
  --wait --timeout 60000
```

Write the static file with a quoted heredoc or an editor; keep private content
out of logs. Quoted `"$(cat ...)"` passes file contents as one argument; do not
use `eval` or interpolate mission text into executable shell code. Confirm the
composer is empty before submission; preserve any user text.

`agent prompt --wait` has an activity guard when submitted from a non-working
state, but does not track individual turns. On an already working agent, its
current turn can satisfy the wait before the queued follow-up runs. For a
critical correction, confirm acknowledgment or changed behavior before relying
on it. If the existing turn has not settled, record the queued message and
keep observing; do not resend it just because pickup is not yet visible.

For an already submitted turn:

```bash
herdr agent wait <target> --timeout 60000
```

The default settled set is `idle`, `done`, `blocked`. Waiting only for `idle`
can miss background completion classified as `done`. A matching current state
can return immediately; `agent wait` does not promise a new transition.
`unknown` is uncertainty, not success; inspect `agent explain <target> --json`
and visible output when classification matters.

For an unrecognized agent or ordinary command, use a signal actually observed
in that CLI:

```bash
herdr pane wait-output <pane-id> --match <observed-signal> \
  --source visible --lines 20 --timeout 60000
```

Output waits search the selected snapshot immediately, including old text and
echoed prompts. Prefer a current-turn completion line; never treat a generic
footer or a marker printed in your own mission as sufficient. Scope the source
and line count to the signal. A marker outside that window may cause a normal
timeout, which is resolved by READ rather than guessed success. If the same
stale text causes repeated immediate matches, change the predicate/source or
use a supported lifecycle wait. If no trustworthy predicate is available,
record the observation limitation instead of spinning on the same false match
or inventing a daemon. Take the smallest direct status/artifact check needed
to establish the next action.

## Keep the controller responsive

Use a **60,000 ms Herdr deadline** as a starting point and a **1,000 ms host
yield** where supported. These are different clocks. Adapt to documented host
limits and the task; always provide a bounded deadline. WAIT runs in the
controller's command session, never inside the occupied worker pane.

Host-tool example, not shell syntax:

```text
exec_command:
  cmd: herdr agent wait <target> --timeout 60000
  yield_time_ms: 1000
  -> if running, record session_id with target and attempt

write_stdin:
  session_id: <same running session_id>
  chars: ""
  yield_time_ms: 1000
  -> consume completion, or keep the same handle
```

If `functions.exec` itself returns a running cell, its `cell_id` belongs to
`functions.wait`. An inner `exec_command` process `session_id` belongs to
`write_stdin`. Consume the outer result before expecting its inner handle.
Never interchange the two. Supported host minima may round the requested
interval upward. If only blocking tools exist, shorten the bounded interval
and state the responsiveness limit.

Launch ready independent tasks before awaiting results serially. Attach their
observers concurrently using native host calls and retain every result/handle.
Between yields, handle user steering, finished tasks, PR deltas and ready work.
Keep one live observer per target attempt; a host yield does not justify a
second observer. Mark old handles settled or retired when replacing them.

## WAIT result → READ → action

Start with 10–20 lines; expand for a missing handback or error. Use `visible`
while working/unknown; settled `recent-unwrapped` can expose the handback.
Some full-screen integrations reject history reads while working; fall back to
visible output. Ask for a file report when terminal history cannot supply it.

```bash
herdr agent read <target> --source visible --lines 20
# Or, after a settled pane-only turn:
herdr pane read <pane-id> --source recent-unwrapped --lines 20
```

| Observation | Interpretation and required next action |
|---|---|
| Host yields a running handle | WAIT is still alive. Resume that handle; no new WAIT and no worker restart. |
| Herdr returns `error.code: timeout` | Predicate was not observed before deadline. READ once; consume a finished result, resolve a blocker, or renew a new bounded WAIT for unfinished work. |
| WAIT matches / agent is idle or done | Explicit READ; confirm current assignment, pending/background jobs and handback. A stale match returns to observation, not delivery completion. |
| Agent is blocked | READ the actual question/error. Answer from existing authority when possible; record a real missing decision and continue independent work. |
| `agent_prompt_stalled` | Submission did not demonstrate expected activity. READ for a queued prompt, hook/startup error or wrong state before deciding to resubmit. |
| Observer connection/host session lost | Mark observation disconnected, not worker stopped. Reconcile live identity/output and PR/artifact state, then replace only the lost observer. |
| `pane_not_found` / `agent_not_running` | Inspect current inventory for closure, move, exit or replacement. Update identity; do not recreate the worker from this error alone. |
| Invalid flag, regex or protocol input | Inspect installed help/error, correct the request once. This is not a normal timeout. |
| Confirmed worker error with unfinished work | Route to [stopped-agent-recovery.md](stopped-agent-recovery.md). |

An invalid host handle does not prove the underlying command died. Inspect the
host's available sessions/process state. Cancel only an identified obsolete
observer through its supported handle before replacing it; never send Ctrl+C
to a healthy worker because its observer failed. If observer identity cannot
be recovered, record the limitation and reconcile current worker state before
choosing a replacement observation path.

Every settled WAIT needs an explicit READ even when its response includes a
snapshot. If the target disappeared, a failed READ followed by inventory
reconciliation records that exception; use preserved artifacts to determine
delivery. A visible prompt with background tests/reviewers still running is
not a completed handback.

When the prompt is idle but a background job remains, observe that job through
its existing native task handle or its actual terminal completion signal. If
only the worker can access the handle, assign one bounded follow-up to await
the existing job and report its exit/result; first account for any already
queued instruction. Keep the resource grant until that evidence arrives.
Do not repeatedly wait on an already idle agent or invent `herdr job wait`.
If neither a task handle nor observable signal is available, record the
limitation, keep the job's owner/resource reservation and advance independent
work while obtaining the missing evidence.

## Diagnose apparent WAIT drops

Keep the exact command, target identity, start/end time, host-handle outcome,
exit code and structured error in the existing ledger. Distinguish:

- planned deadline expiry;
- a still-running call that only yielded;
- a stale immediate match;
- controller/host cancellation or lost connection;
- target replacement/removal;
- a worker/provider failure reported inside the pane.

When needed, locate installed server/client logs through current configuration
and correlate one request by time and target. A `client_disconnected` log can
result from the controller cancelling its own observer; it does not by itself
prove a Herdr defect. Do not label an unexplained drop with a guessed cause.
After two equivalent non-timeout observer errors, change the observation path
or report the concrete limitation before a third identical retry.

Use a native event tool only when exposed by the installed CLI/host. Schema
support alone is not a callable CLI subscription. Reconcile a current snapshot
after reconnect because events may have been missed. Silence alone is not
proof of a broken event stream. Do not build a custom socket watcher.

The 0.9.0 CLI exposes `api snapshot` and `api schema`, not `api watch` or a PR
arrival watcher. Recheck installed help after upgrades. A bounded WAIT is an
attended request, not a durable subscription or an automatic future turn.

## Discover PR changes separately

Herdr observes workers; repository queries discover candidates. A draft may
appear while its author is still working, and research may finish without a
PR. Neither channel replaces the other. Query once at settlement/renewal
points, normally no more often than every 30–60 seconds per repository, using
one snapshot writer. A short host yield is not a reason to hit GitHub again.

Use a supported native PR event source when available. Otherwise use finite
queries below. `gh pr checks --watch` watches checks on one existing PR, not
new arrivals. Titles/latest-number cursors miss edits to older candidates;
use repository + PR number as identity.

Resolve the repository and create the private run directory first. Substitute
real paths in this example:

```bash
TASK_REPO='owner/repository'
gh api --paginate "repos/$TASK_REPO/pulls?state=open&per_page=100" \
  --jq '.[] | {number, url:.html_url, head:.head.sha, base:.base.ref, draft, updated_at}' \
  > /absolute/run/pr-fetch.jsonl &&
jq -se 'all(.[]; (.number | type) == "number" and
  (.head | type) == "string" and (.base | type) == "string" and
  (.draft | type) == "boolean") and
  (length == ([.[].number] | unique | length))' \
  /absolute/run/pr-fetch.jsonl > /dev/null &&
mv /absolute/run/pr-fetch.jsonl /absolute/run/pr-current.jsonl
```

A failed/partial fetch never replaces the last successful current snapshot.
An empty successful list is valid. Duplicate numbers fail validation; fetch
again. Pagination is not atomic during concurrent changes, so confirm missing
rows individually. Repository-specific paths and one writer prevent collisions.

On the first successful fetch, inspect relevant candidates and copy current to
`pr-seen.jsonl`. Later compare using this finite command:

```bash
jq -s --slurpfile previous /absolute/run/pr-seen.jsonl \
  '. as $current |
   {new: [$current[] | . as $p |
      select(any($previous[]; .number == $p.number) | not)],
    changed: [$current[] | . as $p |
      select(any($previous[]; .number == $p.number and . != $p))],
    missing_open: [$previous[] | . as $p |
      select(any($current[]; .number == $p.number) | not) | .number]}' \
  /absolute/run/pr-current.jsonl
```

Consume deltas into the ledger before replacing seen. A failed fetch preserves
both snapshots; retry with bounded backoff, not a loop. For a missing PR:

```bash
TASK_PR_NUMBER=123
gh api "repos/$TASK_REPO/pulls/$TASK_PR_NUMBER" \
  --jq '{number, state, merged_at, head:.head.sha, base:.base.ref}'
```

`closed` alone does not mean merged; inspect `merged_at`. If still open, retain
and reconcile next cycle. An API/access error leaves an unresolved row. After
recording these outcomes, acknowledge discovery by copying current to seen;
the ledger still retains unresolved review/CI/merge work. Act only on this
mission's candidates, even when the snapshot includes others.

Each reconciliation also revisits the ledger's unresolved PR numbers using
the exact-number query above, regardless of whether they appear in the latest
delta. Otherwise a missing PR acknowledged into `seen` can disappear from
future deltas after a transient lookup failure. Keep its retry action/owner
until the exact state is resolved; snapshot acknowledgment never clears it.

Changed metadata is a reason to inspect, not repeat every review. CI can
complete without a useful `updated_at` change: check CI separately for waiting
candidates. Distinguish pending, failed, API/auth errors and "no checks
reported"; absence of checks is neither passing evidence nor automatically a
failed build. Apply repository requirements and verified local evidence.
Before merge, query exact head/base, checks, reviews and mergeability afresh.

Record the last successful snapshot/time and owned live observers in the
existing ledger. Without a supported host scheduler and authorized handoff,
these queries cannot continue after the controller turn ends.
