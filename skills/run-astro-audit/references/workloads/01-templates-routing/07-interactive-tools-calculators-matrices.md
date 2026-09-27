# Mission Brief: Interactive Tools, Calculators & Comparison Matrices Audit

## 3.0 Skills / Tools: view_file, run_command, compare-anything, react-doctor.

## 3.1 Context Block

The application provides interactive utility tools: high-performance canvas comparison matrices (MatrixPage), SERP Preview, SEO Sheets, SEO Quiz, Book Foundry, and DSH Navigator.
In Astro 7, comparison matrix islands must use client:visible to avoid blocking the main thread at initial page render.
Additionally, inline application/json data scripts must carry is:inline to prevent compiler warnings.

Astro Architectural & Best Practice Rules:

- **Route Specificity & Collision Resolution ([03-route-priority-and-collision-resolution.md](../../best-practices/03-routing-and-pages/03-route-priority-and-collision-resolution.md))**:
  Astro enforces a strict, deterministic 8-tier route priority matrix. Static pages take precedence over dynamic routes, and named parameters (`compare/[slug].astro`) take precedence over catch-all rest parameters (`compare/[...rest].astro`). Static matrix indices and directory routes (`compare/index.astro`) must never collide with or be shadowed by `[slug].astro`.
- **Built-in Pagination & Navigation Metadata ([06-built-in-pagination-and-nested-pagination.md](../../best-practices/03-routing-and-pages/06-built-in-pagination-and-nested-pagination.md))**:
  Tool listing directories and matrix catalogs must use Astro's native `paginate()` helper with typed `Page<T>` contracts rather than rolling manual array chunking (`slice((page - 1) * limit, ...)`) and manual URL math.
- **SSR On-Demand vs Static Prerendering ([07-ssr-on-demand-routes-vs-prerendering.md](../../best-practices/03-routing-and-pages/07-ssr-on-demand-routes-vs-prerendering.md))**:
  Astro 5 standardizes build output under `output: 'static'`. Static tool calculators pre-render to HTML, while any real-time live data queries or authenticated calculators must explicitly declare `export const prerender = false` and resolve parameters via `Astro.params` without exporting `getStaticPaths()`.
- **Prerender Boundary for Dynamic Endpoints ([02-prerender-boundary-dynamic-endpoints.md](../../best-practices/05-data-fetching-and-endpoints/02-prerender-boundary-dynamic-endpoints.md))**:
  API calculation endpoints, export handlers, or proxy services (e.g. `/api/tools/calculate.json.ts`) must explicitly declare `export const prerender = false;`. Without this flag, endpoints execute once during CI build and freeze as static artifacts, failing to handle runtime POST mutations.
- **APIRoute Signature & Standard Web Response ([03-apiroute-signature-and-web-response.md](../../best-practices/05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response.md))**:
  All tool endpoints must be strictly typed using `APIRoute` from `astro` and return standard Web API `Response` or `Response.json(...)` instances. Returning naked JavaScript objects or framework-specific wrappers causes runtime fatal errors.
- **Explicit HTTP Method Handlers & Method Guards ([06-http-method-handlers-and-method-guards.md](../../best-practices/05-data-fetching-and-endpoints/06-http-method-handlers-and-method-guards.md))**:
  Export explicit uppercase method handlers (`export const GET: APIRoute`, `export const POST: APIRoute`). Never use monolithic `switch (request.method)` handlers under `ALL`. Explicit exports enable Astro to automatically handle `HEAD` requests and return clean 405 Method Not Allowed responses.
- **Zero-JS Outer Shell & Deferred Island Hydration**: Comparison matrix pages, tool detail routes, and AI workspace directories must keep all surrounding chrome, headers, breadcrumbs, and explanatory prose as zero-JS static HTML. Heavy React islands (`MatrixPage`, `SerpPreviewWidget`) must use `client:visible` or `client:idle`, never blocking initial paint with `client:load`.
- **Slots Over Render Props in Tool Shells**: Static table headers, matrix footnotes, and feature callouts must be passed into tool containers via native Astro `<slot>`, not function render callbacks (`renderHeader={(col) => ...}`) which fail serialization.
- **Client Scripts Over UI Frameworks**: Lightweight interactive tools (e.g. quick snippet copy, tab switching, simple inputs) should use native Web Components (`HTMLElement`) and bundled `<script>` instead of pulling heavy React state libraries.
- **Static-First With getStaticPaths Props**: Dynamic matrix pages (`/compare/[slug].astro` and `/tr/karsilastir/[slug].astro`) compile statically at build time using `getStaticPaths()`. `getStaticPaths()` must pass the comparison data matrix directly via `props: { matrixData }`, eliminating runtime or per-page re-computation.
- **Script Safety & Inline JSON Data**: Any inline `<script type="application/json">` providing client island bootstrapping data must explicitly carry `is:inline` and an explicit closing `</script>` tag.
- **Dynamic Param Decoding**: Dynamic tool and comparison slugs in `Astro.params` are raw strings. Decode them with `decodeURI(slug)`.
- **Pure HTML Templates (No Virtual DOM)**: Prohibit inline `onClick`/`onChange` handlers in tool `.astro` route templates; use Custom Elements or client islands for interactivity.

Critical files to inspect:

- src/pages/compare/[slug].astro and src/pages/tr/karsilastir/[slug].astro
- src/features/tools/components/AiWorkspacesRoute.astro
- src/features/tools/components/ToolDetailRoute.astro
- src/features/tools/components/BookFoundryRoute.astro
- src/features/tools/components/DshNavigatorRoute.astro
- src/features/tools/components/matrix/MatrixPage.tsx
- src/lib/tools/catalog.ts

## 3.2 Mission Objective

Audit all tooling, calculator, and matrix routes for optimal hydration, script safety, route specificity, and data schema integrity.
Outcome: Prove that heavy React matrix islands use client:visible, embedded application/json scripts have is:inline, catalog schemas support the full Locale type, dynamic endpoints enforce explicit prerender boundaries, and static chrome compiles with zero client JavaScript runtime.
Constraints: Read-only audit; verify data schemas and island boundaries.
Autonomy Grant: You own this mission end-to-end. Inspect table rendering engines, memory footprints, and JSON schemas. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Island Hydration Discipline:
   - ❌ Bad Practice: `<MatrixPage client:load />` forcing the browser to download and parse heavy comparison matrix bundles before rendering above-the-fold content.
   - ✅ Best Practice: `<MatrixPage client:visible />` lazy-hydrating the island only when it enters the viewport.
2. Slots over Render Props Audit:
   - ❌ Bad Practice: `<MatrixPage renderHeader={(col) => <th>{col}</th>} />` failing across the serialization boundary.
   - ✅ Best Practice: Passing static headers via `<slot name="header" />` or serializable configuration objects via props.
3. Script Safety & Inline Data:
   - ❌ Bad Practice: `<script type="application/json">` without `is:inline` triggering compiler warnings or broken bundling.
   - ✅ Best Practice: `<script type="application/json" is:inline>` with matching closing `</script>`.
4. getStaticPaths Contract Audit:
   - ❌ Bad Practice: Re-generating or re-fetching comparison matrices inside page frontmatter for each slug.
   - ✅ Best Practice: Computing comparison matrix in `getStaticPaths()` and passing `props: { matrixData }`.
5. Route Specificity & Priority Collision Audit:
   - ❌ Bad Practice: Accidental route collisions between `[slug].astro` and static subpages without respecting Astro's priority matrix (e.g. generating `compare/index` inside `[slug].astro` or shadowing `/compare/categories.astro`).
   - ✅ Best Practice: Explicit path separation or priority resolution order where static routes (`compare/index.astro`) take precedence over dynamic parameters, and params are decoded cleanly with `decodeURI(slug)`.
6. Pagination Contract Audit:
   - ❌ Bad Practice: Rolling custom pagination logic with manual URL query math (`slice((page - 1) * limit, ...)`) instead of Astro's native `paginate()`.
   - ✅ Best Practice: Leveraging native `return paginate(matrixList, { pageSize: 20 })` to obtain typed `Page<T>` with `url.prev` and `url.next`.
7. Dynamic Calculation Endpoints & SSR Boundaries:
   - ❌ Bad Practice: Expecting SSR dynamic behavior on calculation endpoints without `export const prerender = false` (executes once at CI build time and becomes static JSON).
   - ✅ Best Practice: Explicit `export const prerender = false` on dynamic API calculation routes, returning standard `Response.json(...)` typed with `APIRoute`.

### ❌ Bad Practice / Anti-Pattern: Route Collisions & Bloated Handlers

```astro
---
// src/pages/compare/[slug].astro
// Anti-Pattern: Collides with static subpages and uses manual chunking math
export async function getStaticPaths() {
  const tools = await fetchAllTools();
  // Reinventing pagination with manual slicing and query parameters:
  const page1 = tools.slice(0, 10);
  return [
    { params: { slug: "index" }, props: { items: page1 } }, // Shadows compare/index.astro!
    { params: { slug: "semrush-vs-ahrefs" }, props: { items: tools } }
  ];
}
---
<!-- Eagerly loading heavy comparison table island -->
<MatrixPage client:load items={Astro.props.items} />
```

### ✅ Best Practice / Idiomatic: Deterministic Priority & Native paginate()

```astro
---
// src/pages/compare/[slug].astro
// Reference: ../../best-practices/03-routing-and-pages/03-route-priority-and-collision-resolution.md
// Reference: ../../best-practices/03-routing-and-pages/06-built-in-pagination-and-nested-pagination.md
import type { GetStaticPaths } from "astro";
import { getComparisonMatrices } from "@/features/tools/catalog";

export const getStaticPaths = (async () => {
  const matrices = await getComparisonMatrices();
  return matrices.map(matrix => ({
    params: { slug: matrix.slug },
    props: { matrixData: matrix } // Inject pre-computed data directly into props
  }));
}) satisfies GetStaticPaths;

const { slug } = Astro.params;
const decodedSlug = decodeURI(slug);
const { matrixData } = Astro.props;
---
<main>
  <!-- Zero-JS outer shell with viewport-deferred hydration -->
  <header><h1>{matrixData.title}</h1></header>
  <MatrixPage client:visible matrix={matrixData} />
</main>
```

### ❌ Bad Practice / Anti-Pattern: Missing SSR Prerender Boundary on Calculator Endpoint

```ts
// src/pages/api/tools/calculate.ts
// Anti-Pattern: Missing prerender = false in a static Astro project.
// This endpoint executes ONCE at build time and freezes as a static file, rejecting live requests!
import type { APIRoute } from 'astro'

export const POST: APIRoute = async ({ request }) => {
  const data = await request.json()
  return new Response(JSON.stringify({ result: data.x * 2 }))
}
```

### ✅ Best Practice / Idiomatic: Explicit Prerender Boundary & Web Standards

```ts
// src/pages/api/tools/calculate.ts
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
  const calculated = computeToolMetrics(payload)

  return Response.json(
    { success: true, data: calculated },
    {
      status: 200,
      headers: { 'Cache-Control': 'private, no-cache, no-store' },
    },
  )
}
```

8. Inspect BookFoundryRoute.astro: line 94 application/json script must have is:inline and paired </script>.
9. Inspect DshNavigatorRoute.astro: line 201 application/json script must have is:inline and paired </script>.
10. Inspect ToolDetailRoute.astro lines 215-230: verify widget conditional mounts (SerpPreviewWidget, SeoSheetsWidget, SeoQuizWidget).
11. Dynamic Route Decoding: Ensure comparison slugs are decoded with `decodeURI(slug)`.

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/01-templates-routing/07-interactive-tools-calculators-matrices/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Rule ID Mapping**: Every defect recorded in `findings.json` must explicitly map to an authoritative Astro best practice rule identifier using the `rule_id` field (e.g. `RULE-ID: 03-routing-and-pages/03-route-priority-and-collision-resolution`, `RULE-ID: 03-routing-and-pages/06-built-in-pagination-and-nested-pagination`, `RULE-ID: 03-routing-and-pages/07-ssr-on-demand-routes-vs-prerendering`, `RULE-ID: 05-data-fetching-and-endpoints/02-prerender-boundary-dynamic-endpoints`, `RULE-ID: 05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response`, `RULE-ID: 05-data-fetching-and-endpoints/06-http-method-handlers-and-method-guards`).

You must create and populate the following deliverables in `docs/audits/results/01-templates-routing/07-interactive-tools-calculators-matrices/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps. Every item MUST include a valid `rule_id` linking to `../../best-practices/`:

```json
[
  {
    "id": "07-INTERACTIVE-TOOLS-CALCULATORS-MATRICES-001",
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
  --body "docs/audits/results/01-templates-routing/07-interactive-tools-calculators-matrices/issue-body.md" \
  --title "[Audit - Interactive Tools, Calculators & Comparison Matrices Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/01-templates-routing/07-interactive-tools-calculators-matrices/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Run `git grep -n "client:load" src/features/tools/ src/pages/compare/` to verify zero eager hydration on comparison matrix pages.
2. Run `git grep -n "client:visible" src/features/tools/ src/pages/compare/` to confirm lazy hydration is enforced.
3. Run `git grep -n "<script type=\"application/json\"" src/features/tools/` to verify all inline JSON scripts carry `is:inline` and explicit `</script>`.
4. Run `git grep -n "onClick=\|onChange=" src/features/tools/` to ensure no illegal JSX event handlers in `.astro` templates.
5. Run `git grep -n "prerender = false" src/pages/` to audit all on-demand SSR routes and dynamic calculator endpoints.
6. Run `git grep -n "paginate(" src/pages/` to verify native Astro pagination usage in tool directories.
7. Run `git grep -n "export const POST\|export const GET" src/pages/api/` to audit dynamic endpoint method handlers.
8. Verify `getStaticPaths` in `src/pages/compare/[slug].astro` injects pre-computed matrix data via `props`.
9. Verify that `pnpm typecheck` passes cleanly on `src/lib/tools/catalog.ts`.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/01-templates-routing/07-interactive-tools-calculators-matrices/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Interactive Tools, Calculators & Comparison Matrices Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/01-templates-routing/07-interactive-tools-calculators-matrices/findings.json` (N defects logged)
   - `file://docs/audits/results/01-templates-routing/07-interactive-tools-calculators-matrices/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/01-templates-routing/07-interactive-tools-calculators-matrices/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/01-templates-routing/07-interactive-tools-calculators-matrices/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/01-templates-routing/07-interactive-tools-calculators-matrices/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
