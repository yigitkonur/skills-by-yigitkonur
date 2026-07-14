# Real-World Workflows

These flows are aligned to `mcpc 0.2.4` and are intended to be copied, adapted, and scripted.

## Workflow 1: Remote smoke test against Research Powerpack

Use this when you want a real hosted target that exercises tools, resources, and JSON output.

```bash
SESSION=@research-smoke
TARGET=https://research.yigitkonur.com/mcp

mcpc connect "$TARGET" "$SESSION"
mcpc "$SESSION" help
mcpc "$SESSION" grep search
mcpc "$SESSION" tools-list --full
mcpc "$SESSION" resources-list
mcpc --json "$SESSION" tools-call search-reddit '{"queries":["OpenAI MCP"]}' | jq '.isError // false'
mcpc close "$SESSION"
```

Notes:

- start smoke tests from a fresh `connect`; inspect old sessions only when reuse is the point of the task
- the `/mcp` path matters; `https://research.yigitkonur.com` is not the same target
- direct one-shot URL commands were removed in `0.2.x`; always connect first

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
mcpc "$SESSION" tools-call get-roots-list
mcpc close "$SESSION"
```

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
mcpc close "$SESSION"
```

Notes:

- `--task` waits for the final result
- `--detach` returns a task ID, but `tasks-get` only gives task status, not a recovered full result payload
- Everything's `simulate-research-query` is useful for verifying `task:required`

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

## Workflow 5: CI smoke test with isolated state

Use a temporary `MCPC_HOME_DIR` so CI does not reuse a developer's local sessions or credentials.

```bash
set -euo pipefail
export MCPC_HOME_DIR="$RUNNER_TEMP/mcpc-home"
SESSION=@ci
TARGET=https://research.yigitkonur.com/mcp

cleanup() {
  mcpc close "$SESSION" >/dev/null 2>&1 || true
  mcpc clean all >/dev/null 2>&1 || true
}
trap cleanup EXIT

mcpc connect "$TARGET" "$SESSION" --no-profile
mcpc --json "$SESSION" tools-list | jq -e 'length > 0' >/dev/null
RESULT=$(mcpc --json "$SESSION" tools-call search-reddit '{"queries":["OpenAI MCP"]}')
printf '%s' "$RESULT" | jq -e '.isError != true' >/dev/null
```

## Workflow 6: Local proxy for sandboxed tools

Use this when another process can only speak to a local HTTP MCP endpoint.

```bash
SESSION=@research-proxy
mcpc connect https://research.yigitkonur.com/mcp "$SESSION" --proxy 127.0.0.1:8787 --proxy-bearer-token demo-token
curl http://127.0.0.1:8787/health
mcpc connect http://127.0.0.1:8787/mcp @research-proxy-check --no-profile
mcpc close @research-proxy-check
mcpc close "$SESSION"
```

The proxy is owned by the detached bridge for that session.
Once `connect` succeeds, it does not need `nohup` or `tmux` to survive the original terminal.
Treat `/health` as a liveness check only.
If bearer enforcement matters, verify it with real MCP connects on the exact release you are documenting.
