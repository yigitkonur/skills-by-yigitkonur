# Records, identities, and states

The [schema](../schemas/records.schema.json) is the machine contract. This file
defines how to interpret it. Obtain allocated IDs and exact paths from the task
handoff; examples below describe the layout, not permission to choose identities.

## Three file classes

| Suffix | Meaning | Writer |
|---|---|---|
| `*.record.yaml` | Validated canonical record | Controller/CLI publication |
| `*.draft.yaml` | Mutable proposed worker result | Assigned worker |
| `*.view.yaml` | Rebuildable projection | Reconcile/report machinery |

Submit drafts. Preserve accepted worker records and evidence after publication;
corrections receive a new assigned identity/revision. Lifecycle metadata for
campaigns, tasks, findings, and environments is controller-owned. Identical valid submission
content is idempotent; changing accepted content at the same identity conflicts.
Views and a worker's chat summary are not evidence or canonical truth.

The [campaign shape](../assets/templates/campaign.yaml) and
[finding shape](../assets/templates/finding.yaml) are inspection examples for
controller-owned records, not files to submit manually.

## Fixed layout

```text
00-campaign.record.yaml
01-notebook.view.yaml
02-decisions.md
discovery/FT0001-name.record.yaml
plans/P001/{00-scope.md,10-plan.record.yaml,20-audit.record.yaml}
environments/G001/{00-environment.record.yaml,logs/}
tasks/J00001/{00-task.record.yaml,10-handoff.md,draft/}
cases/T0001-slug/
  00-current--PASS.view.yaml
  specs/S001/{01-test-case.md,02-expectations.record.yaml,03-how-to-run.md}
  rounds/R001/
    00-context.record.yaml
    10-execution.record.yaml
    20-verification-a.record.yaml
    21-verification-b.record.yaml
    30-verdict--PASS.record.yaml
    evidences/
findings/F0001-slug/
  00-finding.record.yaml
  10-diagnosis.record.yaml
  20-ticket.record.yaml
  fixes/A001/{10-implementation.record.yaml,20-integration.record.yaml}
report/{index.html,artifacts/}
```

The second verification file exists only when required. Actual outcomes replace
PASS in the derived current marker or sealed verdict filename. IDs/paths do not
change when a mutable task state changes. Keep instructions out of `evidences/`;
it contains captured evidence content only.

## Identity and proof

Every result binds campaign, task/actor, case/spec revision, round, and target as
applicable. Spec acceptance freezes its documents/hashes. The target binds exact
source revision, worktree/fingerprint, runtime generation, and resource setup.
Executors report the assigned identity, not a guessed latest branch name.

The CLI computes artifact hashes during submission. Verifiers record the hash
they inspected and how they inspected it. Changed/missing artifacts invalidate
current proof. A valid late result for its assigned historical target can remain
history; it cannot count for a newer final target. A wrong assigned target is a
validation error, not an acceptable reinterpretation.

## Task lifecycle

`PLANNED` and `READY` describe queued eligibility. `DISPATCHED` reserves capacity
before host launch; `RUNNING` has a bound real handle. `DONE` requires accepted
required outputs and confirmed worker finish. `BLOCKED`, `INTERRUPTED`, and
`CANCELLED` retain why progress stopped. A task's successful submission does not
end its native worker or free its slot by itself.

Close through `task close --finished true` only after observing actual completion.
On interruption, record the reason and inspect whether the worker/processes are
still alive before releasing ownership. Resume with fresh assignments and intact
lineage; never erase a reservation merely to fit more work under the cap.

## Outcome and finding classification

Execution status (`COMPLETED`, `PARTIAL`, `NOT_RUN`) describes what happened.
Verifier expectation verdicts (`PASS`, `FAIL`, `INCONCLUSIVE`, `NOT_ASSESSED`)
describe what the inspected evidence supports. Only reconciliation writes the
aggregate verdict. `ACCEPTED` means structurally admitted, including honest
negative reports; an executor's receipt remains `NOT_DECIDED` for test verdict.

| Finding class | Route |
|---|---|
| `PRODUCT_DEFECT` | Diagnose; ticket only when confirmed and implementation-bound |
| `EXECUTION_ERROR` | Correct execution procedure; fresh executor when necessary |
| `EVIDENCE_GAP` | State missing requirement; collect through fresh executor |
| `EVIDENCE_CONFLICT` | Preserve conflicting observations; investigate before PASS |
| `SPEC_INVALID` | Correct oracle/spec through author and revised plan |
| `ENVIRONMENT_BLOCKER` | Environment operator restores an owned capability |
| `TARGET_DRIFT` | New generation and fresh proof for correct target |
| `VERIFIER_DISAGREEMENT` | INCONCLUSIVE; orchestrator chooses evidence recovery |
| `SIDE_FINDING` | Separate scope decision/confirmation scenario |

Use the supported reason code, such as `MISSING_CREDENTIAL`, `TOOL_UNAVAILABLE`,
`AGENT_ISOLATION_UNAVAILABLE`, `DISK_FULL`, `RUNTIME_START_FAILED`,
`TRANSPORT_UNREACHABLE`, `TUNNEL_PROTOCOL_UNSUPPORTED`, `SOURCE_SELECTION_REQUIRED`,
`GITHUB_UNAVAILABLE`, `MISSING_ARTIFACT`, `EVIDENCE_CHANGED`, `WRONG_TARGET`,
`NOT_EXECUTED`, or `ATTEMPT_LIMIT`. Describe the observed limitation without
guessing worker intent. Keep finding ID/lineage stable across affected tests and
renames; [Scheduling](scheduling.md) owns attempt accounting.
