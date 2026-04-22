# Advanced MCP Protocol Features

12 patterns for sampling, elicitation, roots, completions, progress, cancellation, and the `_meta` field — the parts of the spec beyond tools/resources/prompts that determine whether your server feels static or agentic.

Client support is uneven. Every one of these features can be silently dropped by the client, so capability-checks and graceful fallbacks are non-negotiable.

## Pattern 1: Capability-Gate Every Advanced Feature Before Using It

Rule: never invoke `sampling/createMessage`, `elicitation/create`, or `roots/list` without first inspecting the client's declared capabilities from `initialize`. If the capability is absent, fall back to embedding the request in a regular tool response and let the calling agent handle it.

Most clients silently fail advanced calls. GitHub Copilot CLI returns `"Method not found: sampling/createMessage"` for sampling (community discussion #160291, 2025-09); Claude Code closed the elicitation feature request as "not planned" (anthropics/claude-code #7108, 2025-09-04). A server that assumes support crashes on the majority of clients.

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
        "Please summarize the following document yourself and call `save_summary` with the result.\n\n"
        + doc
    )
```

When to use: always, for every one of `sampling`, `elicitation`, `roots`, and `completions`.

**Source:** [MCP Spec 2025-11-25 — sampling](https://modelcontextprotocol.io/specification/2025-11-25/client/sampling) (2025-11); [GitHub community #160291](https://github.com/orgs/community/discussions/160291) (2025-09)

---

## Pattern 2: Use Sampling to Keep the API Key on the Client Side

Rule: when a tool needs LLM reasoning mid-execution, call `sampling/createMessage` instead of shipping your own API key or HTTP client to a model provider. Inference cost, rate limits, and model choice stay on the user's side.

This unlocks zero-key deployments: the server never needs `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`, so it can be distributed publicly, run in CI, or shipped to untrusted users without credential leakage. The 2025-11-25 revision also added `tools` and `toolChoice` parameters, enabling "server-side agent loops using standard MCP primitives" (WorkOS, 2025-11) — a server can run a bounded inner reasoning loop entirely on the client's LLM.

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

When to use: server-side sub-reasoning (summarization, classification, ranking), multi-step agent loops within one tool call, NPC dialogue generation, or any workflow where the server would otherwise need its own API key.

When NOT to use: the client is Claude Code, Cursor, Windsurf, Zed, Cline, Continue, or Copilot CLI — none of them support sampling as of 2025-12. Detect and fall back per Pattern 1.

**Source:** [MCP Spec 2025-11-25 changelog](https://modelcontextprotocol.io/specification/2025-11-25/changelog) (2025-11); [FastMCP sampling docs](https://gofastmcp.com/servers/sampling) (2025-11)

---

## Pattern 3: Sampling-With-Tools Requires Matching `ToolResultContent` For Every `ToolUseContent`

Rule: when using 2025-11-25 sampling-with-tools to drive a multi-turn inner loop, your server MUST respond to every `ToolUseContent` returned by the client with a matching `ToolResultContent` before the next `createMessage` call. Drop one and the conversation diverges or the client errors.

The `tools: {}` capability flag is new in 2025-11-25 and is absent on pre-2025-11 clients. Check `caps.sampling.tools is not None` before sending tools. Also: wrap the inner loop in an iteration limit (typical: 5-10) to prevent runaway cost on the user's account — users pay for every sampled token.

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

When to use: agentic tools that need several reasoning turns (research, refactoring, planning) and you want the compute paid by the client.

**Source:** [MCP Spec 2025-11-25 — sampling](https://modelcontextprotocol.io/specification/2025-11-25/client/sampling) (2025-11)

---

## Pattern 4: Use Elicitation To Clarify Missing Arguments, Not To Fish For Secrets

Rule: for ambiguous, missing, or confirmable arguments (dates, sizes, destructive confirmations), call `elicitation/create` with a flat JSON Schema. For passwords, API keys, OAuth tokens, or payment details, use URL-mode elicitation (Pattern 5) instead.

Form-mode elicitation (introduced 2025-06-18, expanded 2025-11-25) is restricted by spec to flat objects with primitive properties only — `string`, `number`, `integer`, `boolean`, plus enums. No nested objects, no arrays-of-objects, and `string.format` is limited to `email`, `uri`, `date`, `date-time`. The spec also mandates that clients MUST NOT send passwords via form mode. In practice clients don't enforce the restriction, so a malicious or sloppy server that requests `{"password": "string"}` becomes a credential-exfiltration surface (mor10web on r/mcp, 2025-11).

```python
from pydantic import BaseModel, Field

class BookingPreferences(BaseModel):
    checkAlternative: bool = Field(description="Would you like to check another date?")
    alternativeDate: str = Field(default="2024-12-26", description="Alternative date (YYYY-MM-DD)")

@mcp.tool()
async def book_table(date: str, time: str, party_size: int, ctx: Context) -> str:
    if date == "2024-12-25":
        result = await ctx.elicit(
            message=f"No tables for {party_size} on {date}. Another date?",
            schema=BookingPreferences,
        )
        if result.action == "accept" and result.data:
            return f"[SUCCESS] Booked for {result.data.alternativeDate}"
        return "[CANCELLED] Booking cancelled"
    return f"[SUCCESS] Booked for {date} at {time}"
```

When to use: clarify-missing-arg (shirt size, color), confirm irreversible actions (workspace delete), progressive input gathering inside a single tool call, recover from validation exceptions mid-tool.

When NOT to use: requesting credentials — use Pattern 5. Running under stateless HTTP — see Pattern 12.

**Source:** [MCP Spec 2025-11-25 — elicitation](https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation) (2025-11); [python-sdk elicitation.py](https://github.com/modelcontextprotocol/python-sdk/blob/main/examples/snippets/servers/elicitation.py) (2025-11)

---

## Pattern 5: URL-Mode Elicitation For OAuth, Secrets, And Payments

Rule: when the tool needs the user to authenticate, grant OAuth, or enter a secret/payment detail, use URL-mode elicitation (2025-11-25). The client opens the URL in an isolated browser surface the LLM cannot observe, so tokens never enter the model context.

Form-mode is inadequate for secrets because the value round-trips through the client and (in many implementations) becomes visible in the conversation. URL mode delegates the secret-handling surface to a real browser + your OAuth/payment provider. Pair it with a backend state binding keyed to the user's OAuth `sub` — the spec MUSTs that URL elicitation state be tied to user identity, not just session ID, to prevent session-hijack replay.

```python
# FastMCP-style; raw SDKs use raise UrlElicitationRequiredError
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
    # Backend completes out-of-band; poll or wait
    if state_store.get(eid)["status"] == "granted":
        return "Stripe connected."
    return "Connection not completed."
```

When to use: OAuth flows, API key entry, payment confirmation, any secret-handling UX where the LLM must not see the value.

When NOT to use: simple arg clarification — form mode is lower friction. Client does not advertise `elicitation.url` in capabilities (only VS Code Insiders had it as of 2025-12).

**Source:** [MCP Spec 2025-11-25 — elicitation](https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation) (2025-11); [MCP Spec changelog](https://modelcontextprotocol.io/specification/2025-11-25/changelog) (2025-11)

---

## Pattern 6: Honor `roots/list` Instead Of Hard-Coding Workspace Paths

Rule: on session start (and on every `notifications/roots/list_changed`), call `roots/list` and scope all filesystem access to the returned `file://` URIs. Validate every path with `os.path.realpath` + prefix check to block symlink traversal. Fall back to CLI args or CWD only when the client does not advertise `roots.listChanged`.

The spec explicitly mandates "validate all root URIs to prevent path traversal." Servers that take `--dir=` flags and ignore roots break every time the user opens a new folder mid-session, because the server keeps indexing the old one. Roots are `file://` only — reject `http://`, `s3://`, etc. per spec.

```python
import os

async def refresh_roots(ctx: Context) -> list[str]:
    caps = ctx.session.client_capabilities
    if not (caps and caps.roots):
        return [os.getcwd()]  # fallback
    resp = await ctx.session.list_roots()
    roots = []
    for r in resp.roots:
        if not str(r.uri).startswith("file://"):
            continue
        path = str(r.uri).removeprefix("file://")
        roots.append(os.path.realpath(path))
    return roots

def is_inside_roots(path: str, roots: list[str]) -> bool:
    real = os.path.realpath(path)
    return any(real == r or real.startswith(r + os.sep) for r in roots)
```

When to use: any server that reads or writes files — filesystem, code search, git, build tools.

When NOT to use: the client is Zed, Cursor, Windsurf, Cline, Continue, or Copilot CLI (no roots support 2025-12; see Pattern 12 matrix) — provide an explicit `workspace_path` tool argument instead.

**Source:** [MCP Spec 2025-06-18 — roots](https://modelcontextprotocol.io/specification/2025-06-18/client/roots) (2025-06)

---

## Pattern 7: Implement `completion/complete` With Context-Aware Narrowing

Rule: if your server exposes resource templates or prompts with argument slots, implement `completion/complete`. Use the 2025-11-25 `context.arguments` field to narrow suggestions based on previously selected arguments. Cap responses at 100 values and set `hasMore: true` + `total` when truncating.

Completions are the MCP equivalent of shell tab-completion. Without them, users face freeform text entry for values that have a known finite set — wrong value, tool fails, model retries blindly. The 2025-11-25 `context.arguments` addition closes a usability gap: when a user picks `language=python`, the `framework` completions should return Django/Flask/FastAPI, not Rails.

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

When to use: resource templates with parameters, prompts with enum-ish arguments, dynamic lists (projects, models, repos) fetched live.

When NOT to use: arguments are fully freeform text (user queries, messages). Client does not advertise `completions` (most clients except Claude Desktop and VS Code do not).

**Source:** [MCP Spec 2025-11-25 — completion](https://modelcontextprotocol.io/specification/2025-11-25/server/utilities/completion) (2025-11)

---

## Pattern 8: Progress Tokens Belong In `params._meta`, Not `params`

Rule: the requester puts `progressToken` in `params._meta.progressToken`. The notifier sends `notifications/progress` with that token at the top level of the notification's params. `progress` MUST increase monotonically. Stop sending after the request completes. Never reuse a token across concurrent requests.

Putting `progressToken` at `params.progressToken` is a common, silent bug — the spec only accepts `_meta.progressToken` (base protocol `_meta` rules). Flooding notifications violates the spec's SHOULD-rate-limit clause and some clients drop the connection under load (matt8p on r/mcp, 2025: "very few MCP clients support notifications"). Treat progress as advisory UX only — never rely on it for correctness.

```python
# Request sent by the client (illustrative)
# {"method":"tools/call",
#  "params":{"_meta":{"progressToken":"abc123"},
#            "name":"long_task","arguments":{}}}

@mcp.tool()
async def long_task(ctx: Context) -> str:
    total = 100
    for i in range(total):
        await do_chunk(i)
        # FastMCP auto-reads progressToken from _meta
        await ctx.report_progress(progress=i + 1, total=total, message=f"Processed {i + 1}/{total}")
    return "done"
```

When NOT to use: fast operations (<1s) — overhead exceeds benefit. Stateless HTTP mode with ephemeral worker — no channel to send async notifications (Pattern 12).

**Source:** [MCP Spec 2025-11-25 — progress](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/progress) (2025-11)

---

## Pattern 9: Handle `notifications/cancelled` Cooperatively — And Never Cancel `initialize` Or Tasks

Rule: on receiving `notifications/cancelled` with a matching `requestId`, stop processing, free resources, and do NOT send a response. The sender SHOULD ignore any response that arrives after cancellation. For 2025-11-25 Tasks-primitive requests, use `tasks/cancel` instead — `notifications/cancelled` is for regular requests only.

Uncancellable handlers make cancellation meaningless. A handler that calls blocking `time.sleep(60)` or synchronous HTTP cannot be interrupted, so the client sees the cancel ack but the server burns resources for another minute. Cooperative async with periodic cancel-checks is the only reliable implementation. The spec also forbids cancelling the `initialize` request (client→server) and requires that `notifications/cancelled` only reference requests in the same direction.

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

When NOT to use: you're implementing the 2025-11-25 Tasks primitive — send `tasks/cancel` instead. Request has already completed — spec says receiver MAY ignore.

**Source:** [MCP Spec 2025-11-25 — cancellation](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/cancellation) (2025-11)

---

## Pattern 10: Namespace Custom `_meta` Keys With Reverse-DNS; Reserve Un-Namespaced For The Protocol

Rule: every request, result, and notification MAY carry `_meta`. The only reserved un-namespaced key is `progressToken` (backwards compat). Keys prefixed `io.modelcontextprotocol` are reserved for the spec. All custom keys MUST use reverse-DNS: `com.example/traceId`, `com.mycorp/tenant-id`. Do not put secrets in `_meta` — it is unauthenticated.

SEP-1788 (@domdomegg, PR #1403) formalizes these rules. Un-namespaced custom keys (`tenant_id`, `trace`) will break once the spec adopts a conflicting name. `_meta` is the canonical carrier for: `progressToken`, trace IDs, tenant IDs, experimental features pre-spec, and client build numbers for observability. Clients MAY strip unknown `_meta` keys, so do not rely on round-trip guarantees.

```python
# Propagating a trace ID end-to-end
@mcp.tool()
async def process(order_id: str, ctx: Context) -> dict:
    trace_id = ctx.request_meta.get("com.acme/trace-id") or new_trace_id()
    log.info("processing", trace=trace_id, order=order_id)
    result = await backend.process(order_id, trace=trace_id)
    # Return meta on the result; clients MAY relay it
    ctx.response_meta["com.acme/trace-id"] = trace_id
    ctx.response_meta["com.acme/backend-version"] = backend.version
    return result
```

When NOT to use: storing tokens, API keys, PII — `_meta` is not authenticated, not encrypted on the wire beyond TLS, and may be logged by clients. For secrets use URL-mode elicitation (Pattern 5).

**Source:** [SEP-1788 / PR #1403](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1788) (2025-11); [MCP Spec 2025-11-25 changelog](https://modelcontextprotocol.io/specification/2025-11-25/changelog) (2025-11)

---

## Pattern 11: Compose Progress + Cancellation, Sampling + Elicitation, And URL-Mode + `_meta` For Full Agentic UX

Rule: the advanced features compose. The three highest-leverage compositions:

1. **Long tool = progress + cancellation.** Read `params._meta.progressToken`; emit `notifications/progress` per chunk; check cancellation each loop; on cancel, raise and skip the response.
2. **Clarify-then-execute = elicitation + sampling.** Tool receives ambiguous goal → `elicitation/create` to pick specifics → `sampling/createMessage` to generate the artifact on the client's LLM. No server API key required.
3. **Out-of-band OAuth = URL-mode elicitation + `_meta` + progress.** Tool raises `UrlElicitationRequiredError` → client opens browser → OAuth backend completes → server emits `notifications/progress` carrying `_meta.io.modelcontextprotocol/auth-state: "granted"` to signal readiness.

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

When NOT to use: the target client does not advertise all three capabilities — degrade per Pattern 1 rather than fail.

**Source:** [MCP Spec 2025-11-25 — sampling](https://modelcontextprotocol.io/specification/2025-11-25/client/sampling) (2025-11); [MCP Spec 2025-11-25 — elicitation](https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation) (2025-11)

---

## Pattern 12: Detect Stateless HTTP Mode Early — Advanced Features Silently Break Without A Session

Rule: sampling, elicitation, progress, and cancellation all require a persistent server→client channel. In stateless HTTP mode (no session ID, no SSE) none of them work. Detect stateless mode at server startup and either (a) disable advanced-feature tools, or (b) raise a structured error when the client attempts to call one.

FastMCP issue #1585 (2025) documents this exact foot-gun: "elicitation/sampling/etc cannot work in stateless mode." Teams hit it when moving to serverless deployments (Cloudflare Workers, Lambda) without understanding that Streamable HTTP with sessions is required for bidirectional calls. The failure mode is silent: the server issues a `sampling/createMessage` request, the client never receives it (no open SSE stream), the tool blocks forever or times out.

```python
mcp = FastMCP("server", stateless_http=False)  # default

@mcp.tool()
async def summarize(doc: str, ctx: Context) -> str:
    if ctx.session is None or getattr(ctx.session, "stateless", False):
        return (
            "ERROR: This server is running in stateless HTTP mode and cannot use sampling. "
            "Deploy with stateless_http=False (Streamable HTTP with sessions) to enable."
        )
    ...
```

When to use: every server that plans to deploy behind serverless, load balancers, or any architecture that might be stateless.

**Source:** [FastMCP issue #1585](https://github.com/jlowin/fastmcp/issues/1585) (2025); [MCP Spec 2025-11-25 — basic transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) (2025-11)

---

## Client Support Matrix (2025-12)

Feature support is uneven. Ship capability-checks. `native` = advertises capability and implements it; `partial` = advertises but incomplete/buggy; `ignored` = silently drops or returns "Method not found"; `unknown-YYYY-MM` = not documented or tested at time of survey.

| Feature            | Claude Desktop | Claude Code                  | Cursor                 | Windsurf        | Zed             | Cline           | Continue        | VS Code (Copilot)          | Copilot CLI                    | Goose           |
|--------------------|----------------|------------------------------|------------------------|-----------------|-----------------|-----------------|-----------------|----------------------------|--------------------------------|-----------------|
| sampling           | ignored        | ignored (FR #1785 open)      | ignored (forum 149604) | ignored         | ignored         | ignored (#4522) | ignored         | native (1.101, 2025-06)    | ignored (community #160291)    | partial (2025-11) |
| sampling/tools     | unknown-2025-12| ignored                      | ignored                | ignored         | ignored         | ignored         | ignored         | partial (2025-11-25)       | ignored                        | unknown-2025-12 |
| elicitation (form) | unknown-2025-12| ignored (#7108 "not planned")| native (community)     | ignored         | ignored         | ignored (#4522) | ignored         | native (1.102, 2025-09)    | unknown-2025-12                | native (desktop) |
| elicitation (url)  | unknown-2025-12| ignored                      | unknown-2025-12        | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | partial (Insiders, 2025-11)| unknown-2025-12                | unknown-2025-12 |
| roots              | native         | native (2025-11)             | ignored                | ignored         | ignored (#53156)| ignored         | ignored         | native (1.101)             | ignored                        | native          |
| completions        | native         | unknown-2025-12              | unknown-2025-12        | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | native (1.101)             | unknown-2025-12                | unknown-2025-12 |
| progress           | partial        | unknown-2025-12              | unknown-2025-12        | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | native                     | unknown-2025-12                | unknown-2025-12 |
| cancellation       | unknown-2025-12| unknown-2025-12              | unknown-2025-12        | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | native                     | unknown-2025-12                | unknown-2025-12 |
| `_meta` passthrough| partial        | partial                      | partial                | partial         | partial         | partial         | partial         | partial                    | partial                        | partial         |

**Sources:** [VS Code MCP blog 2025-06-12](https://code.visualstudio.com/blogs/2025/06/12/full-mcp-spec-support) (2025-06); [GitHub Copilot elicitation blog 2025-09-04](https://github.blog/ai-and-ml/github-copilot/building-smarter-interactions-with-mcp-elicitation) (2025-09); [anthropics/claude-code #7108](https://github.com/anthropics/claude-code/issues/7108) (2025-09); [GitHub community #160291](https://github.com/orgs/community/discussions/160291) (2025-09); [zed-industries/zed #53156](https://github.com/zed-industries/zed/discussions/53156) (2025-11)
