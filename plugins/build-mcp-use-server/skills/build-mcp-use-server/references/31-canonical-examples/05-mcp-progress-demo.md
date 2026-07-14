# Canonical: `mcp-use/mcp-progress-demo`

**URL:** https://github.com/mcp-use/mcp-progress-demo
**Hosted demo:** https://crimson-river-pzsz1.run.mcp-use.com/mcp

The progress + interactive primitives reference. One server combines: a long-running tool that reports progress two ways (MCP `progressToken` and a custom polling endpoint), a widget that polls for live updates, tool annotations, and tools that intentionally fail / are destructive / are open-world.

## Load-bearing files

| File | What to read it for |
|---|---|
| `index.ts` (`process-data` tool) | Background work via fire-and-forget IIFE, in-memory `jobs` map, `ctx.reportProgress` |
| `index.ts` (`server.get("/api/progress/:jobId", ...)`) | Custom HTTP endpoint that the widget polls |
| `index.ts` (`fetch-report`, `delete-dataset`, `search-external` tools) | Tool annotations: `readOnlyHint`, `destructiveHint`, `openWorldHint` |
| `index.ts` (`failing-tool` tool) | Demonstrates structured `error()` response |
| `resources/progress-view/widget.tsx` | Polling loop driven by `setInterval`, reads `mcp_url` |

## Patterns demonstrated

| Pattern | Where |
|---|---|
| Fire-and-forget background work — return `widget()` immediately, run pipeline in detached IIFE | `process-data` |
| Dual-channel progress — `ctx.reportProgress` *and* a custom polling endpoint | `process-data` + `/api/progress/:jobId` |
| Module-scope `Map<id, Job>` for in-process state with timed cleanup | `process-data` |
| Tool annotations communicating safety/intent | `readOnlyHint`, `destructiveHint`, `openWorldHint` |
| `error(message)` to surface a structured failure to the client | `failing-tool` |
| Widget polling against `mcp_url` so it works in dev and prod | `widget.tsx` |

## Clusters this complements

- `../14-notifications/` — progress notifications and their wire format
- `../04-tools/` — tool annotations
- `../17-advanced/` — custom Hono routes alongside MCP
- `../30-workflows/12-progress-and-elicit-widget.md` — workflow derived from this repo

## When to study this repo

- You are building any tool that takes more than a couple of seconds.
- You need to combine MCP-spec progress *and* widget-driven polling.
- You are deciding whether a particular tool should be `readOnlyHint` / `destructiveHint` / `openWorldHint`.
- You want to see what an intentional `error()` response looks like end-to-end.

## Local run

```bash
gh repo clone mcp-use/mcp-progress-demo
cd mcp-progress-demo
npm install
npm run dev
```
