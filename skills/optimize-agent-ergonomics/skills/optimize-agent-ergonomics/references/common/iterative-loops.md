# iterative-loops — multi-turn workflows where the agent submits, the tool validates, and the agent repairs

Some workloads can't fit in one call. The agent submits an artifact, the tool validates, returns structured correction guidance, the agent repairs, the tool advances. The same shape works on both surfaces. This file owns the cross-surface envelope, the universal field set, the phase taxonomy, and the repair-budget rules. Surface specifics live in `../cli/iterative-pattern.md` (CLI envelope on stdout) and `../mcp/patterns/agentic-patterns.md` (MCP session-scoped state).

## When the iterative pattern earns its cost

Use it when:

- The agent generates an artifact that has to clear validation before commit (config, manifest, patch, query, schema).
- A single command can't capture the work — the workflow has stages.
- Partial progress is acceptable and resumable.
- The tool can give specific, actionable repair feedback (`validation_errors[]` with field paths and suggested fixes).
- A failure mid-workflow shouldn't force restart from zero.

Skip it when:

- The work is a one-shot read or a single mutation. Adding `phase` and `state_token` to a `get-order` tool is over-engineering.
- The agent doesn't need to repair — it either succeeds or fails permanently.
- The validation rules are so simple that one round-trip suffices.

The iterative envelope adds protocol weight. Pay that weight only when the workflow needs it.

## The 5 universal fields

Every iterative response — CLI or MCP — carries the same five load-bearing fields. Surface formatting differs; semantics do not.

### `phase` (string, required)

The stage of the workflow. The agent reads `phase` to know what kind of feedback to expect and what to run next.

- **Required on every iterative response.** Even on terminal phases (`complete` / `failed`), `phase` tells the agent the workflow is over.
- **Monotonic forward** — never regress. Going from `staging` back to `validating` without a new submission breaks the agent's progress tracking.
- **Drawn from the standard taxonomy below.** Custom phases are allowed but discouraged; if added, document them in the tool's description or `--help`.

### `progress` (object, optional but recommended)

Quantified progress. Helps the agent know how close the workflow is to completion.

```json
{"step": 2, "total_steps": 4, "step_name": "stage"}
{"records_applied": 17, "total": 100, "percent": 17}
{"fields_validated": 3, "total": 5, "attempt": 2, "max_attempts": 3}
```

Universal keys: a count and a total. Add `step_name` when steps are named. Add `attempt` / `max_attempts` to surface the repair budget (see Repair budget below). Add `percent` only when the calculation is meaningful (don't fake-percent a step counter).

### `validation_errors` (array, present when `phase=validating` failed)

When the artifact fails checks, the tool returns ALL violations in one response. Each entry has three required keys.

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

| Key | Required | Content |
|---|---|---|
| `field` | yes | Path to the offending field; agent uses it to locate the fix site |
| `problem` | yes | One-sentence diagnosis ("missing @ sign", not "invalid input") |
| `suggested_fix` | yes | One-sentence remedy the agent can act on |
| `received` | optional | The bad value the agent sent — useful when the path alone isn't enough |
| `expected` | optional | The constraint that was violated (regex, enum, range) |

Return ALL errors at once. One-error-at-a-time forces the agent into a thrash loop where each repair surfaces the next error.

### `next_action` (string or object, required for non-terminal phases)

What the agent does next. Shape varies by surface; semantics are identical.

CLI: a literal command string with the state token pre-filled.

```json
"next_action": "mytool migrate apply --token=abc123"
```

MCP: a tool name and args object.

```json
"next_action": {
  "tool": "migrate_apply",
  "args": {"state_token": "abc123"}
}
```

Free-form text is acceptable when the next move isn't a single call (e.g., "fix the validation errors above, then resubmit"). Required on every iterative response EXCEPT `phase=complete` or `phase=failed` (terminal states have no next action).

### `state_token` (string, required for non-terminal phases)

An opaque continuation token. The agent passes it back unchanged on the next call; the tool uses it to resume the workflow from where it left off.

- **Opaque to the agent.** The agent passes it through; never inspects it.
- **Stable** — the same token works for the same workflow until completion or expiry.
- **Expires** — TTL of 1h–24h depending on workflow lifetime. Document the TTL in the description.
- **Implementation-agnostic.** Can be a UUID pointing to server-side state, a signed blob carrying state inline, or an idempotency key. The agent doesn't care which.

On terminal phases (`complete` / `failed`), the token is no longer valid; omit it or mark it expired.

## Phase taxonomy — the 6 canonical phases

| Phase | Meaning | Agent action |
|---|---|---|
| `validating` | Tool is checking the submitted artifact | Wait for response; repair if `validation_errors` returns |
| `staging` | Artifact accepted; tool computed the change set; agent reviews | Read the staged change; proceed when ready |
| `applying` | Tool is executing the change | Long-running; agent polls or follows progress events |
| `verifying` | Tool is confirming the change took effect | Short check; agent waits for the verdict |
| `complete` | Done | Read `result`; workflow ends; token expired |
| `failed` | Terminal failure | Escalate; do not retry; token expired |

Workflows usually pass through phases in order: `validating` → `staging` → `applying` → `verifying` → `complete`. They may loop back from `validating` (errors found, agent repairs, resubmits). They jump to `failed` from any non-terminal phase if recovery isn't possible.

A 7th phase `paused` exists in some workflows for human approval gates — the tool stops at `paused`, waits for an explicit `resume` call, then advances. Use sparingly; most workflows don't need it.

## Surface mappings

### CLI — envelope-extended single-shot or NDJSON stream

The CLI iterative envelope extends the canonical envelope from `../cli/output-envelope.md`:

```json
{
  "ok": false,
  "phase": "validating",
  "progress": {"fields_validated": 3, "total": 5, "attempt": 2, "max_attempts": 3},
  "validation_errors": [
    {
      "field": "users.email",
      "problem": "missing @ sign",
      "suggested_fix": "add @ between local-part and domain"
    }
  ],
  "next_action": "mytool migrate validate --token=abc123 --schema=corrected.sql",
  "state_token": "abc123",
  "schema_version": "1"
}
```

Long-running phases (`applying`, `verifying`) stream progress as NDJSON — one event per line, `flush=True` after each:

```ndjson
{"type": "progress", "phase": "applying", "percent": 0}
{"type": "progress", "phase": "applying", "percent": 50}
{"type": "progress", "phase": "applying", "percent": 100}
{"ok": true, "phase": "verifying", "next_action": "mytool migrate verify --token=abc123", "state_token": "abc123", "schema_version": "1"}
```

The terminal envelope ends the stream. Progress events MUST NOT carry `ok` — only the terminal envelope does. Cross-link `../cli/iterative-pattern.md` for the full CLI envelope deep dive.

### MCP — session-scoped state plus structured content

MCP iterative tools return the same fields inside `structuredContent`, with `isError` set per phase outcome:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Validation failed on 1 field. Run validate again with the corrected input. Token: abc123."
    }
  ],
  "structuredContent": {
    "phase": "validating",
    "progress": {"fields_validated": 3, "total": 5, "attempt": 2, "max_attempts": 3},
    "validation_errors": [
      {
        "field": "users.email",
        "problem": "missing @ sign",
        "suggested_fix": "add @ between local-part and domain"
      }
    ],
    "next_action": {
      "tool": "migrate_validate",
      "args": {"state_token": "abc123", "schema": "<corrected>"}
    },
    "state_token": "abc123",
    "schema_version": "1"
  },
  "isError": true
}
```

State persistence options on MCP:

- **Session-scoped** — the MCP session holds workflow state in memory. Token is a session-scoped key. Cleared on disconnect.
- **Server-side persisted** — the token points to a row in a database. Survives reconnects. Required for multi-turn workflows that span sessions.
- **Stateless with token-encoded state** — the token is a signed blob containing the workflow state. No server-side storage. Works at any scale.

Cross-link `../mcp/patterns/agentic-patterns.md` (Pattern 6 — server-enforced workflow stages) and `../mcp/patterns/session-and-state.md` for session-vs-stateless trade-offs.

## Worked example — `migrate-database` on both surfaces

A workflow that migrates a database schema with agent-driven repair loops. Same phases on CLI and MCP; the protocol differs.

### CLI form

```bash
# 1. agent starts the workflow.
$ mytool migrate init --schema=new.sql --json
{
  "ok": true,
  "phase": "validating",
  "progress": {"step": 1, "total_steps": 4, "step_name": "init"},
  "next_action": "mytool migrate validate --token=mig-abc",
  "state_token": "mig-abc",
  "schema_version": "1"
}

# 2. agent validates; tool finds 2 errors.
$ mytool migrate validate --token=mig-abc --json
{
  "ok": false,
  "phase": "validating",
  "progress": {"step": 1, "total_steps": 4, "attempt": 1, "max_attempts": 3},
  "validation_errors": [
    {"field": "users.email", "problem": "TEXT incompatible with UNIQUE INDEX", "suggested_fix": "use VARCHAR(255)"},
    {"field": "orders.user_id", "problem": "FK references users.id which changed type", "suggested_fix": "ALTER COLUMN users.id first"}
  ],
  "next_action": "fix the schema and re-run mytool migrate validate --token=mig-abc --schema=corrected.sql",
  "state_token": "mig-abc",
  "schema_version": "1"
}

# 3. agent repairs and resubmits.
$ mytool migrate validate --token=mig-abc --schema=corrected.sql --json
{
  "ok": true,
  "phase": "staging",
  "progress": {"step": 2, "total_steps": 4, "step_name": "stage"},
  "result": {"summary": {"tables_created": 1, "indexes_modified": 2, "estimated_rows_affected": 12450}},
  "next_action": "mytool migrate apply --token=mig-abc",
  "state_token": "mig-abc",
  "schema_version": "1"
}

# 4. agent applies (streamed).
$ mytool migrate apply --token=mig-abc --json --stream
{"type": "progress", "phase": "applying", "percent": 0}
{"type": "progress", "phase": "applying", "percent": 100}
{"ok": true, "phase": "verifying", "next_action": "mytool migrate verify --token=mig-abc", "state_token": "mig-abc", "schema_version": "1"}

# 5. agent verifies. Terminal.
$ mytool migrate verify --token=mig-abc --json
{
  "ok": true,
  "phase": "complete",
  "result": {"migration_id": "mig_001", "rows_affected": 12450, "duration_ms": 4200},
  "schema_version": "1"
}
```

### MCP form

```typescript
// 1. agent starts.
await client.callTool({name: "migrate_init", arguments: {schema: "<new.sql>"}});
// → structuredContent.phase = "validating", state_token = "mig-abc"

// 2. agent validates. Tool returns isError: true with validation_errors.
await client.callTool({name: "migrate_validate", arguments: {state_token: "mig-abc"}});
// → structuredContent.validation_errors = [...]; agent repairs.

// 3. agent resubmits.
await client.callTool({name: "migrate_validate", arguments: {state_token: "mig-abc", schema: "<corrected>"}});
// → structuredContent.phase = "staging", result.summary = {...}

// 4. agent applies. Server emits MCP progress notifications (advanced protocol).
await client.callTool({name: "migrate_apply", arguments: {state_token: "mig-abc"}});
// → progress notifications during execution; final response: phase = "verifying"

// 5. agent verifies. Terminal.
await client.callTool({name: "migrate_verify", arguments: {state_token: "mig-abc"}});
// → structuredContent.phase = "complete"; token expired.
```

The phases are identical. The validation envelope is identical. The state token threads the workflow on both surfaces. The agent's loop logic — read `phase`, react to `validation_errors`, run `next_action`, pass `state_token` — is portable.

## Repair budget — bound the loop

The agent shouldn't loop forever. The tool bounds the loop with a repair budget — a count of how many times the same token can resubmit before the workflow forces `phase=failed`.

Default budgets:

| Phase | Default max attempts | Rationale |
|---|---|---|
| `validating` | 3 | Most validation issues clear within 2 repairs; 3 is the safety net |
| `staging` | 1 | If staging fails, the artifact has a structural issue; escalate |
| `applying` | 1 | Mid-apply failures require human review (data integrity) |
| `verifying` | 2 | Verification can fail on transient state; 2 covers retries |

When the budget exhausts:

```json
{
  "ok": false,
  "phase": "failed",
  "error": {
    "code": "REPAIR_BUDGET_EXHAUSTED",
    "message": "After 3 attempts, validation still fails. The schema may have a structural issue.",
    "next_action": "human review required",
    "retryable": false
  },
  "schema_version": "1"
}
```

The budget appears in `progress` so the agent can plan:

```json
"progress": {"step": 1, "total_steps": 4, "attempt": 2, "max_attempts": 3}
```

When `attempt == max_attempts` and the next call fails, the workflow advances to `failed`. The agent escalates to the user; it does not retry past the budget.

## Anti-patterns to refuse

- **One error at a time.** Tool returns the first validation failure; agent fixes it; tool returns the next failure. Each repair surfaces the next error; agent thrashes. Fix: return ALL `validation_errors` in one response.
- **No state token.** Agent has to repackage the entire context on each call. Fix: opaque continuation tokens.
- **Token that's actually a transcript.** Agent inspects the token, drifts on internal field names. Fix: opaque, signed, or UUID; never structured.
- **No `next_action`.** Agent guesses. Fix: literal command string (CLI) or tool+args (MCP) in `next_action`.
- **No phase taxonomy.** Agent has no idea where it is in the workflow. Fix: standard phases.
- **Phase regressing.** `phase=staging` followed by `phase=validating` without a new submission. Fix: monotonic phases.
- **Infinite repair budget.** Agent loops forever on a structural issue. Fix: cap attempts; emit `phase=failed` on exhaustion.
- **Tokens that don't expire.** Stale state accumulates; old tokens carry old assumptions. Fix: TTL of 1h–24h; document it in the description.
- **Mixing iterative envelope with non-iterative responses.** A tool that sometimes returns `phase` and sometimes doesn't makes the agent's parser branch on shape. Fix: every iterative response has the iterative shape.
- **Carrying business state in the token.** The token is opaque; the workflow state belongs server-side or in a signed blob, not as plaintext fields the agent could inspect.

## Cross-references

- For the CLI envelope and per-phase commands, read `../cli/iterative-pattern.md`.
- For session-scoped state and per-call permission intersection on MCP, read `../mcp/patterns/agentic-patterns.md` and `../mcp/patterns/session-and-state.md`.
- For the validation-error envelope details, read `error-strategy.md` (validation class).
- For idempotency keys vs state tokens, read `idempotency-and-retries.md`.
- For surface choice when iterative is the requirement, read `decide-surface.md` (state-fulness drives the surface).
- For the full design pass that surfaces an iterative requirement, read `design-thinking.md` (workload type — multi-step orchestration).
