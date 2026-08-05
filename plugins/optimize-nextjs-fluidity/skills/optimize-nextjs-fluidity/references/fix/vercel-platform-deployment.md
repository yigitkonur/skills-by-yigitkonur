# Fix: vercel-platform-deployment

**Corpus lineage:** vercel-platform-deployment/04-implementation-compute-runtime-proxy.md,
vercel-platform-deployment/05-implementation-cache-skew-observability.md,
vercel-platform-deployment/06-tradeoffs-pitfalls.md,
vercel-platform-deployment/07-version-lockin-seo-vercel-cost-model.md
**Knowledge baseline:** verified 2026-08-05 against Next.js 16.3.0 docs. Confirm any
config key against the installed package first — see `references/gating/capability-probe.md`.
Cost figures here are directional pointers only — the authoritative rate table lives in
`references/gating/cost-model.md`; do not restate or re-derive prices in this file.

## Recipe index

| Recipe | Requires | Reversibility | Triggered by |
|---|---|---|---|
| Remove Edge exports, move placement to `vercel.json` | Next.js ≥16.3.0 | `component-level-revert` | `runtime = 'edge'` / `preferredRegion` findings; prerequisite for `cacheComponents` |
| `middleware.ts` → `proxy.ts` codemod + narrow matcher | Next.js ≥16.0.0 | `component-level-revert` | `middleware.ts` still present; missing/broad matcher |
| Fluid Compute and function sizing | Vercel platform | `fully-reversible` | I/O-heavy workload cold starts; unmeasured Performance-tier assumption |
| Region colocation | Vercel platform | `fully-reversible` | High TTFB/504s on database-backed routes; unconfirmed region match |
| Cache-header inspection recipe | Vercel platform | n/a — diagnostic only | "Cache-Control looks right but nothing is cached" reports |
| ISR tag-scoped invalidation | Next.js ≥16.0.0 (two-arg `revalidateTag`) | `fully-reversible` | Broad/short blanket revalidation; nondeterministic output; write-unit exhaustion |
| Skew Protection enablement | Pro/Enterprise; Next.js ≥14.1.4 | `fully-reversible` | Server Action/RSC contract changes planned; long-lived sessions |
| Observability setup (Speed Insights / Web Analytics) | Vercel platform | `fully-reversible` | No RUM/CWV instrumentation present |

## Remove Edge exports, move placement to `vercel.json` — requires Next.js ≥16.3.0

**When to apply:** `runtime = 'edge'` and/or `preferredRegion` findings on an install
≥16.3.0. This is a hard, blocking prerequisite for `cacheComponents` — resolve it before,
never inside, that task.

```diff
// app/api/data/route.ts, page.tsx, or layout.tsx
- export const runtime = 'edge'
- export const preferredRegion = 'home'
```

No replacement is required — "The Node.js runtime is the default, so no replacement is
needed."

```json
// vercel.json — example: database in Mumbai
{ "$schema": "https://openapi.vercel.sh/vercel.json", "regions": ["bom1"] }
```

**Why:** `preferredRegion` is removed alongside `runtime = 'edge'`, not independently — it
was an Edge-route placement mechanism with no meaning once the route runs on Node.js,
where `vercel.json` `regions` controls placement instead. No Next.js config replaces the
deleted export.

**Non-mechanical part:** check dependencies previously avoided because Edge lacked Node
APIs (filesystem, restricted built-ins, dynamic-code-eval restrictions) — Node.js can now
use the normal package version. Re-test crypto, request globals, and bundle size; this is
a real behavior-surface change, not a pure rename.

**Verify after applying:** `next build` completes with no Edge-runtime warnings. Exercise
every migrated route in a production-like deployment and confirm no cold-start or
Node-API regression. Confirm `vercel.json` `regions` covers the same placement intent.

**Lock-in / reversibility:** `preferredRegion` side is `component-level-revert`
(config-only). **`runtime = 'edge'` side is a one-way door for new code** — once removed
and dependent code adopts Node-only APIs, reverting requires re-auditing for Edge's
restricted API surface; Vercel's own guidance is to migrate forward, not backward.

**Rollback:** re-add `runtime = 'edge'` only if no Node-only API was adopted since removal
(audit first); re-add `preferredRegion` and remove the corresponding `vercel.json`
`regions` entry.

## `middleware.ts` → `proxy.ts` codemod + narrow matcher — requires Next.js ≥16.0.0

**When to apply:** `middleware.ts` still present on an install ≥16.0.0, or `proxy.ts`
exists with a missing/overly broad `matcher`.

```bash
npx @next/codemod@canary middleware-to-proxy .
```

```diff
- export function middleware() {
+ export function proxy() {
```

```ts
// proxy.ts — Next.js 16.3, Node.js runtime is fixed and cannot be configured.
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Cheap coarse gate: avoid a page render for obviously unauthenticated traffic.
  if (pathname.startsWith('/dashboard') && !request.cookies.has('session')) {
    const login = new URL('/login', request.url)
    login.searchParams.set('next', pathname)
    return NextResponse.redirect(login)
  }

  // Cheap routing decision; no database call.
  if (pathname === '/docs/latest') {
    return NextResponse.rewrite(new URL('/docs/v16', request.url))
  }

  return NextResponse.next()
}

export const config = { matcher: ['/dashboard/:path*', '/docs/latest'] }
```

**Why:** `matcher` lists only the two routes that need the gate — Proxy "will be invoked
for every route in your project" without one, including `_next/static`, `_next/image`,
and `public/` assets; a missing matcher can "unintentionally block CSS, JS, or images from
loading." The cookie check redirects before any page render as a cheap coarse gate, not
the authorization boundary. `runtime` is never set — Proxy is fixed to Node.js.

**Do not trust the cookie-presence check as final authorization.** Every Server
Action/Route Handler must independently validate the session — "A matcher change or a
refactor that moves a Server Function to a different route can silently remove Proxy
coverage," since Server Functions ride the page's own route, not a separately matched one.

**Verify after applying:** `/dashboard` without a cookie redirects once to the correct
destination; `/dashboard` with a forged cookie is still rejected server-side; static
assets and unrelated pages don't invoke Proxy (check production runtime logs for
unexpected volume).

**Lock-in / reversibility:** `component-level-revert`. Codemod-assisted, forward-expected;
reverting means re-adding the deprecated `middleware.ts` convention, which Next.js
discourages.

**Rollback:** rename `proxy.ts` back to `middleware.ts` and `proxy()` back to
`middleware()` — discouraged but not blocked, since `middleware.ts` still functions with
no stated removal version.

## Fluid Compute and function sizing — requires Vercel platform

**When to apply:** an I/O-heavy workload shows cold starts or queued capacity under
concurrent load; or a project assumed the Performance CPU tier is faster without measuring
Active CPU and Provisioned Memory before/after.

```json
// vercel.json
{ "$schema": "https://openapi.vercel.sh/vercel.json", "fluid": true, "regions": ["iad1"] }
```

New projects already default to enabled since 2025-04-23 — check dashboard state before
proposing this key as if unconfigured. Set `"fluid": false"` only for a measured
regression, never by default.

**CPU tier** (dashboard only — "You cannot set your memory size using `vercel.json`"):
Project → Settings → Functions → Advanced Settings → Standard (2GB/1vCPU) or Performance
(4GB/2vCPUs, Pro/Enterprise) → redeploy.

```ts
// app/api/stream/route.ts — Next.js 16.3 App Router
export const maxDuration = 300

export async function POST(request: Request) {
  const body = await request.json()
  const stream = new ReadableStream({
    async start(controller) {
      controller.enqueue(new TextEncoder().encode(`accepted:${body.id}\n`))
      controller.close()
    },
  })
  return new Response(stream, { headers: { 'content-type': 'text/plain; charset=utf-8' } })
}
```

Fluid limits: Hobby default/max 300s; Pro/Enterprise default 300s, GA max 800s;
Pro/Enterprise beta per-function 1800s. Use the shortest ceiling that covers normal
streaming plus retries — for genuinely unbounded work, use Vercel Workflows instead.

**Why:** Fluid's gain is largest when requests alternate short CPU bursts with long I/O
waits — Active CPU is billed only for actual execution, roughly one second of a
ten-second wall-time request in the documented streaming model. Provisioned Memory is
still billed for the whole in-flight lifetime regardless — concurrency doesn't remove that
cost. Never let a handler crash the process uncaught — under Fluid's shared-process model,
an unhandled exception in one endpoint can crash concurrent requests on a *different*
endpoint sharing that instance.

**When the Fluid gain approaches zero:** CPU-bound processing/compression/crypto (little
idle time to reuse); memory-heavy requests hitting limits anyway; single infrequent
invocations; oversized Performance functions on I/O-only work.

**Verify after applying:** Deployment Resources shows Fluid enabled; Observability →
Functions shows Active CPU, Provisioned Memory, invocations, duration. Run simultaneous
I/O-heavy requests and compare cold starts/p95 before/after. For CPU sizing: compare p95
Active CPU, wall duration, Provisioned Memory GB-hours before keeping Performance over
Standard.

**Lock-in / reversibility:** `fully-reversible`. Toggle in dashboard or `vercel.json`;
redeploy; no data migration.

**Rollback:** set `"fluid": false"`; revert Function CPU to Standard; lower `maxDuration`.

## Region colocation — requires Vercel platform

**When to apply:** no confirmed match between the configured Function region and the
primary database's region; or high TTFB/504s on database-backed routes despite lean
queries.

```json
// vercel.json — example: database in Mumbai; per-function overrides for distinct data sources
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "regions": ["bom1"],
  "functions": { "api/eu-data.js": { "regions": ["cdg1"] } }
}
```

**Why:** `regions` is set to the database's region, not a geographically "central"
default — "choosing regions far from those services increases latency." Per-function
overrides apply only when functions genuinely have distinct data sources.

**Single documented practitioner data point (not a platform guarantee):** moving from
`iad1` to `bom1` to match a Mumbai database reportedly cut latency ~800ms→~100ms with zero
code change — but "changing the region in the dashboard is not enough on its own... you
need a fresh deployment."

**Verify after applying:**

```bash
curl -sI https://YOUR_DOMAIN/api/health | grep -Ei 'x-vercel-id|x-vercel-cache'
```

`x-vercel-id` shows the regions hit and where the Function executed. **Region changes
require a fresh deployment** — a dashboard-only change does not apply to existing
production traffic.

**Lock-in / reversibility:** `fully-reversible`. Change config; redeploy. A region change
starts a fresh durable ISR cache (scoped per deployment and region) — a cold-cache side
effect, not data loss.

**Rollback:** revert `regions` to the prior value and redeploy.

## Cache-header inspection recipe — requires Vercel platform

**When to apply:** any "CDN never caches this" or unexpected-cost report — run this
before assuming ISR/CDN is misconfigured.

```bash
curl -sI "https://YOUR_DOMAIN/catalog" | grep -Ei '^(cache-control|cdn-cache-control|x-vercel-cache|x-vercel-id|age|x-nextjs-stale-time):'
```

| Rendering mode | Next.js `Cache-Control` | Expected Vercel behavior |
|---|---|---|
| Fully static | `s-maxage=31536000` | `PRERENDER`/`HIT`, served globally |
| ISR / time-based | `s-maxage={revalidate}, stale-while-revalidate={expire - revalidate}` | Fresh `HIT`; after expiry, `STALE` serves old + refreshes |
| Dynamic page | `private, no-cache, no-store, max-age=0, must-revalidate` | CDN doesn't cache; Function runs; typically `MISS` |
| `use cache` in static shell | Follows resulting static/ISR lifetime | Shell CDN-cacheable; runtime per-instance entries may miss |
| `use cache: remote` in dynamic component | Dynamic page may still carry private/no-store | Remote handler may hit while `x-vercel-cache` stays `MISS` |

`x-vercel-cache` values: `PRERENDER`, `HIT`, `MISS`, `STALE` (old response served, refresh
started), `REVALIDATED` (entry deleted, this request blocks on regeneration), `BYPASS`.

**Why:** the browser-facing `Cache-Control` header is not reliable evidence — Vercel
strips CDN-only directives before sending it to the browser, so a confirmed CDN `HIT` may
still show `cache-control: public, max-age=0, must-revalidate` client-side. Only
`x-vercel-cache` tells the truth. A `REVALIDATED` status means the *next* request blocks
on foreground generation — time broad cache deletions accordingly, not immediately before
a traffic spike.

**Verify after applying:** repeat the `curl` from the same region before/after a TTL
boundary or intentional revalidation; confirm the `x-vercel-cache` transition matches
expectation (`HIT`→`STALE`→fresh `HIT`, or `MISS`→`HIT` after first generation).

**Lock-in / reversibility:** n/a — diagnostic only.

**Rollback:** n/a.

## ISR tag-scoped invalidation — requires Next.js ≥16.0.0 for two-arg `revalidateTag`

**When to apply:** broad/short blanket time-based revalidation, nondeterministic output in
cached HTML, or the write-unit-exhaustion pitfall matches.

```tsx
// app/products/[id]/page.tsx — previous-model ISR; use `use cache` + cacheLife if Cache Components is on.
export const revalidate = 3600

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const product = await fetch(`https://api.example.com/products/${id}`).then((r) => r.json())
  return <article>{product.name}</article>
}
```

Never render `new Date()`, `Math.random()`, or unstable ordering into ISR output —
"unchanged content revalidation incurs no writes; nondeterministic output defeats that
optimization," so every revalidation looks "changed" and consumes a write unit.

```ts
// app/actions.ts
'use server'
import { revalidateTag, updateTag } from 'next/cache'

export async function publishProduct(id: string) {
  await db.products.publish(id)
  revalidateTag(`product-${id}`, 'max')   // SWR: readers may see stale data while refreshing
}

export async function saveOwnProfile(userId: string) {
  await db.users.save(userId)
  updateTag(`user-${userId}`)             // read-your-writes within the mutation flow
}
```

**Why:** `revalidateTag(\`product-${id}\`, 'max')` tags per-product, not a blanket
`'products'` tag — the documented exhaustion incident traced to one save invalidating "far
more cached output than necessary" (canonical page, listing, category, localized
variants, sitemap all invalidating together). `'max'` fits a catalog update tolerating
brief staleness; `updateTag` fits a write the user must see immediately — these are
deliberately different semantics. On Vercel ISR, revalidation purges HTML+RSC together
and propagates across all regions within ~300ms; this guarantee does not extend to a
third-party CDN in front of Vercel.

**Verify after applying:** trigger the invalidation and confirm via the cache-header
recipe that the tagged route transitions correctly while sibling routes sharing the old
blanket tag are unaffected. Check the ISR Observability "Write Utilization" metric
(Observability+) before/after — a fix that doesn't reduce write volume didn't address the
root cause.

**Lock-in / reversibility:** `fully-reversible`. Revert to the prior blanket tag or
time-only revalidation — no persistent state depends on tag names.

**Rollback:** restore the previous single-tag or time-only call.

## Skew Protection enablement — requires Pro/Enterprise, Next.js ≥14.1.4 for `deploymentId`

**When to apply:** a deploy will change Server Action IDs, RSC payload shape, or required
request fields, on a Pro/Enterprise-eligible project with active sessions; or a long-lived
session (exam, editor, call) must survive a mid-session deploy.

**On Vercel-managed builds, no config is required** — Next.js 14.1.4+ needs no additional
config when built on Vercel. Confirm via Project → Settings → Advanced → Skew Protection;
projects created after 2024-11-19 are enabled by default.

**For external/prebuilt workflows only** (`vercel build --prebuilt`, self-hosted CI):

```ts
// next.config.ts — external/prebuilt workflows only
import type { NextConfig } from 'next'

const nextConfig: NextConfig = { deploymentId: process.env.NEXT_DEPLOYMENT_ID }

export default nextConfig
```

**Why:** the config key is **`deploymentId`**, read from **`NEXT_DEPLOYMENT_ID`** — never
`useDeploymentId`, a name absent from current docs; using the wrong key silently does
nothing. This recipe is scoped to external/prebuilt workflows only — a Vercel-managed repo
needs none of it.

**Full document navigations are not pinned by default** — "the framework doesn't pin
full-page navigations" and a hard refresh always gets the latest deployment. For
disruptive long sessions, extend pinning via the `__vdpl` cookie set through Proxy with a
scoped matcher and an appropriate maximum age; clear it when the session ends. **Custom
`fetch()` calls are never auto-pinned** — add `x-deployment-id`/`?dpl=` manually to any
hand-written fetch that must stay pinned.

**Verify after applying:** open production in a tab; deploy a version changing a Server
Action/RSC shape; use the old tab for client navigation; inspect requests for `?dpl=` or
`x-deployment-id` resolving to the old deployment. Dashboard Monitoring filter:
`skew_protection = 'active'`.

**Lock-in / reversibility:** `fully-reversible`. Disable in dashboard; no code change for
default framework-managed pinning. `__vdpl` pinning is `component-level-revert` — remove
the cookie-setting logic in Proxy.

**Rollback:** disable in dashboard; remove `deploymentId` (external workflows only);
remove `__vdpl` cookie logic from `proxy.ts`.

## Observability setup (Speed Insights / Web Analytics) — requires Vercel platform

**When to apply:** no RUM/CWV instrumentation present per
`measurement-regression-guardrails`, and the archetype justifies the per-project fee.

```bash
npm install @vercel/speed-insights
```

```tsx
// app/layout.tsx
import { SpeedInsights } from '@vercel/speed-insights/next'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
        <SpeedInsights />
      </body>
    </html>
  )
}
```
**Why:** `<SpeedInsights />` sits in the root layout, not per-page — it must render on
every route to capture site-wide RUM. Speed Insights measures CWV by route/device/country;
Web Analytics measures visitors/page-views — pick based on which question is actually
needed.

**Cost control:** use `sampleRate`/`beforeSend` to bound event volume — the per-project
base fee dominates on small sites, so sampling matters most for cost control on
high-traffic ones. See `references/gating/cost-model.md` for rates.

**Verify after applying:** enable in dashboard and redeploy; confirm
`/<unique-path>/script.js` appears in the document; confirm vitals in the network tab and
events in the dashboard after a few visits.

**Lock-in / reversibility:** `fully-reversible`. Remove the package/component and disable
in dashboard; billing prorates and stops at cycle end.

**Rollback:** remove `<SpeedInsights />` and uninstall `@vercel/speed-insights`; disable
in dashboard.

## Ordering within this domain

1. **Remove `runtime = 'edge'` and `preferredRegion` first** — the hard architectural
   prerequisite for `cacheComponents`; never bundle into the same task as enabling that
   flag, per `references/gating/priority-matrix.md`'s dependency graph.
2. **Migrate `middleware.ts` → `proxy.ts` and narrow the matcher** — cheap, reversible,
   removes a request-volume cost driver before sizing work is evaluated.
3. **Establish region colocation and Fluid/function sizing** — the dominant TTFB and cost
   levers; do this before tuning cache behavior, since a slow database round trip masks
   whatever caching accomplishes.
4. **Run the cache-header inspection recipe** to establish ground truth before proposing
   ISR invalidation changes — never guess cache state from code alone.
5. **Apply ISR tag-scoped invalidation** once true cache behavior is confirmed.
6. **Enable Skew Protection before any deploy that changes Server Action/RSC contracts** —
   this must land before, not after, the contract-changing deploy it protects.
7. **Add observability last** — it measures the result of everything above, not a
   precondition for any of it.

## Conflicts to watch

- **Broad `proxy.ts` matching taxes every request, including cacheable ones.** "Proxy runs
  before routes, assets, and images" — a cost regression traced here is a matcher-scoping
  bug, not a Fluid Compute pricing surprise; verify the matcher before filing a Fluid cost
  finding.
- **Region changes start a fresh durable ISR cache** — plan for post-change origin load
  exactly as after any new deploy.
- **A build-cost spike may actually be a build-machine tier issue**, not a runtime lever
  here — cross-check `references/detect/build-performance-turbopack.md` before attributing
  a bill increase to Fluid Compute or ISR.
- **Skew Protection doesn't cover custom `fetch()` or full document navigations by
  default** — confirm which request classes needed pinning and whether `__vdpl` or manual
  headers are also required.
