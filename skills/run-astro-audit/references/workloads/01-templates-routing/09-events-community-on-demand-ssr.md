# Mission Brief: Events, Community & On-Demand SSR Audit

## 3.0 Skills / Tools: view_file, run_command, astro-component-architect.

## 3.1 Context Block

While 71 of 73 page types are statically generated (SSG), Events pages (`/events`, `/events/ai`, `/tr/etkinlikler`, `/tr/etkinlikler/yapay-zeka`) are on-demand SSR routes rendered by Cloudflare Workers (`src/worker.ts`).
They dynamically partition conferences into 'upcoming' and 'past' based on current UTC timestamps.
Digitalzone and Meetups pages render community archives, speaker rosters, and talk session videos.

Astro Architectural & Best Practice Rules:

- **Route Specificity & Collision Resolution ([03-route-priority-and-collision-resolution.md](../../best-practices/03-routing-and-pages/03-route-priority-and-collision-resolution.md))**:
  Astro enforces a strict 8-tier route priority matrix. Static subpages (`events/ai.astro`, `events/index.astro`) take precedence over dynamic catch-all routes (`events/[...rest].astro`). Rest parameters must never shadow static community conference hubs, and prerendered dynamic routes take priority over server on-demand dynamic routes.
- **Built-in Pagination & Navigation Metadata ([06-built-in-pagination-and-nested-pagination.md](../../best-practices/03-routing-and-pages/06-built-in-pagination-and-nested-pagination.md))**:
  Community archives (Digitalzone, Meetup talk videos) that generate static paginated archives must use Astro's native `paginate()` helper with typed `Page<T>` contracts rather than rolling manual array chunking (`slice((page-1)*limit, ...)`). For nested conference year pagination, pass `{ params: { year }, pageSize }` into `paginate()`.
- **SSR On-Demand vs Static Prerendering ([07-ssr-on-demand-routes-vs-prerendering.md](../../best-practices/03-routing-and-pages/07-ssr-on-demand-routes-vs-prerendering.md))**:
  Astro 5 standardizes build output under `output: 'static'`. On-demand routes opt into dynamic server execution with `export const prerender = false`. In Astro, exporting `getStaticPaths()` inside an on-demand route triggers a fatal build error; on-demand routes must resolve dynamic parameters on the fly via `Astro.params`.
- **Prerender Boundary for Dynamic Endpoints ([02-prerender-boundary-dynamic-endpoints.md](../../best-practices/05-data-fetching-and-endpoints/02-prerender-boundary-dynamic-endpoints.md))**:
  Dynamic community endpoints (e.g. event registration, ticket booking, live webinar attendance) must explicitly declare `export const prerender = false;`. Without this flag, endpoints execute once at build time and reject incoming HTTP POST requests in production.
- **APIRoute Signature & Standard Web Response ([03-apiroute-signature-and-web-response.md](../../best-practices/05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response.md))**:
  All community API endpoints must be typed with `APIRoute` from `astro` and return standard Web API `Response` or `Response.json(...)` instances. Using legacy Node/Express methods (`res.json()`, `res.status()`) throws fatal runtime errors.
- **Explicit HTTP Method Handlers & Method Guards ([06-http-method-handlers-and-method-guards.md](../../best-practices/05-data-fetching-and-endpoints/06-http-method-handlers-and-method-guards.md))**:
  Export explicit uppercase method handlers (`export const GET: APIRoute`, `export const POST: APIRoute`). Never use monolithic `switch (request.method)` handlers under `ALL`. Explicit exports ensure automatic `HEAD` handling and clean 405 Method Not Allowed semantics.
- **Edge Resiliency & Error Boundary Rule**: SSR runtime execution on Cloudflare Workers must stay within CPU limits (50ms). Unhandled runtime exceptions in SSR mode are caught by `src/pages/500.astro` which receives `Astro.props.error`. Leaking raw `error.stack` or environment details in production is a severe security vulnerability; errors must be logged safely on the server and present a friendly, sanitized message to the user.
- **Hydration Rule**: Video and talk session archives (e.g. Digitalzone/Meetups video rosters) are heavy interactive widgets. They must not use `client:load`. Use `client:visible={{ rootMargin: '200px' }}` so scripts are fetched just before scrolling into view, preventing layout shifts without blocking initial paint.

Critical files to inspect:

- `src/pages/events/[...rest].astro` and `src/features/events/components/EventsRoute.astro`
- `src/features/events/data/event-partition.ts`
- `src/features/community/components/DigitalzoneRoute.astro`
- `src/features/community/components/MeetupsRoute.astro`
- `src/lib/routing/enumerate.ts` (`ON_DEMAND_ROUTE_PATHS`)
- `src/pages/500.astro` and `src/pages/404.astro`

## 3.2 Mission Objective

Audit the on-demand SSR events pipeline, community conference hubs, dynamic registration endpoints, and error boundaries.
Outcome: Verify that on-demand routes handle edge worker execution limits (50ms CPU limit), cache static event metadata effectively, enforce correct Astro 5 `prerender = false` semantics without `getStaticPaths` conflicts, eliminate route collision ambiguity between static and catch-all rest routes, implement secure 500 error boundaries, and hydrate conference video filters with `client:visible={{ rootMargin: '200px' }}`.
Constraints: Read-only audit; inspect Cloudflare Workers runtime boundaries.
Autonomy Grant: You own this mission end-to-end. Trace SSR header policies, time-based event partitioning, and video filter hydration. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `EventsRoute.astro`: check how event partitioning interacts with edge caching headers (`Cache-Control: public, max-age=60, s-maxage=300`).
2. Inspect `DigitalzoneRoute.astro` lines 50-90: verify that video carousel islands use `client:visible={{ rootMargin: '200px' }}` instead of `client:load`.
3. Check `src/lib/routing/enumerate.ts`: ensure `ON_DEMAND_ROUTE_PATHS` lists all on-demand routes accurately.
4. Verify that no SSR on-demand route exports `getStaticPaths()`.
5. Audit `src/pages/500.astro` to ensure raw `error.stack` is never rendered in production.
6. Verify route priority: ensure `src/pages/events/ai.astro` is correctly resolved as static without being captured by `src/pages/events/[...rest].astro`.

### ❌ Bad Practice / Anti-Pattern: Conflicting SSR Flags & Route Priority Collisions

```astro
---
// src/pages/events/[...rest].astro - Conflicting SSR flags & unhandled error leak
export const prerender = false;

// ERROR in Astro: getStaticPaths cannot be used on server-rendered routes!
export async function getStaticPaths() {
  return [{ params: { rest: undefined } }];
}

// Insecure 500 handler leaking internal stack trace in production:
// <pre>{(Astro.props.error as any)?.stack}</pre>
---
<!-- Heavy video carousel blocking critical path -->
<TalkVideoCarousel client:load events={events} />
```

_Why this fails:_ Astro throws compilation errors when `getStaticPaths` is exported on routes with `prerender = false`. Rendering raw `error.stack` leaks server paths, database credentials, and secret traces. `client:load` on video carousels destroys page load metrics.

### ✅ Best Practice / Idiomatic: Clean SSR Route & Priority Resolution

```astro
---
// src/pages/events/[...rest].astro - Idiomatic Astro 5 SSR on-demand route
// Reference: ../../best-practices/03-routing-and-pages/03-route-priority-and-collision-resolution.md
// Reference: ../../best-practices/03-routing-and-pages/07-ssr-on-demand-routes-vs-prerendering.md
export const prerender = false;

// Edge caching headers to protect Cloudflare Worker 50ms CPU budget
Astro.response.headers.set(
  "Cache-Control",
  "public, max-age=60, s-maxage=300, stale-while-revalidate=600"
);

// Dynamic parameters resolved at runtime via Astro.params (never getStaticPaths)
const { rest } = Astro.params;
const { upcoming, past } = await getPartitionedEvents(rest);
---
<main>
  <UpcomingEventsList events={upcoming} />
  <!-- Smooth pre-hydration 200px before scroll entry -->
  <TalkVideoCarousel client:visible={{ rootMargin: '200px' }} events={past} />
</main>
```

### ❌ Bad Practice / Anti-Pattern: Manual Pagination Math in Talk Video Archives

```astro
---
// src/pages/community/talks/[page].astro
// Rolling manual pagination logic with slice() and custom math
export async function getStaticPaths() {
  const talks = await getAllTalkVideos();
  const limit = 12;
  const pages = Math.ceil(talks.length / limit);
  return Array.from({ length: pages }, (_, i) => ({
    params: { page: String(i + 1) },
    props: { talks: talks.slice(i * limit, (i + 1) * limit) }
  }));
}
---
```

### ✅ Best Practice / Idiomatic: Native paginate() with Page Metadata

```astro
---
// src/pages/community/talks/[page].astro
// Reference: ../../best-practices/03-routing-and-pages/06-built-in-pagination-and-nested-pagination.md
import type { GetStaticPaths, Page } from "astro";
import { getAllTalkVideos } from "@/features/community/data";

export const getStaticPaths = (async ({ paginate }) => {
  const talks = await getAllTalkVideos();
  return paginate(talks, { pageSize: 12 });
}) satisfies GetStaticPaths;

interface Props {
  page: Page<TalkVideo>;
}
const { page } = Astro.props;
---
<nav aria-label="Talks Pagination">
  {page.url.prev && <a href={page.url.prev}>Previous</a>}
  <span>Page {page.currentPage} of {page.lastPage}</span>
  {page.url.next && <a href={page.url.next}>Next</a>}
</nav>
```

### ❌ Bad Practice / Anti-Pattern: Missing SSR Prerender Boundary on Event Registration

```ts
// src/pages/api/events/register.ts
// Missing prerender = false in static Astro project: executes once at build time!
import type { APIRoute } from 'astro'

export const POST: APIRoute = async ({ request }) => {
  const registration = await request.json()
  // Fails in production: live user registrations are rejected!
  return new Response(JSON.stringify({ registered: true }))
}
```

### ✅ Best Practice / Idiomatic: Explicit prerender = false & Typed APIRoute

```ts
// src/pages/api/events/register.ts
// Reference: ../../best-practices/05-data-fetching-and-endpoints/02-prerender-boundary-dynamic-endpoints.md
// Reference: ../../best-practices/05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response.md
// Reference: ../../best-practices/05-data-fetching-and-endpoints/06-http-method-handlers-and-method-guards.md
import type { APIRoute } from 'astro'

export const prerender = false

export const POST: APIRoute = async ({ request }) => {
  if (request.headers.get('Content-Type') !== 'application/json') {
    return Response.json({ error: 'Invalid Content-Type' }, { status: 400 })
  }

  const payload = await request.json()
  const confirmed = await registerAttendee(payload)

  return Response.json(
    { success: true, attendee: confirmed },
    {
      status: 201,
      headers: { 'Cache-Control': 'private, no-cache, no-store' },
    },
  )
}
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/01-templates-routing/09-events-community-on-demand-ssr/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Rule ID Mapping**: Every defect recorded in `findings.json` must explicitly map to an authoritative Astro best practice rule identifier using the `rule_id` field (e.g. `RULE-ID: 03-routing-and-pages/03-route-priority-and-collision-resolution`, `RULE-ID: 03-routing-and-pages/06-built-in-pagination-and-nested-pagination`, `RULE-ID: 03-routing-and-pages/07-ssr-on-demand-routes-vs-prerendering`, `RULE-ID: 05-data-fetching-and-endpoints/02-prerender-boundary-dynamic-endpoints`, `RULE-ID: 05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response`, `RULE-ID: 05-data-fetching-and-endpoints/06-http-method-handlers-and-method-guards`).

You must create and populate the following deliverables in `docs/audits/results/01-templates-routing/09-events-community-on-demand-ssr/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps. Every item MUST include a valid `rule_id` linking to `../../best-practices/`:

```json
[
  {
    "id": "09-EVENTS-COMMUNITY-ON-DEMAND-SSR-001",
    "rule_id": "RULE-ID: 03-routing-and-pages/03-route-priority-and-collision-resolution",
    "file": "path/to/file.ext",
    "line": 42,
    "severity": "critical" | "high" | "medium" | "low",
    "category": "syntax" | "hydration" | "parity" | "performance" | "security",
    "defect": "Precise description of what is broken or violating invariants",
    "remediation": "Concrete, actionable instruction on how to fix it"
  }
]
```

2. **`evidence.md`**: Comprehensive investigative research log:
   - Full command outputs, vitest runs, grep matches, AST dumps.
   - Analysis of confirmed facts vs assumptions.
   - Step-by-step reproduction proof.

3. **`handoff.md`**: The executive, action-oriented implementation blueprint for the next subagent:
   - **Executive Summary:** Overall health of this domain (Clean / Minor Defects / Blockers).
   - **Architectural Invariants:** Rules that the fixing agent must NEVER violate while remediating.
   - **Step-by-Step Remediation Checklist:** Prioritized action items (ordered from highest to lowest severity).
   - **Exact Code Replacements:** File paths, line numbers, current faulty snippet, and drop-in replacement snippet.
   - **Verification Battery:** The exact commands the fixing agent must run post-remediation to prove 100% success.

4. **`issue-body.md`**: The publication-ready GitHub Issue markdown body adhering to the two-tier structure:
   - **Checklist Header**: The verified nested checklist of up to 200 items (3 levels max).
   - **Outer Tier (localized primary locale)**: Conversational human summary (1-2 sentences), affected URLs/routes table, surface area table (viewports, themes, components), observed defect vs expected behavior (WITHOUT prescribing code fixes).
   - **Inner Tier (English `<details>`)**: Collapsed block titled `<details><summary><strong>Agent implementation brief — scope, source map, behavior contracts, and verification</strong></summary>...</details>`. Contains exact `file:line` citations, quoted 3-8 lines of code, defect classification (`bug` | `by-design` | `drift` | `reversal`), required behavioral invariants, known traps, acceptance checklist, and embeds the structured `findings.json` table and `handoff.md` remediation steps.

5. **Publication via GitHub CLI (`gh`) & Sub-Issue Creation**:
   Execute the turnkey publisher script `scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, validates the checklist (<= 200 items, <= 3 levels nesting), creates the primary issue, spawns linked sub-issues (capped at 20) for critical and high severity defects, and commits/pushes results directly to `main` without PR:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
# node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/01-templates-routing/09-events-community-on-demand-ssr/issue-body.md" \
  --title "[Audit - Events, Community & On-Demand SSR Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/01-templates-routing/09-events-community-on-demand-ssr/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Verify that `isOnDemandRoutePath('/events')` evaluates to true in `src/lib/routing/enumerate.ts`.
2. Check build output route indicators via `pnpm astro check && pnpm astro build`: confirm on-demand routes render with server indicator (`λ`) and static routes with (`○`).
3. Run `git grep -n "prerender = false" src/pages/` to audit all on-demand SSR routes and dynamic endpoints.
4. Run `git grep -n "paginate(" src/pages/` to verify native Astro pagination in community conference archives.
5. Run `git grep -n "export const POST\|export const GET" src/pages/api/` to audit dynamic endpoint method handlers.
6. Verify that zero SSR routes export `getStaticPaths()` when `prerender = false`.
7. Inspect cache headers via `curl -I http://localhost:4321/events | grep -i "cache-control"`.
8. Audit error pages: confirm `src/pages/500.astro` does not render raw `error.stack` in production environments (`grep -rn "error.stack" src/pages/500.astro || true`).
9. Confirm video carousels in `DigitalzoneRoute.astro` use `client:visible={{ rootMargin: '200px' }}` instead of `client:load`.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/01-templates-routing/09-events-community-on-demand-ssr/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Events, Community & On-Demand SSR Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/01-templates-routing/09-events-community-on-demand-ssr/findings.json` (N defects logged)
   - `file://docs/audits/results/01-templates-routing/09-events-community-on-demand-ssr/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/01-templates-routing/09-events-community-on-demand-ssr/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/01-templates-routing/09-events-community-on-demand-ssr/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/01-templates-routing/09-events-community-on-demand-ssr/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
