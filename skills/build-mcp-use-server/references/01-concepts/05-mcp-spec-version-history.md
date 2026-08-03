# MCP Spec Version History

*Read this when you need to understand which MCP protocol features are available in a given v2 release.*

## Three separate version axes — never conflate them

| Axis | Format | Current value | Governs |
|------|--------|---------------|---------|
| **MCP protocol revision** | Date, `YYYY-MM-DD` | `2026-07-28` | The wire format itself (SEP process, modelcontextprotocol.io/specification) |
| **MCP SDK npm packages** | Semver | `2.0.0` (`@modelcontextprotocol/{client,core,server}`) | The official TypeScript SDK implementing that protocol revision |
| **`mcp-use` framework** | Semver + prerelease | `2.0.0-beta.66` (dist-tag `beta`); `1.34.x` is `latest` (v1, end-of-life) | This skill's framework, built on the SDK packages above |

There is no "MCP protocol v2.0.0." The protocol has never used semver — it uses date-stamped revisions. `2.0.0` is the SDK package version; do not write it as a protocol version anywhere in this skill.

## MCP protocol revision history

| Revision | Status | Headline change |
|----------|--------|------------------|
| `2024-11-05` | Final | Initial public MCP specification |
| `2025-03-26` | Final | OAuth 2.1 authorization; audio content; tool annotations; HTTP+SSE deprecated in favor of Streamable HTTP |
| `2025-06-18` | Final | Structured tool output (`structuredContent`); elicitation; resource links; removed JSON-RPC batching |
| `2025-11-25` | Final | Async tasks (experimental); soft-deprecated `includeContext` `"thisServer"`/`"allServers"` |
| `2026-07-28` | **Current** | Stateless wire (below) |

## What changed in 2026-07-28 (the revision mcp-use v2 targets)

`mcp-use` v2 is built for exactly this revision; it serves `2025`-era clients through a stateless legacy fallback (`ServerConfig.legacy: "stateless" \| "reject"`, default `"stateless"`) rather than implementing their handshake natively.

**Major (breaking) changes:**
- Removed protocol-level sessions and the `Mcp-Session-Id` header. List endpoints (`tools/list`, `resources/list`, `prompts/list`) no longer vary per connection.
- Removed the `initialize`/`notifications/initialized` handshake. Every request carries its protocol version and client capabilities in `_meta` (`io.modelcontextprotocol/protocolVersion`, `io.modelcontextprotocol/clientCapabilities`); version mismatches return `UnsupportedProtocolVersionError`.
- Added `server/discover` — a mandatory RPC servers implement to advertise supported protocol versions, capabilities, and identity.
- Replaced the GET endpoint and `resources/subscribe`/`resources/unsubscribe` with `subscriptions/listen` — one long-lived POST-response stream for opted-in change notifications, tagged with `io.modelcontextprotocol/subscriptionId`. Request-scoped notifications (`notifications/progress`, `notifications/message`) still flow on the originating request's own response stream.
- Removed `ping`, `logging/setLevel`, `notifications/roots/list_changed`. Log level is now per-request via `_meta`.
- Introduced the **Multi Round-Trip Requests (MRTR)** pattern, replacing server-initiated requests (`roots/list`, `sampling/createMessage`, `elicitation/create`). Servers return `InputRequiredResult` (`resultType: "input_required"`); clients retry the original request with `inputResponses`. This is the mechanism underlying mcp-use's `inputRequired`/`inputResponse`/`acceptedContent`/`requestState` primitives (see `04-stateless-model-and-request-state.md`).
- All results now carry `resultType`: `"complete"` or `"input_required"`.
- Removed SSE stream resumability (`Last-Event-ID`) from Streamable HTTP.

**Deprecated (still functional, scheduled for removal):**
- Roots, Sampling, and Logging features (SEP-2577) — mcp-use v2 has no `ctx.sample()` or roots support; use direct LLM provider calls and tool parameters instead.
- HTTP+SSE transport (deprecated since `2025-03-26`, now formally Deprecated).
- OAuth 2.0 Dynamic Client Registration Protocol, in favor of Client ID Metadata Documents.

## Feature support in mcp-use v2 (beta.66)

| Protocol feature | mcp-use v2 support | Notes |
|-------------------|---------------------|-------|
| Tools + schemas | Native | Definition-first API; Standard Schema (Zod v4, etc.) |
| Resources | Native | Static + URI templates; completion callbacks |
| Prompts | Native | Completable arguments; message templates |
| `input_required` / MRTR | Native (primitives) | `inputRequired`, `inputResponse`, `acceptedContent`, `createRequestStateCodec` exported from `mcp-use` root; a `ctx.elicit()` convenience wrapper is documented but not present in the shipped `beta.66` dist — see `04-stateless-model-and-request-state.md` |
| Sampling (server-initiated LLM generation) | **Removed** | Deprecated at the protocol level; host/client generates instead |
| Roots | **Not exposed** | Deprecated at the protocol level; pass paths as tool parameters instead |
| Streamable HTTP | Primary transport | `server.fetch` handler; stateless per request |
| Stdio | **Not served** | HTTP only in mcp-use v2 |
| Resource subscriptions | Native | `server.notifyResourceUpdated(uri)`, `server.notifyResourcesChanged()` |
| Progress tokens | Native | `await ctx.reportProgress(progress, total?, message?)` |
| MCP Apps views | Native | React components in `views/<name>/view.tsx`; `text/html;profile=mcp-app` MIME |
| Structured content | Native | `structuredContent` field, required when a tool declares `outputSchema` |

## Capability detection

Query client capabilities at runtime:

```typescript
ctx.client.can("elicitation")        // Top-level capability presence
ctx.client.supportsViews()           // MCP Apps / UI extension declared
ctx.client.extension("io.example")   // Custom extension settings, if declared
```

## Version skew handling

Clients on older protocol revisions may connect through the stateless legacy fallback. Degrade gracefully when a capability is absent:

```typescript
if (!ctx.client.can("elicitation")) {
  return { content: [{ type: "text", text: "Unsupported" }] };
}
// Proceed with an input_required-dependent flow
```

See `16-client-introspection/02-capabilities.md` for the full surface.

## Migration between mcp-use versions

See cluster `28-migration/` for v1→v2 paths and deprecated-feature removals.
