# agent-integration — how agents actually call your tool

Write tools that match how agents call them. The agent's harness has a contract; honor it. Subprocess wrappers (CLI) and MCP clients (MCP) share more than they differ — both run with timeouts, parse structured responses, classify outcomes, retry on transient. The tool author is responsible for surviving that contract on day one.

## The universal harness contract

Every agent harness — Python `subprocess`, Node `child_process`, MCP client SDK, OpenAI tool-calling layer, Claude Code's tool runner — does roughly the same five things on every call:

| Step | What the harness does | Where it can fail |
|---|---|---|
| 1 | Sends the request with a timeout (default 30s) | Tool hangs waiting for stdin / approval |
| 2 | Captures the response stream | Buffer overflow on large output; mixed channels |
| 3 | Parses the structured payload | Mixed text+JSON; malformed JSON; truncation |
| 4 | Classifies the outcome | Exit code (CLI) or `isError` (MCP); ambiguous mapping |
| 5 | Decides retry / surface / proceed | Missing `retryable` flag; no `retry_after` on rate-limit |

A tool that survives every step in this list is "agent-ready." A tool that fails any one is broken from the agent's perspective, regardless of how well it works under a human's hand.

## Surface mappings

### CLI — subprocess wrappers, stream discipline, signal handling

The harness invokes the CLI as a subprocess with explicit `stdin`, `stdout`, `stderr` channels and a timeout. The tool's job:

| Channel | Discipline | Why |
|---|---|---|
| stdin | Don't read unless `--no-input` or piped data | Agent pipelines have no human typing; reads block forever |
| stdout | Pure machine output (JSON envelope or NDJSON stream) under `--json` | Harness parses stdout as the data channel |
| stderr | Progress, warnings, debug — never the load-bearing data | Harness reads stderr only for diagnostics |
| Exit code | Semantic taxonomy from `../cli/exit-codes.md` | Harness branches on the code; ambiguous codes break recovery |
| Signals | Honor SIGINT / SIGTERM; clean up state and exit non-zero | Harness sends SIGTERM on timeout; orphaned state leaks |

Cross-link `../cli/subprocess-harness.md` for the Python / Node / Bash harness samples and the full failure-mode catalog.

The harness's contract:

```
1. Append --json (or --output=json) to the command.
2. Capture stdout and stderr separately.
3. Apply a timeout (default 30s; override per-command).
4. Wait for the process to exit OR the timeout to fire.
5. On exit, parse stdout as JSON; classify by exit code.
6. On timeout, send SIGTERM, wait briefly, send SIGKILL.
```

The tool's contract:

```
1. Detect non-TTY stdout and auto-emit JSON when it is.
2. Print the envelope on stdout; nothing else.
3. Print progress to stderr; flush on every line.
4. Exit with the semantic code (0 = success, 7 = transient, etc.).
5. Cleanly handle SIGTERM — close files, release locks, exit non-zero.
```

When both contracts are honored, the harness recovers cleanly. When either is broken, the harness either hangs, surfaces garbage, or treats success as failure.

### MCP — MCP client lifecycle, session management, transport quirks

The harness uses an MCP client SDK that runs through this lifecycle on every interaction:

```
1. connect(transport)                   # stdio, Streamable HTTP, or SSE
2. await initialize()                   # protocol handshake, capability negotiation
3. tools = await list_tools()           # one request; cached per session
4. result = await call_tool(name, args) # the actual call
5. parse(result.content, result.structuredContent, result.isError)
6. disconnect() OR keep-alive
```

The tool's contract on each step:

| Step | Tool obligation |
|---|---|
| `initialize` | Respond to capability negotiation; declare supported features (logging, sampling, roots) |
| `tools/list` | Return all tools with stable names, schemas, descriptions; cap at the model's sweet spot |
| `tools/call` | Execute within the timeout; return `content` (text) AND optionally `structuredContent` (machine-parseable); set `isError: true` for business-logic failures |
| Lifecycle | Clean up server-side state on disconnect OR signal session-scoped cleanup explicitly |

Transport-specific quirks the tool author must anticipate:

| Transport | Quirk | Mitigation |
|---|---|---|
| stdio | Process lifecycle = client lifecycle; child process leaks if client crashes | Trap signals; flush stderr; exit cleanly |
| Streamable HTTP | Request-scoped sessions; load balancer can route subsequent requests to a different instance | Stateless per-request OR external session store (HubSpot exemplar) |
| SSE (deprecated) | Long-lived connections; reconnect storms; harder to scale | HubSpot rejects SSE outright; if shipping, keep state external |
| WebSocket | Reconnect logic varies by client; some clients drop session on reconnect | Document reconnect semantics; never assume in-memory state survives |

Cross-link `../mcp/patterns/transport-and-ops.md` for transport selection and `../mcp/patterns/session-and-state.md` for stateful-vs-stateless trade-offs.

## Common harness failure modes

These are the failures every tool author should anticipate. Each has a tool-side fix.

### CLI failures

| Failure mode | Symptom | Tool-side fix |
|---|---|---|
| Tool hangs on stdin | Harness waits, then times out | Detect non-TTY and skip prompts; require `--yes` or `--no-input` for interactive paths |
| Stdout buffer overflow | Harness gets partial output; JSON parse fails | Cap response size; paginate or truncate-with-signal |
| Stderr noise on stdout | Harness sees `Loading...\n{...}` and JSON parse fails | Strict separation: stderr for progress, stdout for envelope only |
| Mixed text and JSON | Harness's parser doesn't know whether to JSON.parse | Single canonical envelope per call; prose only via stderr |
| Malformed JSON | Pretty-printed JSON across multiple lines confuses NDJSON parsers | Compact JSON in single-shot mode; one object per line in NDJSON streams |
| Exit code 1 for everything | Harness can't classify; treats validation, auth, transient identically | Implement the 0–7 taxonomy from `../cli/exit-codes.md` |
| ANSI colors on JSON output | Harness's JSON parser fails on `\x1b[32m{` | `NO_COLOR=1` env, `--json` flag suppresses ANSI; auto-suppress on non-TTY |
| Signal not honored | SIGTERM ignored; harness escalates to SIGKILL; locks stay held | Trap SIGTERM/SIGINT, release resources, exit ≠ 0 |

### MCP failures

| Failure mode | Symptom | Tool-side fix |
|---|---|---|
| Session leak | Server-side state grows unbounded | Per-request ephemeral sessions OR explicit cleanup on disconnect |
| Long-running tool times out | Harness's per-call timeout fires before the work completes | Iterative pattern with progress notifications; tool returns within timeout, agent polls |
| Unparseable response | `content[0].text` is human prose, no `structuredContent` | Ship both: text summary + structuredContent JSON |
| Protocol error for business logic | Harness sees JSON-RPC `-32603`; can't recover | Use `isError: true` in result content; reserve protocol errors for transport |
| Schema drift mid-session | Tool's input schema changes between `tools/list` calls | Stable schemas per server version; cache-friendly |
| Token bloat | `tools/list` returns 17k+ tokens of catalog | Prune descriptions; offer toolset selection at connect |
| Mixed isError semantics | Some failures use `isError: true`, others throw | Single discipline: `isError` for business; throws only for transport bugs |

## Example harnesses

### Python subprocess wrapper for CLI

A harness that captures stdout and stderr separately, applies a timeout, parses JSON, classifies by exit code, and retries on transient.

```python
import subprocess
import json
import time
import random

EXIT_CODE_CLASS = {
    0: "success",
    1: "crash",
    2: "usage",
    3: "not_found",
    4: "auth",
    5: "conflict",
    6: "validation",
    7: "transient",
}

def invoke_cli(cmd: list[str], timeout: int = 30) -> dict:
    """Invoke a CLI with --json; return a normalized dict the agent can branch on."""
    full_cmd = cmd + ["--json"]
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={"NO_COLOR": "1", "TERM": "dumb"},
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": {"class": "timeout", "retryable": True}}

    classification = EXIT_CODE_CLASS.get(result.returncode, "unknown")

    # Parse JSON from stdout; fall back to raw text if parse fails.
    if result.stdout.strip():
        try:
            envelope = json.loads(result.stdout)
            envelope["_exit_classification"] = classification
            return envelope
        except json.JSONDecodeError as e:
            return {
                "ok": False,
                "error": {"class": "parse_failure", "message": str(e), "raw": result.stdout},
                "_exit_classification": classification,
            }

    # No stdout — exit code carries the entire signal.
    return {
        "ok": result.returncode == 0,
        "error": {"class": classification, "message": result.stderr.strip()} if result.returncode else None,
        "_exit_classification": classification,
    }

def invoke_with_retry(cmd: list[str], max_attempts: int = 3) -> dict:
    """Retry on transient (exit 7); fail fast otherwise."""
    for attempt in range(max_attempts):
        result = invoke_cli(cmd)
        if result.get("ok"):
            return result
        err = result.get("error", {})
        if not err.get("retryable") and err.get("class") != "transient":
            return result  # Permanent — fail fast.
        if attempt == max_attempts - 1:
            return result
        delay = err.get("retry_after", 2 ** attempt + random.uniform(0, 1))
        time.sleep(delay)
    return result
```

The harness reads the envelope first, then the exit classification as a fallback. The tool author's job is to make both sources of truth agree.

### MCP client call with timeout and structured error handling

A harness that connects to an MCP server, calls a tool, parses the structured result, and decides retry-or-surface based on `isError` and `structuredContent.error.retryable`.

```python
import asyncio
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def call_mcp_tool(server_cmd: list[str], tool_name: str, args: dict, timeout: int = 30) -> dict:
    """Call an MCP tool; return a normalized envelope the agent can branch on."""
    server = StdioServerParameters(command=server_cmd[0], args=server_cmd[1:])
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            try:
                result = await asyncio.wait_for(
                    session.call_tool(tool_name, args),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                return {"ok": False, "error": {"class": "timeout", "retryable": True}}

            # Parse the structured content if present; fall back to text.
            structured = getattr(result, "structuredContent", None)
            text_blocks = [c.text for c in result.content if c.type == "text"]
            text_summary = "\n".join(text_blocks)

            if result.isError:
                err = (structured or {}).get("error", {})
                return {
                    "ok": False,
                    "error": {
                        "class": err.get("class", "unknown"),
                        "code": err.get("code", "UNKNOWN"),
                        "message": err.get("message") or text_summary,
                        "retryable": err.get("retryable", False),
                        "retry_after_ms": err.get("retry_after_ms"),
                        "next_action": err.get("next_action"),
                    },
                }

            return {"ok": True, "result": structured, "text_summary": text_summary}
```

The harness reads `isError` first; on error, it pulls structured fields for retry / next-action logic. The tool author's job: ship both `content[].text` (human-readable summary) AND `structuredContent` (machine-parseable shape).

## The harness as a unit test

The most reliable way to verify a tool is agent-ready is to put it under a harness and watch what happens. Every tool author should run their tool through the harness shape it'll meet in production before declaring it done.

Concrete checks the harness should perform:

```python
def test_agent_readiness(invoke):
    """Run before declaring a tool agent-ready."""
    # 1. Happy path returns parseable success.
    r = invoke(["mytool", "version"])
    assert r["ok"] is True

    # 2. Not-found returns retryable=False and a non-success class.
    r = invoke(["mytool", "get", "nonexistent"])
    assert r["ok"] is False
    assert r["error"]["retryable"] is False
    assert r["error"]["class"] == "not_found"

    # 3. Transient errors return retryable=True with retry_after.
    r = invoke(["mytool", "trigger-rate-limit"])  # synthetic test endpoint
    assert r["ok"] is False
    assert r["error"]["retryable"] is True
    assert "retry_after" in r["error"]

    # 4. Validation errors carry field paths and suggested fixes.
    r = invoke(["mytool", "apply", "-f", "broken.yaml"])
    assert r["ok"] is False
    assert r["error"]["class"] == "validation"
    assert "field" in r["error"]
    assert "suggestion" in r["error"]

    # 5. Tool times out cleanly (doesn't hang).
    r = invoke(["mytool", "long-job"], timeout=1)
    assert r["error"]["class"] == "timeout"

    # 6. No stderr noise leaks into stdout when --json is set.
    raw = subprocess.run(["mytool", "list", "--json"], capture_output=True, text=True)
    assert raw.stdout.strip().startswith("{")  # JSON envelope only.
```

Same shape for MCP — call_tool through real client, assert on `isError` semantics, parse structured content, verify retry hints.

When the harness passes these six checks, the tool meets the agent-readiness bar. Until then, the tool is "works for humans" but not yet ready for an agent.

## Anti-patterns to refuse

- **Ship without a harness test.** "Works in the terminal" doesn't mean "works under subprocess capture." Run the harness.
- **Same exit code for every failure.** `os.Exit(1)` is the agent-readiness equivalent of `panic`. Map classes to codes (`../cli/exit-codes.md`).
- **Same MCP error shape for transient and permanent.** `isError: true` with no `retryable` flag forces the agent to guess.
- **Hidden state in the agent's context.** Tools that depend on environment from a prior call (e.g., "you must call `auth_login` first") need an explicit `state_token` or a session model.
- **Mixed channels.** Prose on stdout, JSON on stderr. Pick one channel per role and hold it.
- **No timeout default.** A tool with no documented timeout invites 30s default cancellations on legitimate work. Document expected duration.
- **Refusing structured errors when `--json` is set.** A CLI that prints `Error: foo` on stderr and exits 1 even with `--json` set is broken for agents.
- **Returning `content[0].text` as the only channel on MCP.** Agents that respect the spec parse `structuredContent`. Don't force them to JSON.parse a text blob.

## Cross-references

- For the CLI subprocess harness deep dive, read `../cli/subprocess-harness.md`.
- For MCP client lifecycle and transport selection, read `../mcp/patterns/transport-and-ops.md`.
- For exit-code semantics that make subprocess classification work, read `../cli/exit-codes.md`.
- For `isError` semantics that make MCP classification work, read `../mcp/patterns/error-handling.md`.
- For error-envelope design across both surfaces, read `error-strategy.md`.
- For test-friendly response shapes (envelopes, schema versioning), read `output-contracts.md`.
