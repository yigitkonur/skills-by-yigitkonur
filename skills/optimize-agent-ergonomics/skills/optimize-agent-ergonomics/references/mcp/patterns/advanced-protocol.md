# Advanced protocol

Protocol features beyond the basic tool/resource/prompt surface — sampling, elicitation, roots, cancellation. These determine whether a server feels static or genuinely agentic. Client support is uneven; capability checks and graceful fallbacks are non-negotiable. Cross-link to `client-compatibility.md` for the support matrix and `agentic-patterns.md` for the prompt-gate alternative when advanced features are missing.

---

## The "advanced protocol drops" anti-pattern

The single most common bug: a server invokes `sampling/createMessage` without checking whether the client supports it. Most clients (as of 2025-12) silently fail — GitHub Copilot CLI returns `"Method not found: sampling/createMessage"`; Claude Code closed its sampling feature request as "not planned" (anthropics/claude-code #7108, 2025-09-04); Cursor, Windsurf, Zed, Cline, and Continue all ignore it.

A server that assumes support **crashes** on the majority of clients in the field. The first rule of every advanced feature: capability-gate before invoking. If the capability is absent, fall back to embedding the request in a regular tool response and let the orchestrating agent handle it.

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("server")

@mcp.tool()
async def summarize(doc: str, ctx: Context) -> str:
    caps = ctx.session.client_capabilities
    if caps and caps.sampling is not None:
        resp = await ctx.session.create_message(
            messages=[{"role": "user", "content": {"type": "text", "text": f"Summarize: {doc}"}}],
            max_tokens=256,
        )
        return resp.content.text
    # Fallback: ask the orchestrating agent to do it in its own context
    return (
        "SAMPLING_UNAVAILABLE: This client does not support sampling. "
        "Please summarize the document yourself and call save_summary with the result.\n\n"
        + doc
    )
```

This pattern applies to all four advanced features below. Source: MCP Spec 2025-11-25 — sampling; GitHub community #160291 (2025-09).

---

## Sampling

### When to use

Server-side LLM reasoning mid-tool-execution, **without** shipping an API key. The user's client provides the inference; the server consumes it. Three strong use cases:

- Sub-reasoning a partial result (summarization, classification, ranking) before returning.
- Multi-step inner loops where the server wants the LLM's compute paid by the client.
- Public servers, CI runners, or untrusted-deployment scenarios where credential leakage is unacceptable.

### How it works

The 2025-11-25 revision added `tools` and `toolChoice` parameters, enabling "server-side agent loops using standard MCP primitives" (WorkOS, 2025-11) — a server can run a bounded inner reasoning loop entirely on the client's LLM.

```python
@mcp.tool()
async def draft_reply(thread_id: str, ctx: Context) -> str:
    msgs = load_thread(thread_id)
    resp = await ctx.session.create_message(
        messages=[{"role": "user", "content": {"type": "text", "text": render(msgs)}}],
        system_prompt="You draft concise professional email replies.",
        model_preferences={
            "hints": [{"name": "claude-3-5-sonnet"}],
            "intelligencePriority": 0.8,
            "speedPriority": 0.4,
        },
        max_tokens=512,
    )
    return resp.content.text
```

### Sampling-with-tools

When using 2025-11-25 sampling-with-tools to drive a multi-turn inner loop, the server **MUST** respond to every `ToolUseContent` returned by the client with a matching `ToolResultContent` before the next `createMessage` call. Drop one and the conversation diverges or the client errors.

```python
async def inner_agent_loop(ctx: Context, goal: str, max_turns: int = 8):
    messages = [{"role": "user", "content": {"type": "text", "text": goal}}]
    tools = [{"name": "lookup", "description": "...", "inputSchema": {...}}]

    for _ in range(max_turns):
        resp = await ctx.session.create_message(
            messages=messages,
            max_tokens=1024,
            tools=tools,
            tool_choice={"type": "auto"},
        )
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason == "endTurn":
            return resp.content.text
        if resp.stop_reason == "toolUse":
            for block in resp.content:
                if block.type == "tool_use":
                    result = dispatch(block.name, block.input)
                    messages.append({
                        "role": "user",
                        "content": {"type": "tool_result", "tool_use_id": block.id, "content": result},
                    })
    raise RuntimeError("Inner loop exceeded max_turns")
```

### Client support

| Client | Sampling | Sampling-with-tools |
|---|---|---|
| Claude Desktop | ignored | unknown-2025-12 |
| Claude Code | ignored (FR #1785 open) | ignored |
| Cursor | ignored | ignored |
| Windsurf, Zed, Cline, Continue | ignored | ignored |
| VS Code (Copilot) | native (1.101, 2025-06) | partial (2025-11-25) |
| Copilot CLI | ignored (community #160291) | ignored |
| Goose | partial (2025-11) | unknown-2025-12 |

Wrap inner loops in iteration limits (typical: 5-10) — users pay for every sampled token. The `tools: {}` capability flag is new in 2025-11-25 and is absent on pre-2025-11 clients. Check `caps.sampling.tools is not None` before sending tools.

When NOT to use sampling: the client is Claude Code, Cursor, Windsurf, Zed, Cline, Continue, or Copilot CLI — none support it as of 2025-12. Detect and fall back to a regular tool response that asks the orchestrating agent to do the reasoning.

Source: MCP Spec 2025-11-25 changelog; FastMCP sampling docs (gofastmcp.com/servers/sampling); MCP Spec 2025-11-25 sampling.

---

## Elicitation

### When to use

Form-mode elicitation (introduced 2025-06-18, expanded 2025-11-25) is for **clarifying a missing argument** or **confirming an irreversible action** mid-tool-execution. Three legitimate use cases:

- Clarify-missing-arg ("which size? S, M, or L?").
- Confirm irreversible actions ("delete workspace `acme-prod`? type the name to confirm").
- Progressive input gathering inside a single tool call.

### How it works

Form-mode is restricted by spec to flat objects with primitive properties only — `string`, `number`, `integer`, `boolean`, plus enums. No nested objects, no arrays-of-objects, and `string.format` is limited to `email`, `uri`, `date`, `date-time`. The spec also mandates that clients **MUST NOT** send passwords or sensitive credentials via form mode.

```python
from pydantic import BaseModel, Field

class BookingPreferences(BaseModel):
    checkAlternative: bool = Field(description="Would you like to check another date?")
    alternativeDate: str = Field(default="2024-12-26", description="Alternative date (YYYY-MM-DD)")

@mcp.tool()
async def book_table(date: str, time: str, party_size: int, ctx: Context) -> str:
    if date == "2024-12-25":
        result = await ctx.elicit(
            message=f"No tables for {party_size} on {date}. Try another date?",
            schema=BookingPreferences,
        )
        if result.action == "accept" and result.data:
            return f"[SUCCESS] Booked for {result.data.alternativeDate}"
        return "[CANCELLED] Booking cancelled"
    return f"[SUCCESS] Booked for {date} at {time}"
```

### URL-mode elicitation (2025-11-25)

For OAuth flows, payment confirmation, or secret entry — use **URL-mode** elicitation. The client opens the URL in an isolated browser surface the LLM cannot observe, so tokens never enter the model context.

```python
import uuid

@mcp.tool()
async def connect_stripe(ctx: Context) -> str:
    eid = str(uuid.uuid4())
    state_store.put(eid, {"user": ctx.user_sub, "status": "pending"})
    result = await ctx.elicit_url(
        message="Connect your Stripe account to continue.",
        url=f"https://auth.example.com/stripe/start?state={eid}",
        elicitation_id=eid,
    )
    if state_store.get(eid)["status"] == "granted":
        return "Stripe connected."
    return "Connection not completed."
```

URL-mode elicitation state **MUST** be tied to user identity, not just session ID, to prevent session-hijack replay (spec).

### Elicitation abuse — never fish for secrets

The elicitation/abuse threat (`threat-catalog.md` #11) is real: a malicious server uses `elicitation/create` to phish ("Please re-enter your password"). The spec's MUST NOT for credentials is enforced at the **client**; defenders should not rely on servers self-policing. Client-side mitigation: maintain a deny list (patterns containing "password", "SSN", "card number", "security code") and label the server identity prominently in every elicitation dialog.

### Client support

| Client | Form-mode | URL-mode |
|---|---|---|
| Claude Desktop | unknown-2025-12 | unknown-2025-12 |
| Claude Code | ignored (#7108 "not planned") | ignored |
| Cursor | native (community) | unknown-2025-12 |
| VS Code (Copilot) | native (1.102, 2025-09) | partial (Insiders, 2025-11) |
| Goose | native (desktop) | unknown-2025-12 |
| Windsurf, Zed, Cline, Continue, Copilot CLI | ignored | ignored / unknown |

Source: MCP Spec 2025-11-25 — elicitation; python-sdk elicitation.py example; GitHub Copilot elicitation blog (2025-09-04).

---

## Roots

### When to use

Any server that reads or writes files — filesystem servers, code search, git, build tools. Roots are how the client tells the server which directories the user has authorized.

### How it works

On session start (and on every `notifications/roots/list_changed`), call `roots/list` and scope all filesystem access to the returned `file://` URIs. Validate every path with `os.path.realpath` plus a prefix check against the roots to block symlink traversal. The spec explicitly mandates "validate all root URIs to prevent path traversal."

```python
import os

async def refresh_roots(ctx: Context) -> list[str]:
    caps = ctx.session.client_capabilities
    if not (caps and caps.roots):
        return [os.getcwd()]  # fallback only when the client doesn't speak roots
    resp = await ctx.session.list_roots()
    roots: list[str] = []
    for r in resp.roots:
        uri = str(r.uri)
        if not uri.startswith("file://"):
            continue  # spec says roots MUST be file://
        roots.append(os.path.realpath(uri.removeprefix("file://")))
    return roots

def is_inside_roots(path: str, roots: list[str]) -> bool:
    real = os.path.realpath(path)
    return any(real == r or real.startswith(r + os.sep) for r in roots)
```

Roots are `file://` only. Reject `http://`, `s3://`, etc. Servers that take `--dir=` flags and ignore roots break every time the user opens a new folder mid-session, because the server keeps indexing the old one.

### Client support

| Client | Roots |
|---|---|
| Claude Desktop | native |
| Claude Code | native (2025-11) |
| Cursor | ignored |
| Windsurf, Zed, Cline, Continue, Copilot CLI | ignored |
| VS Code (Copilot) | native (1.101) |
| Goose | native |

When NOT to use roots: the client is Cursor / Windsurf / Zed / Cline / Continue / Copilot CLI — provide an explicit `workspace_path` tool argument instead.

Source: MCP Spec 2025-06-18 — roots.

---

## Cancellation

### When to use

Long-running tools where the user might interrupt — searches, batch operations, expensive queries. Without cooperative cancellation, a `Ctrl-C` in the client leaves the server burning resources for the full duration.

### How it works

On receiving `notifications/cancelled` with a matching `requestId`, stop processing, free resources, and **do not send a response**. The sender SHOULD ignore any response that arrives after cancellation. For 2025-11-25 Tasks-primitive requests, use `tasks/cancel` instead — `notifications/cancelled` is for regular requests only.

```python
import asyncio

@mcp.tool()
async def long_search(query: str, ctx: Context) -> list[dict]:
    results = []
    for chunk in paginate(query):
        # Cooperative checkpoint — raises if cancelled
        if ctx.is_cancelled():
            raise asyncio.CancelledError("client cancelled")
        results.extend(await fetch_chunk(chunk))
    return results
```

Uncancellable handlers make cancellation meaningless. A handler that calls blocking `time.sleep(60)` or synchronous HTTP cannot be interrupted, so the client sees the cancel ack but the server burns resources for another minute. Cooperative async with periodic cancel-checks is the only reliable implementation.

### Spec rules

- The `initialize` request **MUST NOT** be cancelled.
- `notifications/cancelled` only references requests in the **same direction**.
- For Tasks-primitive requests (2025-11-25), send `tasks/cancel` — not `notifications/cancelled`.
- If the request has already completed, the receiver MAY ignore the cancel notification.

### Progress notifications — companion to cancellation

Long tools should also report progress. Progress tokens belong in `params._meta.progressToken`, not `params`. The notifier sends `notifications/progress` with that token at the top level of the notification's params. `progress` MUST increase monotonically. Stop sending after the request completes. Never reuse a token across concurrent requests.

```python
@mcp.tool()
async def long_task(ctx: Context) -> str:
    total = 100
    for i in range(total):
        if ctx.is_cancelled():
            raise asyncio.CancelledError()
        await do_chunk(i)
        # FastMCP auto-reads progressToken from _meta
        await ctx.report_progress(progress=i + 1, total=total, message=f"Processed {i + 1}/{total}")
    return "done"
```

Putting `progressToken` at `params.progressToken` is a common silent bug — the spec only accepts `_meta.progressToken`. Treat progress as advisory UX, never as a correctness primitive — many clients drop progress notifications under load.

### Client support

| Client | Cancellation | Progress |
|---|---|---|
| Claude Desktop | unknown-2025-12 | partial |
| VS Code (Copilot) | native | native |
| Most others | unknown-2025-12 | unknown-2025-12 |

Source: MCP Spec 2025-11-25 — cancellation; MCP Spec 2025-11-25 — progress.

---

## Composing the four

The four primitives compose. Three high-leverage compositions:

1. **Long tool = progress + cancellation.** Read `params._meta.progressToken`; emit `notifications/progress` per chunk; check cancellation each loop; on cancel, raise and skip the response.
2. **Clarify-then-execute = elicitation + sampling.** Tool receives ambiguous goal → `elicitation/create` to pick specifics → `sampling/createMessage` to generate the artifact on the client's LLM. No server API key required.
3. **Out-of-band OAuth = URL-mode elicitation + roots-aware persistence.** Tool returns a URL elicitation → client opens browser → OAuth backend completes → server emits `notifications/progress` carrying readiness state. Persist the resulting refresh token keyed by `ctx.user_sub` (see `auth-identity.md` § OBO Pattern C).

```python
@mcp.tool()
async def research(topic: str, ctx: Context) -> str:
    # 1. Clarify with elicitation
    prefs = await ctx.elicit(
        message=f"How should I research '{topic}'?",
        schema=ResearchPreferences,
    )
    if prefs.action != "accept":
        return "cancelled"

    # 2. Long-running work with progress + cancellation
    sources = []
    for i, src in enumerate(iter_sources(prefs.data)):
        if ctx.is_cancelled():
            raise asyncio.CancelledError()
        await ctx.report_progress(i + 1, len(prefs.data.sources), f"Fetched {src.name}")
        sources.append(await fetch(src))

    # 3. Synthesize via sampling (client's LLM, no API key)
    resp = await ctx.session.create_message(
        messages=[{"role": "user", "content": {"type": "text", "text": synthesize_prompt(sources)}}],
        max_tokens=2048,
    )
    return resp.content.text
```

When to use: any agentic tool that runs >5 seconds, has ambiguous inputs, and wants to avoid shipping an API key.

When NOT to use: the target client does not advertise all three capabilities — degrade per the capability-check rule rather than fail.

---

## Stateless HTTP — the silent foot-gun

Sampling, elicitation, progress, and cancellation **all require a persistent server→client channel**. In stateless HTTP mode (no session ID, no SSE) none of them work. The failure mode is silent: the server issues `sampling/createMessage`, the client never receives it (no open SSE stream), the tool blocks forever or times out.

Detect stateless mode at server startup and either disable advanced-feature tools or raise a structured error when the client attempts to call one.

```python
mcp = FastMCP("server", stateless_http=False)  # default

@mcp.tool()
async def summarize(doc: str, ctx: Context) -> str:
    if ctx.session is None or getattr(ctx.session, "stateless", False):
        return (
            "ERROR: This server is running in stateless HTTP mode and cannot use sampling. "
            "Deploy with stateless_http=False (Streamable HTTP with sessions) to enable."
        )
    # ... proceed with sampling
```

FastMCP issue #1585 (2025) documents this exact foot-gun. Teams hit it when moving to serverless deployments (Cloudflare Workers, Lambda) without understanding that Streamable HTTP **with sessions** is required for bidirectional calls. Source: github.com/jlowin/fastmcp/issues/1585; MCP Spec 2025-11-25 — basic transports.

---

## `_meta` field — namespace conventions

Every request, result, and notification MAY carry `_meta`. The only reserved un-namespaced key is `progressToken` (backwards compat). Keys prefixed `io.modelcontextprotocol` are reserved for the spec. **All custom keys MUST use reverse-DNS**: `com.example/traceId`, `com.mycorp/tenant-id`. Do not put secrets in `_meta` — it is unauthenticated.

```python
@mcp.tool()
async def process(order_id: str, ctx: Context) -> dict:
    trace_id = ctx.request_meta.get("com.acme/trace-id") or new_trace_id()
    log.info("processing", trace=trace_id, order=order_id)
    result = await backend.process(order_id, trace=trace_id)
    ctx.response_meta["com.acme/trace-id"] = trace_id
    ctx.response_meta["com.acme/backend-version"] = backend.version
    return result
```

When NOT to use `_meta`: storing tokens, API keys, PII — `_meta` is not authenticated, not encrypted on the wire beyond TLS, and may be logged by clients. For secrets use URL-mode elicitation. Source: SEP-1788 / PR #1403 (2025-11).

---

## Completions

### When to use

If the server exposes resource templates or prompts with argument slots, implement `completion/complete`. The 2025-11-25 `context.arguments` field narrows suggestions based on previously selected arguments — when the user picks `language=python`, the `framework` completions return Django/Flask/FastAPI, not Rails.

### How it works

```python
@mcp.completion()
async def complete(ref, argument, context) -> dict:
    if ref.type == "ref/prompt" and ref.name == "code_review":
        if argument.name == "language":
            values = [l for l in LANGUAGES if l.startswith(argument.value)]
            return {"values": values[:100], "total": len(values), "hasMore": len(values) > 100}
        if argument.name == "framework":
            lang = (context.arguments or {}).get("language", "")
            values = [f for f in FRAMEWORKS_BY_LANG.get(lang, []) if f.startswith(argument.value)]
            return {"values": values[:100], "total": len(values), "hasMore": False}
    return {"values": []}
```

Cap responses at 100 values; set `hasMore: true` and `total` when truncating. Source: MCP Spec 2025-11-25 — completion.

When NOT to use: arguments are fully freeform (user queries, messages); client doesn't advertise `completions` (most clients except Claude Desktop and VS Code don't).

---

## Cross-references

- `client-compatibility.md` — full client-feature support matrix; `unknown-2025-12` markers
- `agentic-patterns.md` — the prompt-gate pattern when sampling/elicitation isn't supported; sampling vs elicitation vs prompt-gate decision
- `prompt-gates.md` — building human-in-the-loop without depending on advanced features
- `auth-identity.md` — URL-mode elicitation for OAuth and how OBO refresh tokens persist
- `transport-and-ops.md` — Streamable HTTP with sessions vs stateless HTTP
- `error-handling.md` — cancellation as an error path; loops and timeouts
- `threat-catalog.md` — sampling-based attacks (#8, #9, #10), elicitation abuse (#11)
