# Clean Architecture Coordination

Use this when a task blends TypeScript MCP server structure with `mcp-use/server` mechanics.

The counterpart reference is in `apply-clean-mcp-architecture` at:

```text
skills/apply-clean-mcp-architecture/skills/apply-clean-mcp-architecture/references/coordinate-with-build-mcp-use-server.md
```

## Ownership split

| Concern | Owner |
|---|---|
| File placement, import direction, layer boundaries, composition root, config seam, handler/presenter placement | `apply-clean-mcp-architecture` |
| Exact `mcp-use/server` APIs, schemas, response helpers, auth/session/transport config, widget CSP, Inspector, deploy mechanics | `build-mcp-use-server` |

If a request blends both, settle placement with `apply-clean-mcp-architecture` first. Then return to this skill for the exact API call, config field, response helper, validation command, or deploy mechanic.

## Worked handoffs

| Request | Structural pass | Mechanical pass |
|---|---|---|
| Add a new tool to a clean-layered repo | Place handler/use case/presenter/bootstrap wiring with `apply-clean-mcp-architecture`. | Use this skill for Zod schema, `server.tool`, response helper, generated types, Inspector/curl validation. |
| Add OAuth to an existing clean architecture server | Place provider construction in infrastructure/auth and config seam. | Use this skill for DCR vs proxy, provider factory, scopes, `ctx.auth`, OAuth diagnostics. |
| Decide whether a widget belongs in the server | Decide ownership, resource folder, and composition-root wiring. | Use this skill for MCP Apps vs tools-only, `server.uiResource`, `widget()`, CSP, `McpUseProvider`. |
| Debug wire-level handshake failures | Skip architecture unless the fix touches placement. | Use this skill first: symptom index, curl handshake, Inspector RPC logs, transport troubleshooting. |

## Do not duplicate

Do not copy the clean-architecture folder layout or guardrails into this skill. Do not copy `mcp-use/server` field-level API docs into `apply-clean-mcp-architecture`. Cross-reference and switch skills at the seam.
