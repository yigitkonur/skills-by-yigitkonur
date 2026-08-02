# Everything Server

The official Everything server is the fastest way to probe `mcpc` capability boundaries. Verified against `mcpc 0.6.0` and `@modelcontextprotocol/server-everything` (npm `latest`, MCP 2025-11-25, stdio and Streamable HTTP both tested).

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
mcpc @everything-http prompts-get args-prompt city:=Paris
mcpc @everything-http resources-list
mcpc @everything-http resources-templates-list
mcpc @everything-http resources-subscribe demo://resource/static/document/architecture.md ./arch.md
mcpc @everything-http tools-call simulate-research-query topic:='"mcpc tasks"' ambiguous:=false --task
mcpc @everything-http tools-call simulate-research-query topic:='"mcpc detach"' ambiguous:=false --detach
mcpc @everything-http tasks-get <taskId>
mcpc @everything-http tasks-result <taskId>   # works even from a separate invocation than the --detach call
```

## Important observations

- `simulate-research-query` is the server's only `[task:required]` tool; every other tool, including `trigger-long-running-operation`, is `[task:forbidden]` — task support is per-tool opt-in, not inferred from runtime.
- `--task` blocks until completion and returns the result wrapped in `_meta.io.modelcontextprotocol/related-task.taskId`; `--detach` returns `{taskId, status:"working"}` immediately. Glyphs: `⟳ working`, `✔ completed`, `⊘ cancelled`.
- `get-roots-list`, `trigger-sampling-request`, `trigger-elicitation-request`, and `trigger-url-elicitation` do **not appear in `tools-list` at all**. The server registers them conditionally, only for clients advertising the matching capability at handshake — and since the v0.5.0 security fix `mcpc` deliberately no longer advertises `sampling`/`roots` capabilities it doesn't implement. Calling one anyway fails with `MCP error -32602: Tool <name> not found` (exit 2) — expected 0.6.0 behavior, not a boundary bug.
- `resources-subscribe <uri> <file>` syncs the file immediately on subscribe, not only on the next change notification; `resources-unsubscribe` stops syncing but keeps the file.
- `logging-set-level` still works (exit 0) but self-reports deprecated (MCP 2026-07-28 drops `logging/setLevel`; this server negotiates 2025-11-25, where it's still valid).

## SSE warning

The server still ships `sse` as a launch mode, and live `mcpc 0.6.0` still behaves like a Streamable HTTP client and fails against those endpoints (unchanged since 0.2.x — no CHANGELOG entry has added HTTP+SSE support).
Bridge logs show `Cannot POST /sse` or `Cannot POST /mcp`. Use the `streamableHttp` entrypoint for this skill.
