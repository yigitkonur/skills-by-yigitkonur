# Reporting, interruption, and closure

Use canonical records as the source. Rebuild views/report from records rather
than editing a display to improve its status. A readable partial report is a
useful deliverable; it is not a full campaign PASS.

## Recover before dispatching more work

1. Read campaign `status`, canonical tasks, current target, findings, and the small
   notebook. Inspect actual host handles for running/reserved assignments.
2. For a live worker, reconnect or interrupt it through the host. For an uncertain
   launch, establish whether a context exists before releasing its reservation.
   Record the task interruption and actual termination separately as supported
   by the CLI. Preserve useful draft/log content.
3. Run `reconcile`. It rebuilds derived views and obligations, preserving sealed
   rounds and detecting changed evidence. Do not rename canonical IDs or delete
   failed rounds to get a clean dashboard.
4. Resume only eligible jobs with available resource leases and full retry
   context. A new worker receives a fresh identity; the lineage/attempt allowance
   does not reset. Do not bind two contexts to the same assignment.

On missing artifact, changed hash, wrong target, disk exhaustion, credential/tool
loss, or failed runtime startup, record the corresponding reason and affected
cases. Recover the actual dependency; do not relabel it as an application failure.
For invalid drafts, keep the role/task identity and correct formatting through
the same validator. For changed accepted content, request a new assigned record.

If an accepted verifier lost independence or reviewed the wrong material, withdraw
that verifier task with `task interrupt`, its concrete reason, and `--finished
true` only after its context has stopped. Create a fresh verifier for the same
case/spec/target/round and the same explicit `verification_slot` (`a` or `b`).
Preserve the original execution and artifacts when they remain valid; a review
replacement does not itself require replaying the application. Reconciliation
can seal a new immutable verdict with `supersedes_record_id`; the old review and
verdict remain history, and only the current valid revision supplies proof.

## Build an inspectable report

```bash
node "$AT_CLI" reconcile --campaign "$CAMPAIGN"
node "$AT_CLI" report build --campaign "$CAMPAIGN"
node "$AT_CLI" report serve --campaign "$CAMPAIGN" --port 0
```

Retain the returned path/URL and owned server identity. The report is static HTML
with safe relative artifact copies. Its server binds to `127.0.0.1`; use an owned
tunnel only if the remote inspection client needs one. Inspect the rendered report and representative
links using the available browser or file viewer; record any unavailable visual
check. HTML generation alone does not prove the application tests passed.

The report must show cases and filtering, expected versus observed outcomes,
round history, screenshot previews, JSON/log links, current and historical
source/runtime identity, issue/PR trail, and blocked/out-of-scope coverage. Missing
or stale artifacts and unresolved obligations remain explicit. It must not silently
promote an old PASS to the final target or hide a failed round behind its retry.

Treat all titles, observations, logs, and external text as untrusted content.
Escape HTML and use only validated contained paths. Serve the generated `report/`
directory, never the repository/campaign root. Exclude secrets, `.env`, private
credentials, symlink escapes, and arbitrary file references. Use the Cloudflare
procedure only when remote inspection needs a public HTTP endpoint.

## Closure audit

Dispatch a fresh plan-auditor task with `phase: closure`. Give it the accepted
plan, final target, canonical results, findings, scope decisions, and current
obligations. It checks completeness without executing cases or fixing defects.

Full PASS requires all accepted expectations to have sufficient independent
current-target proof, all required blind reviews to agree, and no pending
execution/review/retest/fix/scope obligation. Accepted NOT_RUN/PARTIAL, exhausted
attempts, unresolved disagreement, or an empty ready queue are not completion.
Out-of-scope exclusions must remain explicit with their decision source.

The final integrated sweep does not grant more corrective attempts. If a lineage
is exhausted, preserve `ATTEMPT_LIMIT`, show the unresolved coverage, and report
the actual partial result. Keep a late historical result without counting it as
current proof.

## Final handoff and cleanup

State final source/target, accepted-case coverage, closure audit outcome,
unresolved blockers/limits, issue/PR links, and report/application inspection
paths/URLs. Distinguish static review, real functional runs, and untested platforms.
Use the user's language in this handoff.

Leave the final app/report runtime available for inspection as required by the
campaign. Stop only owned unused generations and tunnel processes after identity
checks. `runtime stop` and `report stop` preserve records/artifacts. Report how to
stop retained processes; never apply global cleanup or delete shared credentials.
