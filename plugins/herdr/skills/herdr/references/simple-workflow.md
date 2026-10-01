# Simple workflow

Read for directly supervised work. Root owns the task and verification; no EM,
mission DAG, issue creation, report directory or orchestration ceremony is needed.

## Execute one job

1. Apply the caller/scope gate in SKILL.md. Save the live root return pane.
2. Decide whether a worker is actually needed for the requested operation.
   An explanation or skill edit alone does not launch one. For an authorized
   worker, choose difficulty and [profile](agent-profiles.md).
3. Read [topology](topology-and-worktrees.md). Create a new task tab using the
   current workspace and intended checkout, with `--no-focus`. Parse IDs from
   the result. An ordinary single writer can use the existing checkout; record
   pre-existing edits before assigning ownership.
4. Start the visible agent in the returned shell pane with an explicit profile
   and a 30000ms startup timeout. Read its harness recipe. Inspect readiness;
   startup errors go to [monitoring](event-monitoring.md), not another launch.
5. Submit one scoped brief from [messaging](prompt-and-messaging.md). Include the
   absolute skill path, permitted changes, check commands and root callback.
   For a verified ready target, send it once with
   `herdr agent prompt TARGET BRIEF --wait --timeout 30000` to observe activity
   before settling. Never add `--wait` to a worker's callback.
6. Monitor that submission; do not send the brief again. If the tool yields a
   running session, join it through its session monitor. For work already
   submitted without waiting, use a bounded wait and correlate this job's
   activity/output. On timeout inspect recent/visible output and process
   state. Track this job's handback, not any old completion in the buffer.
7. Read the result and inspect the actual files and check outputs. Do not accept
   “done” as evidence. Resolve fixes in the same owned session when possible.
8. When review is warranted, pair an independent read-only reviewer with the
   task tab. Freeze the candidate; keep the author available for assigned fixes.
9. Deliver or integrate only within the user's authority. Close finished owned
   panes using [cleanup](lifecycle-and-cleanup.md); preserve undelivered files.

A callback can arrive while root is busy. The worker sends without `--wait` and
then yields. Root consumes it at the next tool boundary and checks the result.
Do not make the worker wait for root's turn to finish.

## Several jobs

Keep a small ledger in existing task state: job ID, owned pane/tab, harness,
checkout, writer/reviewer role, pending message, latest result and next action.
A short todo is enough; do not require an Advanced schema for ordinary work.

- Independent read-only jobs may share a checkout in separate tabs.
- Concurrent writes to the same repo need isolated, parent-linked worktrees.
- A coupled change stays with one whole-change writer even across many files.
- Choose concurrency from observed capacity and quotas, including internal
  `/teamwork-preview` agents. There is no fixed Simple job limit.
- Review a ready candidate while other independent work continues; do not wait
  for the entire group before looking at any result.
- If capacity is insufficient, serialize. This does not switch to Advanced.

## Escalation decision

Offer Advanced only when delegated scheduling or durable multi-stage recovery
would concretely help. Explain that it adds one Codex/Claude EM and state/report
handling. Until the user chooses it, keep directly supervising. If chosen, adopt
verified existing jobs into the Advanced ledger instead of duplicating them.
