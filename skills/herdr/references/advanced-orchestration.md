# Advanced orchestration

Read only after the user explicitly chooses Advanced. The topology is root plus
one Codex/Claude Engineering Manager, with visible workers. There is no AGY EM,
managerless Advanced variant or automatic task-size upgrade.

## 1. Establish the manager's authority

Root owns the user's deliverable, mode choice, authority and final verification.
EM owns scheduling, worker registrations, report intake and integration within
that authority. Root remains engaged; “follow only the EM” is not a completion
rule. The manager's findings must lead to actual edits, checks and delivery.

If the EM harness/effort is unspecified, ask once: Codex or Claude, and effort,
with a recommendation from agent-profiles.md. Launch one EM in a new task tab,
using the caller gate, explicit profile, absolute Herdr skill prefix and root
return pane. No hidden leader or additional management layer.

Give the EM the concrete assignment, permitted side effects, existing sessions,
repo/base, owned areas, checks and an absolute run-root outside disposable
worktrees. Advanced does not imply authority to create issues, commit, push,
merge, change settings or operate other projects.

## 2. Register and schedule useful units

Adopt explicitly owned existing jobs before launching replacements. Verify live
pane/tab/terminal/session, cwd, role, pending instruction, current attempt and
callback. Unknown sessions are not adopted solely because they are visible.

Build a dependency list from coherent deliverables and interfaces. Keep coupled
changes with one whole-change writer. Schedule independent ready jobs as capacity
permits; include internal AGY teamwork agents. No fixed wave count, lane minimum,
fleet size or barrier waiting for every job before reviewing one ready candidate.
Create GitHub tickets only if the task authorizes that external action.

Use topology-and-worktrees.md: new tabs for independent jobs, parent-linked
worktrees for concurrent writers, paired review in each task's tab when it fits.
One authorized integration owner lands accepted candidates serially.

## 3. Durable state without message bureaucracy

Use two coordination artifact kinds at the run-root:

- Mutable `state.yaml`, written by the EM alone on meaningful state transitions.
- Immutable producer reports, one uniquely named file per handback, formal review,
  material blocker or recovery/authority decision. Routine Q/A stays native text.

Captured candidate snapshots and check artifacts support those reports; they do
not create another coordination protocol. Keep them at the same preserved
run-root and reference their exact paths/digests.

State records mission/root/EM identity and skill revision; task dependency and
ownership; registered producer runtime/pane/tab/terminal/session; current attempt;
base/candidate; review state; pending dispatch/integration effects; accepted
report IDs/digests; failure count; and the next action. Write an updated temporary
file then atomically replace state. Keep it outside worktrees and avoid multiple
managers writing it.

Save intent before dispatch or integration and acknowledgement after observable
consumption/effect. A successful prompt is only submitted. On interruption,
reconcile the recipient/process/Git result before repeating a pending effect.
Do not dispatch dependencies while unresolved effects remain unaccepted.
For a ready worker assignment, send once with `agent prompt ... --wait
--timeout 30000`; callbacks still omit waiting. Inspect its actual response
before updating delivery state. Never mark submitted unconditionally after a
failed CLI call, or use `sed -i` for checkpoints. A wait timeout can follow
successful delivery: record uncertainty and reconcile without resubmitting.

### Producer report v1

Keep the established field names for existing consumers. JSON-formatted YAML is
an option when no YAML parser exists; a JSON parser cannot validate arbitrary
YAML. Include concrete values, never placeholder successful evidence.

```yaml
schema_version: 1
mission_id: <mission>
task_id: <task>
attempt: 1
report_id: <unique task-attempt-purpose ID>
producer:
  runtime: <agy|codex|claude>
  model: <observed identifier or explicitly unverified>
  role: <implementer|reviewer|integrator|manager|recovery_executor>
  pane_id: <live pane>
  tab_id: <live tab>
  terminal_id: <live terminal>
  session_id: <verified session or null>
  skill_path: <absolute SKILL.md>
  skill_revision: <revision or checksum>
manager:
  pane_id: <EM pane>
  tab_id: <EM tab>
cto:
  pane_id: <root pane>
  tab_id: <root tab>
status: <in_progress|completed|blocked|failed|milestone|registered>
summary: <result>
evidence:
  - command: <actual command>
    exit_code: <actual exit code>
    result: <output or artifact location>
git:
  base: <verified full commit ID, or null for non-Git work>
  head: <verified full commit ID, or null for uncommitted/non-Git work>
  branch: <branch or null>
  worktree: <absolute path or null>
  pr: <number/url or null>
files: ["relative/path/to/changed-file"]
unresolved_effects: []
requested_action: <review|merge|unblock_decision|integrate|none>
```

`files` is an array of checkout-relative path strings; use `[]` for no file
changes. `unresolved_effects` is an array of descriptive strings. IDs, paths,
summary and evidence command/result are strings; evidence exit codes are
integers. Use `.yaml` for the report filename even when its contents are JSON.
Keep `producer`, `manager`, `cto` and `git` as mappings. An unavailable session
or Git value uses actual null, never the string "null".

For an uncommitted candidate keep `git.head: null` and add this mapping:

```yaml
candidate_snapshot:
  path: <absolute captured diff/content path>
  base: <verified full base commit ID, or null for non-Git work>
  sha256: <verified SHA256 of captured bytes>
```

Optional observed HEAD does not identify uncommitted changes. Capture real bytes,
not a successful-looking placeholder. Do not commit merely to satisfy a field.
Give every snapshot a unique path and preserve it once captured. For a Git diff,
this one-operation shell form refuses an existing destination:

```bash
(set -C; git -C "$CHECKOUT" diff --binary > "$SNAPSHOT")
```

On failure inspect the existing artifact; do not overwrite it or notify a new
report as though capture succeeded. Hash the captured bytes only after success.

### Publish and consume

For JSON-formatted YAML, use the bundled
[one-operation publisher](../scripts/publish-report.mjs) instead of rewriting
validation/publication shell code. `SKILL_PATH` is the resolved absolute
SKILL.md supplied in this assignment, never a guessed global installation:

```bash
SKILL_DIR=$(dirname "$SKILL_PATH")
node "$SKILL_DIR/scripts/publish-report.mjs" "$PARTIAL" "$REPORT_PATH"
```

Both paths must be absolute; destination ends in `.yaml`. It validates v1 shape, checkout-relative file paths, full 40/64-hex Git object
ID syntax and any snapshot digest. It reads a regular partial through a
no-follow descriptor, publishes a private copy of those bytes without
overwriting via a hard link, rechecks the snapshot and original partial,
then removes the unchanged partial. It returns path/SHA256 as JSON;
errors exit 1 and retain diagnostic artifacts. A post-publication integrity
error can leave a destination for diagnosis; do not notify or accept it. Keep partial and destination on
the same filesystem. Requires Node.js and a filesystem supporting hard links.
The helper does not send a notice, validate live registry/authority, verify task
correctness or update state. Those remain separate steps below. Extra fields
are allowed; empty command output is a valid evidence result string.

1. Write a unique `.partial` report on the same filesystem as its destination.
2. Validate syntax and required key types/mappings, registered identity, positive
   integer attempt, permitted status and concrete evidence. Compute SHA256.
3. Publish without overwriting: check destination absence, use same-filesystem
   no-clobber publication, then verify source removed, destination present and
   digest unchanged. With `mv -n`, exit 0 alone is insufficient: a collision can
   leave the source. Preserve failed partials; never notify an ambiguous report.
4. Send the EM a notice containing job/attempt, absolute report path and digest
   using `herdr agent prompt TARGET TEXT` without `--wait`, then yield.
   If its approval/question UI rejects the notice, preserve the published report
   and mark notification undelivered; do not manage the EM's UI. EM can discover
   registered unconsumed reports from its run-root during reconciliation.
5. EM verifies path is within run-root, digest and mission/task/producer registry,
   then attempt. Reject obsolete attempts; quarantine unregistered/future ones.
   Compare skill revision to the producer's recorded loaded revision, not the
   current bytes at a path being edited during the run. Record legitimate skill
   drift separately; do not rewrite an immutable report to match a newer file.
6. Same report ID + same digest is an idempotent duplicate: no second dispatch,
   integration or acknowledgement chain. Same ID + different digest is
   `MUTATED_REPORT_REJECTED`; preserve evidence and quarantine.
7. Record consumption separately from technical acceptance. Receipt is not
   review approval. Check files, evidence and unresolved effects before advancing.

Only EM increments attempts. A correction gets a new report ID; prior reports
stay immutable. Old notices and generic terminal “done” cannot advance a task.
When incrementing an attempt, reset the task's current acceptance/completion,
review eligibility and pending dispatch/result for the new attempt. Preserve
old candidate/review/report records and acknowledged effects as history with their
attempt identity;
an old `report_accepted` badge must not qualify the new attempt for scheduling.
Save that transition before accepting new notices. An unchanged file snapshot
alone does not establish completion of the new assigned attempt.
Discover a registered published report from the run-root during reconciliation
even if its notice failed. Normal readiness waits include idle, done and blocked;
do not reconstruct that default as only done/blocked. The live EM did so and
timed out while its producer was actually idle. Verify the exact report rather
than waiting for a preferred badge or repeatedly requesting its callback.

## 4. Review, fixes and integration

Dispatch a fresh independent read-only reviewer as soon as a coherent candidate
is ready. Bind review to verified full base/head commit IDs or an immutable
captured uncommitted snapshot. Freeze the candidate; compare it again at intake.
If it changes, approval expires and the resulting candidate/delta needs review.
Author can clarify intent but cannot approve their own changes.

Review findings identify severity, file/behavior, evidence and required fix.
Keep the author for assigned fixes or explicitly transfer ownership before pane
closure. Do not invent material waivers to turn an unresolved review green.
Two equivalent failed fix/recovery rounds stop automatic retry; ask for the
concrete unresolved decision, without resetting attempts or relaunching a fleet.

Integration occurs only when authorized and after evidence/review gates. Use one
integrator, the current authorized target base and ordinary non-force push.
Rebase/merge changes candidate identity; rerun affected checks and obtain delta
review when behavior changed. A green old SHA is not approval of a new one.

For conflicts: inspect both changes' intent and the recorded bases, resolve with
the owner, stage only resolved paths safely (NUL-delimited paths for spaces), run
the required checks and continue noninteractively where appropriate. If intent
is unclear, preserve the in-progress state and escalate. Never blind `ours/theirs`
or force-push to hide conflicts. Do not check out a target branch already owned
by another worktree.

## 5. Root checkpoints, recovery and closure

EM sends root meaningful milestone/blocker/completion notices without `--wait`.
Root reads the underlying artifacts and requested edits, verifies delivered work
and remaining authority, and returns actual results to the user. Root does not
stop at the EM's summary or create another fleet to “verify” an unconsumed report.

For manager replacement, prove the old manager has relinquished control or is
stopped, preserve state/reports, then adopt verified workers and reconcile only
unconsumed/pending items. No two state writers or duplicate dispatch. Invalid
root/manager pane identity is a routing blocker, not external-supervisor license.

Bounded waits, modals, quotas and pause behavior use event-monitoring.md. Retire
finished owned panes promptly using lifecycle-and-cleanup.md; checkout deletion
and branch retention remain separate. Keep the EM until its remaining intake,
handback and ownership are resolved, then close it too. No global cleanup.
