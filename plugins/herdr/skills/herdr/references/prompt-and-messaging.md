# Prompt and messaging

Read when authoring a task, notifying a supervisor, or reconciling a pending
message. One decision has one pending message per verified target.

## New task brief

Resolve the absolute path of the exact SKILL.md the worker should read. Do not
invent a globally installed path or use the mutable old install when testing a
candidate. Prefix by receiving harness:

| Receiver | Start of a new task brief |
|---|---|
| AGY, difficulty 2–5 | `/teamwork-preview /herdr (/absolute/path/herdr/SKILL.md)` |
| AGY, difficulty 1 | `/herdr (/absolute/path/herdr/SKILL.md)` |
| Claude | `/herdr (/absolute/path/herdr/SKILL.md)` |
| Codex | `$herdr (/absolute/path/herdr/SKILL.md)` |

Then supply this compact authority block in plain language:

```text
Job: <unique job ID>; attempt: <supervisor-assigned attempt>.
Role: writer / read-only reviewer / EM; difficulty: <1–5>.
Checkout: <absolute path>; base: <verified revision, if relevant>.
Goal and completion: <concrete change and expected result>.
Own: <areas>; exclude: <other work and existing edits>.
Authority: <read/write/check/commit/push/PR permissions actually granted>.
Checks: <commands and observable outputs>; report failures honestly.
Return pane: <live supervisor pane>; skill: <resolved absolute SKILL.md>.
Finish: send a detailed result with herdr agent prompt to the return pane,
without --wait, then yield. Include files, checks/exit codes, candidate identity,
unresolved effects, blockers and requested next action.
```

For a reviewer, add exact frozen candidate, review scope and read-only authority.
For an EM, add run-root, root callback and owned worker registrations. Never
include commit/push/merge rights merely because the role is “manager”.

If named skill discovery fails, read the supplied absolute SKILL.md directly.
AGY's `/teamwork-preview` requirement is not an installation approval flow.
If the parser rejects a prefix, inspect the actual error once and correct the
specific discovery/syntax issue; do not repeat the rejected message or silently
remove required context. Do not apply AGY tokens to Codex/Claude.

## Submit without shell expansion

Keep complex briefs in a temporary file outside the checkout, then pass its
contents as one quoted CLI argument. Write the file with a quoted heredoc so
literal dollar signs and backticks stay text:

For example, this is a **Codex** brief. For AGY/Claude use the prefix from
the table above; the quoted shell transport stays the same.

```bash
cat > "$BRIEF_PATH" <<'BRIEF'
$herdr (/resolved/absolute/path/herdr/SKILL.md)
<job scope, authority, checks and verified return pane>
BRIEF
if BRIEF_TEXT=$(cat "$BRIEF_PATH") && test -n "$BRIEF_TEXT"; then
  herdr agent prompt "$TARGET" "$BRIEF_TEXT" --wait --timeout 30000
else
  printf 'Brief unreadable or empty; no submission.\n' >&2
  false
fi
```

This is the controller's one submission to a ready target; callbacks omit the
wait flags. Quoted command substitution does not re-evaluate the file's content.
Do not use `eval` or concatenate it into shell code. Structured subprocess argv
is also suitable when already available. `JSON.stringify` is not shell quoting.
A timeout leaves delivery uncertain: inspect the target before retrying. Brief
files are temporary communication, not new repository deliverables.

## Callback and consumption

Verify the supplied return route with `herdr agent get "$RETURN_PANE"`: the
target is positional. Do not copy `--pane` from process-info onto other
subcommands. The live AGY walkthrough first guessed `pane get --pane` and had
to correct it. For your own identity use `herdr pane current --current`.
Inspect one failed lookup before choosing recovery; no help sweep is needed
when these known forms work.

Workers send a detailed callback, without task prefixes or `--wait`:

```text
JOB <id> ATTEMPT <n>: completed/blocked/failed.
Changes: <files and resulting behavior>.
Evidence: <commands, exit codes and output/artifact paths>.
Candidate: <full commit ID or frozen snapshot identity>.
Unresolved effects: <list or none>.
Next: <review/fix/decision/none>.
```

`herdr agent prompt TARGET TEXT` submits text and Enter. Exit 0 is submission,
not acknowledgement. Distinguish submitted, visibly consumed, acted and verified.
The worker yields after its callback; it never waits for a busy supervisor.
The supervisor verifies job/attempt, producer and actual evidence before acting.
Do not dispatch twice because a callback arrived twice or arrived late.

A working recipient can receive a callback, but a recipient at a question or
approval dialog can reject it with `agent_blocked` before sending any bytes.
Preserve the result/report path and digest, mark the notice undelivered, and
yield. Do not poll, press the supervisor's approval keys, inspect its user's
conversation, or reroute without an explicitly assigned fallback. The supervisor
reconciles registered published reports after resolving its own dialog.

For Simple, the ledger can record the last accepted job result. Advanced uses
immutable reports and the deduplication contract in advanced-orchestration.md.
A callback directed to a deleted pane is a concrete routing blocker: preserve
result evidence, report the failed target, and request a live return route.
Do not route to whichever pane has focus.

## Busy recipient

Read state and the harness recipe before sending follow-ups. Ordinary technical
Q/A and notices need no skill prefixes. Do not stack long tasks into a busy AGY
composer. Codex Enter steering and next-turn queue are distinct; the default is
to send the next task after verified readiness. No unverified queue shortcut.

## Questions during work

A worker's asynchronous question can coexist with ongoing edits. Preserve its
question/options/job identity and send a no-wait notice to the supervisor when
a reply is needed there. Continue only independent work with explicit provisional
values. The supervisor follows event-monitoring.md to inspect the native panel,
obtain the actual user's choice, and verify correlated consumption. A settled
Herdr badge or accepted question-tool call does not clear an unanswered item.
If the turn ends and the panel disappears, retain the question and use a
correlated follow-up answer; never report an invented choice or repeat a task.
