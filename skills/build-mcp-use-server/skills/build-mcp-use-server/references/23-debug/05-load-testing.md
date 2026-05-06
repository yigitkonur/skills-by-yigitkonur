# Load Testing

Load test before you trust a deploy. MCP servers have unusual traffic shapes — long-lived sessions, streaming responses, sampling round-trips — so generic HTTP load tools need adaptation.

---

## What to measure

| Metric | Why it matters | Target |
|---|---|---|
| **p50 latency per tool** | Typical user experience | Tool-dependent; document baseline per tool |
| **p95 / p99 latency per tool** | Tail experience; what slow users see | Within 3x p50; flag drift |
| **Error rate** | Reliability | <0.1% for healthy servers |
| **Concurrent sessions sustainable** | Capacity ceiling | Until p95 doubles or errors >1% |
| **RSS memory at sustained load** | Leak detection | Plateau, not climb |
| **Event-loop lag** | Whether async I/O is starving | <10ms p99 |
| **CPU at sustained load** | Headroom | <70% sustained per core |

---

## Approach 1 — Bash + parallel curl

Cheapest, no dependencies. Good for smoke tests and ratio-of-success checks.

```bash
#!/bin/bash
BASE="http://localhost:3000/mcp"
N=50
PAR=10

# Pre-create one session and reuse — closer to real client behavior
SESSION=$(curl -s -D - -X POST "$BASE" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"load","version":"1.0.0"}},"id":1}' \
  | grep -i "mcp-session-id" | awk '{print $2}' | tr -d '\r')

call_tool() {
  local i=$1
  curl -s -o /dev/null -w "%{http_code} %{time_total}\n" -X POST "$BASE" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -H "Mcp-Session-Id: $SESSION" \
    -H "MCP-Protocol-Version: 2025-11-25" \
    -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"greet\",\"arguments\":{\"name\":\"u$i\"}},\"id\":$i}"
}

export -f call_tool
export BASE SESSION

seq 1 "$N" | xargs -P "$PAR" -I {} bash -c 'call_tool "$@"' _ {}
```

Pipe through `awk` to compute p50/p95:

```bash
… | awk '{print $2}' | sort -n | awk '
  { a[NR]=$1 }
  END {
    n=NR
    print "p50:", a[int(n*0.5)]
    print "p95:", a[int(n*0.95)]
    print "p99:", a[int(n*0.99)]
  }
'
```

---

## Approach 2 — k6

Better for sustained load and realistic ramps. Install: `brew install k6`.

```javascript
// loadtest.js
import http from 'k6/http';
import { check } from 'k6';

const BASE = __ENV.BASE || 'http://localhost:3000/mcp';

export const options = {
  stages: [
    { duration: '30s', target: 10 },   // ramp to 10 VUs
    { duration: '1m',  target: 10 },   // hold
    { duration: '30s', target: 50 },   // ramp to 50
    { duration: '2m',  target: 50 },   // hold
    { duration: '30s', target: 0 },    // ramp down
  ],
  thresholds: {
    'http_req_duration{tool:greet}': ['p(95)<500'],
    'http_req_failed': ['rate<0.01'],
  },
};

export function setup() {
  const res = http.post(BASE, JSON.stringify({
    jsonrpc: '2.0', method: 'initialize',
    params: { protocolVersion: '2025-11-25', capabilities: {}, clientInfo: { name: 'k6', version: '1.0.0' }},
    id: 1,
  }), { headers: { 'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream' }});
  return { session: res.headers['Mcp-Session-Id'] };
}

export default function (data) {
  const res = http.post(BASE, JSON.stringify({
    jsonrpc: '2.0', method: 'tools/call',
    params: { name: 'greet', arguments: { name: `u${__VU}-${__ITER}` }},
    id: __ITER,
  }), {
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/event-stream',
      'Mcp-Session-Id': data.session,
      'MCP-Protocol-Version': '2025-11-25',
    },
    tags: { tool: 'greet' },
  });
  check(res, { 'status is 200': (r) => r.status === 200 });
}
```

Run:

```bash
k6 run loadtest.js
```

k6 prints latency percentiles, error rate, and threshold pass/fail at the end.

---

## Approach 3 — autocannon

Lighter than k6 for HTTP throughput: `npx autocannon -m POST -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "Mcp-Session-Id: $SESSION" -H "MCP-Protocol-Version: 2025-11-25" -b '<body>' -c 50 -d 30 http://localhost:3000/mcp` (`-c` = concurrent connections, `-d` = seconds).

---

## Multi-session vs single-session

Real-world MCP traffic is many sessions × few calls each, not one session × many calls. Test both shapes:

| Shape | Why |
|---|---|
| **One session, many calls** | Stresses tool handler hot path; uniform request shape |
| **Many sessions, few calls each** | Stresses session creation, init handshake, OAuth verify |
| **Bursts of new sessions** | Catches lock contention in session store |

Pseudo-shell for new-sessions burst:

```bash
for i in {1..100}; do
  (curl -s -X POST "$BASE" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"l","version":"1"}},"id":1}' \
    > /dev/null) &
done
wait
```

---

## What to watch on the server

While the load test runs, watch:

| Metric | Command |
|---|---|
| CPU + memory | `top -pid $(pgrep -f dist/server.js)` |
| Open connections | `lsof -i :3000 \| wc -l` |
| RSS over time | `while true; do ps -o rss= -p $(pgrep -f dist/server.js); sleep 5; done` |
| Event-loop lag warnings | `node --trace-warnings dist/server.js` |

If using Langfuse (`02-observability-langfuse.md`), the per-tool latency dashboard updates in near-real-time during the test.

---

## Common load-test failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Latency climbs linearly with concurrency | Single shared resource (DB connection, file lock) | Pool the resource; profile under load |
| Error rate spikes at N concurrent | Exhausted file descriptors or DB pool | `ulimit -n`; raise pool max |
| RSS climbs and never plateaus | Per-session leak (state cache, listeners) | Heap snapshot diff before/after |
| Errors only on first calls per session | Init handshake bottleneck | Profile session-create path |
| p99 >> p95 | Tail caused by GC pauses or rare slow path | `--max-old-space-size`, check slow path code |
| Tunnel rejects after ~10 min | Tunnel rate limits (10 creates/hr per IP) | Use real deploy URL for serious load tests |

---

## Production load tests

Don't load-test production — load-test a production-shaped staging environment. Same Node version, same instance size, same DB. Otherwise results lie.

Acceptance gate before promoting to prod:

- [ ] p95 within target across all tools at expected peak load
- [ ] Error rate <0.1% sustained for 10 minutes
- [ ] No memory growth over 30 minutes at sustained load
- [ ] No event-loop-lag spikes >100ms
