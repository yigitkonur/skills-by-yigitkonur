# Mission Brief: Glossaries, Algorithmic Updates & Checklists Audit

## 3.0 Skills / Tools: view_file, run_command, astro-component-architect.

## 3.1 Context Block

The application hosts comprehensive digital marketing and AI glossaries (thousands of terms) and the Google Algorithmic Updates tracker.
Routes: `GlossaryTermRoute.astro`, `ChecklistPage.astro` (SEO & GEO Checklists), and `AlgorithmUpdatesRoute.astro`.
These pages feature heavy cross-linking, alphabet letter pagination, category filtering, and structured DefinedTerm schema.

Astro Architectural & Best Practice Rules:

- **Route Specificity & Collision Resolution ([03-route-priority-and-collision-resolution.md](../../best-practices/03-routing-and-pages/03-route-priority-and-collision-resolution.md))**:
  Astro enforces a strict 8-tier route priority matrix. Static directory routes (`glossary/index.astro`, `glossary/seo.astro`) take precedence over dynamic term parameters (`glossary/[slug].astro`). Parameterized letter routes (`glossary/[letter]/[page].astro`) must never collide with or shadow category indices.
- **Built-in Pagination & Navigation Metadata ([06-built-in-pagination-and-nested-pagination.md](../../best-practices/03-routing-and-pages/06-built-in-pagination-and-nested-pagination.md))**:
  Glossary letter indexes and algorithmic update history must use Astro's native `paginate()` helper with typed `Page<T>` contracts rather than rolling manual array chunking (`slice((page-1)*limit, ...)`). For nested pagination across alphabet letters (`/glossary/[letter]/[page]`), flatMap across letters and pass `{ params: { letter }, pageSize }` into `paginate()` to preserve contextual navigation (`url.prev`, `url.next`).
- **SSR On-Demand vs Static Prerendering ([07-ssr-on-demand-routes-vs-prerendering.md](../../best-practices/03-routing-and-pages/07-ssr-on-demand-routes-vs-prerendering.md))**:
  Astro 5 unifies output modes under `output: 'static'`. Static term pages pre-render to HTML, while any real-time search queries or interactive live glossary lookups must explicitly declare `export const prerender = false` and resolve parameters via `Astro.params` without exporting `getStaticPaths()`.
- **Prerender Boundary for Dynamic Endpoints ([02-prerender-boundary-dynamic-endpoints.md](../../best-practices/05-data-fetching-and-endpoints/02-prerender-boundary-dynamic-endpoints.md))**:
  Dynamic search, term suggestion, or checklist state sync endpoints (e.g. `/api/glossary/search.json.ts`) must explicitly declare `export const prerender = false;`. Without this flag, endpoints execute once at build time and reject incoming HTTP POST/GET queries in production.
- **APIRoute Signature & Standard Web Response ([03-apiroute-signature-and-web-response.md](../../best-practices/05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response.md))**:
  All glossary and checklist endpoints must be typed with `APIRoute` from `astro` and return standard Web API `Response` or `Response.json(...)` instances. Returning raw objects or Express-style handlers causes runtime fatal errors.
- **Explicit HTTP Method Handlers & Method Guards ([06-http-method-handlers-and-method-guards.md](../../best-practices/05-data-fetching-and-endpoints/06-http-method-handlers-and-method-guards.md))**:
  Export explicit uppercase method handlers (`export const GET: APIRoute`, `export const POST: APIRoute`). Never use monolithic `switch (request.method)` handlers under `ALL`. Explicit exports ensure automatic `HEAD` handling and clean 405 Method Not Allowed semantics.
- **High-Scale Build Memory Optimization in `getStaticPaths()`**: The project's glossaries and algorithm trackers generate thousands of static pages across 3 locales. In Astro, `getStaticPaths()` retains all returned `props` in Node.js heap memory throughout the entire build. Passing full HTML strings, related terms arrays, and markdown ASTs in `props` causes severe heap exhaustion (`ERR_WORKER_OUT_OF_MEMORY`). Only lightweight identifiers (`{ id, slug }`) must be passed in `props`; individual terms must be loaded and rendered on-demand during page compilation.
- **Hydration Rule**: Static Leaf Checklists over Hydrated Mega-Grids. The SEO and GEO Checklists contain hundreds of items. Wrapping the entire checklist in a React component with `client:load` forces the client to download and parse all item markup as JavaScript. Render items as pure static Astro HTML, scoping hydration to an isolated `client:idle` leaf island for localStorage progress persistence.

Critical files to inspect:

- `src/pages/glossary/` and `src/pages/tr/sozluk/`
- `src/pages/seo-glossary/` and `src/pages/ai-glossary/`
- `src/pages/google-algorithm-updates/`
- `src/features/glossary/components/GlossaryTermRoute.astro`
- `src/features/checklist/components/ChecklistPage.astro`
- `src/features/algorithm-updates/`
- `src/lib/glossary/dictionary-families.test.ts`

## 3.2 Mission Objective

Audit all Lexicon, Glossary, Checklist, and Algorithmic Update routes and API endpoints.
Outcome: Ensure alphabet pagination handles edge cases using Astro's native `paginate()` helper, `getStaticPaths()` memory remains optimized with lightweight props, DefinedTerm schema is valid JSON-LD, autolinking does not collide with headers, route collision priority is preserved, dynamic endpoints enforce prerender boundaries, and checklists render with pure static HTML and `client:idle` leaf hydration.
Constraints: Read-only audit; verify SEO schema and taxonomy mapping.
Autonomy Grant: You own this mission end-to-end. Inspect glossary indices, checklist interactive items, and term data collections. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `ChecklistPage.astro` line 340: verify `client:idle` directive on the interactive checklist island and ensure items render as static HTML.
2. Audit `GlossaryTermRoute.astro`: ensure Definition/Term JSON-LD schemas contain no unescaped strings and `getStaticPaths()` returns only lightweight props.
3. Verify alphabet letter pagination: check that nested `[letter]/[page].astro` uses Astro's native `paginate()` helper with proper params.
4. Verify `src/lib/glossary/dictionary-families.test.ts`: ensure multilingual term registries pass test assertions.
5. Check route collisions: ensure static category routes (`/glossary/seo`, `/glossary/ai`) are not shadowed by `src/pages/glossary/[slug].astro`.
6. Audit dynamic endpoints: check that search and checklist sync endpoints enforce `export const prerender = false`.

### ❌ Bad Practice / Anti-Pattern: Bloated getStaticPaths Props & Route Collisions

```astro
---
// src/pages/glossary/[slug].astro - Bloated props in getStaticPaths & manual pagination
export async function getStaticPaths() {
  const allTerms = await loadAllGlossaryTermsWithFullMarkdown(); // 3,000+ heavy entries
  return allTerms.map(term => ({
    params: { slug: term.slug },
    props: { term } // OOM hazard: 3,000 full term ASTs kept in Node heap!
  }));
}
const { term } = Astro.props;
---
<!-- Bloated checklist mega-island -->
<InteractiveChecklist items={term.checklist} client:load />
```

_Why this fails:_ Passing 3,000+ complete term objects in `getStaticPaths` props exhausts Node heap memory during sharded builds. Using `client:load` on checklists downloads hundreds of kilobytes of unnecessary JavaScript on static content pages.

### ✅ Best Practice / Idiomatic: Native Nested paginate() & Lightweight Props

```astro
---
// src/pages/glossary/[letter]/[page].astro - Native paginate & lightweight props
// Reference: ../../best-practices/03-routing-and-pages/03-route-priority-and-collision-resolution.md
// Reference: ../../best-practices/03-routing-and-pages/06-built-in-pagination-and-nested-pagination.md
import type { GetStaticPaths } from "astro";
import ChecklistCheckbox from "../components/ChecklistCheckbox.tsx";

export const getStaticPaths = (async ({ paginate }) => {
  const alphabet = ["a", "b", "c", /* ... */];
  const allTerms = await getLightweightTermIndex(); // slug & id only

  return alphabet.flatMap(letter => {
    const letterTerms = allTerms.filter(t => t.slug.startsWith(letter));
    return paginate(letterTerms, {
      params: { letter },
      pageSize: 50,
    });
  });
}) satisfies GetStaticPaths;

const { page } = Astro.props;
const { letter } = Astro.params;
---
<nav aria-label="Alphabetical pagination">
  {page.url.prev && <a href={page.url.prev}>Previous</a>}
  <span>Page {page.currentPage} of {page.lastPage}</span>
  {page.url.next && <a href={page.url.next}>Next</a>}
</nav>
<!-- Static HTML with deferred idle leaf island for persistence -->
<ChecklistCheckbox termId={letter} client:idle={{ timeout: 1000 }} />
```

### ❌ Bad Practice / Anti-Pattern: Custom Pagination Math in Glossary Listings

```astro
---
// src/pages/glossary/[page].astro
// Rolling custom pagination logic with manual URL query math instead of Astro's native paginate()
export async function getStaticPaths() {
  const terms = await getLightweightTermIndex();
  const limit = 50;
  const pages = Math.ceil(terms.length / limit);
  return Array.from({ length: pages }, (_, i) => ({
    params: { page: String(i + 1) },
    props: { items: terms.slice(i * limit, (i + 1) * limit) }
  }));
}
---
```

### ✅ Best Practice / Idiomatic: Astro Native paginate() Helper

```astro
---
// src/pages/glossary/[page].astro
// Reference: ../../best-practices/03-routing-and-pages/06-built-in-pagination-and-nested-pagination.md
import type { GetStaticPaths, Page } from "astro";
import { getLightweightTermIndex } from "@/features/glossary/data";

export const getStaticPaths = (async ({ paginate }) => {
  const terms = await getLightweightTermIndex();
  return paginate(terms, { pageSize: 50 });
}) satisfies GetStaticPaths;

interface Props {
  page: Page<TermSummary>;
}
const { page } = Astro.props;
---
<nav aria-label="Glossary Pagination">
  {page.url.prev && <a href={page.url.prev}>Previous</a>}
  <span>Page {page.currentPage} of {page.lastPage}</span>
  {page.url.next && <a href={page.url.next}>Next</a>}
</nav>
```

### ❌ Bad Practice / Anti-Pattern: Missing SSR Prerender Boundary on Search Endpoint

```ts
// src/pages/api/glossary/search.ts
// Missing prerender = false in static Astro project: executes once at build time!
import type { APIRoute } from 'astro'

export const GET: APIRoute = async ({ request }) => {
  const url = new URL(request.url)
  const q = url.searchParams.get('q') ?? ''
  // Fails in production: query params are not evaluated dynamically at runtime!
  return new Response(JSON.stringify({ query: q, results: [] }))
}
```

### ✅ Best Practice / Idiomatic: Explicit prerender = false & Typed APIRoute

```ts
// src/pages/api/glossary/search.ts
// Reference: ../../best-practices/05-data-fetching-and-endpoints/02-prerender-boundary-dynamic-endpoints.md
// Reference: ../../best-practices/05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response.md
// Reference: ../../best-practices/05-data-fetching-and-endpoints/06-http-method-handlers-and-method-guards.md
import type { APIRoute } from 'astro'

export const prerender = false

export const GET: APIRoute = async ({ request }) => {
  const url = new URL(request.url)
  const query = url.searchParams.get('q') ?? ''
  const results = await searchGlossaryTerms(query)

  return Response.json(
    { success: true, count: results.length, results },
    {
      status: 200,
      headers: {
        'Cache-Control': 'public, max-age=60, s-maxage=300, stale-while-revalidate=600',
      },
    },
  )
}
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/01-templates-routing/10-glossaries-algorithmic-updates-checklists/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Rule ID Mapping**: Every defect recorded in `findings.json` must explicitly map to an authoritative Astro best practice rule identifier using the `rule_id` field (e.g. `RULE-ID: 03-routing-and-pages/03-route-priority-and-collision-resolution`, `RULE-ID: 03-routing-and-pages/06-built-in-pagination-and-nested-pagination`, `RULE-ID: 03-routing-and-pages/07-ssr-on-demand-routes-vs-prerendering`, `RULE-ID: 05-data-fetching-and-endpoints/02-prerender-boundary-dynamic-endpoints`, `RULE-ID: 05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response`, `RULE-ID: 05-data-fetching-and-endpoints/06-http-method-handlers-and-method-guards`).

You must create and populate the following deliverables in `docs/audits/results/01-templates-routing/10-glossaries-algorithmic-updates-checklists/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps. Every item MUST include a valid `rule_id` linking to `../../best-practices/`:

```json
[
  {
    "id": "10-GLOSSARIES-ALGORITHMIC-UPDATES-CHECKLISTS-001",
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
  --body "docs/audits/results/01-templates-routing/10-glossaries-algorithmic-updates-checklists/issue-body.md" \
  --title "[Audit - Glossaries, Algorithmic Updates & Checklists Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/01-templates-routing/10-glossaries-algorithmic-updates-checklists/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Run `pnpm vitest run src/lib/glossary/dictionary-families.test.ts` to verify lexicon contracts and term definitions.
2. Run `git grep -n "prerender = false" src/pages/` to audit all on-demand SSR routes and dynamic endpoints.
3. Run `git grep -n "paginate(" src/pages/` to verify native Astro pagination across glossary letter and listing archives.
4. Run `git grep -n "export const POST\|export const GET" src/pages/api/` to audit dynamic endpoint method handlers.
5. Verify zero missing letter anchor jumps in glossary index templates.
6. Profile memory during static site build: `NODE_OPTIONS="--max-old-space-size=4096" pnpm astro build` to confirm memory does not scale linearly with term count.
7. Verify pagination boundary safety: check `dist/glossary/` to confirm `page.url.prev` is null on first page and `page.url.next` is null on last page.
8. Validate DefinedTerm JSON-LD schemas via schema checker or `curl -s http://localhost:4321/glossary/seo | grep -i '"@type": "DefinedTerm"'`.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/01-templates-routing/10-glossaries-algorithmic-updates-checklists/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Glossaries, Algorithmic Updates & Checklists Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/01-templates-routing/10-glossaries-algorithmic-updates-checklists/findings.json` (N defects logged)
   - `file://docs/audits/results/01-templates-routing/10-glossaries-algorithmic-updates-checklists/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/01-templates-routing/10-glossaries-algorithmic-updates-checklists/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/01-templates-routing/10-glossaries-algorithmic-updates-checklists/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/01-templates-routing/10-glossaries-algorithmic-updates-checklists/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
