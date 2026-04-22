# Specification Enhancement Proposals (SEPs) — Overview

SEPs are the mechanism for proposing changes to the MCP specification. Each SEP provides technical specification and rationale. Status: Draft → In-Review → Accepted → Final.

## Developer impact summary

| SEP | Title | Status | Impact | Area |
|---|---|---|---|---|
| 414 | OpenTelemetry trace context propagation | Final | Low | Observability |
| 932 | MCP governance structure | Final | Info | Governance |
| 973 | Icons for tools, resources, prompts, implementations | Final | Medium | Metadata |
| 985 | OAuth protected resource metadata discovery fallback | Final | Medium | Auth |
| 986 | Tool name format specification | Final | Medium | Tools |
| 990 | Enterprise IdP policy controls (ID-JAG) | Final | High | Auth |
| 991 | URL-based client registration (Client ID Metadata Documents) | Final | High | Auth |
| 994 | Shared communication practices | Final | Info | Process |
| 1024 | Client security requirements for local server install | Final | Medium | Security |
| 1034 | Default values for elicitation primitive schemas | Final | Low | Elicitation |
| 1036 | URL mode elicitation for out-of-band interactions | Final | High | Elicitation |
| 1046 | OAuth client credentials flow (M2M) | Final | Medium | Auth |
| 1302 | Working Groups and Interest Groups | Final | Info | Governance |
| 1303 | Input validation errors as tool execution errors | Final | Medium | Tools |
| 1319 | Decouple request payloads from RPC method definitions | Final | Low | Schema |
| 1330 | Elicitation enum schema improvements and multi-select | Final | Medium | Elicitation |
| 1577 | Sampling with tools (agentic tool-use loops) | Final | High | Sampling |
| 1613 | JSON Schema 2020-12 as default dialect | Final | Medium | Schema |
| 1686 | Tasks (durable long-running operations) | Final | High | Tasks |
| 1699 | SSE polling via server-side disconnect | Final | Medium | Transport |
| 1730 | SDK tiering system (Tier 1/2/3) | Final | Info | SDK governance |
| 1850 | PR-based SEP workflow | Final | Info | Process |
| 1865 | MCP Apps (interactive UIs via `ui://` resources) | Final | Medium | Extensions |
| 2085 | Governance succession and amendment | Final | Info | Governance |
| 2133 | Extensions framework (`extensions` in capabilities) | Final | High | Protocol |
| 2148 | Contributor ladder | Final | Info | Governance |
| 2149 | Working group charter template | Final | Info | Governance |
| 2207 | OIDC refresh token guidance | **Accepted** | Medium | Auth |
| 2260 | Server requests must be tied to client requests | **Accepted** | High | Transport |

## SEPs most relevant to SDK developers

**Must-know for server builders:**
- SEP-986 (tool naming format)
- SEP-973 (icons metadata)
- SEP-1303 (validation errors as tool errors)
- SEP-1613 (JSON Schema 2020-12)
- SEP-2133 (extensions framework)

**Must-know for auth implementation:**
- SEP-985, 991, 1046, 1036, 990

**Must-know for advanced features:**
- SEP-1686 (tasks)
- SEP-1577 (sampling with tools)
- SEP-1699 (SSE polling)
- SEP-1865 (MCP Apps)

**Upcoming changes (Accepted, not yet Final):**
- SEP-2207 (OIDC refresh tokens)
- SEP-2260 (server requests tied to client requests)

## Detailed reference files

| File | SEPs covered |
|---|---|
| `auth-security.md` | 985, 990, 991, 1024, 1036, 1046, 2207 |
| `tools-metadata.md` | 414, 973, 986, 1303, 1577, 1686 |
| `protocol-transport.md` | 1034, 1319, 1330, 1613, 1699, 1865, 2133 |
| `upcoming.md` | 2207, 2260 |
