# Performance Profiling

When a tool is slow, the symptom is usually clear (>1s tool call) but the cause rarely is. Reach for the right tool: timings, V8 profiler, async hooks, or production tracing.

---

## Step 1 — Establish the baseline

Before optimizing, measure. The cheapest measurement is `console.time` inside the handler.

```typescript
server.tool({ name: "slow-tool", schema }, async (args, ctx) => {
  console.time("slow-tool");
  console.time("slow-tool:fetch");
  const data = await fetchUpstream(args);
  console.timeEnd("slow-tool:fetch");

  console.time("slow-tool:transform");
  const result = transform(data);
  console.timeEnd("slow-tool:transform");

  console.timeEnd("slow-tool");
  return text(result);
});
```

For HTTP-level timing of an entire request:

```bash
curl -s -o /dev/null -w "status=%{http_code} total=%{time_total}s connect=%{time_connect}s\n" \
  -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"slow-tool","arguments":{}},"id":99}'
```

---

## Step 2 — Flame graphs with Node Inspector

Best when you suspect CPU work (parsing, hashing, large object building) is the bottleneck.

```bash
# Attach to running server
node --inspect dist/server.js

# Break on first line (when you need to inspect startup)
node --inspect-brk dist/server.js
```

Open `chrome://inspect` in Chrome → **Open dedicated DevTools for Node** → **Performance** tab → record while exercising the slow tool. The flame graph shows function call stacks by time spent.

For VS Code: add to `.vscode/launch.json`:

```json
{
  "type": "node",
  "request": "attach",
  "name": "Attach to mcp-use",
  "port": 9229
}
```

---

## Step 3 — V8 sampling profiler

For a non-interactive profile (CI, prod-shaped load):

```bash
node --prof dist/server.js
# … exercise the server, hit Ctrl+C …
# Produces isolate-0xNN-v8.log; convert to readable form:
node --prof-process isolate-*-v8.log > profile.txt
```

`profile.txt` lists hot functions by tick count.

---

## Step 4 — Async hooks for I/O bottlenecks

CPU profilers miss async waits (HTTP, DB, file). Use `--trace-warnings` and observability spans, or wrap suspect calls:

```typescript
async function timed<T>(label: string, fn: () => Promise<T>): Promise<T> {
  const t0 = performance.now();
  try {
    return await fn();
  } finally {
    console.error(`[perf] ${label} ${(performance.now() - t0).toFixed(1)}ms`);
  }
}

server.tool({ name: "slow-tool", schema }, async (args, ctx) => {
  const data = await timed("fetch", () => fetchUpstream(args));
  const result = await timed("transform", () => transform(data));
  return text(result);
});
```

---

## Common bottlenecks in MCP servers

| Bottleneck | Symptom | Fix |
|---|---|---|
| **Synchronous JSON parsing of huge payloads** | One tool blocks the event loop; other sessions stall | Stream-parse, or move parse off-main-thread |
| **Sequential awaits when parallelizable** | Tool latency = sum of subcalls | `Promise.all([…])` for independent fetches |
| **Per-request OAuth verification with no cache** | Every call adds 100–300ms | Cache verified tokens by jti for token lifetime |
| **Zod schema with `.strict()` on huge inputs** | Validation latency dominates | Profile; consider `.passthrough()` if extra fields are safe |
| **Per-call DB connection acquire** | Each call adds connection-pool wait | Use a long-lived pool; never `new Pool()` per call |
| **Large `structuredContent` payloads** | Network time, not CPU | Trim or paginate; use a resource URL for large blobs |
| **Logger at `trace` level in prod** | Disk I/O dominates | Set `MCP_DEBUG_LEVEL=info` (see `01-debug-flag-and-tiered-levels.md`) |
| **HMR file-watch on huge dirs** | Dev mode slow; prod fine | Tighten watcher patterns or `--no-hmr` |
| **Widget asset bundling on every request** | First call slow; subsequent fine | Pre-build with `mcp-use build`; serve from disk |

---

## Memory

Watch for leaks across long-running sessions. RSS climbing without traffic is the giveaway.

```bash
# Sample RSS every 5s
while true; do
  ps -o rss= -p $(pgrep -f dist/server.js) | awk '{print strftime("%H:%M:%S"), $1/1024 "MB"}'
  sleep 5
done
```

Heap snapshots in Chrome DevTools (via `--inspect`) → **Memory** tab → record three snapshots, compare. Look for retained closures over `ctx`, unbounded session-state caches, listeners that never detach.

---

## Production tracing

Once you've fixed the obvious, leave production observability on (`02-observability-langfuse.md`) so the next regression is visible:

- p50 / p95 / p99 per tool
- Error rate per tool
- Sampling cost per tool (if applicable)

When p95 spikes, drill into a slow trace span-by-span instead of starting a profiling session blind.

---

## Quick-fire optimizations

| Optimization | Cost | Win |
|---|---|---|
| Switch synchronous fs to async | Trivial | Unblocks event loop |
| Cache config reads | Trivial | Saves disk reads per call |
| Use `Promise.all` for independent awaits | Low | Latency drops to max-of, not sum-of |
| Pin Node to current LTS | Low | Engine perf improvements |
| Move CPU-heavy work to a worker thread | Medium | Other sessions stop stalling |
| Precompile Zod schemas (no `.parse` on hot path) | Medium | Schema overhead drops |
| Switch JSON serializer to fast-json-stringify | Medium | Big payloads serialize faster |
