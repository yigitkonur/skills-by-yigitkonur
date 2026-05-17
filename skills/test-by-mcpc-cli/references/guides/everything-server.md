# Everything Server

The official Everything server is the fastest way to probe `mcpc` capability boundaries.

## Why it matters

One server covers tools, prompts, resources, templates, logging, tasks, roots-aware helpers, and sampling demos.

## stdio setup

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
mcpc connect /tmp/everything-mcp.json:everything @everything-stdio
```

## Streamable HTTP setup

```bash
PORT=3011 npx -y @modelcontextprotocol/server-everything streamableHttp
mcpc connect http://127.0.0.1:3011/mcp @everything-http
```

Selection rule:

- if you did not explicitly start `streamableHttp`, do not assume an old `@everything-http` session is usable
- for fresh local verification, start with `stdio`
- use the HTTP session only when you are intentionally testing Streamable HTTP behavior

## What worked during verification

```bash
mcpc @everything-http tools-list --full
mcpc @everything-http prompts-list
mcpc @everything-http resources-list
mcpc @everything-http resources-templates-list
mcpc @everything-http tools-call get-roots-list
mcpc @everything-http tools-call simulate-research-query topic:='"mcpc tasks"' --task
mcpc @everything-http tools-call simulate-research-query topic:='"mcpc detach"' --detach
mcpc @everything-http tasks-get <taskId>
```

## Important observations

- `simulate-research-query` is `task:required`
- `trigger-long-running-operation` is `task:forbidden`
- `get-roots-list` is exposed because `mcpc` advertises roots capability, but it reports an empty configured root set
- sampling demo tools can return `isError: true` with `Method not found`
- `trigger-elicitation-request` is not exposed for `mcpc`

## SSE warning

The server still ships `sse`, but live `mcpc 0.2.4` behaved like a Streamable HTTP client and failed against those endpoints.
Bridge logs showed `Cannot POST /sse` or `Cannot POST /`.
Use the `streamableHttp` entrypoint for this skill.
