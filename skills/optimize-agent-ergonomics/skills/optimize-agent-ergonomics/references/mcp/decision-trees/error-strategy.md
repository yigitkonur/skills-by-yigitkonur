# Decision tree — error strategy

Design error responses so the agent can recover. Errors are the primary steering signal — get them right, the agent fixes its own mistake in one turn; get them wrong, the agent abandons the workflow after the first failure. This tree routes by error semantics.

## The one rule

`isError: true` for business-logic failures the LLM must see and act on. **JSON-RPC error codes are reserved for transport, framework, and protocol failures.** The client swallows protocol errors before the LLM ever reads them — using protocol errors for business logic is the most common reason agents fail to recover.

## Decision branches

```
START: What kind of failure is this?
|
+-- Protocol failure (bad JSON, unknown method, server crash, transport break)
|   --> JSON-RPC error code (the only legitimate use)
|   --> The LLM does NOT see this; client surfaces "tool unavailable"
|
+-- Business logic failure (validation, auth, rate-limit, conflict, missing data)
|   --> isError: true + content explaining the failure and the next move
|   |
|   +-- Validation error (input shape, value range, malformed param)
|   |   --> name the offending field; suggest the fix; agent repairs and retries
|   |
|   +-- Auth / permission error
|   |   --> name the missing scope or step-up consent path; agent escalates
|   |
|   +-- Transient (rate limit, upstream timeout, brief outage)
|   |   --> include retry_after_ms; suggest the retry count cap; agent backs off
|   |
|   +-- Permanent (resource doesn't exist, immutable conflict)
|   |   --> state explicitly that retry will not help; suggest alternative tool
|   |
|   +-- Loop detected (agent retried identical call N times)
|       --> server-side circuit breaker; respond "loop detected, ask user"
|
+-- Destructive operation precondition unmet (delete without confirm, send without verify)
    --> guard tool pattern: boolean precondition or token from prerequisite tool
    --> ../patterns/agentic-patterns.md
```

## isError vs protocol error — examples

### Protocol error (correct use)

```json
{ "jsonrpc": "2.0", "id": 7, "error": { "code": -32600, "message": "Invalid Request" } }
```

Client sees this and shows "MCP server unavailable" or similar. Reserved for: malformed RPC, unknown method, server crash, transport break.

### isError business failure (correct use)

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "result": {
    "isError": true,
    "content": [{ "type": "text", "text": "Date '2024-07-31' is in the past. Use a future date and retry." }]
  }
}
```

The LLM reads the content, fixes the input, retries. **The result object is still a successful protocol response — the JSON-RPC layer succeeded; the business operation did not.**

### Anti-pattern (incorrect)

```json
{ "jsonrpc": "2.0", "id": 7, "error": { "code": -32603, "message": "Date is in the past" } }
```

The LLM never sees this. The agent reports "unknown error" to the user and stops.

## Branch detail

### Validation error

Frame as "prevented" when the catch happened **before** execution; frame as "failed" when the operation ran and returned a domain error.

```
{ "isError": true, "content": [
    { "type": "text", "text": "Parameter `email` must be a valid RFC 5322 address. Got 'foo@'. Did you mean 'foo@example.com'?" }
]}
```

Embed the specific value the agent passed and a corrected suggestion when possible. Vague messages ("invalid input") cause the agent to guess.

### Auth / permission error

```
{ "isError": true, "content": [
    { "type": "text", "text": "Missing scope `mcp:write`. Current scopes: ['mcp:read']. Re-authorize with `step_up_consent(scopes=['mcp:write'])` or escalate to the user." }
]}
```

Name the missing scope. Name the recovery path. Don't assume the agent knows your scope vocabulary.

### Transient error

```
{ "isError": true, "content": [
    { "type": "text", "text": "Rate limit hit. Retry after 1500 ms. This is attempt 1/3; after 3 attempts escalate to the user." }
]}
```

Include `retry_after_ms`. Include the attempt count and the cap. **Agents cannot detect their own loops** — server-side enforcement is the only safe choice.

### Permanent error

```
{ "isError": true, "content": [
    { "type": "text", "text": "Order `ord_42` does not exist. Retrying will not help. Try `search_orders(query=...)` if you have partial info, or escalate to the user." }
]}
```

State explicitly that retry is futile. Suggest the alternative tool by name.

### Loop detection

Hash `tool_name + JSON.stringify(params)` server-side. If the same hash fires N times within T seconds (default: 3 calls in 120s), respond:

```
{ "isError": true, "content": [
    { "type": "text", "text": "Loop detected: `delete_record(id='r_42')` called 3x in 120s with no progress. Stop retrying and ask the user for guidance." }
]}
```

This is a server-side defense — agents cannot reliably detect their own loops.

## Destructive-operation guards

Match guard strength to consequences:

| Stakes | Guard | Pattern |
|---|---|---|
| Low (toggle a flag, set a label) | Soft — boolean self-report (`confirmed: true`) | Cheap; trust the agent |
| Medium (modify a record) | Token from a prerequisite tool (`preview_id` from `preview_change`) | Server checks token validity |
| High (delete data, send to many users, run a billable op) | Server re-runs the precondition itself | Don't trust agent state at all |

Deep dive: `../patterns/agentic-patterns.md`, `../patterns/prompt-gates.md`.

## Recovery guidance — embed the next move

Always tell the agent what to do next.

| Bad | Good |
|---|---|
| `"Failed."` | `"Failed: order ord_42 not found. Try search_orders(query=...)"` |
| `"Invalid input."` | `"Invalid `email='foo@'`. Try `foo@example.com`."` |
| `"Permission denied."` | `"Missing scope `mcp:write`. Re-authorize with `step_up_consent(scopes=['mcp:write'])`."` |
| `"Try again."` | `"Rate limited; retry_after_ms=1500. Attempt 1/3."` |

The "next move" is the difference between a tool the agent uses confidently and one it abandons.

## Anti-patterns

- **Protocol errors for business logic.** The LLM never sees them. Use `isError: true`.
- **Vague messages.** "Invalid input" — what input? Use the field name and the value.
- **Unbounded retries.** Always cap. Loops are the #1 cause of cost spikes.
- **Forgetting recovery guidance.** A naked failure tells the agent to give up.
- **Frame mismatch.** A pre-execution catch should read "prevented", not "failed" — or the agent abandons a valid approach.
- **Generic recovery.** "Try again with valid input" — what counts as valid?
- **Trusting the agent on destructive ops.** Soft guards on high-stakes calls is a footgun.

## Cross-references

- Universal error taxonomy across surfaces: `../../common/error-strategy.md`.
- MCP-specific implementation (isError shape, structured failure payloads): `../patterns/error-handling.md`.
- Agentic patterns for guards and confirmation flows: `../patterns/agentic-patterns.md`.
- Prompt gates for approval workflows: `../patterns/prompt-gates.md`.

## When to re-evaluate

- Agent transcripts show repeated identical calls — add or tighten loop detection.
- Agents abandon valid approaches after validation errors — fix framing (likely prevented vs failed).
- Cost spikes from retry loops — tighten the circuit breaker.
- A new destructive tool is added — pick guard strength.
- Auth scopes change — make sure error messages name the new scopes.
