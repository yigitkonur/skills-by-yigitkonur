# Detect: vercel-platform-deployment

**Corpus lineage:** vercel-platform-deployment/00-overview-feature-inventory.md,
vercel-platform-deployment/03-when-to-use.md,
vercel-platform-deployment/06-tradeoffs-pitfalls.md,
vercel-platform-deployment/07-version-lockin-seo-vercel-cost-model.md

## Applicability gate

| Feature / config key | Introduced | Requires | Removed-in | Gate rule |
|---|---|---|---|---|
| Fluid Compute | default for new projects since 2025-04-23 | Vercel platform; Node.js or Python runtime for full concurrency benefit | n/a | INFORMATIONAL if already default-on and unmodified. NOT APPLICABLE if the target is not deployed on Vercel. |
| `vercel.json` → `"fluid": true` | current | Vercel platform | n/a | NOT APPLICABLE if the project predates the default and Fluid is already enabled via dashboard — check dashboard state before proposing the JSON key as if it were missing. |
| `vercel.json` → `regions` / `functions.*.regions` | current | Vercel platform | n/a — replaces route-level `preferredRegion` | BLOCKED-precondition: confirm the primary database's region before proposing a value; a guessed region is worse than no finding. |
| `functionFailoverRegions` | current | Enterprise plan | n/a | NOT APPLICABLE below Enterprise. |
| `export const maxDuration = N` | Next.js App Router ≥13.5 | n/a | n/a | Always applicable; absence is not itself a finding unless a route is known to run long operations without a Workflow. |
| `export const runtime = 'edge'` | older App Router | n/a | **Deprecated in Next.js 16.3** for pages/layouts/route handlers | REMOVE if found on an install ≥16.3.0 — probe first per `references/gating/capability-probe.md`. On <16.3, this is not yet deprecated; do not file removal. **BLOCKED precondition for `cacheComponents`** — see `references/detect/rendering-strategy-caching.md` row 1. |
| `export const preferredRegion` | older Edge placement API | n/a | **Deprecated in Next.js 16.3** | REMOVE if found on an install ≥16.3.0; replace with `vercel.json` `regions`/`functions.*.regions`. Tied to the deprecated Edge route runtime — remove alongside `runtime = 'edge'`, not independently. |
| `proxy.ts` / exported `proxy()` | Next.js 16.0; renamed from `middleware.ts` | n/a | n/a (Node.js runtime fixed, cannot be configured) | NOT APPLICABLE below 16.0 (repo still correctly uses `middleware.ts`). On ≥16.0, `middleware.ts` presence is itself a finding (see graveyard row below). |
| `middleware.ts` / exported `middleware()` | classic | n/a | **Deprecated + renamed in 16.0**, no stated removal version | REMOVE (migrate) if found on an install ≥16.0.0 via the `middleware-to-proxy` codemod. Still functional — this is `minor`, never `critical`, absent a stated removal version. |
| `config.matcher` in `proxy.ts`/`middleware.ts` | current | n/a | n/a | Absence on a repo with either file is itself a finding — Proxy/Middleware runs on every request without one. |
| `use cache: remote` | Next.js 16.0 with Cache Components | `cacheComponents: true` | n/a | NOT APPLICABLE if `cacheComponents` absent — see `references/detect/rendering-strategy-caching.md`. |
| ISR (`export const revalidate` / `use cache` + `cacheLife`) | classic / 16.0 | n/a | n/a | Always applicable; findings here are about invalidation scope and determinism, not the mechanism's presence. |
| `revalidateTag(tag, 'max')` two-arg form | Next.js 16.0 (arity change) | n/a | n/a | See `references/gating/version-matrix.md` graveyard row for the single-arg deprecated form — that finding belongs to `data-fetching-patterns`, cross-referenced here only for ISR-invalidation-scope findings. |
| `deploymentId` config key | stable since Next.js 14.1.4 | n/a — auto-applied on Vercel-managed builds | n/a | INFORMATIONAL if the repo is built and deployed entirely through Vercel's own pipeline (no config needed there). BLOCKED-precondition (must be set) if the repo uses an external/prebuilt build workflow (`vercel build` / `vercel deploy --prebuilt`, self-hosted CI) — the automatic case does not cover it. **The config key is `deploymentId` / env `NEXT_DEPLOYMENT_ID` — never `useDeploymentId`; that name does not exist in current docs.** |
| Vercel Skew Protection | default for projects created after 2024-11-19 | Pro/Enterprise plan | n/a | NOT APPLICABLE below Pro. INFORMATIONAL if already default-on for an eligible project with no Server Action/RSC contract changes planned. |
| Speed Insights / `@vercel/speed-insights` | current | n/a | n/a | Absence alone is not a finding — only propose when the repo has no other RUM/CWV measurement per `measurement-regression-guardrails`. |
| Web Analytics | current | n/a | n/a | Same treatment as Speed Insights — absence is not automatically a finding. |
| Instant Rollback | current | n/a | n/a | Applicability check is procedural (is a prior eligible deployment retained), not code-based — rarely a repo-grep finding. |

## Detection commands

```bash
# 1. runtime = 'edge' exports — deprecated in 16.3, hard blocker for cacheComponents
rg -n "export const runtime\s*=\s*['\"]edge['\"]" --glob 'app/**/*.{ts,tsx}' <target-repo-root>
```

```bash
# 2. preferredRegion exports — deprecated in 16.3, tied to Edge runtime
rg -n "export const preferredRegion\s*=" --glob 'app/**/*.{ts,tsx}' <target-repo-root>
```

```bash
# 3. middleware.ts still present — deprecated, renamed to proxy.ts in 16.0
find <target-repo-root> -maxdepth 2 \( -name 'middleware.ts' -o -name 'middleware.tsx' -o -name 'middleware.js' \)
```

```bash
# 4. proxy.ts / middleware.ts matcher — absence means it runs on every request
rg -n "export const config" -A 5 --glob 'proxy.{ts,js}' --glob 'middleware.{ts,js}' <target-repo-root>
```

```bash
# 5. Overly broad or missing matcher patterns — catches assets/robots.txt/sitemap.xml/OG routes
rg -n "matcher\s*:" -A 10 --glob 'proxy.{ts,js}' --glob 'middleware.{ts,js}' <target-repo-root>
```

```bash
# 6. vercel.json region configuration — confirm it exists and check the value
rg -n '"regions"' --glob 'vercel.json' <target-repo-root>
```

```bash
# 7. deploymentId / NEXT_DEPLOYMENT_ID configuration — required for external/prebuilt workflows
rg -n "deploymentId|NEXT_DEPLOYMENT_ID|useDeploymentId" --glob 'next.config.*' --glob '.github/workflows/*.{yml,yaml}' <target-repo-root>
```

```bash
# 8. nondeterministic output inside cached/ISR routes — defeats "unchanged content writes nothing"
rg -n "new Date\(\)|Math\.random\(\)|crypto\.randomUUID\(\)" --glob 'app/**/page.{ts,tsx}' <target-repo-root>
```

```bash
# 9. short blanket ISR revalidation intervals — candidate for narrow tag-scoped invalidation instead
rg -n "export const revalidate\s*=\s*[0-9]+" --glob 'app/**/*.{ts,tsx}' <target-repo-root>
```

```bash
# 10. Function region hints in code/comments vs. known database region — manual cross-check
rg -n "regions\s*:" --glob 'vercel.json' --glob '**/*.{ts,tsx}' <target-repo-root>
```

## Domain severity rubric

- **critical**
  - `export const runtime = 'edge'` present on an install ≥16.3.0 — no longer supported;
    routes and pages run on Node.js regardless, so the export is dead and misleading, and
    it hard-blocks any `cacheComponents` adoption.
  - `proxy.ts`/`middleware.ts` has no `config.matcher` at all on a repo with any
    non-trivial logic in the handler (auth check, cookie read, redirect logic) — every
    request including static assets and image optimization requests pays the cost; the
    docs explicitly warn this "can unintentionally block CSS, JS, or images from loading."
  - Server Action/RSC-contract-changing deploy planned with Skew Protection absent or
    disabled on a Pro/Enterprise-eligible project with active user sessions.

- **major**
  - `export const preferredRegion` present on an install ≥16.3.0 — deprecated, no longer
    maps to a supported placement mechanism for Node.js routes.
  - Function region configured (or defaulted to `iad1`) with no evidence it matches the
    primary database's region — the documented mechanism for cross-region TTFB inflation.
  - `middleware.ts` still present (not yet migrated to `proxy.ts`) on an install ≥16.0.0 —
    functional today, but the renamed convention is the documented forward path.
  - Nondeterministic output (`new Date()`, `Math.random()`, `crypto.randomUUID()`) rendered
    directly into an ISR or `"use cache"`-scoped route — every revalidation looks
    "changed," consuming a write unit each time even though content should be identical.
  - Short, blanket time-based ISR revalidation applied broadly across content types
    (article + listing + category + locale + sitemap all on the same short interval) with
    no event-driven tag scoping — the documented write-unit-exhaustion pattern.

- **minor**
  - `proxy.ts` matcher present but broader than necessary — catching `robots.txt`,
    `sitemap.xml`, or `api/og` routes that don't need the gate logic.
  - `deploymentId`/`NEXT_DEPLOYMENT_ID` absent on a repo confirmed to use an external or
    prebuilt build workflow — Skew Protection's automatic Vercel-managed path does not
    cover it, but no active incident is implied yet.
  - Speed Insights or Web Analytics absent with no other RUM/CWV instrumentation in the
    repo, and the archetype (public-traffic site) would benefit.

- **informational**
  - Fluid Compute already default-on and unmodified, or explicitly configured via
    `"fluid": true"` with no measured regression — nothing to propose.
  - `regions` already set to a value matching the confirmed database region.
  - `deploymentId` correctly absent because the repo builds and deploys entirely through
    Vercel's own managed pipeline (auto-covered).
  - `middleware.ts`/`proxy.ts` matcher already narrowly scoped to exactly the routes that
    need the gate.

## False-positive filters

- **Comments/docstrings are not live usage.** A `runtime = 'edge'` or `preferredRegion`
  match inside `//`, `/* */`, or a JSDoc block explaining why it was removed is not a
  finding.
- **Test files are excluded.** `**/*.test.{ts,tsx}`, `**/*.spec.{ts,tsx}`, `__tests__/`,
  `e2e/` — runtime/region exports in test fixtures are not production deployment
  configuration.
- **`vercel.json` absence is not automatically a finding.** A project relying entirely on
  dashboard-configured regions/Fluid settings has no `vercel.json` — check the dashboard
  state (or ask) before proposing the JSON key as if the feature were unconfigured.
- **A short `revalidate` interval on genuinely fast-changing content (live scores, stock
  levels) is not automatically a finding.** The write-unit-exhaustion pattern requires
  *broad* short intervals across content that doesn't actually change that often — a single
  deliberately fast-revalidating route with a comment explaining the volatility is
  informational.
- **`new Date()`/`Math.random()` used for telemetry or logging inside a route, not
  rendered into the cached/ISR output itself, is not a finding.** Only flag nondeterminism
  that actually reaches the response body of a cached route — `performance.now()` used for
  server-side timing logs is not the same as a timestamp rendered into HTML.
- **A `middleware.ts` file that only re-exports from a shared implementation is one
  finding, not N** — collapse to the shared file per the wrapper-collapse rule.
- **Matches inside `.next/`, `node_modules/`, or other build/dependency output are not
  live usage** — restrict globs to `app/**`, `proxy.{ts,js}`, `middleware.{ts,js}`,
  `vercel.json`, and `next.config.*`.
- **`preferredRegion` exports on an install below 16.3 are not yet deprecated** — probe
  the installed version first; do not file a removal finding against a still-valid API.

## Evidence format — what each finding file must contain

Every finding the audit subagent writes under `findings/vercel-platform-deployment/` must
include:
- `file:line` (exact)
- literal matched text (copied from the `rg`/`find` output)
- which gate row or pitfall signature it maps to
- severity
- one-line why-this-matters (drawn from the corpus prose above)
- suggested fix recipe section name from `references/fix/vercel-platform-deployment.md`
- the resolved `next` version and, where relevant, the confirmed (or unconfirmed) primary
  database region — record both once at the top of the findings file since region findings
  depend on the latter and Edge-runtime findings depend on the former

## Pitfall signatures

| Failure signature | Cause | Fix direction | Recipe section |
|---|---|---|---|
| Intermittent `405 Method Not Allowed` on an unrelated endpoint, log shows "Node.js process exited with exit status: 1" | An unhandled exception in one endpoint crashes the shared process under Fluid's in-function concurrency, taking down concurrent requests sharing that instance | Never let a request handler throw uncaught — catch and return an explicit HTTP error response | Fluid/function sizing |
| Consistently high TTFB / 504 timeouts on database-backed routes despite lean queries | Function region far from the database region (e.g. `iad1` default vs. a database on another continent) | Set project or per-function `regions` to the database's region and redeploy — dashboard-only region changes do not apply until a fresh deployment | Region colocation |
| Static assets, images, or unrelated routes are slow, blocked, or unexpectedly redirected; authenticated-looking traffic passes with a forged cookie | Missing `matcher` — Proxy runs on every request including `_next/static`, `_next/image`, `public/` assets; and/or relying on Proxy alone for authorization while a Server Function rides a different, unmatched route | Add a precise or negative-lookahead matcher; validate authentication/authorization inside every Server Function, never Proxy alone | `middleware.ts` → `proxy.ts` codemod + narrow matcher |
| ISR write quota exhausted far faster than expected (Hobby: 100% of 200,000 included writes) | One content change or short recurring revalidation interval invalidates far more cached output than necessary (draft saves invalidating public listings; canonical + listing + category + locale + sitemap all revalidating together) | Move from recurring time-based revalidation to event-driven, narrowly tagged invalidation (`cacheTag` per article/listing/category/language/sitemap); add pagination to bound blast radius | ISR tag-scoped invalidation |
| CDN never appears to cache a page even though `Cache-Control` looks correct in code | Relying solely on the browser-facing `Cache-Control` header — Vercel strips `s-maxage`/`stale-while-revalidate` before sending it to the browser, returning `cache-control: public, max-age=0, must-revalidate` even on a cache HIT | Check `x-vercel-cache`, not the rewritten browser-facing `Cache-Control`, to confirm cache status | Cache-header inspection recipe |
| Long-open tab (dashboard, live exam) suddenly errors mid-session right after a deploy, even with Skew Protection enabled | Full document (hard) navigations are not pinned by default — only framework-managed assets, client-side navigations, and Server Actions are; a hard refresh always gets the latest deployment | For genuinely disruptive long sessions, explicitly set the `__vdpl` cookie via Proxy with a scoped matcher | Skew Protection enablement |
| Build minutes suddenly far more expensive with no explicit machine-type change | Build machine defaulted to a higher tier (e.g. Turbo, 30 vCPU) — a build-pricing issue, distinct from Fluid Compute or ISR | Confirm current build machine assignment in Project Settings → Build and Deployment before assuming a Fluid-related cause | (cross-domain — see `references/fix/build-performance-turbopack.md`) |
| Vercel bill spikes traced to auth Proxy/middleware logic running on every landing-page request instead of only protected routes | Broad `matcher` (or no matcher) causing Proxy to execute — and count against Fluid Active CPU — on every request | Restrict the matcher to only the routes that actually need the gate | `middleware.ts` → `proxy.ts` codemod + narrow matcher |

## Cross-domain interactions

1. **`runtime = 'edge'` removal is a hard prerequisite for `cacheComponents`.** Any finding
   here for edge-runtime exports routes to this domain's fix file first — never propose
   enabling Cache Components (`rendering-strategy-caching`) in the same task as the Edge→Node
   migration; sequence them per `references/gating/priority-matrix.md`.
2. **A misdiagnosed "Vercel cost spike" may actually be a build-machine assignment issue,
   not Fluid Compute or ISR.** Confirm the build machine tier via
   `references/detect/build-performance-turbopack.md` before filing a runtime-cost finding.
3. **Skew Protection findings interact with any task changing Server Action or RSC payload
   shape** across `data-fetching-patterns` and `rendering-strategy-caching` — a route
   whose action IDs or payload shape will change on the next deploy needs Skew Protection
   confirmed *before* that deploy, not after.
4. **Image transformation/cache-write billing is owned by `image-optimization`**, not this
   domain — a cost finding about `width × quality × format` variant explosion belongs
   there; this domain owns Fluid, region, ISR, and Proxy cost drivers only. See
   `references/gating/cost-model.md`.

## Reference pointer

Fix recipes for this domain live in `references/fix/vercel-platform-deployment.md`.
