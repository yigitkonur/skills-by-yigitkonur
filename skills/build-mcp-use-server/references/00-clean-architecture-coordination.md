# Clean Architecture Coordination

Use this when a task blends TypeScript MCP server structure with mcp-use v2 mechanics.

The counterpart reference is in `build-clean-mcp-architecture` at:

```text
skills/build-clean-mcp-architecture/skills/build-clean-mcp-architecture/references/coordinate-with-build-mcp-use-server.md
```

## Ownership split

| Concern | Owner |
|---|---|
| File placement, import direction, layer boundaries, composition root, config seam, handler/presenter placement | `build-clean-mcp-architecture` |
| Exact mcp-use v2 APIs: tool definitions and schemas, raw result envelopes, oauth providers, transports/runtime adapters, views and CSP, Inspector, deploy mechanics | `build-mcp-use-server` |

If a request blends both, settle placement with `build-clean-mcp-architecture` first. Then return to this skill for the exact API call, config field, result envelope, validation command, or deploy mechanic.

## Worked handoffs

| Request | Structural pass | Mechanical pass |
|---|---|---|
| Add a new tool to a clean-layered repo | Place handler/use case/presenter/bootstrap wiring with `build-clean-mcp-architecture`. | Use this skill for the zod v4 `inputSchema`/`outputSchema`, the definition-first tool + callback, raw `CallToolResult`, Inspector/curl validation. |
| Add OAuth to an existing clean architecture server | Place provider construction in infrastructure/auth and config seam. | Use this skill for the `mcp-use/oauth/*` provider factory, `oauth` server config, `ctx.auth` fields, permission guards, OAuth diagnostics. |
| Decide whether a view belongs in the server | Decide ownership, `views/` folder placement, and composition-root wiring. | Use this skill for MCP Apps vs tools-only, the tool `view` field, `structuredContent` props, CSP metadata, `mcp-use/react` hooks. |
| Debug wire-level handshake failures | Skip architecture unless the fix touches placement. | Use this skill first: symptom index, curl handshake, Inspector, transport troubleshooting. |

## Do not duplicate

Do not copy the clean-architecture folder layout or guardrails into this skill. Do not copy mcp-use field-level API docs into `build-clean-mcp-architecture`. Cross-reference and switch skills at the seam.
