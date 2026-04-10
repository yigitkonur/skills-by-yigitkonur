# SEPs — Auth and Security

## SEP-985: OAuth Protected Resource Metadata Discovery Fallback

**Status:** Final

Aligns MCP with RFC 9728. Servers no longer MUST include `WWW-Authenticate` header on 401 responses — they SHOULD include it, but clients MUST fall back to probing `/.well-known/oauth-protected-resource` when the header is absent.

**SDK impact:** Auth middleware must implement two-step discovery:
1. Check `WWW-Authenticate` for `resource_metadata` URL
2. If absent, probe `/.well-known/oauth-protected-resource`

## SEP-990: Enterprise IdP Policy Controls (ID-JAG)

**Status:** Final (as extension `io.modelcontextprotocol/enterprise-managed-authorization`)

Enables enterprise SSO-governed MCP authorization via the Identity Assertion Authorization Grant (ID-JAG) pattern. Uses RFC 8693 Token Exchange + RFC 7523 JWT Bearer.

**Flow:** Employee authenticates via enterprise IdP → client gets ID token → client exchanges for ID-JAG via token exchange → client exchanges ID-JAG for MCP access token at the MCP Authorization Server. No consent screen — the IdP is the policy decision point.

**Capability declaration:**
```json
{
  "capabilities": {
    "extensions": {
      "io.modelcontextprotocol/enterprise-managed-authorization": {}
    }
  }
}
```

**SDK impact:** High — requires new grant type handler on the AS side and new auth flow branch in the client. ID-JAGs have 300-second expiry for frequent policy re-evaluation.

## SEP-991: URL-Based Client Registration (Client ID Metadata Documents)

**Status:** Final

Clients use an HTTPS URL as their `client_id`. The URL points to a hosted JSON document with client metadata. Servers fetch and validate the document instead of requiring pre-registration or DCR.

**Client metadata document:**
```json
{
  "client_id": "https://app.example.com/oauth/client-metadata.json",
  "client_name": "Example MCP Client",
  "redirect_uris": ["http://127.0.0.1:3000/callback"],
  "grant_types": ["authorization_code"],
  "token_endpoint_auth_method": "none"
}
```

**Server advertises support:** `"client_id_metadata_document_supported": true` in OAuth AS metadata.

**SDK impact:** Server auth must handle URL-format `client_id` detection, document fetching with SSRF protection, and redirect URI validation. DCR downgraded from SHOULD to MAY.

## SEP-1024: Client Security for Local Server Installation

**Status:** Final

Mandates a consent dialog before one-click local MCP server installation. Clients MUST display the exact command, all arguments, and a danger warning. Requires explicit user approval before execution.

**SDK impact:** Client applications with install-server UX must add consent gates. No server-side changes.

## SEP-1036: URL Mode Elicitation

**Status:** Final

Extends elicitation with `mode: "url"` for sensitive out-of-band interactions (API keys, OAuth flows, payments). Server provides a URL; client opens it in a secure browser context outside the MCP channel.

**New error code:** `-32042` (URLElicitationRequiredError) — servers return this when a tool call cannot proceed without URL-mode elicitation.

**Completion notification:** `notifications/elicitation/complete` with `elicitationId`.

**Security rules:**
- Clients MUST NOT auto-fetch URLs, MUST show full URL for review, MUST use secure browser (not WebView)
- Servers MUST NOT include sensitive info in the URL, MUST verify user identity matches at start and end
- Servers MUST NOT use URL elicitation as substitute for MCP client authorization

**SDK impact:** High — new elicitation mode, new error code, completion notification handler, URL security validation.

## SEP-1046: OAuth Client Credentials Flow (M2M)

**Status:** Final

Explicitly allows OAuth 2.1 client credentials flow for machine-to-machine scenarios (CI pipelines, backend agents, server-to-server). No end-user interaction needed.

**Preferred:** RFC 7523 JWT Assertions (`private_key_jwt`)
**Acceptable:** Client secrets (for rapid prototyping)

**SDK impact:** Server AS needs client credentials grant handler. Client needs non-interactive credential mode.

## SEP-2207: OIDC Refresh Token Guidance (Upcoming)

**Status:** Accepted (not yet Final)

Provides guidance for OIDC-flavored deployments where refresh token issuance depends on `offline_access` scope.

**Key rules:**
- Clients SHOULD include `refresh_token` in `grant_types` in client metadata
- Clients MAY add `offline_access` to scopes if AS advertises it in `scopes_supported`
- Resource servers SHOULD NOT include `offline_access` in their scopes
- Clients MUST NOT assume requesting `offline_access` guarantees a refresh token

**SDK impact:** Client auth flow conditionally appends `offline_access`. Server Protected Resource Metadata should omit `offline_access` from `scopes_supported`.
