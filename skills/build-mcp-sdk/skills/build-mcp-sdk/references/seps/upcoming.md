# Upcoming Spec Changes (Accepted SEPs)

These SEPs have been accepted but do not yet have final reference implementations. They represent future changes that may affect how you build MCP servers. Monitor for finalization before implementing.

## SEP-2207: OIDC Refresh Token Guidance

**Status:** Accepted (created 2026-02-04)

Provides guidance for deployments using OIDC-style authorization servers where refresh token behavior depends on `offline_access` scope.

**What changes:**

For **clients:**
- Include `refresh_token` in `grant_types` in client metadata
- Check if AS metadata lists `offline_access` in `scopes_supported`
- If yes and client needs refresh token, append `offline_access` to authorization scopes
- Do NOT assume `offline_access` guarantees a refresh token

For **resource servers (MCP servers):**
- SHOULD NOT include `offline_access` in `WWW-Authenticate` scope parameter
- SHOULD NOT include `offline_access` in Protected Resource Metadata `scopes_supported`
- This is a "stay out of the conversation" guidance — refresh token decisions are between client and AS

**When to prepare:** If you're implementing custom OAuth auth middleware. Unlikely to affect servers using the SDK's built-in auth unless you're customizing Protected Resource Metadata.

## SEP-2260: Server Requests Must Be Tied to Client Requests

**Status:** Accepted (created 2026-02-16)

Tightens the spec from SHOULD to MUST: `sampling/createMessage`, `roots/list`, and `elicitation/create` MUST only be sent within the context of an active client-to-server request (e.g., inside a tool handler). Standalone server-initiated requests of these types MUST NOT be implemented.

**What is prohibited:**
```typescript
// WRONG — background task with no client request context
async function backgroundTask(session) {
  const result = await session.createMessage(...); // MUST NOT
}
```

**What remains correct:**
```typescript
// RIGHT — nested inside a tool handler (client request context exists)
server.registerTool("analyze", config, async (args, extra) => {
  const result = await extra.sendRequest({ method: "sampling/createMessage", ... });
  // This is fine — we're inside a tool handler
});
```

**Exception:** `ping` MAY be sent by either party at any time.

**What changes for transport:**
- POST-response messages MUST relate to the originating client request
- On standalone GET SSE streams: server MAY send notifications and pings only
- Clients receiving unsolicited server-to-client requests SHOULD respond with `-32602`

**When to prepare:** If your server uses `sampling/createMessage` or `elicitation/create` from background tasks, timers, or event handlers that are not within a tool/resource/prompt handler. Redesign those flows to trigger from within request handlers.

## SDK Tiering System (SEP-1730)

**Status:** Final (informational for SDK developers)

Defines three tiers for MCP SDKs with different conformance and maintenance requirements:

| Tier | Conformance | Feature timeline | Issue response |
|---|---|---|---|
| **Tier 1** | 100% tests | Before spec release | 2 business days |
| **Tier 2** | 80% tests | Within 6 months | Active tracking |
| **Tier 3** | No minimum | No commitment | No commitment |

The TypeScript SDK (`@modelcontextprotocol/sdk`) is the reference implementation maintained by Anthropic and is a natural Tier 1 candidate, though specific assignments are not published in the SEP.

**What this means for you:** Tier 1 SDKs implement all protocol features before each spec release. When you see a new spec feature, the TypeScript SDK should have it available shortly after (or before) the spec ships.
