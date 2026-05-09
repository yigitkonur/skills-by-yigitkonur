# error-strategy — errors an agent can parse and recover from

Errors are the hard part. A tool the agent uses confidently has retry-friendly error envelopes; a tool the agent abandons after one failure does not. Distinguish transient from permanent. Surface the next action. Schema-version the envelope. Source: `optimize-agentic-mcp/patterns/error-handling.md` (9 patterns), `optimize-agentic-cli/references/output-contracts.md` (error section), and `optimize-agentic-cli/references/execution-patterns.md` (retry-safe section).

## Universal principles

### Distinguish transient from permanent — every time

The first thing an agent reads from an error is "should I retry?" If the answer requires interpretation, the agent will guess wrong. Make the answer explicit.

```json
{ "ok": false, "error": { "class": "...", "retryable": true, "retry_after": 30 } }
```

```json
{ "ok": false, "error": { "class": "...", "retryable": false, "next_action": "stop" } }
```

A boolean `retryable` field is the minimum. Pair with `retry_after` for rate-limit / transient. Pair with `next_action` or `suggestion` for permanent errors so the agent has somewhere to go.

### Always include a machine-readable error code

Free-text error messages don't survive translation; codes do. The agent should be able to switch on the code without parsing English.

```json
{
  "error": {
    "class": "validation",
    "code": "INVALID_DATE_FORMAT",
    "message": "Date '2026-13-45' is not a valid ISO 8601 date.",
    "field": "deadline",
    "expected": "YYYY-MM-DD",
    "retryable": false
  }
}
```

Code conventions: `SCREAMING_SNAKE_CASE`. Stable across versions within the same `class`. Document them in the tool description or `--help`.

### Always include a human message AND a `next_action` hint

The message tells the agent what went wrong. The `next_action` hint tells the agent what to do next. Both are required:

```json
{
  "error": {
    "class": "conflict",
    "code": "RESOURCE_EXISTS",
    "message": "Issue 'fix-login-bug' already exists at /issues/143.",
    "retryable": false,
    "next_action": {
      "kind": "fetch_existing",
      "command": "myco get-issue 143 --json",
      "tool": "get_issue",
      "args": { "issue_id": "143" }
    }
  }
}
```

The `next_action` shape adapts to the surface — for CLI it includes the next command line; for MCP it names the tool and args. Either way, the agent doesn't have to guess.

### Never use protocol errors for business logic

The most common MCP failure mode: throwing a JSON-RPC protocol error (`-32xxx` codes) when the actual problem is "user not found" or "invalid input." The LLM never sees these — the client typically swallows them. From `optimize-agentic-mcp/patterns/error-handling.md` Pattern 1:

```json
// BAD — protocol error for business failure; LLM never sees the message
{ "jsonrpc": "2.0", "id": 1, "error": { "code": -32603, "message": "User not found" } }

// GOOD — tool-call error; appears in result content; LLM can recover
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [{
      "type": "text",
      "text": "User 'alice' not found. Available users: alice2, alice_co, alice.eng. Try search_users(query='alice') for fuzzy match."
    }],
    "isError": true
  }
}
```

CLI parallel: never use exit code 1 for everything. Map business errors to semantic exit codes (see `../cli/exit-codes.md`) and put the structured error in the JSON envelope on stdout. Stderr can carry the human-readable summary.

### Surface hidden constraints

If the failure is caused by a constraint the agent doesn't know about, the message should say so. Constraints the agent can't see become invisible walls.

Bad: "Invalid input"
Good: "deadline=2024-07-31 is in the past. The schedule_meeting tool requires a future date. Today is 2026-05-08; pass a date after that."

The good form embeds the rule (must be future), the current state (today's date), and the corrective action (pass a later date). The agent can repair without guessing.

### Embed recovery tool names in error messages

When a tool fails because of a state-change prerequisite, name the tool that resolves it:

```json
{
  "error": {
    "class": "conflict",
    "code": "INSTANCE_RUNNING",
    "message": "Cannot terminate instance i-abc123 while it is running. Call stop_instance(instance_id='i-abc123') first, then retry terminate_instance(instance_id='i-abc123').",
    "retryable": false,
    "next_action": { "tool": "stop_instance", "args": { "instance_id": "i-abc123" } }
  }
}
```

The agent now has the exact tool name AND the exact args to pass. Don't make the agent figure out what to call.

### Use "preventive" framing, not "punitive" framing

When a tool catches bad input before executing, it *prevented* a problem — it didn't *fail*. Wording shapes the agent's behavior. From `optimize-agentic-mcp/patterns/error-handling.md` Pattern 6:

Bad — punitive:
```
"Error: invalid date. Operation canceled."
```

Good — preventive:
```
"Caught early: 2023-11-15 is in the past. schedule_meeting requires a future date.
Use a date after 2026-05-08 and retry: schedule_meeting(date='2026-06-01', ...)"
```

The flag (`isError: true`) tells the protocol something went wrong. The text tells the agent whether to feel bad about it or just adjust one parameter. The text matters more than the flag.

### Avoid "not found" framing — return what exists

"X not found" anchors the LLM on failure. From `optimize-agentic-mcp/patterns/error-handling.md` Pattern 7:

Bad: `"Module 'color' not found."`
Good: `"Available modules: fs, http, path, crypto. Pick one and retry."`

The agent reads a menu and picks. No drama, no failure-recovery loop. Same principle for users, files, endpoints.

### Bound retries — include a fallback

Unbounded retry guidance traps the agent in loops. Always include a limit and a fallback:

```json
{
  "error": {
    "class": "transient",
    "code": "PAYMENT_PROCESSING_FAILED",
    "message": "Payment processing temporarily failed (attempt 2/3). Retry in 5s.",
    "retryable": true,
    "retry_after": 5,
    "attempt": 2,
    "max_attempts": 3,
    "fallback_after_max": "Ask the user to complete payment manually at https://co.com/pay/{order_id}"
  }
}
```

After max attempts, surface the fallback path (manual escalation, alternate tool, human-in-loop). The agent shouldn't loop indefinitely.

## The 6-category taxonomy

Every error fits one of six categories. Pick the right one — the agent's recovery behavior depends on it.

| Class | Retryable | Agent behavior |
|---|---|---|
| **validation** | No | Repair input and resubmit. The agent has the data to fix. |
| **auth** | No | Escalate. The agent doesn't have the data to fix; the user does. |
| **not-found** | No | Disambiguate. Agent narrows or retries with a different ID. |
| **conflict** | No | Re-read state and decide. Force flag, alternate name, or surface to user. |
| **transient** | Yes (with backoff) | Retry with exponential backoff + jitter; respect `retry_after`. |
| **permanent** | No | Stop. Report to user. Don't loop. |

Each category has a canonical bad-vs-good error pair, side-by-side for both surfaces.

### validation — the agent can repair

The input was malformed. The agent has everything needed to fix it; tell the agent exactly what.

CLI bad:
```
$ myco apply --file deploy.yaml
Error: invalid input
exit 1
```

CLI good:
```json
{
  "ok": false,
  "error": {
    "class": "validation",
    "code": "MISSING_REQUIRED_FIELD",
    "message": "Field 'replicas' is required for service 'web'.",
    "field": "spec.replicas",
    "file": "deploy.yaml",
    "line": 12,
    "expected": "integer >= 1",
    "retryable": false,
    "suggestion": "Add 'replicas: <count>' to the service spec at line 12."
  },
  "schema_version": "1"
}
```
exit 6 (validation)

MCP bad:
```json
{ "content": [{"type":"text","text":"Invalid input"}], "isError": true }
```

MCP good:
```json
{
  "content": [{
    "type": "text",
    "text": "Field 'priority' must be one of [0,1,2,3,4]: 0=No priority, 1=Urgent, 2=High, 3=Normal, 4=Low. You sent 'urgent'. Retry with priority=1."
  }],
  "structuredContent": {
    "error": {
      "class": "validation",
      "code": "INVALID_ENUM_VALUE",
      "field": "priority",
      "received": "urgent",
      "expected": [0,1,2,3,4],
      "retryable": false
    }
  },
  "isError": true
}
```

### auth — the agent must escalate

Token expired, scope missing, no permission. The agent typically can't fix this; surface it cleanly.

CLI:
```json
{
  "ok": false,
  "error": {
    "class": "auth",
    "code": "TOKEN_EXPIRED",
    "message": "Auth token expired at 2026-05-08T09:00:00Z.",
    "retryable": false,
    "suggestion": "Re-run: myco auth login --json"
  }
}
```
exit 4 (auth)

MCP:
```json
{
  "content": [{
    "type": "text",
    "text": "Auth token expired. The agent cannot recover this without user action. Ask the user to re-authenticate via https://co.com/oauth/refresh."
  }],
  "structuredContent": {
    "error": {
      "class": "auth",
      "code": "TOKEN_EXPIRED",
      "expired_at": "2026-05-08T09:00:00Z",
      "retryable": false,
      "human_action_required": "https://co.com/oauth/refresh"
    }
  },
  "isError": true
}
```

### not-found — the agent disambiguates

The resource doesn't exist or doesn't match. Don't say "not found" — list what does exist so the agent picks the closest.

CLI:
```json
{
  "ok": false,
  "error": {
    "class": "not_found",
    "code": "RESOURCE_NOT_FOUND",
    "message": "No order matches 'ord_xyz'. Closest matches: ord_xy (Acme Inc), ord_zy (Beta Corp).",
    "retryable": false,
    "suggestion": "Retry with one of the suggested IDs, or call myco list-orders --json to browse."
  }
}
```
exit 3 (not_found)

MCP:
```json
{
  "content": [{
    "type": "text",
    "text": "Available users: alice, bob, carol. Pick one and retry assign_issue(assignee='<user>')."
  }],
  "structuredContent": {
    "error": {
      "class": "not_found",
      "code": "USER_NOT_FOUND",
      "received": "alic",
      "available": ["alice","bob","carol"],
      "retryable": false
    }
  },
  "isError": true
}
```

### conflict — re-read state and decide

The resource exists in a state incompatible with the request. The agent re-reads, then chooses: alternate name, force flag, or escalate.

CLI:
```json
{
  "ok": false,
  "error": {
    "class": "conflict",
    "code": "RESOURCE_EXISTS",
    "message": "Resource 'web' already exists in deployment 'prod'.",
    "existing_id": "res_abc123",
    "retryable": false,
    "suggestion": "Use --force to overwrite, or rename: myco apply --file deploy.yaml --rename web=web-v2."
  }
}
```
exit 5 (conflict)

MCP:
```json
{
  "content": [{
    "type": "text",
    "text": "Issue 'fix-login' already exists at /issues/143 (status=open). Either fetch it via get_issue(issue_id='143') and update, or create with a different title."
  }],
  "structuredContent": {
    "error": {
      "class": "conflict",
      "code": "ISSUE_EXISTS",
      "existing_issue_id": "143",
      "existing_status": "open",
      "retryable": false,
      "next_actions": [
        { "tool": "get_issue", "args": { "issue_id": "143" } },
        { "tool": "create_issue", "args": { "title": "<new_title>" } }
      ]
    }
  },
  "isError": true
}
```

### transient — retry with backoff

Rate limit, timeout, network blip, upstream 5xx. Tell the agent how long to wait.

CLI:
```json
{
  "ok": false,
  "error": {
    "class": "rate_limit",
    "code": "RATE_EXCEEDED",
    "message": "Rate limit exceeded: 100 requests per minute.",
    "retryable": true,
    "retry_after": 45,
    "suggestion": "Wait 45 seconds, or use --rate-limit 50 to throttle.",
    "details": { "limit": 100, "window_seconds": 60, "reset_at": "2026-05-08T10:31:00Z" }
  }
}
```
exit 7 (transient)

MCP:
```json
{
  "content": [{
    "type": "text",
    "text": "Upstream API timed out after 30s. This is transient. Retry in 5s; max 3 retries before surfacing to user."
  }],
  "structuredContent": {
    "error": {
      "class": "transient",
      "code": "UPSTREAM_TIMEOUT",
      "retryable": true,
      "retry_after_ms": 5000,
      "max_attempts": 3,
      "current_attempt": 1
    }
  },
  "isError": true
}
```

### permanent — stop

The error won't be fixed by retry, repair, or alternate ID. Stop and report.

CLI:
```json
{
  "ok": false,
  "error": {
    "class": "internal",
    "code": "INTERNAL_BUG",
    "message": "Unexpected nil pointer in deploy handler. This is a bug; please report.",
    "retryable": false,
    "request_id": "req_abc123",
    "suggestion": "File at https://github.com/co/myco/issues with request_id=req_abc123."
  }
}
```
exit 1 (crash)

MCP:
```json
{
  "content": [{
    "type": "text",
    "text": "Unsupported operation: this server does not support batch deletion. Stop and report to user; this won't be fixed by retry."
  }],
  "structuredContent": {
    "error": {
      "class": "permanent",
      "code": "UNSUPPORTED_OPERATION",
      "retryable": false,
      "human_action_required": "feature_request_or_alternate_workflow"
    }
  },
  "isError": true
}
```

## Combined envelope shapes

### CLI canonical error envelope

```json
{
  "ok": false,
  "schema_version": "1",
  "error": {
    "class": "<one of: validation | auth | not_found | conflict | rate_limit | timeout | network | dependency_failed | internal | partial_success>",
    "code": "<SCREAMING_SNAKE_CASE>",
    "message": "<human-readable, embeds constraints>",
    "retryable": "<bool>",
    "retry_after": "<seconds, only when retryable>",
    "suggestion": "<what to do next>",
    "details": { "<context-specific>": "..." }
  }
}
```

Plus exit code per `../cli/exit-codes.md`.

### MCP canonical error envelope

```typescript
{
  content: [
    { type: "text", text: "<human-readable summary, embeds next action>" }
  ],
  structuredContent: {
    error: {
      class: "validation" | "auth" | "not_found" | "conflict" | "transient" | "permanent",
      code: string,             // SCREAMING_SNAKE_CASE
      message: string,
      retryable: boolean,
      retry_after_ms?: number,
      next_action?: { tool: string; args: Record<string, unknown> },
      suggested_actions?: string[],
      param_hints?: Record<string, string>,
    }
  },
  isError: true
}
```

`isError: true` flags the result; the structured content carries the machine-readable detail; the text carries the agent-facing instruction.

## Anti-patterns to refuse

**Same exit code for every failure.** `os.Exit(1)` for usage errors, validation errors, transient errors, auth errors. The agent has no way to classify; everything looks like "internal crash." Fix by mapping classes to exit codes (see `../cli/exit-codes.md`).

**Free-text error without a code.** `"Error: something went wrong"`. The agent cannot switch on this. Add a code; document the codes.

**Protocol errors for business logic.** Throwing JSON-RPC `-32603` for "user not found" — agent never sees it. Use `isError: true` in result content.

**`retryable: true` with no `retry_after`.** Agent waits 0ms and hammers the upstream. Always pair retryable transient errors with `retry_after`.

**Missing `next_action` on permanent errors.** Agent gets `"Operation canceled"` and gives up. Add the recovery hint — alternate tool, manual fallback, or escalation path.

**Renaming error fields between releases.** `error.message` → `error.detail` mid-version. Stable field names within a version; bump major to change.

**Dumping raw upstream error verbatim.** `"upstream said: 500 Internal Server Error: java.lang.NullPointerException at com.foo.bar.Baz.doStuff(Baz.java:142)"`. Translate to your taxonomy; preserve the upstream detail in `error.details.upstream` for debugging.

**Loop without a budget.** No `max_attempts`, no fallback. Agent loops on transient errors. Bound the retries explicitly.

**`retryable: false` with no actionable hint.** Tells the agent to stop with no path forward. Always pair permanent errors with a `next_action` or `suggestion` — even if it's "escalate to user."

**Loop detection missing on the server side.** Agents can't detect their own loops. Server-side hash-based deduplication (see `optimize-agentic-mcp/patterns/error-handling.md` Pattern 8) catches `update_record(id=42, status="active")` called 5× with identical params and surfaces a "Loop detected — stop retrying and ask the user" error.

## Cross-references

- For exit-code mapping (CLI), read `../cli/exit-codes.md`.
- For idempotency-aware retry semantics, read `idempotency-and-retries.md`.
- For multi-step iterative repair (validation errors with `field` + `suggested_fix`), read `iterative-loops.md`.
- For description-as-prompt principles that pair with error messages, read `descriptions-as-prompts.md`.
- For surface-specific error patterns, read `../mcp/patterns/error-handling.md` (MCP-specific 9 patterns).
