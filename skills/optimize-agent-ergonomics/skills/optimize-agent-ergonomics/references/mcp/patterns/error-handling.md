# Error handling

How to design MCP error responses that an agent can recover from on the next call. Cross-surface principles — retry-friendly, transient vs permanent, schema-versioned envelopes — live in `../../common/error-strategy.md`. This file is the MCP-specific expression: the `isError` flag, the protocol-vs-result distinction, structured content shapes, and the recovery hints the model reads next.

---

## The `isError: true` + structured content pattern

MCP has two error paths. Picking the wrong one is the most common error-handling mistake and kills agent recovery silently.

**Protocol-level error** — JSON-RPC `error` field. The tool wasn't found, the request was malformed, the server crashed. The LLM **never sees this**. The client swallows it.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": { "code": -32001, "message": "Request Timeout" }
}
```

**Tool-call error** — `isError: true` in `result`. The tool ran but the operation failed. The error text **lands in the LLM's context window**, so the model can reason about it and recover.

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [{
      "type": "text",
      "text": "Cannot terminate instance while it is running. Call stop_instance(instance_id='i-abc123') first, then retry."
    }],
    "isError": true
  }
}
```

The rule: **protocol errors are reserved for transport/framework failures.** Bad JSON, unknown method, server crash — those are the only things that belong in the JSON-RPC `error` field. Every business logic failure — validation errors, permission issues, "resource not found", state conflicts, rate limits — uses `isError: true` so the agent can see the message and try again.

When throwing a protocol-level error for a business failure, the agent gets a generic "tool call failed" with no information to fix the problem. With `isError: true`, the error text becomes part of the conversation and the model adjusts its approach. Source: alpic.ai — "Better MCP tool call error responses" (2025); MCP specification 2025-11-25, Tools.

---

## Educational error messages

Every error message is the documentation **at that moment**. The model has no other source of truth for what went wrong. Treat each one as a teaching surface.

Bad — real example from Supabase MCP:

```json
{ "error": "Unauthorized" }
```

This stops the model cold. It thinks it lacks permissions and gives up.

Good:

```json
{
  "content": [{
    "type": "text",
    "text": "Project ID 'proj_abc123' not found or you lack permissions. Use list_projects() to see available projects, then retry with a valid project_id."
  }],
  "isError": true
}
```

Error message checklist:

1. Name the specific field that caused the failure.
2. State the expected format or valid values.
3. Show an example of correct input.
4. Suggest a recovery action with a specific tool name and arguments.

Helper template:

```python
def format_error(field: str, problem: str, expected: str, recovery_tool: str | None = None, recovery_args: dict | None = None) -> dict:
    msg = f"Parameter '{field}': {problem}. Expected: {expected}."
    if recovery_tool:
        args = ", ".join(f"{k}={v!r}" for k, v in (recovery_args or {}).items())
        msg += f" Recover with {recovery_tool}({args})."
    return {"content": [{"type": "text", "text": msg}], "isError": True}

# Usage
format_error(
    field="start_date",
    problem="Date '2024-07-31' is in the past",
    expected="A future date in YYYY-MM-DD format",
    recovery_tool="schedule_meeting",
    recovery_args={"date": "2025-08-01", "title": "Standup"},
)
```

If the model gets the call right 90%+ of the time, exhaustive descriptions covering every edge case cost more tokens than they save. Errors handle the long tail. Source: u/sjoti on r/mcp (2025-07).

---

## Retry-friendly response: error code + message + `next_action`

For an agent loop, the message alone is not enough. Add a structured taxonomy so the agent can decide programmatically — retry, switch tools, escalate, stop — without parsing free text.

```typescript
return {
  content: [{
    type: "text",
    text: JSON.stringify({
      error_category: "RATE_LIMITED",
      message: "GitHub API rate limit exceeded. Retry after 60s.",
      retryable: true,
      retry_after_ms: 60_000,
      next_action: { tool: "wait_then_retry", args: { delay_ms: 60_000 } },
    }),
  }],
  isError: true,
};
```

The cross-surface taxonomy lives in `../../common/error-strategy.md`. The MCP-specific shape:

| Field | Type | Required | Purpose |
|---|---|---|---|
| `error_category` | string enum | yes | Coarse class (`RATE_LIMITED`, `NOT_FOUND`, `INVALID_INPUT`, `AUTH_FAILED`, `CONFLICT`, `INTERNAL`) |
| `message` | string | yes | Human-readable; same string the model reads in `content[0].text` |
| `retryable` | boolean | yes | The single bit the agent loop branches on |
| `retry_after_ms` | number | when retryable | Honor before retry |
| `next_action` | `{tool, args}` | when applicable | Specific recovery call |

The `retryable` field is the most important. Without it, the agent has to guess from the text whether a second attempt would help — and it usually guesses wrong. Source: alpic.ai (2025); see also `../decision-trees/error-strategy.md`.

---

## Recovery tool names directly in messages

When a tool call fails, name the next call. State-change prerequisites, validation errors, and permission gates are the three patterns that benefit most.

State-change prerequisite:

```python
@tool
def terminate_instance(instance_id: str):
    instance = get_instance(instance_id)
    if instance.state == "running":
        return {
            "content": [{
                "type": "text",
                "text": (
                    f"Instance '{instance_id}' is currently running. "
                    f"Call stop_instance(instance_id='{instance_id}') first, "
                    f"wait for it to reach 'stopped' state, then retry "
                    f"terminate_instance(instance_id='{instance_id}')."
                ),
            }],
            "isError": True,
        }
    # ... proceed
```

Validation with corrected suggestions:

```json
{
  "content": [{
    "type": "text",
    "text": "The requested travel date cannot be in the past. You asked for July 31 2024 but today is May 8 2026. Did you mean July 31 2026?"
  }],
  "isError": true
}
```

Spell out the actual parameter values. Don't make the model figure out what arguments to pass — pass them.

---

## Retry limits and fallbacks

Unbounded retry guidance ("try again") traps models in infinite loops. From the agent's perspective, every retry is a fresh attempt with renewed optimism. Always include a limit and a fallback.

```python
@tool
def process_payment(order_id: str, _retry_count: int = 0):
    try:
        return payment_api.charge(order_id)
    except TransientError:
        if _retry_count >= 2:
            return {
                "content": [{
                    "type": "text",
                    "text": (
                        f"Payment processing failed after 3 attempts for order '{order_id}'. "
                        f"Ask the user to complete payment manually at: "
                        f"https://dashboard.example.com/orders/{order_id}/pay"
                    ),
                }],
                "isError": True,
            }
        return {
            "content": [{
                "type": "text",
                "text": (
                    f"Payment processing temporarily failed (attempt {_retry_count + 1}/3). "
                    f"Call process_payment(order_id='{order_id}', _retry_count={_retry_count + 1}) to retry."
                ),
            }],
            "isError": True,
        }
```

The fallback prevents the model from giving up entirely — it provides a human escalation path. Without limits, some models retry 10+ times, burning tokens and time. Source: alpic.ai; Stainless — "Error Handling and Debugging MCP Servers" (2025).

---

## Loop detection — circuit breakers outside the model

Agents can't detect their own loops. To them, every retry is fresh. Detect loops outside the model's decision-making.

The failure mode: agent calls `update_record(id=42, status="active")`, gets a validation error, "fixes" the call, sends the **identical** parameters, gets the **same** error, repeats indefinitely. The "$63 overnight" agent loop incident on r/AI_Agents (2025) was exactly this.

Hash-based state tracking:

```python
import hashlib
from collections import defaultdict
from time import time

class LoopBreaker:
    def __init__(self, max_repeats: int = 3, window_seconds: int = 120):
        self.max_repeats = max_repeats
        self.window = window_seconds
        self.seen: dict[str, list[float]] = defaultdict(list)

    def check(self, tool_name: str, params: dict) -> str | None:
        state = hashlib.sha256(
            f"{tool_name}:{sorted(params.items())}".encode()
        ).hexdigest()[:16]
        now = time()
        self.seen[state] = [t for t in self.seen[state] if now - t < self.window]
        self.seen[state].append(now)
        if len(self.seen[state]) >= self.max_repeats:
            return (
                f"Loop detected: {tool_name} called {self.max_repeats} times "
                f"with identical parameters in {self.window}s. "
                f"Stop retrying and ask the user for guidance."
            )
        return None

loop_breaker = LoopBreaker()

def handle_tool_call(tool_name: str, params: dict):
    msg = loop_breaker.check(tool_name, params)
    if msg:
        return {"content": [{"type": "text", "text": msg}], "isError": True}
    return execute_tool(tool_name, params)
```

Hash the full execution state — tool name, all parameters, file references. `search("foo")` and `search("bar")` are different calls; `search("foo")` three times in a row is a loop.

Default tuning: 3 repeats within 2 minutes. Tighten for fast tools, loosen for tools with legitimate retries (file uploads with transient failures).

---

## Cancellation and timeouts

Cancellation is a cooperative protocol primitive — `notifications/cancelled` carries a `requestId` and the receiving handler must stop, free resources, and **not send a response**. A handler that calls blocking `time.sleep(60)` or synchronous HTTP cannot be interrupted; the client sees the cancel ack but the server burns resources for another minute.

Cooperative async with periodic cancel-checks is the only reliable pattern:

```python
import asyncio

@mcp.tool()
async def long_search(query: str, ctx: Context) -> list[dict]:
    results = []
    for chunk in paginate(query):
        if ctx.is_cancelled():
            raise asyncio.CancelledError("client cancelled")
        results.extend(await fetch_chunk(chunk))
    return results
```

Spec rules:

- The `initialize` request MUST NOT be cancelled.
- `notifications/cancelled` only references requests in the same direction.
- For 2025-11-25 Tasks-primitive requests, use `tasks/cancel` instead.

Timeout responses follow the same pattern as any other failure — `isError: true`, error category, `retryable: true` with a sensible `retry_after_ms`. See `advanced-protocol.md` § cancellation for the full pattern.

---

## Transport errors

Transport-layer failures (TCP reset, TLS handshake, malformed JSON-RPC) belong to the protocol-error path. The client sees them; the agent does not. The server's job is two-fold:

1. **Don't pollute stdout** — every byte that isn't a JSON-RPC message corrupts the stream and the client disconnects with `parse error`. Logs go to stderr. See `transport-and-ops.md` § Keep stdout pure JSON-RPC.
2. **Surface transport-impacting state on the next tool call** — when the client reconnects after a transport error, the next tool call should resume from a known state. See `session-and-state.md` for stage persistence patterns.

The 2025-11-25 spec clarified that Streamable HTTP returns HTTP 403 on invalid `Origin`. Servers that return 500 here for an `Origin` mismatch trip every browser-based client incorrectly.

---

## Bad-vs-good examples

### Example 1 — auth failure

Bad — protocol error eats the message:

```json
{ "jsonrpc": "2.0", "id": 1, "error": { "code": -32001, "message": "Auth failed" } }
```

The agent gets a generic failure and gives up.

Good — `isError` with recovery hint:

```json
{
  "result": {
    "content": [{
      "type": "text",
      "text": "Auth failed. Token expired at 2026-05-08T09:00Z. Call refresh_session() to renew, then retry list_projects()."
    }],
    "isError": true
  }
}
```

### Example 2 — validation error framing

Bad — punitive framing, agent assumes a hard failure:

```json
{
  "content": [{ "type": "text", "text": "Error: invalid date. Operation canceled." }],
  "isError": true
}
```

Good — preventive framing, agent makes one parameter adjustment:

```json
{
  "content": [{
    "type": "text",
    "text": "Caught early — 2023-11-15 is in the past. Use a date after 2026-05-08 and retry: schedule_meeting(date='<future>', title='<unchanged>')."
  }],
  "isError": true
}
```

`isError: true` tells the protocol something went wrong. The text tells the agent whether to feel bad about it or just adjust one parameter. Source: u/jbr on r/mcp (2025).

### Example 3 — "not found" anchor

Bad — negative anchor first:

```json
{
  "content": [{ "type": "text", "text": "Module 'color' not found. Available modules: fs, http, path, crypto." }],
  "isError": true
}
```

The agent fixates on "not found" and may tell the user the module doesn't exist or hallucinate alternatives.

Good — options only:

```json
{
  "content": [{ "type": "text", "text": "Available modules: fs, http, path, crypto. Retry load_module(name=<one of these>)." }],
  "isError": true
}
```

The agent reads a menu, picks the best fit, retries. LLMs are pattern-completion machines: "not found" primes a failure-recovery pattern; a list of options primes a selection pattern. The selection pattern is more productive.

### Example 4 — successful empty result is not an error

Empty results from a valid query are not failures. Use `isError: false`:

```json
{
  "content": [{
    "type": "text",
    "text": "No contacts found for 'Jane at Acme'. Try a broader search term, or use list_companies() to browse available companies."
  }],
  "isError": false
}
```

Mislabeling an empty result as an error trains the agent to abandon the workflow instead of refining the search.

---

## Cross-references

- `../../common/error-strategy.md` — universal taxonomy: transient vs permanent, retry-friendly envelopes, schema versioning
- `../decision-trees/error-strategy.md` — diagnostic tree: which envelope shape for which failure
- `tools.md` — tool design and the `isError` mechanics in tool responses
- `agentic-patterns.md` — SERF taxonomy and machine-readable error categories
- `session-and-state.md` — resuming workflow stages after transport errors
- `advanced-protocol.md` — cancellation and progress notifications
- `schema-design.md` — turning validation failures into recovery messages with examples
