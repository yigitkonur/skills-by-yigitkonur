# CLI, strict YAML, and submission

Run the bundled CLI with Node.js 22 or newer. Resolve the installed skill root
once; use a task-specific variable such as `AT_CLI` for its
`scripts/agentic-tests.mjs`. In this file, `$CAMPAIGN`, `$TASK_ID`, `$DRAFT`, and
`$HANDLE` are exact values returned by the controller/host, not example IDs.

## Command surface

| Command | Required/optional arguments and purpose |
|---|---|
| `doctor` | `[--project PATH] [--setup]`; inspect/setup locked dependencies |
| `init` | `--project PATH --slug SLUG [--mode interactive\|autonomous] [--max-active 20] [--host-capacity N] [--max-attempts 5]` |
| `task create` | `--campaign PATH --request FILE`; allocate task/actor, paths, draft, handoff |
| `task dispatch` | `--campaign PATH --task-id ID`; check eligibility/resources/capacity and reserve |
| `task bind` | `--campaign PATH --task-id ID --handle HANDLE`; bind actual host context |
| `task close` | `--campaign PATH --task-id ID --finished true`; confirm outputs and worker termination |
| `task interrupt` | `--campaign PATH --task-id ID --reason TEXT [--finished true]`; retain interruption; confirm termination only when observed |
| `plan accept` | `--campaign PATH --file PLAN --audit AUDIT`; independent approved audit and frozen DAG/specs |
| `submit` | `--campaign PATH --task-id ID --file DRAFT [--check]`; same validation in both modes |
| `reconcile` | `--campaign PATH`; compute verdicts, obligations, current views, notebook |
| `status` | `--campaign PATH`; current target, active counts, blockers, obligations, completion |
| `records` | `--campaign PATH [--record-id ID] [--kind KIND] [--case-id ID] [--round-id ID] [--ready] [--format json\|yaml-stream]` |
| `runtime start` | `--campaign PATH --file ENV_DRAFT`; owned process and declared readiness |
| `runtime inspect` / `runtime stop` | `--campaign PATH --target-id ID`; inspect/stop verified owned generation |
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

## Every worker's submission protocol

1. Read the assigned task and generated handoff. Copy only the corresponding
   template into the assigned draft path. Preserve all allocated IDs, role,
   target/spec identity, and output paths.
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

## Queries and output

Default stdout is machine JSON; logs use stderr. Exit 0 means the command was
accepted, including accepted FAIL reports. Other exits: 2 usage, 3 validation,
4 conflict, 5 dependency/access, 6 I/O/internal. On error, inspect
`error.code`, `error.message`, and `error.details`; `worker_may_finish` is false.

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
