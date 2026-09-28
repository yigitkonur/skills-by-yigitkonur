# CLI, strict YAML, and submission

Run the bundled CLI with Node.js 22 or newer. Resolve the installed skill root
once; use a task-specific variable such as `AT_CLI` for its
`scripts/agentic-tests.mjs`. In this file, `$CAMPAIGN`, `$TASK_ID`, `$DRAFT`, and
`$HANDLE` are exact values returned by the controller/host, not example IDs.

## Command surface

| Command | Required/optional arguments and purpose |
|---|---|
| `doctor` | `[--project PATH] [--setup]`; inspect/setup locked dependencies |
| `init` | `--project PATH --slug SLUG [--mode interactive\|autonomous] [--max-active 20] [--host-capacity N] [--max-attempts 5] [--locale en] [--github-remote origin]` |
| `task create` | `--campaign PATH --request FILE`; allocate task/actor, paths, draft, handoff |
| `task dispatch` | `--campaign PATH --task-id ID`; check eligibility/resources/capacity and reserve |
| `task bind` | `--campaign PATH --task-id ID --handle HANDLE`; bind actual host context |
| `task close` | `--campaign PATH --task-id ID --finished true`; confirm outputs and worker termination |
| `task interrupt` | `--campaign PATH --task-id ID --reason TEXT [--finished true]`; retain interruption; confirm termination only when observed |
| `plan accept` | `--campaign PATH --file PLAN --audit AUDIT`; independent approved audit and frozen DAG/specs |
| `finding decide` | `--campaign PATH --finding-id ID --scope in_scope\|out_of_scope --reason TEXT --source TEXT`; controller records an authorized scope decision, never a verdict override |
| `finding link` | `--campaign PATH --file REQUEST`; link confirmed related roots without discarding their history |
| `submit` | `--campaign PATH --task-id ID --file DRAFT [--check]`; same validation in both modes |
| `reconcile` | `--campaign PATH`; compute verdicts, obligations, current views, notebook |
| `status` | `--campaign PATH`; current target, active counts, blockers, obligations, completion |
| `records` | `--campaign PATH [--record-id ID] [--kind KIND] [--case-id ID] [--round-id ID] [--finding-id ID] [--ready] [--format json\|yaml-stream]` |
| `runtime start` | `--campaign PATH --file ENV_DRAFT`; owned process and declared readiness |
| `runtime inspect` / `runtime stop` | `--campaign PATH --target-id ID`; inspect/stop verified owned generation |
| `runtime recover` | `--campaign PATH --target-id ID --file REQUEST`; allocate a successor and environment task, preserving source/integration lineage |
| `report build` | `--campaign PATH`; static HTML and safe relative artifacts |
| `report serve` | `--campaign PATH [--port 0]`; owned report-only server |
| `report stop` | `--campaign PATH`; stop only that report server |

The CLI performs bookkeeping and validation. It does not launch host agents,
decide evidence semantics, implement a reverse proxy, or grant external access.
Use `--help` for the installed command's syntax; report a mismatch rather than
inventing `run`, `retry`, `approve`, `merge`, or `verify` commands.

`doctor --setup` installs the locked dependencies into a cache outside the
installed skill directory, keyed by the lockfile. It does not use global npm
installation. Optional Mike Farah `yq` is for querying only. The strict parser
rejects duplicate mapping keys, multiple documents, anchors/aliases, custom tags,
merge keys, invalid types, and undeclared fields. Successful `yq` parsing is not
schema or evidence validation. Quote timestamps and ambiguous scalar values.

## Read inputs and generated packets

Plain `required_inputs` strings resolve inside the campaign. Source inputs use
`{base: project, path: src/app.mjs}`; `{base: project, path: .}` names the project
root. Paths are read-only inputs and must remain inside the real project after
symlink resolution. Output paths remain campaign-contained. Source copying is
unnecessary. The generated handoff resolves exact installed/project/campaign
paths and gives role-specific write scopes and commands.

The campaign records its tested project's selected GitHub remote. Use the
generated `github_repository.repository` with `gh --repo`; the installed skill
directory is never a delivery target. Remote drift blocks delivery tasks while
independent local work can continue.

Corrective tasks carry generated `history_basis` and `prior_context`. Preserve
these when reading the packet. Supply the proposed change/hypothesis in the
request; let the controller attach the latest per-case failure and prior delivery
records. If dispatch returns `STALE_RETRY_CONTEXT`, finish/interrupt the unused
task accurately and allocate a fresh packet from current history. Do not edit
the digest or drop old records to force dispatch.

## Recover an owned runtime

Pass a small request file to `runtime recover`; for example:

```yaml
reason: "Readiness failed because the saved probe used the wrong marker."
requested_action: "Correct the readiness probe using the preserved logs, then prepare the same integrated code."
```

The result supplies `task`, `predecessor_target_id`, `successor_target_id`, and
an immutable `recovery` record. Dispatch and bind that task normally. The new
operator edits its generated environment draft and runs `runtime start`.
Optionally supply a `source` object to select an isolated provider/worktree for
the same code. The controller retains the expected revision; startup verifies
actual source identity. Do not use `source` as a free-text citation.

Correct copied argv/cwd, ports, probes, and tool-session attachment to the new
target. Give client-owned sessions a fresh private state directory and session
identity; never attach the successor over the predecessor's session. Accept an
updated target plan and collect fresh evidence before closure. Old records and
readiness logs remain available through the predecessor link.

## Every worker's submission protocol

1. Read the assigned task and generated handoff. Edit the generated draft in
   place; consult the corresponding template for field shapes. Preserve IDs,
   role, timestamps, digests, target/spec identity, and output paths. Do not
   retype opaque values from displayed text. Parse the existing draft and modify
   only result fields, or make a bounded text edit that leaves metadata intact.
   Use a template as a base only when no generated draft exists. Record artifact
   capture times only from actual tool/clock observations.
2. Produce every required output. For an unavailable observation, write the
   explicit gap and reason in the supported result shape. Never invent a file
   reference, expected behavior, or PASS to make the record structurally complete.
3. Validate without publishing:

   ```bash
   node "$AT_CLI" submit --campaign "$CAMPAIGN" --task-id "$TASK_ID" --file "$DRAFT" --check
   ```

4. Read the entire receipt. Correct formatting/contract errors in the draft and
   repeat validation. A repeated identity/role/target error needs a controller
   correction; workers cannot fix it by changing their assigned identity.
5. Publish using the same command without `--check`:

   ```bash
   node "$AT_CLI" submit --campaign "$CAMPAIGN" --task-id "$TASK_ID" --file "$DRAFT"
   ```

6. Retain `record_id`, `submission_status`, `worker_may_finish`, and `next_actions`.
   Finish only when required outputs are accepted and `worker_may_finish` permits
   it. Report blockers honestly. The orchestrator observes host termination and
   closes the task; workers do not close themselves or launch follow-up roles.

The executor does not declare the final result: its accepted receipt carries
`test_verdict: NOT_DECIDED`. Negative reports can be accepted. Missing files that
are claimed as captured evidence are rejected; explicitly declared capture gaps
can be accepted and remain incapable of supporting PASS.

The environment operator is the publication exception: its assigned draft goes
to `runtime start`, which writes the required canonical environment output once.
It does not resubmit that record through `submit`. The orchestrator still checks
the output and actual worker termination before closing its task.

## Honest blocked role results

Feature scouts, scenario authors, planners, plan auditors, diagnosticians, ticket
writers, implementers, and integrators can submit a typed partial/blocked result.
Keep the generated identity fields; omit unavailable success-only fields instead
of inventing an issue URL, commit, diagnosis, or approval. Add:

```yaml
result_status: BLOCKED
blocker:
  reason_code: GITHUB_UNAVAILABLE
  detail: "The requested repository could not be accessed with the available account."
summary: "Ticket preparation is saved; no issue has been created."
artifacts: []
```

Choose the actual supported reason code and use `PARTIAL` when useful assigned
work was completed. Remove unfilled success placeholders from the draft. List
only existing permitted artifacts. Acceptance lets the worker finish; it leaves
a `ROLE_BLOCKED` campaign obligation and cannot authorize downstream success.
Executors use `execution_status` with explicit observation gaps; verifiers use
their per-expectation inconclusive/unassessed results. Environment operators
preserve the runtime command's `FAILED` record and logs. Do not apply this generic
envelope to those three roles.

After restoring the dependency, the controller creates a fresh same-role task
with `replaces_task_id` set to the finished blocked task. Preserve its case and
finding scope. The allocator supplies new output identities where needed; never
overwrite an accepted blocked report or delete its history to clear an obligation.

## Queries and output

Default stdout is machine JSON; logs use stderr. Exit 0 means the command was
accepted, including accepted FAIL reports. Other exits: 2 usage, 3 validation,
4 conflict, 5 dependency/access, 6 I/O/internal. On error, inspect
`error.code`, `error.message`, and `error.details`; `worker_may_finish` is false.
Structured `error.issues` identifies the field/rule, offending property name,
expected or allowed shape, and remedy. `next_actions` explains recovery. Correct
the named draft field; do not guess an enum or echo secret values into a report.

Canonical queries have no hidden truncation. Prefer filtered `records` over
loading an entire campaign into each worker:

```bash
node "$AT_CLI" records --campaign "$CAMPAIGN" --case-id "$CASE_ID" --format json
node "$AT_CLI" records --campaign "$CAMPAIGN" --kind execution --format yaml-stream
node "$AT_CLI" status --campaign "$CAMPAIGN"
```

When optional Mike Farah `yq` is available, the explicit stream output can be
queried directly; its wrapper is removed by the CLI:

```bash
node "$AT_CLI" records --campaign "$CAMPAIGN" --kind execution --format yaml-stream |
  yq '.execution_status'
```

Use YAML streams only for export/query. Submit one strict YAML document per
draft. Read the complete JSON result when deciding success; a filtered query
cannot establish that a campaign has no pending obligations.
