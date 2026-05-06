# Vercel vs Railway — pick deliberately

Both can host Next.js. Pick by the project's actual workload.

## Quick decision

| Workload | Vercel | Railway |
|---|---|---|
| Static + serverless Next.js | ✓✓ | ✓ |
| Edge runtime / global distribution | ✓✓ | ✗ |
| Per-PR preview deploys | ✓✓ (free, automatic) | ✓ (manual) |
| Marketing / blog / docs | ✓✓ | ✓ |
| BullMQ workers | ✗ | ✓✓ |
| SSE > 5min | ✗ | ✓✓ |
| WebSocket server | ✗ | ✓✓ |
| Background queue consumers | ✗ | ✓✓ |
| Long-running cron (>10s) | ✗ (Hobby) / ✓ (Pro+) | ✓✓ (free) |
| Custom Docker | ✗ | ✓✓ |
| Native deps > 50MB | ✗ | ✓✓ |
| In-cluster Postgres / Redis | ✗ | ✓✓ (managed in same project) |
| WebGPU / GPU compute | ✗ | partial |

## The Vercel sweet spot

- Static Next.js page → CDN edge (instant)
- API route → serverless function (cold-start ~1s)
- Per-PR preview → unique URL per PR (5min build → live)
- Custom domain → Let's Encrypt cert (5min DNS)

For these workloads, Vercel is unbeatable. Free tier handles real production traffic for many projects.

## The Railway sweet spot

- Anything that can't fit in a 5-min serverless invocation
- Anything that needs warm in-memory state (DB connection pools, in-memory cache)
- Anything that needs to *consume* (queues, streams, WebSocket connections)
- Multi-service apps (web + worker + DB + Redis as one project)
- Custom Dockerfiles for nontrivial build steps

For these, Vercel will fight you at every turn. Railway is the right tool.

## The "split" pattern

A common production architecture: **Vercel for web, Railway for everything else**.

```
Vercel (web)
├── Next.js app
├── API routes that are quick (auth, simple CRUD)
└── ↓ for slow/queued work, hits Railway

Railway (workers + queue)
├── BullMQ worker service
├── BullMQ queue (Redis)
├── Postgres (for queue durability)
└── Cron service for scheduled jobs
```

Vercel's web service POSTs jobs to a Railway endpoint, which enqueues. Worker consumes. Done.

Setup:

1. Vercel project for the Next.js app
2. Railway project with: web (lightweight API for queue ops), worker, redis, postgres
3. Vercel env: `WORKER_URL=https://my-worker.railway.app`
4. Web hits Worker URL to enqueue

## Vercel hidden costs

- **Function invocations** — generous free tier, but high-volume APIs add up
- **Edge Functions** — separate quota; cheaper per invocation
- **Bandwidth** — includes ~100GB/mo free; overages charged
- **Build minutes** — 6,000 min/mo on Hobby; preview deploys eat this fast in busy repos
- **Cron invocations** — 2 per project on Hobby

Read the [pricing page](https://vercel.com/pricing) before committing.

## Railway hidden costs

- **Compute** — billed per CPU-second; idle services still cost
- **Bandwidth** — egress to internet metered
- **Storage** — DB volumes count toward limits
- **No free tier for production** — Trial credits only ($5 then pay)

For toy projects, Vercel's free tier wins. For production with workers, Railway's hourly billing is predictable.

## Detection: when to flag the wrong choice

If user is asking for `make-vercel` but their project has any of these patterns, recommend make-railway instead:

```bash
# Detector for "wrong-shape-for-Vercel" patterns
grep -rE "BullMQ|new Worker\\(|@bullmq/|new Queue\\b|ioredis" src/ 2>/dev/null
grep -rE "EventSource|res\\.write\\(|TransferEncoding" src/ 2>/dev/null    # SSE patterns
grep -rE "WebSocket|ws://|wss://|new WebSocket\\(" src/ 2>/dev/null
grep -rE "node-cron|@nestjs/schedule|setInterval.*60.*60" src/ 2>/dev/null  # in-process cron
```

If any of these match, surface a warning:

```
⚠ Detected long-running workload patterns (BullMQ/SSE/WebSocket).
  Vercel functions are stateless and time-limited. Consider Railway instead:
  → see make-railway skill
```

The user can override and proceed if they know what they're doing — but don't deploy quietly.

## When users ask "is Vercel always right for Next.js?"

No. Next.js is a framework; Vercel is a host with optimizations for it. The host is decided by workload, not framework.

If the answer is "yes" 90% of the time for their project, Vercel's the call. If their backend has any of the patterns above, mixed deployment (Vercel + Railway) is usually right.
