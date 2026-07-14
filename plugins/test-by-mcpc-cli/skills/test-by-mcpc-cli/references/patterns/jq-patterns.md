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
mcpc --json @research-test tools-get search-reddit | jq '.inputSchema.required'
mcpc --json @research-test tools-list | jq '.[] | select(.execution.taskSupport == "forbidden") | .name'
```

## Tool results

```bash
mcpc --json @research-test tools-call search-reddit '{"queries":["OpenAI MCP"]}' | jq '.isError // false'
mcpc --json @research-test tools-call search-reddit '{"queries":["OpenAI MCP"]}' | jq -r '.content[]?.text? // empty'
```

## Grep output

```bash
mcpc --json @research-test grep search | jq '.totalMatches'
mcpc --json @research-test grep search | jq '.sessions[] | {name, toolCount: (.tools | length)}'
```

## Tasks

```bash
mcpc --json @everything-http tasks-list | jq '.tasks[]? | {taskId, status, toolName}'
mcpc --json @everything-http tasks-get <taskId> | jq '{taskId, status, statusMessage}'
```

## Error handling reminder

Successful MCP calls that still failed logically often return exit `0` with `isError: true`.
That is why the payload check belongs in your pipeline.
