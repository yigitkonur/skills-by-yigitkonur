# jq Patterns

Use native `mcpc` discovery first, then add `jq` when you need exact machine assertions.

## Sessions and profiles

```bash
mcpc --json | jq '.sessions[] | {name, status, server}'
mcpc --json | jq '.sessions[] | select(.status != "live")'
mcpc --json | jq '.profiles[] | select(.serverUrl == "https://mcp.example.com/mcp")'
```

## Tool metadata

```bash
mcpc --json @research-test tools-list | jq '.[].name'
mcpc --json @research-test tools-get web-search | jq '.inputSchema.required'
mcpc --json @research-test tools-list | jq '.[] | select(.execution.taskSupport == "forbidden") | .name'
```

## Tool results

```bash
mcpc --json @research-test tools-call web-search '{"queries":["OpenAI MCP"]}' | jq '.isError // false'
mcpc --json @research-test tools-call web-search '{"queries":["OpenAI MCP"]}' | jq -r '.content[]?.text? // empty'
```

## Grep output

```bash
mcpc --json @research-test grep search | jq '.totalMatches'
mcpc --json @research-test grep search | jq '.sessions[] | {name, toolCount: (.tools | length)}'
```

## Tasks

```bash
mcpc --json @everything-http tasks-list | jq '.tasks[]? | {taskId, status, statusMessage}'
mcpc --json @everything-http tasks-get <taskId> | jq '{taskId, status, statusMessage}'
```

Task objects from `tasks-list`/`tasks-get` have no `toolName` field — don't
project one. Use `tasks-result <taskId>` to get the real `CallToolResult`.

## Error handling reminder

`isError: true` on a `tools-call`/`tasks-result` payload exits `2` (since
v0.5.0) — but keep the payload check in your pipeline anyway; it's what
tells you *why*.
