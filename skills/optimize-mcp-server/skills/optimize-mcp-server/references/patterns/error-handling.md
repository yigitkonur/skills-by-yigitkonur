# Error Handling Patterns

How to design MCP error responses that enable agent self-recovery instead of dead ends. These 9 patterns cover error framing, recovery guidance, loop prevention, and using errors as a teaching mechanism.

## Pattern 1: Use isError in the Result Object, Not Protocol-Level Errors

MCP has two error paths — picking the wrong one is a common mistake that kills agent recovery.

**Protocol-level error** (JSON-RPC `error` field): The tool wasn't found, the request was malformed, or the server crashed. The LLM typically never sees this — the client swallows it.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": { "code": -32001, "message": "Request Timeout" }
}
```

**Tool-call error** (`isError: true` in `result`): The tool was called and ran, but the operation failed. This gets injected into the LLM's context window, enabling the model to reason about and recover from the failure.

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Cannot terminate instance while it is running. Call stop_instance(instance_id='i-abc123') first, then retry."
      }
    ],
    "isError": true
  }
}
```

**The rule:** Use protocol-level errors only for actual protocol failures (bad JSON, unknown method, server crash). For all business logic failures — validation errors, permission issues, resource not found — use `isError: true` in the result so the LLM can see the error and attempt recovery.

When you throw a protocol-level error for a business failure, the LLM never sees the error message. It gets a generic "tool call failed" and has no information to fix the problem. With `isError: true`, the error text becomes part of the conversation and the model can adjust its approach.

**Source:** [alpic.ai — Better MCP tool call error responses](https://alpic.ai/blog/better-mcp-tool-call-error-responses-ai-recover-gracefully); [MCP specification — Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)

---

## Pattern 2: Make Error Messages Educational, Not Technical

An error message IS the documentation at that moment. The model has no other source of truth to figure out what went wrong.

**Bad (real example from Supabase MCP):**
```json
{"error": "Unauthorized"}
```
This stops the model cold. It thinks it lacks permissions and gives up.

**Good:**
```json
{
  "error": "Project ID 'proj_abc123' not found or you lack permissions. To see available projects, use the listProjects() tool.",
  "isError": true
}
```

**Error message checklist:**
1. **Name the specific field** that caused the failure
2. **State the expected format** or valid values
3. **Show an example** of correct input
4. **Suggest a recovery action** with a specific tool name

**Template:**
```python
def format_error(field: str, problem: str, expected: str, recovery_tool: str = None) -> dict:
    msg = f"Parameter '{field}': {problem}. Expected: {expected}."
    if recovery_tool:
        msg += f" Use {recovery_tool} to get valid values."
    return {"content": [{"type": "text", "text": msg}], "isError": True}

# Example usage:
format_error(
    field="start_date",
    problem="Date '2024-07-31' is in the past",
    expected="A future date in YYYY-MM-DD format",
    recovery_tool=None
)
# Output: "Parameter 'start_date': Date '2024-07-31' is in the past. Expected: A future date in YYYY-MM-DD format."
```

If a model gets the tool call right 90%+ of the time, and can self-correct from a good error message the other 10%, you don't need exhaustive descriptions covering every edge case upfront. Errors handle the long tail.

**Source:** [u/sjoti on r/mcp](https://reddit.com/r/mcp/comments/1lq69b3/) (280 upvotes) — "The Supabase MCP... its response is `{"error": "Unauthorized"}`, which is technically correct but completely unhelpful."

---

## Pattern 3: Embed Recovery Tool Names Directly in Error Messages

When a tool call fails, don't just say what went wrong — tell the model exactly which tool to call next to fix it.

```json
{
  "content": [{
    "type": "text",
    "text": "You can't terminate an instance while it is running. Call stop_instance(instance_id='i-abc123') first, then retry terminate_instance()."
  }],
  "isError": true
}
```

**Pattern: State-change prerequisite errors**
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
                )
            }],
            "isError": True
        }
    # ... proceed with termination
```

**Pattern: Validation with corrected suggestions**
```json
{
  "content": [{
    "type": "text",
    "text": "The requested travel date cannot be in the past. You asked for July 31 2024 but today is July 25 2025. Did you mean July 31 2025?"
  }],
  "isError": true
}
```

**Key principle:** Include the actual parameter values the model should use, not just the tool name. Don't make the model figure out what arguments to pass — spell them out.

**Source:** [alpic.ai — Better MCP tool call error responses](https://alpic.ai/blog/better-mcp-tool-call-error-responses-ai-recover-gracefully)

---

## Pattern 4: Include Retry Limits and Fallback Instructions in Errors

Unbounded retry guidance ("try again") can trap the model in infinite loops. Always include a limit and a fallback.

```json
{
  "content": [{
    "type": "text",
    "text": "An unknown error occurred while processing the payment. Retry now. After three consecutive failures, provide the user a link to https://dashboard.example.com/manual-payment to complete the payment manually."
  }],
  "isError": true
}
```

**Implementation pattern:**
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
                    )
                }],
                "isError": True
            }
        return {
            "content": [{
                "type": "text",
                "text": (
                    f"Payment processing temporarily failed (attempt {_retry_count + 1}/3). "
                    f"Call process_payment(order_id='{order_id}', _retry_count={_retry_count + 1}) to retry."
                )
            }],
            "isError": True
        }
```

Without limits, some models will retry 10+ times, burning tokens and time. The fallback also prevents the model from giving up entirely — it provides a human escalation path.

**Source:** [alpic.ai — Better MCP tool call error responses](https://alpic.ai/blog/better-mcp-tool-call-error-responses-ai-recover-gracefully); [Stainless — Error Handling And Debugging MCP Servers](https://www.stainless.com/mcp/error-handling-and-debugging-mcp-servers)

---

## Pattern 5: Let Errors Handle the Long Tail Instead of Bloating Descriptions

If a model gets the tool call right 90%+ of the time, you don't need to cram every edge case into the tool description. Let good error messages handle the remaining 10%.

**The trade-off:**
- **Exhaustive descriptions** cover every case upfront but waste tokens on every call, even when the model would have gotten it right
- **Minimal descriptions + rich errors** keep the initial context lean and only inject detailed guidance when needed

**In practice:**
```python
@tool(description="Search for contacts by name, email, or company.")
def search_contacts(query: str, limit: int = 10):
    """
    Description is intentionally brief. Edge cases are handled by errors.
    """
    if not query.strip():
        return error("Query cannot be empty. Provide a name, email, or company name.")

    if limit > 100:
        return error(
            f"Limit {limit} exceeds maximum of 100. "
            f"Call search_contacts(query='{query}', limit=100) instead."
        )

    results = db.search(query, limit=limit)
    if not results:
        return {
            "content": [{"type": "text", "text":
                f"No contacts found for '{query}'. "
                f"Try a broader search term or check spelling. "
                f"You can also use list_companies() to browse available companies."
            }],
            "isError": False  # Not an error - valid empty result with guidance
        }
    return format_results(results)
```

This is especially true for APIs with many endpoints. Stuffing documentation into descriptions leads to context overload (30+ detailed tools = performance degradation). Error-driven learning keeps the initial footprint small.

**Caveat:** Don't take this too far. Core usage patterns should be in the description. Only edge cases and rare failure modes belong in error messages.

**Source:** [u/sjoti on r/mcp](https://reddit.com/r/mcp/comments/1lq69b3/); [u/Nako_A1 on r/mcp](https://reddit.com/r/mcp/comments/1npfoo9/) — error-driven learning (solution #6)

---

## Pattern 6: Distinguish "Prevented" from "Failed" in Error Framing

When a tool catches bad input before executing, it *prevented* a problem — it didn't *fail*. The wording you choose changes the agent's entire subsequent behavior.

**Why it matters:**
- "Error detected, operation canceled" triggers frustration loops — the agent assumes *it* broke something and produces unproductive recovery sequences
- "Caught early — here's how to fix it" tells the agent the system is working *with* it, encouraging a single corrective retry

**Bad — punitive framing:**
```json
{
  "content": [{"type": "text", "text": "Error: invalid date. Operation canceled."}],
  "isError": true
}
```

The agent reads this as a hard failure. It may abandon the approach, apologize to the user, or attempt a completely different strategy — all unnecessary.

**Good — preventive framing:**
```json
{
  "content": [{
    "type": "text",
    "text": "The date 2023-11-15 is in the past — schedule_meeting requires a future date. Use a date after 2025-01-15 and retry with schedule_meeting(date='2025-01-20', ...)."
  }],
  "isError": true
}
```

**The pattern in code:**
```python
def schedule_meeting(date: str, title: str):
    parsed = parse_date(date)
    if parsed < datetime.now():
        return {
            "content": [{"type": "text", "text":
                f"Great catch — {date} is in the past. "
                f"Use a future date (after {datetime.now().strftime('%Y-%m-%d')}) "
                f"and retry: schedule_meeting(date='<future_date>', title='{title}')"
            }],
            "isError": True
        }
    # proceed with scheduling...
```

**Key distinction:** `isError: true` tells the protocol something went wrong. The *text* tells the agent whether to feel bad about it or just adjust one parameter. The text matters more than the flag.

**Source:** [u/jbr, commenting on r/mcp](https://reddit.com/r/mcp/comments/1lhws59/) (261-upvote thread by u/incidentjustice)

---

## Pattern 7: Avoid "Not Found" Phrasing — Return What Exists Instead

Returning "X not found" anchors the LLM on failure. Drop the negative prefix entirely and return the available options. The model picks the closest match itself without the discouraging framing.

**Bad — negative anchor first:**
```json
{
  "content": [{"type": "text", "text": "Module 'color' not found. Available modules: fs, http, path, crypto."}],
  "isError": true
}
```

The agent fixates on "not found" and may tell the user the module doesn't exist, or attempt to install it, or hallucinate an alternative — all before considering the list you provided.

**Good — options only:**
```json
{
  "content": [{"type": "text", "text": "Available modules: fs, http, path, crypto. Select one to proceed."}],
  "isError": true
}
```

The agent reads a menu, picks the best fit, and retries. No drama.

**Implementation pattern:**
```python
MODULES = {"fs", "http", "path", "crypto", "stream"}

def load_module(name: str):
    if name not in MODULES:
        available = ", ".join(sorted(MODULES))
        # Don't say "not found" — just show what's there
        return {
            "content": [{"type": "text", "text":
                f"Available modules: {available}. "
                f"Retry load_module(name='<module>') with one of these."
            }],
            "isError": True
        }
    return {"content": [{"type": "text", "text": f"Loaded {name} successfully."}]}
```

**Same principle applies broadly:**
- Users: Don't say "User not found." Say "Matching users: alice, bob, carol."
- Files: Don't say "File missing." Say "Files in directory: config.yaml, schema.json."
- Endpoints: Don't say "Invalid action." Say "Supported actions: create, read, update, delete."

LLMs are pattern-completion machines. "Not found" primes a failure-recovery pattern. A list of options primes a selection pattern. The selection pattern is far more productive.

**Source:** Community best practices from [r/mcp](https://reddit.com/r/mcp); LLM behavioral observations on negative vs. positive framing

---

## Pattern 8: Build Circuit Breakers for Agent Loop Detection

Agents can't detect their own loops. From the LLM's perspective, every retry is a fresh attempt with renewed optimism. You must detect and break loops *outside* the LLM's decision-making.

**The problem:** An agent calls `update_record(id=42, status="active")` -> gets a validation error -> "fixes" the call -> sends the exact same parameters -> same error -> repeats indefinitely. The LLM genuinely believes each attempt is different.

**Solution — hash-based state tracking:**
```python
import hashlib
from collections import defaultdict
from time import time

class LoopBreaker:
    def __init__(self, max_repeats=3, window_seconds=120):
        self.max_repeats = max_repeats
        self.window = window_seconds
        self.seen: dict[str, list[float]] = defaultdict(list)

    def check(self, tool_name: str, params: dict) -> str | None:
        state = hashlib.sha256(
            f"{tool_name}:{sorted(params.items())}".encode()
        ).hexdigest()[:16]

        now = time()
        # Prune old entries outside the window
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
```

**Wire it into your tool handler:**
```python
def handle_tool_call(tool_name: str, params: dict):
    loop_msg = loop_breaker.check(tool_name, params)
    if loop_msg:
        return {"content": [{"type": "text", "text": loop_msg}], "isError": True}

    return execute_tool(tool_name, params)
```

**What to hash:** Include the full execution state — tool name, all parameters, and any file references. Don't just hash the tool name; `search("foo")` and `search("bar")` are different calls. But `search("foo")` three times in a row is a loop.

**Tuning:** 3 repeats within 2 minutes is a reasonable default. Tighten for fast tools (API lookups), loosen for tools with legitimate retries (file uploads with transient failures).

**Source:** [u/Main_Payment_6430 on r/AI_Agents](https://reddit.com/r/AI_Agents/comments/1qxh5ip/) — "$63 overnight" agent loop incident

---

## Pattern 9: Return Normalized Inputs in Every Response

When your server accepts flexible input formats and normalizes them internally (e.g., "yesterday" -> "2024-01-15"), include the normalized values in the response. This teaches the agent the canonical format, improving every subsequent call.

**Without normalized feedback:**
```
Agent: get_events(date="yesterday")       -> works
Agent: get_events(date="the day before")  -> works (maybe)
Agent: get_events(date="24 hours ago")    -> works (maybe)
```
The agent never learns the canonical format. It keeps inventing variations, each one a parsing gamble.

**With normalized feedback:**
```json
{
  "result": { "events": [{"title": "Standup", "time": "09:00"}] },
  "normalized_inputs": {
    "date": "2025-01-15",
    "note": "Interpreted 'yesterday' as 2025-01-15"
  }
}
```
After seeing this once, the agent starts using `"2025-01-15"` format directly.

**Implementation:**
```python
from datetime import datetime, timedelta

def get_events(date: str):
    resolved = resolve_date(date)
    events = db.query_events(resolved)
    return {
        "content": [{"type": "text", "text": json.dumps({
            "events": events,
            "normalized_inputs": {
                "date": resolved.strftime("%Y-%m-%d"),
                "note": f"Interpreted '{date}' as {resolved.strftime('%Y-%m-%d')}"
            }
        })}]
    }

def resolve_date(raw: str) -> datetime:
    shortcuts = {"today": datetime.now(), "yesterday": datetime.now() - timedelta(days=1)}
    return shortcuts.get(raw.lower()) or dateparser.parse(raw)
```

**Same principle for rate-limit errors — return structured retry info:**
```json
{"rate_limited": true, "retry_after_seconds": 30, "reset_at": "2025-01-15T10:05:00Z"}
```

**The principle:** Every response is a training signal. Return the canonical form of what you understood, and the agent converges on clean inputs fast.

**Source:** Parameter coercion patterns from production MCP servers; community patterns from [r/mcp](https://reddit.com/r/mcp)
