# MCP Client Compatibility: Per-Client Behavior

How to ship an MCP server that survives the 11 major clients in production, each of which interprets the same wire protocol differently, often silently.

## Master Capability Matrix

Columns are clients; cells use `native` (fully works), `partial` (implemented with caveats), `ignored` (announced but silently dropped), `unknown-YYYY-MM` (not verifiable as of that month). Sources: [apify/mcp-client-capabilities v0.0.14](https://github.com/apify/mcp-client-capabilities) (2026-02), [mcp-availability.com](https://mcp-availability.com/) (2026-02), and per-client changelogs linked in each profile.

| Feature | Claude Desktop | Claude Code | Cursor | Windsurf | Zed | Cline | Continue | VS Code | Copilot CLI | Codex CLI | Goose |
|---|---|---|---|---|---|---|---|---|---|---|---|
| tools | native | native | native | native | native | native | native | native | native | native | native |
| static resources | partial (manual `+` attach) | native | native (v1.6, 2025-09) | native | ignored | native | ignored | native | ignored | ignored | native |
| dynamic resource templates | ignored ([python-sdk #263](https://github.com/modelcontextprotocol/python-sdk/issues/263)) | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | ignored | unknown-2026-02 | unknown-2026-02 | native | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 |
| prompts | partial (manual attach) | native (`/mcp__svr__prompt`) | native | native | native (agent panel since 2025-12) | ignored | native | native (`/mcp.server.promptname`) | ignored | ignored | native |
| sampling | unknown-2026-02 | ignored ([FR #1785](https://github.com/anthropics/claude-code/issues/1785)) | ignored ([forum 149604](https://forum.cursor.com/)) | ignored | ignored | ignored ([#4522](https://github.com/cline/cline/discussions/4522)) | ignored | native (1.101, 2025-06) | ignored ("Method not found") | ignored | partial |
| elicitation (form) | unknown-2026-02 | ignored ([#7108 closed not-planned 2025-09](https://github.com/anthropics/claude-code/issues/7108)) | native (late 2025) | ignored | ignored | ignored | ignored | native (1.102+, 2025-09) | ignored | native | native (late 2025) |
| elicitation (URL mode) | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | partial (Insiders) | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 |
| roots | unknown-2026-02 | native | native | ignored | ignored ([#53156](https://github.com/zed-industries/zed/discussions/53156)) | ignored | unknown-2026-02 | native | ignored | ignored | ignored |
| completions | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | native (prompt inputs) | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 |
| progress notifications | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | partial (no UI stream) | partial (no UI stream, [#5790](https://github.com/continuedev/continue/issues/5790)) | native | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 |
| cancellation | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | native | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 |
| tools/list_changed | unknown-2026-02 | ignored | native | native | native | native | unknown-2026-02 | native | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 |
| annotations (readOnlyHint) | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | native (auto-approve) | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 |
| outputSchema / structuredContent | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | ignored ([#1865](https://github.com/cline/cline/issues/1865)) | unknown-2026-02 | native | unknown-2026-02 | native (`--output-schema`) | unknown-2026-02 |
| OAuth 2.1 | native (PKCE/S256) | partial (basic-auth reports) | native (browser flow) | native | native | ignored ([#3090](https://github.com/cline/cline/issues/3090), [#4188](https://github.com/cline/cline/issues/4188)) | unknown-2026-02 | native | partial (header-based) | native (`codex mcp login`) | partial (via `envs`) |
| Dynamic Client Registration | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 | ignored | unknown-2026-02 | native (with client-credentials fallback) | unknown-2026-02 | unknown-2026-02 | unknown-2026-02 |
| MCP Apps (interactive UI) | ignored | ignored | ignored | ignored | ignored | ignored | ignored | native (first client, [2026-01-26](https://code.visualstudio.com/blogs/2026/01/26/mcp-apps-support)) | ignored | ignored | partial (separate track) |
| stdio transport | native | native | native | native | native | native | native | native | native | native | native |
| Streamable HTTP | native | native | native | native | native | partial (regression v3.17.5+, [#3829](https://github.com/cline/cline/issues/3829)) | native | native | native (`type: http`) | native | partial (remote-only) |
| SSE (legacy) | unknown-2026-02 | unknown-2026-02 | native (legacy) | native | unknown-2026-02 | native | native | native | native (backcompat) | ignored | partial (remote-only) |
| spec revision targeted | 2025-06-18+ | 2025-06-18+ | 2025-11-25 | ≥2025-03-26 | 2025-11-25 | 2025-06-18 | "v1" | 2025-06-18 (full) | 2025-06-18 | 2025-06-18+ | 2025-06-18 (partial) |

---

## Pattern 1: Never rely on dynamic resource templates

Resource templates with URI parameters (`greeting://{name}`) are silently dropped by most consumer clients. Claude Desktop filters them out before they reach the UI; the user cannot attach them via the `+` menu. The same server works in Cline and VS Code. This behavior has been tracked in `python-sdk #263` as **open since 2025-03**.

Expose templates as tools parameterized by the same URI args:

```python
# DON'T: silently ignored by Claude Desktop
@mcp.resource("greeting://{name}")
def greet(name: str) -> str: ...

# DO: works everywhere
@mcp.tool(description="Generate a greeting for a named recipient.")
def greet(name: str) -> str: ...
```

Affected clients: Claude Desktop (confirmed), Zed (no resource subsystem at all), Copilot CLI, Codex CLI, Continue.

**Source:** [python-sdk #263](https://github.com/modelcontextprotocol/python-sdk/issues/263) — open 2025-03.

---

## Pattern 2: Keep tool count at or below 40

Cursor enforced a **hard 40-tool cap** from launch until **2025-09**, when it was doubled to **80**. Over the limit, tools appear enabled in the UI but are not callable — the agent will apologize that it "cannot find the tool." Windsurf documents a **100** cap. Claude Code does not cap but suffers **context bloat of roughly 15–30k tokens per server**; four servers consume ~67k before the first prompt, and community reports show many-server setups hitting ~150k tokens up-front (Tool Search, rolled out late 2025, claims a 46.9% reduction: 51k → 8.5k).

Prefer aggregated "router" tools that dispatch via an `action` parameter (see `tool-design.md` Pattern 8 — Toolhost facade).

Affected clients: Cursor (hard cap), Windsurf (hard cap), Claude Code (soft but expensive).

**Source:** [r/modelcontextprotocol — Cursor 40→80](https://www.reddit.com/r/modelcontextprotocol/comments/1ndfkcy/cursor_just_doubled_the_mcp_tools_limit_40_80/) (2025-09); [forum.cursor.com t/67976](https://forum.cursor.com/t/tools-limited-to-40-total/67976) (2024-12); [Windsurf Cascade docs](https://docs.windsurf.com/windsurf/cascade/mcp) (2026-02); [code.claude.com server-managed-settings](https://code.claude.com/docs/en/server-managed-settings) (2026-02).

---

## Pattern 3: Never ship prompts that take more than one argument

Zed's `context_store.rs::acceptable_prompt` filters out any prompt whose schema exceeds **one argument**. The prompt is dropped with no log and no UI indication — users see an empty prompt list. The filter has been in place since Zed's MCP support landed; the tracking issue was closed as **not-planned**.

Collapse multi-arg prompts into a single JSON argument, or expose the same logic as a tool:

```python
# DON'T: invisible in Zed
@mcp.prompt("code_review")
def review(path: str, language: str, strict: bool): ...

# DO: single JSON arg passes Zed's filter
@mcp.prompt("code_review")
def review(payload: str): ...  # payload: {"path": "...", "language": "...", "strict": true}
```

Affected clients: Zed.

**Source:** [zed-industries/zed #21944](https://github.com/zed-industries/zed/issues/21944) (2024-12, closed not-planned); [PR #43523](https://github.com/zed-industries/zed/pull/43523) (2025-12-16, agent-panel prompts landed).

---

## Pattern 4: Always return a text content block alongside `structuredContent`

Cline renders `ImageContent` and structured-only responses as `"Empty Response"`. Continue's UI does not stream progress updates even when the server emits them. Only VS Code fully round-trips structured output, annotations, and progress updates.

Dual-encode every response:

```python
return {
  "content": [
    {"type": "text", "text": summary_for_humans},
  ],
  "structuredContent": machine_readable_payload,
}
```

Affected clients: Cline (ImageContent bug), Continue (no progress UI), likely others with partial rendering.

**Source:** [cline/cline #1865](https://github.com/cline/cline/issues/1865); [continuedev/continue #5790](https://github.com/continuedev/continue/issues/5790).

---

## Pattern 5: Send `Authorization` with exact header casing

Windsurf's HTTP client is **case-sensitive** on `Authorization`; `authorization` (lowercase) is dropped during request construction. Cline goes further: it **does not forward the `Authorization` header to SSE or Streamable HTTP servers at all** (multiple open issues). Servers then return 401, Cline surfaces `"Connection closed"`, and users blame the server.

On the server, always log the resolved auth header on startup and expose a `whoami`-style tool that echoes the received headers so operators can confirm end-to-end:

```python
@mcp.tool(description="Echo the auth principal the server sees. Use to debug missing credentials.")
def whoami(ctx) -> dict:
    return {"authenticated_as": ctx.principal, "headers_seen": list(ctx.request.headers.keys())}
```

Affected clients: Windsurf (case bug), Cline (full drop).

**Source:** [cline/cline #3090](https://github.com/cline/cline/issues/3090); [cline/cline #4188](https://github.com/cline/cline/issues/4188); Windsurf header-casing surfaced in [docs.windsurf.com/cascade/mcp](https://docs.windsurf.com/windsurf/cascade/mcp) field examples (2026-02).

---

## Pattern 6: Treat sampling as optional, not available

The `sampling/createMessage` round-trip — which lets the server ask the client to run a model call on its behalf — is supported in **VS Code** (1.101+, uses the user's subscription and respects `modelPreferences`), JetBrains AI, Mistral Le Chat, and a few niche clients. Every other major client returns `Method not found` or ignores the request. Claude Code's FR is still open; Cursor declined; Cline and Copilot CLI return hard errors.

Capability-check first; fall back to a static path otherwise:

```python
if "sampling" in ctx.client_capabilities:
    summary = await ctx.session.create_message(prompt, max_tokens=500)
else:
    summary = local_template_summarize(data)  # no model needed
```

Affected clients: everyone except VS Code and a handful of partners.

**Source:** [anthropics/claude-code #1785](https://github.com/anthropics/claude-code/issues/1785); [cline/cline discussion #4522](https://github.com/cline/cline/discussions/4522); [github community discussion 160291](https://github.com/orgs/community/discussions/160291) (Copilot CLI); [code.visualstudio.com/blogs/2025/06/12/full-mcp-spec-support](https://code.visualstudio.com/blogs/2025/06/12/full-mcp-spec-support).

---

## Pattern 7: Branch on the config root key in installers

Every client except Zed consumes a top-level `"mcpServers"` key. **Zed uses `"context_servers"`** under `settings.json`; feeding it `"mcpServers"` yields no error and no servers. Cursor silently ignores any file whose root key is not exactly `"mcpServers"` — a typo of `"servers"` produces "No Tools Found" with nothing in logs.

If you ship an installer/deeplink, branch on target client:

```js
const key = client === "zed" ? "context_servers" : "mcpServers";
writeJson(configPath, { [key]: { myserver: spec } });
```

Affected clients: Zed (divergent key), Cursor (strict match).

**Source:** [zed.dev/docs/assistant/model-context-protocol](https://zed.dev/docs/assistant/model-context-protocol); [truefoundry.com — Cursor MCP setup guide](https://www.truefoundry.com/blog/mcp-servers-in-cursor-setup-configuration-and-security-guide) (2025).

---

## Pattern 8: Do not put safety logic in the `instructions` field

The initialize-result `instructions` string is rendered differently by every client: Claude Desktop injects it into the system prompt, Cursor appends it to the tool list, Zed treats it as a block of documentation, and VS Code surfaces it in a collapsible panel. Do not place guardrails ("never delete without confirmation") there — they will be trimmed, outranked by user prompts, or ignored entirely.

Put enforcement on the server side (require an explicit `confirm: true` parameter, or use `elicitation/create` where supported). Use `instructions` only for non-security orientation text.

Affected clients: all — behavior is not portable.

**Source:** [modelcontextprotocol.io specification/2025-11-25/changelog](https://modelcontextprotocol.io/specification/2025-11-25/changelog) (2025-11).

---

## Pattern 9: Assume `tools/list_changed` is a no-op somewhere

Claude Code ignores `tools/list_changed` notifications — the tool list is captured once per session. Cursor, Windsurf, Zed, Cline, and VS Code refresh on notification. If your server adds tools after a gated unlock (auth, feature flag), either:

1. Advertise all tools at startup and return `isError: true` until unlocked, **or**
2. Require a session restart after unlock and surface that in the unlock tool's response.

Affected clients: Claude Code (silent no-op).

**Source:** [apify/mcp-client-capabilities v0.0.14](https://github.com/apify/mcp-client-capabilities) (2026-02).

---

## Pattern 10: Prefer Streamable HTTP, keep an SSE fallback for one more release

The 2025-06-18 spec deprecates SSE. Codex CLI has already dropped SSE entirely. VS Code, Copilot CLI, Cursor, and Cline still accept SSE for backcompat. Goose supports only remote transports for SSE/HTTP; local stdio is recommended. Cline **regressed Streamable HTTP in v3.17.5+** — servers that worked on 3.17.4 disconnect after seconds on 3.17.5.

Serve both transports from the same origin, advertise Streamable HTTP first, and log a deprecation warning when SSE is used so you can retire it.

Affected clients: Codex CLI (SSE gone), Cline (HTTP regression), Goose (remote-only for both).

**Source:** [modelcontextprotocol.io specification/2025-11-25/changelog](https://modelcontextprotocol.io/specification/2025-11-25/changelog); [cline/cline #3829](https://github.com/cline/cline/issues/3829); [developers.openai.com/codex/cli/reference](https://developers.openai.com/codex/cli/reference) (2026-02).

---

## Pattern 11: Never assume OAuth 2.1 DCR works

Dynamic Client Registration (RFC 7591) is only verified in **VS Code**, which also implements a client-credentials fallback when DCR is unavailable. Claude Desktop requires PKCE + S256 but pre-registered clients only. Cline drops auth entirely on HTTP. Copilot CLI uses header-based auth with no DCR.

For remote servers, publish both:
- OAuth 2.1 PKCE with a pre-registered client ID (works in Claude Desktop, Cursor, Windsurf, Zed)
- Static bearer token via `Authorization` header (works in Copilot CLI, Codex CLI, fallback for Cline users who patched around #3090)

Document both in your README; do not rely on DCR alone.

Affected clients: all except VS Code for DCR; Cline for OAuth at all.

**Source:** [code.visualstudio.com/api/extension-guides/ai/mcp](https://code.visualstudio.com/api/extension-guides/ai/mcp); [cline/cline #3090](https://github.com/cline/cline/issues/3090).

---

## Pattern 12: Bypass Cloudflare AI-bot blocking on remote endpoints

Claude Desktop's OAuth flow completes the `/token` call (200) but the final POST to `/mcp` never arrives when Cloudflare's "Block AI Training Bots" managed rule is enabled on the origin. Users see OAuth succeed, then the connection silently hangs. Disable the Cloudflare AI-bot rule for the MCP path, or add a WAF exception for `User-Agent: Claude-User` and Anthropic IP ranges.

Affected clients: Claude Desktop (confirmed 2025-09 and 2025-11 reports).

**Source:** [r/mcp — after successful auth Claude never connects](https://www.reddit.com/r/mcp/comments/1nmp2wh/after_successful_auth_claude_never_connects_to_my/) (2025-11).

---

## Pattern 13: Emit human-readable text even when elicitation is declined

Elicitation (`elicitation/create`) lets a server pop a form in the client for structured input. VS Code (1.102+), Cursor (late 2025), Codex CLI, and Goose support it; Claude Code declined the feature as not-planned ([#7108](https://github.com/anthropics/claude-code/issues/7108), 2025-09). When elicitation is unavailable, the request returns either `Method not found` or a capability-error; the model then has no idea what was needed.

Always fall back to a plain-text prompt-for-input embedded in the tool response:

```python
if "elicitation" in ctx.client_capabilities:
    answer = await ctx.session.elicit(schema=ConfirmDelete)
else:
    return {"content": [{"type": "text",
        "text": "This action is destructive. Reply with `confirm=true` in the next call to proceed."}]}
```

Affected clients: Claude Code, Cline, Windsurf, Zed, Copilot CLI, Continue.

**Source:** [anthropics/claude-code #7108](https://github.com/anthropics/claude-code/issues/7108); [github.blog — MCP elicitation in Copilot](https://github.blog/ai-and-ml/github-copilot/building-smarter-interactions-with-mcp-elicitation-and-vs-code-1-102/) (2025-09-04).

---

## Pattern 14: Do not assume MCP Apps (interactive UI) is portable

MCP Apps — the 2026-01 spec addition that lets servers return interactive web UI panels — is so far implemented **only in VS Code** ([2026-01-26 Insiders → Stable](https://code.visualstudio.com/blogs/2026/01/26/mcp-apps-support)). Goose is tracking on a separate roadmap track. Everyone else ignores the content type.

If you use MCP Apps for the UI, always include an equivalent text/structured response path so the server degrades to a normal tool call on non-MCP-Apps clients:

```python
return {
  "content": [
    {"type": "text", "text": text_summary},
    {"type": "mcp/app", "url": "https://...", "sandbox": "strict"},  # ignored elsewhere
  ],
  "structuredContent": data,
}
```

Affected clients: every client except VS Code.

**Source:** [code.visualstudio.com/blogs/2026/01/26/mcp-apps-support](https://code.visualstudio.com/blogs/2026/01/26/mcp-apps-support).

---

## Pattern 15: Gate `readOnlyHint` annotations on VS Code

VS Code uses the `readOnlyHint` annotation to **skip the confirmation dialog** for read-only tools (big UX win: no modal on every `search`). No other client acts on the annotation. If you mark a tool `readOnlyHint: true` you MUST ensure it has no side effects — even a write of a cache file will now skip VS Code's confirmation and the user will have no chance to block it.

Reserve the hint for pure reads. For tools that are usually read-only but sometimes write (e.g., cache-warming reads), leave the hint off.

```python
@mcp.tool(
  description="Search the knowledge base.",
  annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
def search(query: str) -> list: ...
```

Affected clients: VS Code (acts on hint), others ignore.

**Source:** [code.visualstudio.com/api/extension-guides/ai/mcp](https://code.visualstudio.com/api/extension-guides/ai/mcp) (2026-02).

---

## Documented silent-failure cases

1. **Cursor "No Tools Found" on wrong root key.** `.cursor/mcp.json` with `{"servers": {...}}` instead of `{"mcpServers": {...}}`. The file parses, no error log, no warning, the agent simply sees no tools. Reproduce: swap the top-level key on a working config; restart Cursor. Fix: the key must be exactly `mcpServers`.
2. **Zed prompts with >1 argument disappear.** Server advertises `code_review(path, language)`; Zed's `acceptable_prompt` filter drops it. Reproduce: register any prompt with two arguments, call `prompts/list` from Zed's MCP inspector — prompt is absent. No UI indicator, no debug log. Fix: collapse to one JSON argument.
3. **Claude Desktop dynamic resources ignored.** Server exposes `config://app` and `greeting://{name}`; Claude Desktop's `+` menu shows only `config://app`. Identical server works in Cline. Reproduce: register one static and one templated resource; open the attach menu. Fix: expose templated URIs as tools.
4. **Cline drops `Authorization` on SSE/HTTP.** Configure a bearer token in `cline_mcp_settings.json`; tool calls arrive at the server with no `Authorization` header; server returns 401; Cline shows `"Connection closed"`. Reproduce: tcpdump the request. Fix: none in Cline; use stdio, or wait for #4188.
5. **Cursor >40-tool silent truncation (pre-2025-09).** Six servers × 7 tools each = 42 tools; all appear enabled in UI but calling tool #41 prompts the agent to apologize with `"I cannot find a tool called..."`. Reproduce: exceed the cap and enumerate tools. Fix: consolidate to ≤40 tools, or upgrade Cursor to 2025-09+ for the 80 cap.
6. **Claude Desktop + Cloudflare tunnel OAuth deadlock.** OAuth `/token` returns 200 then the Claude backend never POSTs to `/mcp`. Cloudflare's `cf.bot_management.managed_challenge` under "Block AI Training Bots" is the cause. Reproduce: put any origin behind Cloudflare with the AI-bot rule on, configure Claude Desktop to OAuth against it. Fix: WAF exception.

---

## Per-client profiles

### Claude Desktop (Anthropic)
- **Config path:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS); `%APPDATA%\Claude\claude_desktop_config.json` (Windows).
- **Packaging:** Desktop Extensions (`.mcpb`) now preferred over manual JSON.
- **Tool cap:** soft (no documented hard limit).
- **Spec revision:** 2025-06-18+.
- **Known bugs:** resources and prompts announced but only reachable through the `+` attach menu; dynamic resource templates silently dropped ([python-sdk #263](https://github.com/modelcontextprotocol/python-sdk/issues/263)); OAuth final POST blocked by Cloudflare AI-bot rule (reports 2025-09/11).
- **OAuth:** PKCE + S256 required, redirect to `https://claude.ai/api/mcp/auth_callback`.

### Claude Code (Anthropic)
- **Config path:** `~/.claude.json` plus workspace `./.mcp.json` — **not** `~/.claude/settings.json` despite some docs ([bug tracked 2025-11](https://www.petegypps.uk/blog/claude-code-mcp-configuration-bug-documentation-error-november-2025)).
- **Tool cap:** none, but context bloat is severe — 4 servers ≈ 67k tokens; many servers ≈ 150k. Tool Search feature (late 2025) cuts ~46.9% (51k → 8.5k).
- **Spec revision:** 2025-06-18+.
- **Known bugs:** server-managed settings cannot distribute MCP configs (enterprise blocker, [code.claude.com server-managed-settings](https://code.claude.com/docs/en/server-managed-settings)); `tools/list_changed` ignored; sampling and elicitation both declined ([#1785](https://github.com/anthropics/claude-code/issues/1785), [#7108](https://github.com/anthropics/claude-code/issues/7108)).
- **Prompt invocation:** `/mcp__<server>__<prompt>`.

### Cursor (Anysphere)
- **Config path:** `.cursor/mcp.json` (workspace) or `~/.cursor/mcp.json` (global). Root key **must** be `mcpServers`.
- **Tool cap:** **40 (2024 – 2025-09), doubled to 80 (2025-09)**; over-limit tools silently non-callable.
- **Spec revision:** 2025-11-25 linked.
- **Known bugs/CVEs:** MCPoison ([CVE-2025-54136](https://nvd.nist.gov/vuln/detail/CVE-2025-54136), fixed 1.3); CurXecute ([CVE-2025-54135](https://nvd.nist.gov/vuln/detail/CVE-2025-54135), fixed 1.3.9); path-case ([CVE-2025-59944](https://nvd.nist.gov/vuln/detail/CVE-2025-59944), fixed 1.7); install-dialog spoof ([CVE-2025-64106](https://nvd.nist.gov/vuln/detail/CVE-2025-64106), fixed 2.0); MCP access regression reported on 2.3.41 (2025-10).
- **Resources:** supported only since v1.6 (2025-09).

### Windsurf (Codeium)
- **Config path:** `~/.codeium/windsurf/mcp_config.json`. Supports `${env:VAR}` and `${file:/path}` interpolation.
- **Tool cap:** **100 (explicit hard limit)**.
- **Spec revision:** ≥2025-03-26.
- **Known bugs:** `Authorization` header is case-sensitive — lowercase is dropped. Windows 11 + local `npx @upstash/context7-mcp` triggers infinite Marketplace refresh loop ([upstash/context7 #829](https://github.com/upstash/context7/issues/829), 2025).

### Zed
- **Config path:** `settings.json` under the **`"context_servers"`** key (divergent from everyone else).
- **Tool cap:** none documented.
- **Spec revision:** 2025-11-25 linked.
- **Known bugs:** prompts with more than one argument are filtered out silently in `context_store.rs::acceptable_prompt` ([#21944](https://github.com/zed-industries/zed/issues/21944)); agent-panel prompt support only since [PR #43523](https://github.com/zed-industries/zed/pull/43523) (2025-12-16); no resources, no roots (FR [#53156](https://github.com/zed-industries/zed/discussions/53156) open); mixed `command`-string vs `command`-object shapes cause parse failures.

### Cline (VS Code extension)
- **Config path:** `cline_mcp_settings.json` with `alwaysAllow: []` allow-list.
- **Tool cap:** none.
- **Spec revision:** 2025-06-18 referenced.
- **Known bugs:** Streamable HTTP regression v3.17.5+ ([#3315, #3829](https://github.com/cline/cline/issues/3829)); `Authorization` header not sent to SSE/HTTP servers ([#3090](https://github.com/cline/cline/issues/3090), [#4188](https://github.com/cline/cline/issues/4188)); SSE server names rendered as `undefined` ([#3837](https://github.com/cline/cline/issues/3837)); TCP connections close after 5 minutes on SSE ([#3662](https://github.com/cline/cline/issues/3662)); `ImageContent` displayed as `"Empty Response"` ([#1865](https://github.com/cline/cline/issues/1865)); default MCP directory hardcoded `Documents/Cline/MCP` breaks on Japanese Windows and iCloud-synced Documents ([#2762, #3501](https://github.com/cline/cline/issues/3501)); sampling and elicitation both rejected ([#4522](https://github.com/cline/cline/discussions/4522)).

### Continue
- **Config path:** `.continue/mcpServers/*.yaml` (workspace) or hub `config.yaml`.
- **Tool cap:** none.
- **Spec revision:** "v1" (project-internal).
- **Known bugs:** MCP only active in agent mode (not chat or edit); Streamable HTTP progress updates not rendered in UI ([#5790](https://github.com/continuedev/continue/issues/5790), closed without resolution).
- **Docs:** [docs.continue.dev/customize/deep-dives/mcp](https://docs.continue.dev/customize/deep-dives/mcp).

### VS Code (native MCP, Microsoft)
- **Config paths:** `.vscode/mcp.json` (workspace), user profile `mcp.json`, `devcontainer.json` under `customizations.vscode.mcp.servers`, CLI `code --add-mcp '{...}'`, or `vscode:mcp/install?{json}` web-install URL.
- **Tool cap:** none.
- **Spec revision:** **2025-06-18 (full implementation)**.
- **GA:** 2025-07-14 with v1.102 under org-policy gate ([github.blog/changelog/2025-07-14](https://github.blog/changelog/2025-07-14-model-context-protocol-mcp-support-in-vs-code-is-generally-available/)).
- **Unique features:** annotations (`readOnlyHint` auto-approves reads); prompt-input completions; resource updates and streaming logs; elicitation; sampling using the user's model subscription respecting `modelPreferences`; roots; DCR + client-credentials fallback; **MCP Apps first client** ([2026-01-26 Insiders → Stable](https://code.visualstudio.com/blogs/2026/01/26/mcp-apps-support)).
- **Sandboxing:** enabled on macOS/Linux stdio; not on Windows.

### Copilot CLI (GitHub)
- **Config path:** `~/.copilot/mcp-config.json`.
- **Transports:** stdio / HTTP (Streamable, `type: http`) / SSE (legacy backcompat).
- **Tool cap:** `*` wildcard default; no numeric limit.
- **Spec revision:** 2025-06-18.
- **Capabilities:** tools only — no resources, prompts, sampling, elicitation, roots.
- **Commands:** `/mcp show`, `/mcp edit`, `/mcp disable`.
- **Docs:** [docs.github.com/copilot/copilot-cli/add-mcp-servers](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers); sampling rejection discussed in [community 160291](https://github.com/orgs/community/discussions/160291).

### Codex CLI (OpenAI)
- **Config path:** `~/.codex/config.toml` with `[mcp_servers.<name>]` blocks; supports `supports_parallel_tool_calls` and per-tool `[mcp_servers.<name>.tools.<tool>] approval_mode`.
- **Transports:** stdio, Streamable HTTP. **SSE not supported.**
- **Tool cap:** none.
- **Spec revision:** 2025-06-18+.
- **Distinctive behavior:** MCP tools run **serialized by default**; parallel tool calls are opt-in. Codex Cloud does not yet support MCP servers (cited proxy/credential-forwarding blockers). `codex mcp-server` exposes Codex itself as an MCP stdio server. `codex mcp login <server>` handles Streamable HTTP OAuth. `--output-schema` flag for structured output. Reference: [developers.openai.com/codex/cli/reference](https://developers.openai.com/codex/cli/reference).

### Goose (Block)
- **Config path:** `~/.config/goose/config.yaml`.
- **Install:** deeplink only for stdio + `uvx`; HTTP/SSE manual. Deeplink does **not** pass env vars.
- **Tool cap:** none.
- **Spec revision:** 2025-06-18 (partial).
- **Known behavior:** elicitation landed late 2025 (Desktop confirmed); Tasks from 2025-11-25 spec not supported despite initial community belief ([r/mcp — 2026-02](https://www.reddit.com/r/mcp/comments/1qhkpk4/goose_support_for_mcp_tasks_and_elicitation/)). Remote-only for Streamable HTTP and SSE.
- **Docs:** [gofastmcp.com/integrations/goose](https://gofastmcp.com/integrations/goose).

---

## How to use this reference

- Before shipping a server, read the **matrix** row-by-row and list every feature you use; any `ignored` or `partial` cell for a target client is a portability task.
- Run the server under at least three clients spanning the compatibility spectrum: VS Code (full spec), Claude Desktop (loose), Cline (strict bugs) — that triad catches most silent failures.
- When a user reports a bug, check the **Documented silent-failure cases** before debugging your server code: 60%+ of "broken MCP" tickets are client quirks.
- Cite the `YYYY-MM` markers in the matrix when escalating: `unknown` means unverified as of that month, not absent.
