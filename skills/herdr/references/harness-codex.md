# Codex interactive harness

Read for Codex startup, steering and queue decisions. All work stays in a visible
interactive TUI, including reviewers and the Advanced EM.

## Start and identify

Use the chosen profile and `--config 'model_reasoning_effort="EFFORT"'` after the
Herdr `--` separator. Use appropriate native sandbox authority; read-only for a
reviewer, workspace-write for an authorized writer. Never add approval bypasses
by default. Record requested vs natively observed model/effort separately. A new folder
can show trust/continue even when start reports input-ready; complete the
first-folder sequence in event-monitoring.md before submitting the task.

New task briefs use `$herdr (/resolved/absolute/path/herdr/SKILL.md)`, preserved
literally through quoted file-based CLI arguments or subprocess argv. Do not send AGY's `/teamwork-preview` or
`/herdr` parser token to Codex. If skill discovery fails, read the absolute file.

## Verify Herdr transport permissions

The live `workspace-write` worker could edit/check its assigned files but Herdr
reads failed with `Operation not permitted`: the sandbox denied local socket
access. With `approval_policy=never`, scoped escalation was unavailable. This is
a transport/permission blocker, not evidence of a deleted pane or failed task.
Preserve the result and report the callback failure; do not retry identical
commands or guess new IDs.

When interactive approvals are within the assignment's authority, a per-launch
`--ask-for-approval on-request --no-daemon` kept the tested sandbox while enabling
native command-specific approval. The pilot resumed the exact session, approved
only its displayed Herdr reads/callback once, and delivered the callback. No
global config, persistent prefix grant or sandbox bypass was needed. Inspect
each actual command before approving it; do not approve unrelated operations.
If approvals are disallowed, retain terminal/file evidence for the supervisor
and mark delivery blocked. Verify socket access before relying on Codex as EM.

## Immediate steering vs next task

`herdr agent prompt TARGET TEXT` pastes text and Enter. On a working Codex turn,
Enter can steer the current turn at its next opportunity. It does not promise a
separate next turn. Read visible/recent output to confirm actual consumption.

Default for a distinct next task: wait until input-ready, then submit it once.
Track one pending message per target. Never resend because a tool is still busy;
never apply AGY Escape staging to Codex.

## Next-turn queue: capability-gated

Only use this path after a live disposable pilot confirms Tab queues text in the
installed Codex TUI. Help listing `tab` as a key proves transport support only,
not queue behavior. If Tab is unverified or does not work, use the ready-state
path above; do not substitute the CLI `codex queue` command.
The 0.159.2 pilot staged one follow-up with Tab; its distinct reply appeared
after the active phase completed, with a separate turn completion. This is
installed-version evidence, not a guarantee for another build.

On a verified working Codex pane with an empty composer and no modal:

```bash
herdr pane send-text "$PANE_ID" "$TEXT"
```

Read the visible composer and confirm the intended literal text, then:

```bash
herdr pane send-keys "$PANE_ID" tab
```

Inspect the visible pending-message surface and eventual distinct next-turn
consumption. Do not press Enter after Tab as an assumed fallback. If Tab only
changes focus or leaves text in the composer, do not resend/append: reconcile the
staged text, and return to verified readiness before submitting the next task.
If a live pilot disproves this path, remove the queue recipe from the local
instructions and keep ready-state submission. Never claim queue success based
on the key-injection exit code.

## Recovery

Read registry, visible screen and process-info before intervention. Resume the
exact native session only after confirming the old process is dead and the pane
is a shell. Check installed `codex resume --help` for syntax. Preserve scope and
pending delivery; no `codex exec`, noninteractive `codex review`, CLI queue or
hidden runner is a recovery substitute. See event-monitoring.md for bounded
waits and fail-stop rules.
