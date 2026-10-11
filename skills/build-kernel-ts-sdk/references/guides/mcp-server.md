# Kernel MCP server

Hosted remote MCP server that exposes the Kernel API as tools, for agents that call tools instead of writing SDK code. Source: `kernel-mcp-server` README and `src/lib/mcp/*`, docs `reference/mcp-server`. For TypeScript code that ships in your own service, use `@onkernel/sdk`; use MCP when a coding agent (Claude Code, Cursor, Codex, ...) should drive browsers directly.

## Connect

| Item | Value |
|---|---|
| URL (streamable HTTP, recommended) | `https://mcp.onkernel.com/mcp` |
| stdio fallback | `npx -y mcp-remote https://mcp.onkernel.com/mcp` |
| Auth: OAuth | OAuth 2.1 with dynamic client registration; the consent screen can grant org-wide access or a single project. Project-scoped tokens cannot switch projects. |
| Auth: API key | `Authorization: Bearer <KERNEL_API_KEY>` header. The server treats any non-JWT bearer token as an API key. Use it for CI, servers, and clients whose strict OAuth issuer check (RFC 9207) rejects the flow (fx; docs `reference/mcp-server/troubleshooting`). |
| Protocol | The same `/mcp` endpoint serves SDK-v1/2025-era clients and protocol `2026-07-28` stateless clients. |

```json
{ "mcpServers": { "kernel": { "url": "https://mcp.onkernel.com/mcp", "headers": { "Authorization": "Bearer ${KERNEL_API_KEY}" } } } }
```

(`${KERNEL_API_KEY}` is a placeholder; use the env-var syntax your client supports, or paste the key.) fx is the exception: it rejects a literal `Authorization` header and (per the docs fx page) currently fails the OAuth issuer check, so use `"bearer_token_env": "KERNEL_API_KEY"` in `~/.fx/mcp.json`. `kernel mcp install --target fx` always writes the OAuth config (`"oauth": {}`), so switch to `bearer_token_env` by hand.

```python
# OpenAI Agents SDK (docs integrations/openai/agents-sdk)
MCPServerStreamableHttp(name="kernel", params={"url": "https://mcp.onkernel.com/mcp",
    "headers": {"Authorization": f"Bearer {os.environ['KERNEL_API_KEY']}"}})
```

### Clients

```bash
kernel mcp install --target cursor|claude|claude-code|antigravity|windsurf|vscode|goose|zed|fx
claude mcp add --transport http kernel https://mcp.onkernel.com/mcp   # then run /mcp once to authenticate
codex mcp add kernel --url https://mcp.onkernel.com/mcp && codex mcp login kernel
```

| Client | Transport the CLI configures |
|---|---|
| Cursor, Claude Code, VS Code, fx | HTTP (`https://mcp.onkernel.com/mcp`) |
| Claude Desktop (`--target claude`), Windsurf, Goose, Zed, Antigravity | stdio via `mcp-remote` with a per-client OAuth callback port and `MCP_REMOTE_CONFIG_DIR` cache |
| Claude.ai / Claude Desktop (Pro, Max, Team, Enterprise) | Custom connector at `https://mcp.onkernel.com/mcp` (not available to Free plans) |
| OpenCode | `"type": "remote"` entry, then `opencode mcp auth kernel` |
| Smithery, others | Smithery proxy URL, or the `mcp-remote` stdio command |

`kernel mcp install` merges only the Kernel entry and keeps your other servers. `kernel mcp server` only prints connection details. To reset a stuck login: `rm -rf ~/.mcp-auth`, or `Cursor: Clear All MCP Tokens`.

## Tools

`KERNEL_MCP_TOOL_NAMES` (src/lib/mcp/tool-names.ts) lists **34** names. What a connection sees depends on gating (entitlements are resolved from `GET /org/entitlements` on `tools/list` and gated calls, cached up to 30 minutes per credential):

| Visible when | Tools |
|---|---|
| Always (25) | `get_connection_context`, `manage_browsers`, `manage_browser_pools`, `manage_profiles`, `manage_proxies`, `manage_extensions`, `manage_apps`, `manage_projects`, `manage_api_keys`, `manage_config_registry`, `manage_replays`, `manage_browser_files`, `manage_auth_connections`, `manage_credentials`, `manage_credential_providers`, `manage_playwright_executors`, `execute_playwright_code`, `browser_repl`, `computer_action`, `browser_curl`, `exec_command`, `webmcp`, `search_docs`, `get_more_tools`, `submit_feedback` |
| Org entitlement `features.vaults.enabled` (+6) | `manage_vaults`, `manage_vault_items`, `manage_vault_credentials`, `manage_vault_wallets`, `manage_vault_cards`, `manage_vault_provider_configs` |
| Org Search entitlement (+1) | `web_search` |
| Client declares MCP Apps support (+2) | `open_auth_login`; `begin_auth_login` is app-only (hidden from the model) |

The docs changelog counts 10 tools (Feb 27) then 16 (June 5); the tool pages under `reference/mcp-server/tools` document only 13. Do not hard-code a count: list tools at runtime. Self-hosted deployments trim with `KERNEL_MCP_ENABLED_TOOLSETS` / `KERNEL_MCP_DISABLED_TOOLSETS`; `get_connection_context` is always available.

Conventions:
- Every `manage_*` tool takes an `action` (`create`, `list`, `get`, `delete`, ...). The hosted server adds a required short `context` argument to every advertised tool, where the agent says why it is calling (analytics instrumentation in `src/lib/mcp/analytics.ts`; docs changelog Aug 7; no credentials, tokens or URLs in it).
- Browser tools (`manage_browsers`, `computer_action`, `execute_playwright_code`, `browser_repl`, `exec_command`, `browser_curl`, `manage_browser_files`, `manage_replays`, `webmcp`) accept a live session's **name or ID**; deleted sessions and `manage_browser_pools` `release` need the ID.
- `execute_playwright_code` and `browser_repl` need an existing `session_id`; create and delete browsers with `manage_browsers`. `execute_playwright_code` takes an optional `executor` (one tab per executor, max 8; `manage_playwright_executors` lists/deletes them).
- `browser_repl`: `timeout_sec` 1-150 (default 60); a timeout/crash terminates the REPL (`repl_terminated: true`). `webmcp`: `list`, `invoke` (exact `tool_ref`, `timeout_sec` 1-120 default 60), `list_custom`, `add_custom`, `remove_custom`; never retry `invoke` after `outcome_unknown`.
- `manage_apps` actions: `list_apps`, `invoke` (returns an invocation id immediately; `version` defaults to `latest`), `get_deployment`, `list_deployments`, `delete_deployment`, `get_invocation`, `list_invocation_browsers`.
- `manage_browser_files`: absolute paths; `read`/`download` refuse files over `max_bytes` (default 10 MiB, max 25 MiB).
- `manage_replays` needs a paid plan and a headful browser. `manage_browsers get_telemetry` reads archived telemetry.
- Project scoping: call `get_connection_context` first; project-scoped tools accept `project` (name or ID). Org-wide connections may omit it.
- `submit_feedback` text is redacted for emails, URLs, IPs, paths, domains and token-shaped values before analytics; `get_more_tools` reports capability gaps and does not install anything.
- Flat inputs such as `proxy_id`, `proxy_routes`, `browser_region`, `custom_host` are deprecated aliases for the nested `proxy`, `network`, `browser`, `config` objects; do not combine an alias with its nested form.
- Resources: docs list `browsers://`, `browser_pools://`, `profiles://`, `apps://`; the README uses `kernel://orgs/{org}/projects/{project}/...`. Prompts: `kernel-concepts`, `debug-browser-session`.

## Minimal flow (what an MCP-driven agent does)

1. `manage_browsers` `create` (`stealth: true`) -> `session_id`, live view URL.
2. `execute_playwright_code` (`return await page.title();`), `computer_action` (end with a `screenshot` action), or `browser_repl`.
3. `manage_browsers` `delete` in every path, same as `deleteByID` in SDK code.
