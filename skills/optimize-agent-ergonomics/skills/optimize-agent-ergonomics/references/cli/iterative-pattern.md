# cli/iterative-pattern.md

A CLI that drives a multi-turn agent workflow with validate → repair → advance. The agent submits work, the CLI validates, the CLI returns structured correction guidance, the agent repairs, the workflow advances only when the artifact is acceptable. This file specifies the CLI-specific iterative envelope, the phase taxonomy, the state-token pattern, and a worked schema-migration example. Cross-link to `../common/iterative-loops.md` for the cross-surface principles.

## When to use

Use the iterative pattern when:

- The agent generates an artifact (config, manifest, patch, query) that needs validation before commit.
- A single command can't capture the work — the workflow has stages.
- Partial progress is acceptable and resumable.
- The CLI can give specific, actionable repair feedback.

Do not use this pattern for one-shot lookups, simple CRUD, or anything where a single envelope answers the question. Iterative adds protocol complexity; only invest when the workflow needs it.

## The iterative envelope

Extends the canonical envelope from `output-envelope.md` with six iterative-specific fields:

```json
{
  "ok": false,
  "phase": "validating",
  "progress": { "fields_validated": 3, "total": 5 },
  "validation_errors": [
    {
      "field": "name",
      "problem": "too long (37 chars; max 32)",
      "suggested_fix": "truncate to 32 chars"
    }
  ],
  "next_action": "mytool submit --field name=<truncated> --token=abc123",
  "state_token": "abc123",
  "schema_version": "1"
}
```

Every field's role:

### `phase` (string, required)

The stage of the workflow. The agent reads `phase` to know what kind of feedback to expect and what command to run next.

Standard phases (see Phase taxonomy below for full list):
- `validating` — checking the submitted artifact
- `staging` — artifact accepted, computing the change set
- `applying` — executing the change
- `verifying` — confirming the change took effect
- `complete` — done; the workflow is over
- `failed` — terminal failure; agent should escalate

### `progress` (object, optional)

Quantified progress. Helps the agent know how close the workflow is to completion. Shape is workflow-specific but should be agent-readable:

```json
{"fields_validated": 3, "total": 5}
{"records_applied": 17, "total": 100, "percent": 17}
{"step": 2, "total_steps": 4, "step_name": "schema-migrate"}
```

The two universal keys: a count and a total. Add `step_name` when steps are named, `percent` when convenient.

### `validation_errors` (array, optional)

Present when `phase=validating` and the artifact failed checks. Each entry tells the agent exactly what's wrong with one specific piece of input:

```json
[
  {
    "field": "users[3].email",
    "problem": "missing @ sign",
    "suggested_fix": "add @ between local-part and domain"
  },
  {
    "field": "config.timeout",
    "problem": "must be a positive integer; got -5",
    "suggested_fix": "use a value >= 1"
  }
]
```

Required keys per entry: `field` (string path), `problem` (one-sentence diagnosis), `suggested_fix` (one-sentence remedy).

The CLI MUST return ALL validation errors at once, not one at a time. Returning errors one at a time forces the agent into a thrash loop where each repair surfaces the next error.

### `next_action` (string, required)

A literal command string the agent can paste into a shell, with the state token pre-filled. The agent doesn't have to construct the next call — the CLI already did.

```json
"next_action": "mytool migrate apply --token=abc123"
```

Free-form text is acceptable when the next move isn't a single command:

```json
"next_action": "fix validation errors above, then call `mytool submit` with the same token"
```

Required on every iterative envelope EXCEPT when `phase=complete` or `phase=failed` (terminal states).

### `state_token` (string, required for non-terminal phases)

An opaque continuation token. The client passes it back on subsequent calls; the CLI uses it to resume the workflow from where it left off.

- Opaque to the agent. The agent passes it through; never inspects it.
- Stable: the same token works for the same workflow until the workflow completes or expires.
- Expires: tokens have a TTL (e.g., 1 hour). After expiry, the agent restarts from `init`.

Implementation: the token can be a UUID pointing to server-side state, a signed blob carrying the state inline, or an idempotency key. The agent doesn't care which.

### `schema_version` (string, required)

Same field as the canonical envelope. Increment when the iterative envelope shape changes. See `output-envelope.md`.

## Phase taxonomy

The five canonical phases plus terminal states:

| Phase | Meaning | Agent action |
|---|---|---|
| `validating` | CLI is checking inputs | Wait for response; repair if `validation_errors` returns |
| `staging` | Inputs accepted; CLI is computing the change set | Wait; the staging output is what the agent reviews |
| `applying` | CLI is executing the change | Long-running; agent polls or follows |
| `verifying` | CLI is confirming the change took effect | Short check; agent waits |
| `complete` | Done | Read `result`; workflow ends |
| `failed` | Terminal failure | Escalate; do not retry |

Workflows usually pass through phases in order: `validating` → `staging` → `applying` → `verifying` → `complete`. They may loop back from `validating` (errors found, agent repairs, resubmits). They jump to `failed` from any non-terminal phase if recovery isn't possible.

Custom phases are allowed but discouraged. When the workload needs `seeding`, `replicating`, etc., document them in `--help` and explain when each fires.

## State-token pattern

The state token is the load-bearing primitive of the iterative pattern.

```bash
# 1. agent starts the workflow.
$ mytool migrate init --schema=new.sql --json
{
  "ok": true,
  "phase": "validating",
  "next_action": "mytool migrate validate --token=abc123",
  "state_token": "abc123",
  "schema_version": "1"
}

# 2. agent runs the next step, passing the token.
$ mytool migrate validate --token=abc123 --json
{
  "ok": false,
  "phase": "validating",
  "validation_errors": [{"field": "users.email", "problem": "...", "suggested_fix": "..."}],
  "next_action": "mytool migrate validate --token=abc123 --schema=corrected.sql",
  "state_token": "abc123",
  "schema_version": "1"
}

# 3. agent repairs and re-validates with the same token.
$ mytool migrate validate --token=abc123 --schema=corrected.sql --json
{
  "ok": true,
  "phase": "staging",
  "result": {"would_drop": ["legacy_users"], "would_create": ["users_v2"]},
  "next_action": "mytool migrate apply --token=abc123",
  "state_token": "abc123",
  "schema_version": "1"
}

# 4. agent applies.
$ mytool migrate apply --token=abc123 --json
{
  "ok": true,
  "phase": "complete",
  "result": {"migration_id": "mig_001", "rows_affected": 12450},
  "schema_version": "1"
}
```

The token threads state through the workflow without making the agent track it. Each command emits a token; the agent passes it back unchanged.

## Worked example: schema migration CLI

A CLI that migrates database schemas with agent-driven repair loops.

### Command set

```
mytool migrate init     <schema>     # parse + create state token
mytool migrate validate <--token>    # static checks; return errors or advance
mytool migrate apply    <--token>    # execute migration; return progress + complete
mytool migrate verify   <--token>    # confirm rows / constraints; advance to complete
mytool migrate status   <--token>    # query current phase without changing state
```

Each subcommand accepts and returns the iterative envelope.

### Walk-through

**Step 1: agent submits a schema**

```bash
mytool migrate init --schema=new.sql --json
```

Response:

```json
{
  "ok": true,
  "phase": "validating",
  "progress": {"step": 1, "total_steps": 4, "step_name": "init"},
  "next_action": "mytool migrate validate --token=mig-2026-05-08-abc",
  "state_token": "mig-2026-05-08-abc",
  "schema_version": "1"
}
```

**Step 2: agent validates**

```bash
mytool migrate validate --token=mig-2026-05-08-abc --json
```

Response (errors found):

```json
{
  "ok": false,
  "phase": "validating",
  "progress": {"step": 1, "total_steps": 4, "step_name": "init"},
  "validation_errors": [
    {
      "field": "users.email",
      "problem": "column type 'TEXT' incompatible with existing UNIQUE INDEX",
      "suggested_fix": "use VARCHAR(255) or drop the index first"
    },
    {
      "field": "orders.user_id",
      "problem": "FK references users.id but users.id changed type",
      "suggested_fix": "add ALTER COLUMN users.id ... before this migration"
    }
  ],
  "next_action": "fix the schema and re-run mytool migrate validate --token=mig-2026-05-08-abc --schema=corrected.sql",
  "state_token": "mig-2026-05-08-abc",
  "schema_version": "1"
}
```

The agent reads `validation_errors`, edits the schema file (using its own tools), and resubmits.

**Step 3: agent re-validates**

```bash
mytool migrate validate --token=mig-2026-05-08-abc --schema=corrected.sql --json
```

Response (passing):

```json
{
  "ok": true,
  "phase": "staging",
  "progress": {"step": 2, "total_steps": 4, "step_name": "stage"},
  "result": {
    "summary": {
      "tables_created": 1,
      "tables_dropped": 0,
      "indexes_modified": 2,
      "estimated_rows_affected": 12450
    }
  },
  "next_action": "mytool migrate apply --token=mig-2026-05-08-abc",
  "state_token": "mig-2026-05-08-abc",
  "schema_version": "1"
}
```

The agent reviews the staged change, optionally surfaces the summary to the user, and proceeds.

**Step 4: agent applies**

```bash
mytool migrate apply --token=mig-2026-05-08-abc --json --stream
```

Streaming response:

```ndjson
{"phase": "applying", "progress": {"step": 3, "total_steps": 4, "percent": 0}}
{"phase": "applying", "progress": {"step": 3, "total_steps": 4, "percent": 50}}
{"phase": "applying", "progress": {"step": 3, "total_steps": 4, "percent": 100}}
{"ok": true, "phase": "verifying", "progress": {"step": 4, "total_steps": 4}, "next_action": "mytool migrate verify --token=mig-2026-05-08-abc", "state_token": "mig-2026-05-08-abc", "schema_version": "1"}
```

**Step 5: agent verifies**

```bash
mytool migrate verify --token=mig-2026-05-08-abc --json
```

Response (terminal):

```json
{
  "ok": true,
  "phase": "complete",
  "result": {
    "migration_id": "mig_001",
    "rows_affected": 12450,
    "duration_ms": 4200,
    "verification": "all FK constraints satisfied, all indexes valid"
  },
  "schema_version": "1"
}
```

No `next_action` — the workflow is over. No `state_token` — the token is now invalid (the workflow completed).

## Single-command-with-`--phase` alternative

Some CLIs collapse the per-phase subcommands into one command driven by `--phase`:

```bash
mytool migrate --phase=init --schema=new.sql
mytool migrate --phase=validate --token=...
mytool migrate --phase=apply --token=...
mytool migrate --phase=verify --token=...
```

Trade-offs:

- Pro: smaller surface; one command, one help page.
- Con: less self-documenting; agent has to know the phase enum.
- Pro: easier to add new phases without new subcommands.
- Con: harder to do per-phase auth or tab-completion.

Pick subcommands for workflows with stable phase counts. Pick `--phase` for workflows that may grow new phases over time.

## Repair budget

The agent shouldn't loop forever. The CLI bounds the loop with a repair budget — a count of how many times the same token can be resubmitted before the workflow forces `phase=failed`.

```python
state.attempt += 1
if state.attempt > state.max_attempts:
    emit({
        "ok": False,
        "phase": "failed",
        "error": {
            "code": "REPAIR_BUDGET_EXHAUSTED",
            "message": f"after {state.max_attempts} attempts, validation still failing",
            "next_action": "human review required; the schema may have a structural issue"
        },
        "state_token": state.token,
        "schema_version": "1"
    })
    sys.exit(6)
```

Default budget: 3 attempts for validation phases, 1 for apply/verify (those should succeed on the first try; if they don't, escalate).

The budget appears in `progress` so the agent can see its remaining attempts:

```json
"progress": {"step": 2, "total_steps": 4, "attempt": 2, "max_attempts": 3}
```

## Stable identifiers across iterations

The state token is one identifier. Inside the workflow, ALL identifiers must be stable across iterations:

- The same artifact (e.g., `users` table) keeps the same `field` value across calls.
- Validation errors for the same problem keep the same `problem` text — agents diff successive responses to track repair progress.
- Phase transitions are monotonic: never go from `staging` back to `validating` without a new submission.

Drift in any of these breaks the agent's ability to reason about progress.

## Anti-patterns

- **Returning errors one at a time.** Each repair surfaces the next error; agent thrashes. Fix: return ALL `validation_errors` at once.
- **No state token.** Agent has to repackage the entire context on each call. Fix: opaque continuation tokens.
- **Token that is actually a transcript.** Agent inspects the token and drifts. Fix: opaque, signed, or UUID; never structured.
- **No `next_action`.** Agent guesses. Fix: literal command string in `next_action`.
- **No phase taxonomy.** Agent has no idea where it is in the workflow. Fix: standard phases.
- **Phase regressing.** `phase=staging` followed by `phase=validating` without a new submission. Fix: monotonic phases.
- **Infinite repair budget.** Agent loops forever on a bad input. Fix: cap and emit `phase=failed` on exhaustion.
- **Tokens that don't expire.** Stale state accumulates. Fix: TTL of 1h–24h, document it.

## Cross-references

- `output-envelope.md` — the canonical envelope this file extends.
- `exit-codes.md` — exit 6 (validation) and 7 (transient) drive the loop; exit 0 (complete) terminates.
- `flags-and-discovery.md` — `--phase`, `--token`, `--stream` flags used by iterative commands.
- `architect-new.md` — when to choose iterative for a new CLI.
- `subprocess-harness.md` — how the harness loops through iterative responses.
- `../common/iterative-loops.md` — cross-surface iterative principles (CLI + MCP).
