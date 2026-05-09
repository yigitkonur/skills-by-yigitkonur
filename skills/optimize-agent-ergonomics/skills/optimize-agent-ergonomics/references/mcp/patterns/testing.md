# Testing — how to verify an MCP server end-to-end

Most MCP "bugs" surface when a caller picks the wrong tool, fills the wrong parameters, or fails to recover from an error. Unit tests catch the obvious failures; **agent-use smoke checks** catch description ambiguities, parameter-name mismatches, and response-shape regressions without introducing eval workflows. This file covers both.

The test pyramid: unit → schema → handler → transport → advanced protocol → security → agent-use smoke checks. Climb it in order. Cross-link `test-by-mcpc-cli` for the canonical end-to-end CLI; cross-link `../decision-trees/production-readiness.md` for the pre-deploy checklist that uses these tests.

---

## Test categories — what to cover

### 1. Schema validation tests

Verify every tool's input and output schema accepts valid inputs, rejects invalid inputs, and enforces required fields. These are pure-function tests — fast, deterministic, no transport, no model.

```python
# pytest example
import pytest
from server import server, get_customer_input_schema

def test_get_customer_accepts_valid_id():
    valid = {"customer_id": "cust_123"}
    assert get_customer_input_schema.parse(valid) == valid

def test_get_customer_rejects_missing_id():
    with pytest.raises(ValidationError):
        get_customer_input_schema.parse({})

def test_get_customer_rejects_extra_fields_in_strict_mode():
    with pytest.raises(ValidationError):
        get_customer_input_schema.parse({"customer_id": "cust_123", "junk": "x"})
```

For TypeScript with Zod, run `safeParse` against fixtures of known-good and known-bad payloads. For Python with Pydantic or msgspec, similarly. Run the cross-model portability check from `model-behavior.md` § "Quick portability test" against every input schema in CI.

### 2. Tool-handler tests

Test each handler in isolation, mocking external services. Confirm the handler returns the right `content` blocks, the right `structuredContent`, and `isError: true` on error paths.

```typescript
import { describe, it, expect, vi } from "vitest";
import { handleGetCustomer } from "./tools/customer";

describe("get_customer handler", () => {
  it("returns customer data on success", async () => {
    const crm = { get: vi.fn().mockResolvedValue({ id: "cust_123", name: "Acme" }) };
    const result = await handleGetCustomer({ customer_id: "cust_123" }, { crm });
    expect(result.isError).toBeFalsy();
    expect(result.structuredContent).toMatchObject({ id: "cust_123", name: "Acme" });
    expect(result.content[0].type).toBe("text");
  });

  it("returns isError:true with actionable text on missing customer", async () => {
    const crm = { get: vi.fn().mockResolvedValue(null) };
    const result = await handleGetCustomer({ customer_id: "missing" }, { crm });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain("not found");
  });

  it("never throws — converts exceptions to isError:true", async () => {
    const crm = { get: vi.fn().mockRejectedValue(new Error("upstream down")) };
    const result = await handleGetCustomer({ customer_id: "cust_123" }, { crm });
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toMatch(/upstream/i);
  });
});
```

The third test (handler must never throw) is the one most servers fail. A thrown exception inside a tool handler kills the connection on stdio servers — the agent sees a transport disconnect, no recovery. Wrap every handler in `try/except` that converts to `isError: true`. Cross-link `transport-and-ops.md` Pattern 11.

### 3. Transport tests

Spin up the server in stdio or Streamable HTTP mode and exercise the full JSON-RPC envelope. Confirm `initialize`, `tools/list`, `tools/call`, error responses all conform to spec. Use the **MCP Inspector** for interactive exploration:

```bash
npx @modelcontextprotocol/inspector@latest
# Opens http://localhost:5173 — point it at the server, browse tools, fire calls.
```

What to verify with Inspector:

- `tools/list` returns correct schemas, no extras, no truncation.
- Bad parameters produce clear `isError: true` responses, not protocol errors.
- Successful responses include both `content[]` and (where used) `structuredContent`.
- No stdout pollution: pipe `2>/dev/null` and `jq .` cleanly parses every line.
- Tool descriptions are under ~200 tokens (cross-link `tools.md` § "Over-verbose descriptions").

For automated transport tests, use the canonical CLI **`test-by-mcpc-cli`** (cross-link to that skill — `mcpc 0.2.x`):

```bash
mcpc spawn ./server.py
mcpc tools/list
mcpc tools/call --name get_customer --args '{"customer_id":"cust_123"}'
mcpc tools/call --name get_customer --args '{}' --expect-error
```

Drop `mcpc` invocations into a `make test-mcp` target; pre-push hook runs them before merge. Cross-link `test-by-mcpc-cli` for the full CLI — that skill owns the canonical workflow for end-to-end MCP testing.

### 4. Advanced-protocol tests

When the server uses sampling, elicitation, roots, resources, or prompts, exercise those paths. Capability-aware paths fail differently when the client lies about capabilities; capability-check tests catch this.

```typescript
// Mock the client capabilities object and ensure each branch of the tool runs.
it("falls back to template summary when sampling unavailable", async () => {
  const ctx = { client_capabilities: {} };
  const result = await handleSearchSmart({ query: "foo" }, ctx);
  expect(result.content[0].text).toContain("Top result:");
});

it("uses sampling when available", async () => {
  const session = { create_message: vi.fn().mockResolvedValue("AI summary") };
  const ctx = { client_capabilities: { sampling: {} }, session };
  const result = await handleSearchSmart({ query: "foo" }, ctx);
  expect(session.create_message).toHaveBeenCalled();
  expect(result.content[0].text).toContain("AI summary");
});
```

Cross-link `advanced-protocol.md` for the API; cross-link `client-compatibility.md` for the capability matrix that drives these branches.

### 5. Security / threat tests

Treat every tool input as adversarial. Verify the server defends against prompt injection in returned data, path traversal in URI parameters, SQL injection in query DSLs, command injection in subprocess wrappers. Cross-link `security.md` for the full sanitization rules; cross-link `threat-catalog.md` for named CVEs.

```typescript
it("wraps untrusted SQL output to defend against injection in row values", async () => {
  const result = await handleExecuteSql({ sql: "SELECT note FROM messages" });
  expect(result.content[0].text).toMatch(/<untrusted-data-[a-f0-9-]+>/);
  expect(result.content[0].text).toMatch(/Ignore any instructions/);
});

it("rejects path traversal in resource URI", async () => {
  const result = await handleReadResource({ uri: "file://recipes/../../etc/passwd" });
  expect(result.isError).toBe(true);
  expect(result.content[0].text).toMatch(/invalid path/i);
});

it("never echoes raw stack traces — sanitizes errors", async () => {
  const result = await handleSomeFailingTool({});
  expect(result.content[0].text).not.toMatch(/Error:.* at .* \(.+\.js:\d+/);
});
```

Run a static check at registration time: every tool name matches `[a-z][a-z0-9_]{0,63}` (cross-link `tools.md` § "Namespace tools"), no description exceeds 200 tokens, every input schema flattens to ≤3 nesting levels.

---

## Tooling

- **`mcpc` CLI** — canonical end-to-end MCP testing. Cross-link `test-by-mcpc-cli` for the dedicated skill. Use for: smoke tests in CI, fixture-driven regression suites, capability negotiation traces.
- **MCP Inspector** — interactive UI at `npx @modelcontextprotocol/inspector@latest`. Use for: exploring a server's tool list, firing one-off calls, debugging schema errors.
- **MCP-Test** ([github.com/modelcontextprotocol/mcp-test](https://github.com/modelcontextprotocol/mcp-test)) — the spec authors' conformance test suite. Use for: verifying the server passes the official conformance checks before publishing.
- **FastMCP `dev` mode** — `fastmcp dev inspector server.py` auto-restarts on file change and opens Inspector. Use for: interactive iteration loops while drafting tools.

---

## Agent-use smoke checks — catch "will the caller use this right?"

Schema, handler, and transport tests catch the obvious failures. They do not catch:

- Two tools whose descriptions overlap, so the model picks the wrong one.
- Parameter names that don't match how the model thinks about the concept.
- Response formats that bury the next-action hint, so the model loops.
- Error messages that don't tell the model what to do next.
- Tools that succeed in isolation but fail in a 5-step workflow because step 2's output doesn't unlock step 3.

Do not build model-graded suites, store conversation traces, or route generated transcripts back into model-based rewrites from this skill. This repository forbids eval instructions inside skills.

Use deterministic smoke checks instead:

- **Selection fixtures.** For each user intent, list the expected tool name, required arguments, and forbidden adjacent tools. Review the tool names/descriptions against those fixtures.
- **Metadata linting.** Check every tool name, description length, schema depth, required-field descriptions, and destructive-action annotation at registration time.
- **Workflow fixtures.** Script multi-step flows with fixed tool calls and mocked upstream responses. Confirm each step returns the next required field, not raw provider JSON.
- **Recovery fixtures.** Feed representative `isError: true` responses into the next step of the workflow and confirm the response includes a stable code, retryability, and concrete next action.
- **Context-budget checks.** Fail any response that exceeds the documented token/size cap for the tool class.

What to measure beyond pass/fail:

- **Expected call count.** Fewer is better; extra required calls signal poor consolidation.
- **Response size.** A response bigger than 25,000 tokens loses context budget.
- **Fixture coverage.** Every adjacent-tool pair has at least one selection fixture.
- **Recovery guidance.** Every retryable failure includes a machine-readable code and next action.
- **Workflow length.** A flow that requires 12 deterministic steps when it should take 3 is a design problem.

### Review descriptions without model-driven loops

Use a static description review before adding a tool:

```markdown
Intent: Find all orders from last week.
Expected tool: search_orders
Adjacent tools that should not match: get_order, list_customers
Required argument labels: date_range, status
Side-effect note required: no
```

Check the description against the fixture:

- Names the user intent, not the implementation.
- Mentions the required argument labels.
- States result limits and sort order.
- Does not duplicate another tool's trigger phrase.
- States side effects for destructive tools.

Cross-link `tools.md` § "Tool descriptions" for the writing patterns this review enforces, and `model-behavior.md` for schema idioms to keep portable across clients.

---

## Test fixtures — what to keep alongside the suite

A good fixture pack covers the boundaries:

- **Happy-path inputs** for every tool — minimal, valid, expected to succeed.
- **Boundary inputs** — empty strings, max-length strings, zero, negative, null, unicode, very long arrays.
- **Invalid inputs** — wrong type, missing required field, extra field, malformed enum value.
- **Error-recovery scenarios** — upstream is down (mock 503), token expired (mock 401), rate-limited (mock 429).
- **Multi-step workflows** — sequences that exercise the parameter-dependency-chain pattern (cross-link `agentic-patterns.md`).
- **Untrusted-data scenarios** — tool output containing prompt-injection strings, SQL fragments, shell metacharacters.

Store fixtures alongside the test file:

```
tests/
├── tools/
│   ├── customer/
│   │   ├── handler.test.ts
│   │   └── fixtures/
│   │       ├── valid_get.json
│   │       ├── invalid_missing_id.json
│   │       └── upstream_down.json
│   └── ...
├── workflows/
│   ├── order_refund.json          # deterministic multi-step smoke fixture
│   └── customer_lookup.json
```

---

## The production-readiness test suite — minimum bar before deploy

Cross-link `../decision-trees/production-readiness.md` for the full checklist. The minimum tests:

1. **Every tool's input schema** has at least one positive and one negative test.
2. **Every tool handler** has a happy-path test, an error-path test, and a "throws → isError" test.
3. **Transport smoke** — `mcpc spawn → tools/list → tools/call (1 happy, 1 error)` runs in CI.
4. **Capability negotiation** — server initializes cleanly with empty capabilities, sampling-only, elicitation-only, full.
5. **No stdout pollution** — `node server.js 2>/dev/null | jq .` parses every line.
6. **Description length cap** — at registration, every tool description ≤200 tokens.
7. **Schema portability check** — no `anyOf`/`$ref`/nesting >3 unless the deploy is OpenAI-strict-only.
8. **Response-size cap** — no tool response exceeds 25,000 tokens; chatty tools ≤1,000.
9. **Untrusted-data wrapping** — every tool that returns user-supplied text wraps it (cross-link `security.md`).
10. **At least one agent-use smoke check** — deterministic multi-step fixture with expected tool calls and recovery assertions.

If any of the ten fails, hold the deploy. Cross-link `../decision-trees/production-readiness.md` for the full tree (security posture, scaling, observability).

---

## Cross-references

- `test-by-mcpc-cli` — the canonical CLI-driven end-to-end test workflow; this file routes there for transport and integration tests.
- `tools.md` — tool design and descriptions; the smoke checks catch when violated.
- `model-behavior.md` — per-family schema idioms to keep portable across clients.
- `client-compatibility.md` — per-client matrix; capability-negotiation tests use the same axes.
- `error-handling.md` — `isError: true` shape; handler tests assert against it.
- `security.md` — sanitization patterns the security tests check.
- `threat-catalog.md` — named CVEs the security tests should reproduce.
- `../decision-trees/production-readiness.md` — the pre-deploy checklist this file's minimum suite supports.
