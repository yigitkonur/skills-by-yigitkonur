# Real-World Workflows

These flows are aligned to `mcpc 0.6.0` and are intended to be copied, adapted, and scripted.

## Workflow 1: Remote smoke test against Research Powerpack

Use this when you want a real hosted target that exercises tools, resources, and JSON output.

```bash
SESSION=@research-smoke
TARGET=https://research-mcp.yigitkonur.com/mcp

mcpc connect "$TARGET" "$SESSION"
mcpc "$SESSION" help
mcpc "$SESSION" grep search
mcpc "$SESSION" tools-list --full
mcpc "$SESSION" resources-list
mcpc --json "$SESSION" tools-call web-search '{"queries":["OpenAI MCP"]}' | jq '.isError // false'
mcpc close "$SESSION"
```

Notes:

- server exposes exactly four tools (mcp-researchpowerpack v9.0.0, MCP 2025-11-25): `plan-research`, `web-search`, `extract-evidence`, `review-research`
- start smoke tests from a fresh `connect`; inspect old sessions only when reuse is the point of the task
- the `/mcp` path matters; `https://research-mcp.yigitkonur.com` is not the same target
- direct one-shot URL commands were removed in `0.2.x` and are still gone in `0.6.0`; always connect first

## Workflow 2: Local stdio verification against Everything

Use this to test the official reference server through a standard `mcpServers` config.

```json
{
  "mcpServers": {
    "everything": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"]
    }
  }
}
```

```bash
SESSION=@everything-stdio
mcpc connect /tmp/everything-mcp.json:everything "$SESSION"
mcpc "$SESSION"
mcpc "$SESSION" tools-list --full
mcpc "$SESSION" prompts-list
mcpc "$SESSION" resources-list
mcpc "$SESSION" resources-templates-list
mcpc "$SESSION" tools-call get-sum '{"a":2,"b":3}'
mcpc close "$SESSION"
```

The reference server's tool set changes across its own releases — verify with `tools-list` before assuming a specific tool name exists. `get-roots-list` (a name mentioned only in the server's instructions text, not a real tool as of `server-everything` 2.0.0) is not callable; `get-sum` is a real, deterministic tool confirmed live.

## Workflow 3: Streamable HTTP plus task execution

Use this when you need to verify `task:required` tools and current `tasks-*` behavior.

```bash
PORT=3011 npx -y @modelcontextprotocol/server-everything streamableHttp

SESSION=@everything-http
mcpc connect http://127.0.0.1:3011/mcp "$SESSION"
mcpc "$SESSION" tools-list --full | rg simulate-research-query
mcpc "$SESSION" tools-call simulate-research-query topic:='"mcpc tasks"' --task
DETACHED=$(mcpc --json "$SESSION" tools-call simulate-research-query topic:='"mcpc detach"' --detach)
TASK_ID=$(printf '%s' "$DETACHED" | jq -r '.taskId')
mcpc --json "$SESSION" tasks-get "$TASK_ID"
mcpc --json "$SESSION" tasks-list
mcpc --json "$SESSION" tasks-result "$TASK_ID"
mcpc close "$SESSION"
```

Notes:

- `--task` waits for the final result and prints it directly
- `--detach` returns a task ID immediately; `tasks-get`/`tasks-list` only report status (`working`/`completed`/`cancelled`), never the result body — run `tasks-result "$TASK_ID"` for the actual `CallToolResult` payload, even from a fresh process, once status is `completed`
- Everything's `simulate-research-query` is useful for verifying `task:required`
- `--task`/`--detach` against a tool or server without task support now fails outright instead of silently falling back to a synchronous call

## Workflow 4: Headless OAuth login then connect

Use this for servers that require OAuth in CI, SSH, or container sessions.

```bash
SERVER=https://mcp.example.com/mcp
PROFILE=work
SESSION=@secured

mcpc login "$SERVER" --profile "$PROFILE" --scope "read write"
# If the browser cannot open, follow the printed URL manually and paste the callback URL back into mcpc.
mcpc connect "$SERVER" "$SESSION" --profile "$PROFILE"
mcpc "$SESSION" ping
mcpc close "$SESSION"
```

If you also need x402 auto-payment, make the profile explicit during `connect`.
`--x402` skips default-profile auto-selection unless `--profile` is also provided.

For CI/CD or daemons with no browser, use `--grant client-credentials` instead of the default `authorization-code` grant; for corporate-SSO-gated servers use `--grant id-jag`. See `references/guides/authentication.md` for the full grant-type reference.

## Workflow 5: CI smoke test with isolated state

Use a temporary `MCPC_HOME_DIR` so CI does not reuse a developer's local sessions or credentials.

```bash
set -euo pipefail
export MCPC_HOME_DIR="$RUNNER_TEMP/mcpc-home"
SESSION=@ci
TARGET=https://research-mcp.yigitkonur.com/mcp

cleanup() {
  mcpc close "$SESSION" >/dev/null 2>&1 || true
  mcpc clean all >/dev/null 2>&1 || true
}
trap cleanup EXIT

mcpc connect "$TARGET" "$SESSION" --no-profile
mcpc --json "$SESSION" tools-list | jq -e 'length > 0' >/dev/null
mcpc --json "$SESSION" tools-call web-search '{"queries":["OpenAI MCP"]}' >/dev/null
```

Since v0.5.0, `tools-call` exits `2` on `isError: true`, so `set -euo pipefail` alone fails the script on that line — no separate `jq -e '.isError != true'` check needed. Capture the JSON and add a payload check only if you need to branch on *why* it failed.

## Workflow 6: Local proxy for sandboxed tools

Use this when another process can only speak to a local HTTP MCP endpoint.

```bash
SESSION=@research-proxy
mcpc connect https://research-mcp.yigitkonur.com/mcp "$SESSION" --proxy 127.0.0.1:8787 --proxy-bearer-token demo-token
curl http://127.0.0.1:8787/health
mcpc connect http://127.0.0.1:8787/mcp @research-proxy-check --no-profile -H "Authorization: Bearer demo-token"
mcpc close @research-proxy-check
mcpc close "$SESSION"
```

The proxy is owned by the detached bridge for that session.
Once `connect` succeeds, it does not need `nohup` or `tmux` to survive the original terminal.
`/health` is unauthenticated (liveness check only, confirmed live). When `--proxy-bearer-token` is set, the `/mcp` endpoint itself does require it — a checking `connect` without `-H "Authorization: Bearer <token>"` fails with "Authentication required by server" (confirmed live); always pass the header, as shown above.
Since v0.5.0 the proxy also validates `Host`/`Origin` headers against DNS-rebinding and correctly terminates sessions on HTTP DELETE.
