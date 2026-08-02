# Quick Diagnostic Table

*Read this when you know the visible symptom but not yet the failing v2 layer.*

| Symptom | First check | Next step |
|---|---|---|
| Import or module error | `MCPServer` comes from `mcp-use`; source uses ESM; Node is supported. | `references/26-anti-patterns/01-sdk-misuse.md` |
| Zod type or runtime validation error | `npm ls zod` shows Zod v4 without an old duplicate. | `references/26-anti-patterns/03-schemas.md` |
| Process exits before listening | Read the first startup exception; verify required env and port. | `references/08-server-config/07-lifecycle-listen-fetch-shutdown.md` |
| `EADDRINUSE` | Identify the process that owns `PORT`. | Stop it or choose another port. |
| Works on localhost, not in container | Check `HOST`; v2 defaults to `127.0.0.1`. | `references/08-server-config/02-network-basepath-and-endpoints.md` |
| Client uses a command instead of a URL | Check whether it expects stdio. v2 serves HTTP only. | `references/09-transports/05-no-stdio-and-sse-history.md` |
| 404 at `/sse` or `/stdio` | Wrong v1 endpoint. | Connect to `/mcp`. |
| HTML returned to MCP client | Wrong endpoint, auth redirect, or proxy page. | Inspect status, `content-type`, and redirects with curl. |
| Browser CORS error | `cors` config is missing or incomplete. | `references/08-server-config/03-cors-and-allowed-origins.md` |
| Host validation 403 | Hostname is absent from `allowedHosts`. | `references/08-server-config/04-dns-rebinding-and-host-validation.md` |
| No tools | Confirm registration occurs before serving and inspect `tools/list`. | `references/04-tools/02-registering-a-tool.md` |
| Tool absent from View types | Static tool is not an exported const, or `mcp-use typecheck` has not run. | Export the `ToolRef` and run typecheck. |
| Tool call rejected before callback | Input failed `inputSchema`. | `references/04-tools/06-validation-pipeline.md` |
| Tool succeeds but output validation fails | `structuredContent` does not match `outputSchema`. | `references/04-tools/07-input-schema-vs-output-schema.md` |
| `ctx.auth.user.userId` missing | v1 field path. | Use `ctx.auth.user.id`. |
| `ctx.sample` missing | Removed feature. | `references/13-sampling/01-sampling-removed-in-v2.md` |
| 401 before callback | Missing/invalid bearer token or provider resource mismatch. | `references/27-troubleshooting/03-oauth-issues.md` |
| OAuth Proxy import missing | Removed in v2. | `references/11-auth/07-oauth-proxy-removed.md` |
| View not discovered | `view.name` and `views/<name>/view.tsx` differ. | `references/27-troubleshooting/04-view-rendering-issues.md` |
| View tool lacks types | Tool lacks `outputSchema` or exported `ToolRef`. | `references/18-mcp-apps/server-surface/01-tool-view-field.md` |
| View blank | Open the iframe console; inspect CSP and runtime errors. | `references/27-troubleshooting/05-csp-violations.md` |
| `useWidget` missing | v1 hook. | Use `useToolContext` from `mcp-use/react`. |
| View works in Inspector only | Host capability or CSP differs. | `references/18-mcp-apps/05-host-capability-detection.md` |
| CLI command not found | Command may be a removed v1 command such as `serve` or `generate-types`. | `references/03-cli/01-overview.md` |
| Production serves stale output | Build/start uses `.mcp-use/build/`; source edits are not the artifact. | `references/03-cli/04-mcp-use-build-and-typecheck.md` |

If the first check is inconclusive, follow `references/27-troubleshooting/06-decision-tree.md` in order rather than changing several layers at once.