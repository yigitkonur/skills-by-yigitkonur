# Client compatibility — what each MCP client actually supports

Not every MCP client implements every feature. The wire protocol is one thing; the rendering, the silent feature drops, the schema dialects, and the transport quirks are another. Ship a server that works only on the spec and it will silently fail on Claude Desktop, Cursor, Cline, or Goose. This file is the per-client reality check. Cross-link `advanced-protocol.md` for sampling/elicitation/roots specifics, `model-behavior.md` for model-side tendencies, and `tools.md` for response-shape choices.

The headline rule: **negotiate features at handshake, degrade gracefully when missing**. A server that crashes on a client that doesn't support sampling is worse than a server that announces "this client doesn't support sampling — please summarize the data manually."

---

## The capability matrix

Columns: clients in production usage as of 2026-02. Cells: `native` (works), `partial` (caveats), `ignored` (announced but silently dropped), `—` (not applicable). Sources: [apify/mcp-client-capabilities v0.0.14](https://github.com/apify/mcp-client-capabilities) (2026-02), [mcp-availability.com](https://mcp-availability.com/) (2026-02), per-client changelogs.

| Feature | Claude Desktop | Claude Code | Cursor | VS Code | Goose | Cline | Continue |
|---|---|---|---|---|---|---|---|
| tools | native | native | native | native | native | native | native |
| static resources | partial (manual `+`) | native | native (1.6+, 2025-09) | native | native | native | ignored |
| dynamic resource templates | ignored | unknown | unknown | native | unknown | unknown | unknown |
| prompts | partial (manual attach) | native (`/mcp__svr__prompt`) | native | native | native | ignored | native |
| sampling (`sampling/createMessage`) | unknown | ignored | ignored | native (1.101+) | partial | ignored | ignored |
| elicitation (form mode) | unknown | ignored ([#7108](https://github.com/anthropics/claude-code/issues/7108)) | native (late 2025) | native (1.102+) | native (late 2025) | ignored | ignored |
| elicitation (URL mode) | unknown | unknown | unknown | partial (Insiders) | unknown | unknown | unknown |
| roots | unknown | native | native | native | ignored | ignored | unknown |
| structured content (`outputSchema`) | unknown | unknown | unknown | native | unknown | ignored ([#1865](https://github.com/cline/cline/issues/1865)) | unknown |
| tools/list_changed | unknown | ignored | native | native | unknown | native | unknown |
| readOnlyHint annotations | unknown | unknown | unknown | native (auto-approve) | unknown | unknown | unknown |
| stdio transport | native | native | native | native | native | native | native |
| Streamable HTTP | native | native | native | native | partial (remote-only) | partial (regression v3.17.5+) | native |
| SSE (legacy) | unknown | unknown | native | native | partial | native | native |
| OAuth 2.1 + DCR | partial (PKCE; pre-registered only) | partial | native (browser) | native (DCR + client-credentials) | partial | ignored ([#3090](https://github.com/cline/cline/issues/3090)) | unknown |

Add Codex CLI, Copilot CLI, Windsurf, Zed if you ship to those — see the source links above for the wider matrix. The seven columns above cover roughly 90% of installed-base usage.

---

## Common compatibility gotchas

### 1. Schema dialects are not portable

OpenAI strict mode and DeepSeek accept `$ref`, `oneOf`, `anyOf`, `allOf`. Gemini rejects `anyOf` and `$ref`. Mistral accepts only the bare minimum (`type`, `object`, `properties`, `required`, `string`). Llama 4 has no first-party tool-use training. The model side of this lives in `model-behavior.md`; the implication for client compatibility is that **your input schemas must lowest-common-denominator across the model the client routes to.**

Ship `oneOf` only when you know the model is OpenAI strict or DeepSeek. Otherwise:

```typescript
// Portable across all models — action enum substitutes for oneOf.
const schema = z.object({
  action: z.enum(["create", "update", "delete"]),
  payload: z.record(z.unknown()),
});
```

Cross-link `tools.md` § "CRUD — combined vs separate" and `model-behavior.md` Pattern 2 (Gemini `oneOf` substitution).

### 2. Content type rendering varies

VS Code renders `image`, `audio`, `resource`, and `mcp/app` content blocks. Claude Desktop renders text and image. Cline renders text only — `ImageContent` shows as `"Empty Response"` ([#1865](https://github.com/cline/cline/issues/1865)). Continue does not render progress notifications even when the server emits them.

**Always include a text content block alongside structured content or images:**

```python
return {
    "content": [
        {"type": "text", "text": human_readable_summary},
        {"type": "image", "mimeType": "image/png", "data": base64_png},
    ],
    "structuredContent": structured_payload,
}
```

The text block survives every client; the image and structured payload light up where supported. Never make the only content block a non-text one.

### 3. Transport support is not uniform

Stdio works everywhere. Streamable HTTP works on every modern client; Cline regressed it in v3.17.5+ ([#3829](https://github.com/cline/cline/issues/3829)) — connections drop after seconds. SSE was deprecated by the spec on 2025-06-18; Codex CLI removed it; VS Code, Cursor, Cline, and Continue still accept it for backcompat; Goose supports it remote-only.

Ship Streamable HTTP first, advertise it in your README, keep an SSE endpoint as a deprecated fallback for one more release, and log a warning when SSE is used. Once your client telemetry shows zero SSE traffic, retire it. See `transport-and-ops.md` for transport implementation details.

### 4. Authorization headers get dropped

Cline does not forward the `Authorization` header to SSE or Streamable HTTP servers ([#3090](https://github.com/cline/cline/issues/3090)). Windsurf is case-sensitive on `Authorization` and silently drops `authorization` (lowercase). Server-side workaround: log the resolved auth header on startup and expose a `whoami` tool that echoes received headers so operators can confirm end-to-end:

```typescript
server.tool("whoami", "Echo the auth principal the server sees.", {}, async (_, ctx) => ({
  content: [{ type: "text", text: JSON.stringify({
    authenticated_as: ctx.principal,
    headers_seen: Object.keys(ctx.request.headers),
  }, null, 2) }],
}));
```

### 5. Config root keys are not standardized

Every client except Zed reads a top-level `"mcpServers"` key. Zed reads `"context_servers"` under `settings.json`. Cursor strictly matches `"mcpServers"` — `"servers"` parses without error and produces "No Tools Found" with no log entry. If you ship an installer or deeplink, branch on target client:

```javascript
const key = client === "zed" ? "context_servers" : "mcpServers";
writeJson(configPath, { [key]: { acme: serverSpec } });
```

### 6. `tools/list_changed` is a no-op on Claude Code

Claude Code captures the tool list once per session and ignores `tools/list_changed` notifications. Cursor, Windsurf, Zed, Cline, and VS Code refresh on notification. If your server adds tools after a gated unlock (auth, feature flag), either:

1. Advertise all tools at startup and return `isError: true` on locked tools until unlocked, or
2. Require a session restart after unlock and surface that in the unlock tool's response.

Don't rely on `tools/list_changed` if Claude Code is in your client matrix.

### 7. The `instructions` field renders differently everywhere

The `initialize` response's `instructions` field is rendered by Claude Desktop into the system prompt, by Cursor as a tool-list footer, by Zed as a documentation block, by VS Code in a collapsible panel. **Don't put guardrails or security logic in `instructions`** — they will be trimmed, outranked, or ignored. Use `instructions` only for orientation: "this server manages billing; common workflows are X, Y, Z." Put enforcement on the server side (signed tokens, scope checks, gates).

---

## Feature negotiation at handshake

The MCP `initialize` response includes the client's `capabilities` object. Read it once, branch your behavior across the session.

```typescript
server.setRequestHandler(InitializedNotificationSchema, () => {
  const caps = server.getClientCapabilities() ?? {};
  serverState.client = {
    supportsSampling:    !!caps.sampling,
    supportsElicitation: !!caps.elicitation,
    supportsRoots:       !!caps.roots,
    supportsStructured:  !!caps.experimental?.structuredContent,
  };
});
```

Three patterns ride on top of this:

**Capability-aware tool selection.** Some tools require sampling or elicitation. Hide them from `tools/list` if the client doesn't support what they need:

```typescript
function listTools(): Tool[] {
  const tools = [coreTools.search, coreTools.fetch];
  if (serverState.client.supportsSampling) tools.push(samplingTools.summarize);
  if (serverState.client.supportsElicitation) tools.push(elicitTools.confirm_action);
  return tools;
}
```

**Capability-aware fallback inside a tool.** When a tool would prefer sampling but can do without:

```python
async def search_smart(ctx, query: str):
    results = await search_index(query, top_k=20)
    if "sampling" in (ctx.client_capabilities or {}):
        summary = await ctx.session.create_message(
            f"Summarize key findings:\n{json.dumps(results)}", max_tokens=300,
        )
        return {"results": results, "summary": summary}
    return {"results": results,
            "summary": "Sampling unavailable on this client. Top result: " + results[0]["title"]}
```

**Capability-aware response shape.** Send `structuredContent` always, but include a text content block for clients that ignore the structured payload (Cline, several others):

```python
return {
    "content": [{"type": "text", "text": human_summary}],
    "structuredContent": data,
}
```

Cross-link `advanced-protocol.md` for the full sampling and elicitation API; cross-link `tools.md` for `structuredContent` and content-block shapes.

---

## Graceful degradation — concrete patterns

### Sampling unavailable

```python
if "sampling" in ctx.client_capabilities:
    summary = await ctx.session.create_message(prompt, max_tokens=500)
else:
    summary = naive_template_summary(data)
```

The fallback may be lower quality but the tool returns a useful answer. Never crash on missing capabilities.

### Elicitation unavailable

```python
if "elicitation" in ctx.client_capabilities:
    answer = await ctx.session.elicit(message="Confirm deletion?", schema=ConfirmSchema)
    if not answer.confirmed: return {"content": [{"type": "text", "text": "Cancelled."}]}
else:
    return {"content": [{"type": "text",
        "text": "Confirmation required. Re-call with confirm=true to proceed."}]}
```

Cross-link `prompt-gates.md` for the `requires_approval` shape that works without elicitation.

### Structured content unavailable

```typescript
return {
  content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
  structuredContent: payload,                // ignored where unsupported
};
```

Vercel AI SDK and several others parse JSON from the text block. Always send both. Supabase is a public exemplar of opting out of `structuredContent` ([Supabase server source](https://github.com/supabase-community/supabase-mcp)) — they rely on text-block JSON parsing because Vercel AI SDK is their primary consumer.

### Roots unavailable

When the client doesn't support `roots/list`, fall back to a `working_directory` parameter on tools that need filesystem context:

```python
@mcp.tool
async def read_project_file(ctx, path: str, working_directory: str | None = None):
    if "roots" in ctx.client_capabilities:
        roots = await ctx.session.list_roots()
        base = roots[0].uri if roots else None
    else:
        base = working_directory or "."
    return {"content": [{"type": "text", "text": Path(base, path).read_text()}]}
```

### Resource templates unavailable

Many clients silently drop resource templates. Expose the same surface as a tool too:

```python
@mcp.resource("recipe://{cuisine}/{name}")  # works on VS Code, ignored on Claude Desktop
def recipe_resource(cuisine: str, name: str) -> str: ...

@mcp.tool(description="Get a recipe by cuisine and name. Use when resource://recipe is unavailable.")
def get_recipe(cuisine: str, name: str) -> dict: ...
```

The duplication is the cost of portability. Cross-link `resources-and-prompts.md` for the resource patterns, `client-compatibility.md` Pattern 1 above for the template-drop matrix.

---

## Test triad — three clients catch most issues

Run the server end-to-end on at least three clients spanning the compatibility spectrum:

- **VS Code** — full-spec implementation. If a feature works here and not on a target client, it's a client gap, not a server bug.
- **Claude Desktop or Claude Code** — loose interpretation, common consumer baseline.
- **Cline** — strict bugs, useful for catching missing fallbacks (auth header, ImageContent, structured content drops).

Add Cursor and Goose for a four-client matrix when shipping a public server. Cross-link `testing.md` for the broader test pyramid.

---

## Documented silent-failure cases

When a user reports "MCP doesn't work," check this list before suspecting your server:

1. **Cursor "No Tools Found" on wrong root key.** `.cursor/mcp.json` with `"servers": {...}` instead of `"mcpServers": {...}`. Parse succeeds, no tools surface, no warning. Fix: rename the key.
2. **Zed prompts with >1 argument disappear.** Server registers `code_review(path, language)`; Zed's `acceptable_prompt` filter drops it. Fix: collapse to a single JSON-string argument.
3. **Claude Desktop dynamic resources ignored.** `greeting://{name}` is invisible in the `+` attach menu; the same server works in Cline and VS Code. Fix: expose templates as tools too.
4. **Cline drops `Authorization` on SSE/HTTP.** Bearer token configured client-side; tool calls arrive at the server with no auth header; server returns 401; Cline shows "Connection closed." Fix: stdio transport, or wait for upstream Cline fix.
5. **Cursor >40-tool silent truncation (pre-2025-09).** Tools beyond cap appear enabled but are non-callable; agent apologizes "I cannot find a tool called…". Fix: ≤40 tools (or upgrade Cursor to 2025-09+ for the 80 cap).
6. **Claude Desktop + Cloudflare AI-bot rule.** OAuth completes (`/token` 200) but the next POST to `/mcp` hangs because Cloudflare's "Block AI Training Bots" managed rule fires. Fix: WAF exception for the MCP path.

Roughly 60% of "broken MCP" tickets in the wild are client quirks, not server bugs. Read the matrix first.

---

## Cross-references

- `advanced-protocol.md` — sampling, elicitation (form + URL), roots, cancellation; the full API for the capabilities tracked above.
- `model-behavior.md` — model-side schema and tool-call quirks that compound with client behavior.
- `tools.md` — response shape (`content` array, `structuredContent`, annotations); design decisions impacted by client rendering.
- `transport-and-ops.md` — stdio vs Streamable HTTP vs SSE, CORS, observability — the transport gotchas that surface as client failures.
- `resources-and-prompts.md` — resource and prompt primitives; template-drop matrix lives there.
- `prompt-gates.md` — the in-band approval pattern for clients that don't support elicitation.
- `testing.md` — the test triad and per-client smoke tests; agent-driven evals across clients.
