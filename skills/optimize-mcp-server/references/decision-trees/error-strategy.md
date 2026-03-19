# Choosing Your Error Handling Strategy

Errors in MCP tools are the primary steering mechanism for agent recovery. The wrong error path kills recovery; the right one guides the agent to a fix in one turn. This tree covers error routing, guard tools, retry limits, and loop detection.

## Decision Tree

```
START: What kind of error occurred?
|
+-- Protocol failure (bad JSON, unknown method, server crash)
|   +-- Use JSON-RPC error field (code + message)
|   +-- The LLM will NOT see this -- client swallows it
|   +-- Only use for actual transport/protocol failures
|
+-- Business logic failure (validation, permissions, state conflict)
|   +-- Use isError: true in the result object
|   +-- The LLM WILL see this and can attempt recovery
|   +-- --> error-handling.md
|   |
|   +-- Was the error caught BEFORE execution?
|   |   +-- YES --> Frame as "prevented," not "failed"
|   |   |   ("Date is in the past -- use a future date and retry")
|   |   |   Prevents frustration loops where the agent abandons approach
|   |   +-- NO  --> Frame as a failure with recovery instructions
|   |       ("Payment processing failed. Call check_status(order_id) first.")
|   |
|   +-- Does the error have a prerequisite fix?
|   |   +-- YES --> Embed the exact tool name + params to call next
|   |   |   ("Call stop_instance(id='i-abc') first, then retry terminate")
|   |   +-- NO  --> Provide corrected parameter suggestions
|   |       ("Did you mean date='2025-07-31' instead of '2024-07-31'?")
|   |
|   +-- Is the error retryable?
|       +-- YES --> Include retry count and limit (attempt 1/3)
|       |   +-- After max retries, provide human escalation fallback
|       |   +-- ("After 3 failures, direct user to /manual-payment")
|       +-- NO  --> State clearly that retry will not help
|           +-- Suggest alternative approach or tool
|
+-- Is the tool destructive (delete, send, modify external state)?
|   +-- YES --> Add guard tool pattern
|   |   +-- Boolean precondition params (tests_verified, backup_confirmed)
|   |   +-- Choose guard strength by stakes:
|   |       +-- Low stakes  --> Soft guard (boolean self-report)
|   |       +-- Medium      --> Token/ID from prerequisite tool
|   |       +-- High stakes --> Server re-runs precondition check
|   |   +-- --> agentic-patterns.md
|   +-- NO  --> Standard error handling is sufficient
|
+-- Is the agent stuck in a retry loop?
    +-- Implement circuit breakers (server-side, not agent-side)
    +-- Hash tool_name + params; track call frequency
    +-- Default: 3 identical calls within 120s = loop detected
    +-- Response: "Loop detected. Stop retrying, ask user for guidance."
    +-- --> error-handling.md, agentic-patterns.md
```

## Key Decision Factors

| Factor | Options | Recommendation |
|---|---|---|
| Error visibility | Protocol error vs isError in result | Always use isError for business logic so the LLM sees it |
| Error framing | "Failed" vs "Prevented" | Use "prevented" for pre-execution validation catches |
| Recovery guidance | Generic vs tool-specific | Always embed exact tool name and parameter values |
| Retry strategy | Unbounded vs limited with fallback | Always cap retries (3 is default) with human escalation |
| Loop detection | Agent-side vs server-side | Server-side only; agents cannot detect their own loops |
| Destructive ops | No guard vs soft/medium/hard guard | Match guard strength to consequences of the action |

## When to Re-evaluate

- When agent transcripts show repeated identical tool calls (add circuit breaker)
- When agents abandon valid approaches after validation errors (fix framing)
- When a new destructive tool is added (decide guard strength)
- When retry loops cause unexpected cost spikes (tighten circuit breaker)
