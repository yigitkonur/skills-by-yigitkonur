# `audit-server-readiness.sh`

Read-only readiness scan for an existing or nearly-existing `mcp-use/server` package.

## Run

```bash
bash scripts/audit-server-readiness.sh .
bash scripts/audit-server-readiness.sh packages/my-server
```

## What it checks

The script scans the target directory for:

- `package.json`, `"type": "module"`, scripts, `mcp-use`, `@mcp-use/cli`, `@mcp-use/react`, `zod`
- `mcp-use/server` imports, `new MCPServer`, `server.tool`, `server.uiResource`
- `allowedOrigins`, CORS, auth, session stores, stateless mode
- `resources/`, `widgetMetadata`, widget helper usage, React widget imports
- `/health`, `/ready`, `generate-types`, `.mcp-use/tool-registry.d.ts`

It prints categorized checklist sections: setup, tools/schemas, transport, auth/session, widgets, production, validation.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Scan completed. Missing checklist items are informational. |
| `2` | Target directory does not exist. |

## How to use the output

- Existing-server work: run this before choosing the intent route.
- Production audit: pair the output with `references/25-deploy/02-pre-deploy-checklist.md`.
- Widget audit: any widget signal should route to `references/18-mcp-apps/` and Inspector CSP mode.
- Live verification: once the server runs, use `test-by-mcpc-cli` for named-session CLI checks.
