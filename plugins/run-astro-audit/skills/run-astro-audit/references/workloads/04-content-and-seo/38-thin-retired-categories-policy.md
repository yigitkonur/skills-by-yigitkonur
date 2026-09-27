# Mission Brief: Thin & Retired Categories Redirect Policy Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

To maintain high search quality and crawl efficiency, thin category archives (categories with fewer than 2 published articles) and retired taxonomy categories are redirected to their parent hubs with HTTP 308 Permanent Redirect or served with explicit HTTP 410 Gone status codes.
These rules are governed by `src/lib/redirects/thin-categories.ts` and `category-references.ts`.

### Authoritative Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`09-custom-404-and-500-error-routing.md`](../../best-practices/03-routing-and-pages/09-custom-404-and-500-error-routing.md) — Custom error routing, HTTP status code fidelity, and handling pruned or non-existent routes without leaking server internals or generating soft 404s (`RULE-ID: 03-routing-and-pages/09-custom-404-and-500-error-routing`).
- [`04-define-type-safe-schemas-with-zod.md`](../../best-practices/04-content-layer-and-collections/04-define-type-safe-schemas-with-zod.md) — Type-safe frontmatter schema definitions, taxonomy validation, and JSON-LD modeling (`RULE-ID: 04-content-layer-and-collections/04-define-type-safe-schemas-with-zod`).
- [`11-filter-queries-with-sqlite-query-store.md`](../../best-practices/04-content-layer-and-collections/11-filter-queries-with-sqlite-query-store.md) — High-speed SQLite querying, filtering out draft and thin entries upstream in `getCollection()` (`RULE-ID: 04-content-layer-and-collections/11-filter-queries-with-sqlite-query-store`).
- [`12-ui-translation-dictionaries-and-type-safety.md`](../../best-practices/08-i18n-and-localization/12-ui-translation-dictionaries-and-type-safety.md) — Type-safe translation dictionaries and localized metadata across category hierarchies (`RULE-ID: 08-i18n-and-localization/12-ui-translation-dictionaries-and-type-safety`).
- [`15-content-layer-store-architecture.md`](../../best-practices/01-architecture-and-philosophy/15-content-layer-store-architecture.md) — Content Layer data store architecture isolating taxonomy and content synchronization from page rendering (`RULE-ID: 01-architecture-and-philosophy/15-content-layer-store-architecture`).

Architectural facts and SEO invariants:

- Crawl Budget & Soft-404 Prevention: Emitting empty or near-empty category archive pages (< 2 published articles) dilutes domain authority and triggers soft-404 algorithmic penalties in Google Search Central.
- Permanent Link Equity Transfer: Pruned categories must issue HTTP 308 (Permanent Redirect) preserving link equity to their immediate logical parent hub (e.g. `/tr/blog/kategori/eski-konu` -> `/tr/blog`), or return explicit HTTP 410 Gone if intentionally retired without successor.
- Strict Static Sitemap Filtering: `@astrojs/sitemap` must filter out pruned/thin categories so crawlers are never directed to redirect endpoints via XML sitemaps.
- Multi-Locale Independence: Content counts must be evaluated per-locale; a category active in localized primary locale (5 articles) but empty in English (0 articles) must emit a 308 redirect on English routes while rendering cleanly on localized primary locale routes.
- Directory & Static Generation Alignment: In `src/pages/[...lang]/blog/category/[slug].astro`, `getStaticPaths()` must only return routes for categories satisfying the threshold (`count >= 2`), avoiding build-time emission of empty `index.html` files.

Critical files to inspect:

- `src/lib/redirects/thin-categories.ts`
- `src/lib/routing/category-references.ts`
- `src/content/categories/`
- `src/pages/[locale]/blog/category/[...slug].astro`
- `astro.config.mjs`

## 3.2 Mission Objective

Audit thin category pruning and redirect emission.
Outcome: Ensure no thin category emits an empty 0-item archive page, verify that 308 redirects preserve link equity to parent categories (or emit explicit 410 Gone status for permanently retired nodes), and ensure sitemaps exclude thin categories.
Constraints: Read-only audit; verify category item counts.
Autonomy Grant: You own this mission end-to-end. Count published records per category, verify redirect targets, and inspect sitemaps. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `thinCategoryRemovals()`: check criteria for classification as 'thin' (< 2 items) vs 'retired'.
2. Verify that active categories with 2+ articles are never accidentally suppressed.
3. Inspect `getStaticPaths()` in category archive pages: ensure suppressed categories are excluded from static generation.
4. Check `@astrojs/sitemap` `filter` option: ensure redirected thin category URLs never appear in `sitemap-*.xml`.
5. Validate per-locale content counts: ensure English, localized primary locale, and localized secondary locale category listings are partitioned properly.
6. Contrast naive 200 OK soft-404 emission or redirect loops with authoritative 301/308 redirects and 410 Gone status responses.

### ❌ Bad Practice / Anti-Pattern (Generic Soft-404s, 200 OK Empty Pages, & Redirect Loops)

```typescript
// src/pages/blog/category/[slug].astro - Next.js / naive pattern emitting soft-404s or infinite loops
export async function getStaticPaths() {
  const categories = await getCollection('categories')
  // BAD: Returns every category regardless of article count or retired status
  return categories.map((cat) => ({ params: { slug: cat.slug } }))
}

// In template: if articles.length === 0, renders 200 OK with "Henüz içerik bulunamadı" (Soft-404)
// Or in edge redirect table: redirecting /blog/category/seo -> /blog/category/seo/ (Trailing slash loop)
// Or redirecting retired category to itself or intermediate dead-end hops:
// /blog/category/old-topic -> /blog/category/legacy-topic -> /blog/category/old-topic (Infinite loop)
```

_Why this fails:_ Emitting 200 OK pages with "no content" triggers Google Search Console soft-404 algorithmic demotions, wasting crawl budget. Leaving retired URLs unmanaged or caught in redirect loops causes crawler abandonment and drops index equity.

### ✅ Best Practice / Idiomatic (Explicit 410 Gone or Authoritative 301/308 Single-Hop Redirects)

```typescript
// src/pages/blog/category/[slug].astro - Strict threshold filtering via Content Layer
import { getCollection } from 'astro:content'

export async function getStaticPaths() {
  // Query content store and evaluate published count per locale
  const allArticles = await getCollection('articles', ({ data }) => !data.draft)
  const categories = await getCollection('categories')

  return categories
    .filter((cat) => {
      const publishedCount = allArticles.filter((a) => a.data.category === cat.id).length
      return publishedCount >= 2 // Strict threshold: Only emit archive pages with >= 2 published articles
    })
    .map((cat) => ({ params: { slug: cat.slug } }))
}

// src/lib/redirects/thin-categories.ts & src/worker.ts - Authoritative 410 Gone or 301/308 single hop
export function handlePrunedCategory(
  requestUrl: URL,
  categorySlug: string,
  isPermanentlyDeleted: boolean,
): Response {
  if (isPermanentlyDeleted) {
    // Explicit 410 Gone: Informs search engines the resource is intentionally and permanently deleted
    return new Response('410 Gone - This taxonomy category has been permanently retired.', {
      status: 410,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'public, max-age=604800',
      },
    })
  }

  // Authoritative 301 / 308 Permanent Redirect directly to closest parent hub in exactly 1 hop
  const parentHub = `/tr/blog`
  return Response.redirect(new URL(parentHub, requestUrl.origin), 308)
}
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/04-content-and-seo/38-thin-retired-categories-policy/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: 03-routing-and-pages/09-custom-404-and-500-error-routing`, `RULE-ID: 04-content-layer-and-collections/11-filter-queries-with-sqlite-query-store`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/04-content-and-seo/38-thin-retired-categories-policy/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "38-THIN-RETIRED-CATEGORIES-POLICY-001",
    "rule_id": "RULE-ID: 03-routing-and-pages/09-custom-404-and-500-error-routing",
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
   Execute the turnkey publisher script `scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting (<= 200 items, max 3 levels deep), creates the primary issue, spawns linked sub-issues (capped at 20) for critical and high severity defects, and commits/pushes results directly to `main` without PR:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/04-content-and-seo/38-thin-retired-categories-policy/issue-body.md" \
  --title "[Audit - Thin & Retired Categories Redirect Policy Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/04-content-and-seo/38-thin-retired-categories-policy/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Scan for thin category references and redirect declarations across the codebase:
   ```bash
   git grep -n "thinCategories" src/
   git grep -n "308" src/lib/redirects/
   ```
2. Confirm that all thin categories return HTTP 308 to their parent hub in edge policy tests:
   ```bash
   pnpm vitest run src/lib/redirects/thin-categories.test.ts tests/int/category-references.test.ts
   ```
3. Verify zero empty category listing pages emitted in build output:
   ```bash
   find dist/ -path "*/blog/category/*" -name "index.html" -exec grep -l "0 içerik" {} + || echo "PASS: No empty category archives"
   ```
4. Verify sitemap excludes thin and retired categories:
   ```bash
   grep -E "blog/category/(retired|thin)" dist/sitemap-*.xml || echo "PASS: No thin categories in sitemap"
   ```
5. Verify edge redirects return HTTP 308 or explicit 410 Gone with curl:
   ```bash
   curl -sI http://localhost:4321/blog/category/retired-category | grep -E "(308 Permanent|410 Gone|location:)"
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/04-content-and-seo/38-thin-retired-categories-policy/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Thin & Retired Categories Redirect Policy Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/04-content-and-seo/38-thin-retired-categories-policy/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/04-content-and-seo/38-thin-retired-categories-policy/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/04-content-and-seo/38-thin-retired-categories-policy/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/04-content-and-seo/38-thin-retired-categories-policy/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/04-content-and-seo/38-thin-retired-categories-policy/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
