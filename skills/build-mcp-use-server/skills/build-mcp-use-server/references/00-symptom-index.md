# Symptom Index

Use this file when the user gives an error string, observable failure, or "it does not work" report. Match the symptom first, run the diagnostic command, then open the first reference. Do not start with the full reference inventory.

| Symptom or error fragment | Likely cause | First reference | First diagnostic command |
|---|---|---|---|
| `Cannot find module 'mcp-use/server'`, `ERR_PACKAGE_PATH_NOT_EXPORTED`, `SyntaxError: Unexpected token export` | Missing `mcp-use`, CommonJS package mode, or non-Node16/NodeNext TypeScript resolution | `02-setup/01-prerequisites.md` | `node -p "require('./package.json').type" && npm ls mcp-use typescript` |
| `Cannot find module 'zod'`, TypeScript cannot resolve Zod types | `zod` missing from the project's own dependencies | `02-setup/01-prerequisites.md` | `node -e "const p=require('./package.json'); console.log((p.dependencies||{}).zod || 'zod missing from dependencies')"` |
| Inspector connects but no tools are listed | Tool registration order, wrong entry file, or multiple `MCPServer` instances | `27-troubleshooting/06-decision-tree.md` | `rg "new MCPServer|server\\.tool|mcp-use dev|generate-types" .` |
| HTTP returns HTML, wrong endpoint, or handshake fails | Calling `/`, `/inspector`, a proxy redirect, or an auth gate instead of `/mcp` | `22-validate/02-curl-handshake.md` | `curl -i -X POST "$MCP_URL" -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'` |
| `ctx.auth` is undefined in a protected tool | OAuth not mounted, request missing bearer token, or old `mcp-use` auth-context regression | `11-auth/03-ctx-auth-object.md` | `npm ls mcp-use && rg "oauth|ctx\\.auth|Authorization" src index.ts` |
| `Incompatible auth server`, missing `registration_endpoint`, DCR failure | Provider does not support DCR or `.well-known` metadata is wrong | `11-auth/02-dcr-vs-proxy-mode.md` | `curl -sS "$MCP_URL/.well-known/oauth-authorization-server" | jq '{issuer,registration_endpoint,authorization_endpoint,token_endpoint}'` |
| Supabase OAuth redirect mismatch, PKCE failure, token exchange failure | Supabase DCR/proxy mismatch, localhost redirect allowlist, or custom token handler bug | `27-troubleshooting/03-oauth-and-supabase-issues.md` | `rg "oauthSupabaseProvider|oauthProxy|SUPABASE|redirect_uri|code_verifier" .` |
| Session lost, 404 after restart, `Mcp-Session-Id` drift | Client not echoing session header, in-memory store after restart, or missing Redis store | `10-sessions/02-lifecycle.md` | `curl -i -X POST "$MCP_URL/mcp" -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | rg -i "mcp-session-id|mcp-protocol-version"` |
| Notification, progress, sampling, or resource update not delivered | Stateless mode, unsupported client capability, no progress token, or missing `RedisStreamManager` in multi-instance deploy | `14-notifications/06-when-notifications-fail.md` | `rg "stateless|sendNotification|reportProgress|ctx\\.sample|notifyResourceUpdated|RedisStreamManager" src index.ts` |
| Widget blank, plain HTML, or CSP violation | Host lacks MCP Apps support, CSP blocked assets/fetches, or wrong widget MIME/protocol | `27-troubleshooting/04-widget-rendering-issues.md` | `rg "widgetMetadata|server\\.uiResource|type: .mcpApps.|connectDomains|resourceDomains|frameDomains" resources src index.ts` |
| `useWidget` or `useCallTool` throws outside provider | Widget tree is not wrapped in `McpUseProvider` | `18-mcp-apps/widget-react/01-mcpuseprovider.md` | `rg "McpUseProvider|useWidget|useCallTool" resources src` |
| Next.js drop-in alias failure, Tailwind mismatch, or `server-only` import error | `--mcp-dir` layout, path alias, or server-only shim mismatch | `19-nextjs-drop-in/01-overview.md` | `rg -- "--mcp-dir|server-only|paths|tailwind|@/" package.json tsconfig.json next.config.* mcp src app` |
| `/health` or `/ready` returns HTML, 404, or blocks deploy | Health/readiness route missing or registered after Inspector catch-all | `24-production/05-health-routes.md` | `curl -i "$MCP_URL/health" && curl -i "$MCP_URL/ready"` |

## Escalation path

If the symptom is absent here:

1. Grep the troubleshooting cluster for the exact error string: `rg -n "<error fragment>" references/27-troubleshooting references/23-debug references/22-validate`.
2. Run the curl handshake from `22-validate/02-curl-handshake.md` to separate transport failure from tool failure.
3. Use Inspector RPC logging (`20-inspector/07-rpc-logging.md`) when the wire payload matters.
4. Use `test-by-mcpc-cli` for a live named-session check after the server is running.
