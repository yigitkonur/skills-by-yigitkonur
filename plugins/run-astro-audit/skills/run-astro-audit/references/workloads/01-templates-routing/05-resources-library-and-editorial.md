# Mission Brief: Resources Library & Long-Form Editorial Route Audit

## 3.0 Skills / Tools: view_file, run_command, astro-component-architect.

## 3.1 Context Block

The project's editorial engine serves hundreds of in-depth articles, strategic guides, e-books, webinars, and podcast episodes.
Route controllers include `ArticleDetailRoute.astro`, `BookDetailPage.astro`, `VideoDetailPage.astro`, and `CategoryListingPage.astro`.
Astro 7's Sätteri engine parses Markdown/MDX bodies into HAST/HTML. The templates wrap these bodies with reading time estimates, table of contents, author biographies, and social share anchors.

### Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`04-getstaticpaths-contract-params-vs-props.md`](../../best-practices/03-routing-and-pages/04-getstaticpaths-contract-params-vs-props.md) — Passing pre-computed props vs refetching inside components (`RULE-ID: ASTRO-ROUTING-04`).
- [`05-large-build-memory-optimization-in-getstaticpaths.md`](../../best-practices/03-routing-and-pages/05-large-build-memory-optimization-in-getstaticpaths.md) — Avoiding massive memory retention in `getStaticPaths` across thousands of pages (`RULE-ID: ASTRO-ROUTING-05`).
- [`01-content-layer-architecture-v5.md`](../../best-practices/04-content-layer-and-collections/01-content-layer-architecture-v5.md) — Astro 5 Content Layer store and collection definitions (`RULE-ID: ASTRO-CONTENT-01`).
- [`02-sqlite-backed-content-store.md`](../../best-practices/04-content-layer-and-collections/02-sqlite-backed-content-store.md) — High-speed SQLite-backed cache vs repetitive disk reads (`RULE-ID: ASTRO-CONTENT-02`).
- [`03-custom-loaders-over-filesystem.md`](../../best-practices/04-content-layer-and-collections/03-custom-loaders-over-filesystem.md) — Using custom loaders for API/CMS integration (`RULE-ID: ASTRO-CONTENT-06`).
- [`11-filter-queries-with-sqlite-query-store.md`](../../best-practices/04-content-layer-and-collections/11-filter-queries-with-sqlite-query-store.md) — Efficient filtering of references and case studies (`RULE-ID: ASTRO-CONTENT-10`).

Invariants:

- **Zero-JS Editorial Reading Experience**: Long-form editorial article pages (`ArticleDetailPage.astro`, `BookDetailPage.astro`, `VideoDetailPage.astro`, `ResourcesHubPage.astro`) must compile to static HTML with 0 KB client JavaScript. Prose reading should never block on framework runtimes.
- **getStaticPaths Memory & Query Hygiene**: Across hundreds of articles and guides, `getStaticPaths()` must return lightweight route keys (`params: { slug }`) or targeted metadata props (`props: { id }`), avoiding retaining thousands of rich markdown ASTs simultaneously in heap memory.
- **Catch-All Rest Parameters**: Resource category and listing routes using `[...slug].astro` must return `{ params: { slug: undefined } }` in `getStaticPaths()` to match the root `/resources` overview route without 404s. Never return empty string `""` or `"/"`.
- **Dynamic Route Param Decoding**: URL segments such as tags or category filters in `Astro.params` are raw strings. Decode them explicitly with `decodeURI(Astro.params.tag)` to handle special characters.
- **Client Scripts Over UI Frameworks**: Social share popups, reading progress bars, and table-of-contents observers should use native Custom Elements (`HTMLElement`) and bundled `<script>`, shipping 0 KB React runtime.
- **Scoped Style Encapsulation**: Prose typography and syntax highlighting must use scoped `<style>` or well-bounded `.prose` classes, avoiding `<style is:global>` leaks into headers, navigation, or footer elements.

Critical files to inspect:

- src/features/resources/components/ArticleDetailPage.astro
- src/features/resources/components/BookDetailPage.astro
- src/features/resources/components/VideoDetailPage.astro
- src/features/resources/components/ResourcesHubPage.astro
- src/features/resources/articles/data/data.ts
- src/features/resources/data/data.ts
- src/pages/resources/
- src/pages/blog/

## 3.2 Mission Objective

Audit all Resources and Editorial route templates for Astro 7 compiler compliance and performance.
Outcome: Ensure zero unescaped characters in editorial layouts, verify that table of contents (TOC) generators skip callout headers, confirm reading time calculations exclude code blocks and raw JSON, verify former team member author attribution links resolve cleanly without 404, audit RSS/Atom XML feed generation (/rss.xml, /tr/rss.xml), and verify zero client runtime bloat on prose routes.
Constraints: Read-only audit; verify data contracts and responsive article typography.
Autonomy Grant: You own this mission end-to-end. Trace article layouts, typography tokens, and resource grids. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Audit `ArticleDetailPage.astro`: inspect article hero image loading, author bio card markup, and structured TechArticle schema.
2. Audit `BookDetailPage.astro`: inspect line 188 where book download form is mounted; verify hydration directive (`client:visible`).
3. Audit `VideoDetailPage.astro`: verify embedded YouTube player uses privacy-enhanced mode (`youtube-nocookie.com`) without layout shift.
4. Verify reading time algorithm: ensure code blocks, tables, and JSON nodes are deducted from prose word count.
5. Audit author slugs: verify that articles authored by former team members resolve to valid team profiles or archive routes rather than 404.
6. Verify that `/rss.xml` and `/tr/rss.xml` emit valid XML with proper CDATA and publication dates.
7. Dynamic Route Decoding: Ensure `decodeURI(Astro.params.tag)` is used in dynamic tag/category routes.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Monolithic Props in getStaticPaths vs Memory Optimization (RULE-ID: ASTRO-ROUTING-05)

##### ❌ Bad Practice / Anti-Pattern: Passing entire monolithic collection arrays as props in `getStaticPaths()`, retaining gigabytes of AST memory during sharded builds

```astro
---
// src/pages/blog/[slug].astro - Leaking full article collection ASTs into memory
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  // Anti-Pattern: Loading hundreds of articles with raw ASTs and rich bodies into props
  const articles = await getCollection('articles');
  return articles.map((article) => ({
    params: { slug: article.id },
    props: { article }, // Keeps all rich article ASTs simultaneously in heap
  }));
}

const { article } = Astro.props;
---
<article>
  <h1>{article.data.title}</h1>
</article>
```

_Why this fails:_ Across hundreds of rich long-form articles, passing full markdown ASTs and body content inside `props` causes Node.js heap consumption to explode, leading to GC thrashing and `ERR_WORKER_OUT_OF_MEMORY` build failures.

##### ✅ Best Practice / Idiomatic: Returning minimal `{ params: { slug: entry.id } }` and fetching lightweight records via `getEntry()` in page frontmatter

```astro
---
// src/pages/blog/[slug].astro - Minimal params with targeted on-demand fetch
import { getCollection, getEntry, render } from 'astro:content';

export async function getStaticPaths() {
  const articles = await getCollection('articles');
  // Idiomatic: Only return lightweight routing identifiers
  return articles.map((article) => ({
    params: { slug: article.id },
  }));
}

const { slug } = Astro.params;
// Resolve the single rich record on-demand; garbage-collected immediately after render
const article = await getEntry('articles', slug!);
if (!article) return Astro.redirect('/404');
const { Content, headings } = await render(article);
---
<article>
  <h1>{article.data.title}</h1>
  <Content />
</article>
```

#### Pattern 2: In-Memory Filtering vs Content Layer Predicates & SQLite Query Store (RULE-ID: ASTRO-CONTENT-10)

##### ❌ Bad Practice / Anti-Pattern: In-memory JavaScript `.filter()` over thousands of entries inside UI components

```astro
---
// src/components/resources/CategoryFilter.astro - Wasteful full collection read
import { getCollection } from 'astro:content';

interface Props {
  category: string;
}
const { category } = Astro.props;

// Anti-Pattern: Pulls entire collection into memory and executes client-style array filtering
const allArticles = await getCollection('articles');
const categoryArticles = allArticles.filter((a) => a.data.category === category && !a.data.draft);
---
<div class="articles-grid">
  {categoryArticles.map((a) => <div>{a.data.title}</div>)}
</div>
```

_Why this fails:_ Pulling all entries into component memory and executing post-hoc array filtering bypasses Astro 5's Content Layer query optimizations, wastes CPU cycles, and repeatedly parses untargeted collection items across hundreds of pages.

##### ✅ Best Practice / Idiomatic: Targeted Content Layer queries and SQLite indexing via predicate parameter

```astro
---
// src/components/resources/CategoryFilter.astro - Upstream filtered query
import { getCollection } from 'astro:content';

interface Props {
  category: string;
}
const { category } = Astro.props;

// Idiomatic: Filter upstream at collection query time leveraging SQLite DataStore
const categoryArticles = await getCollection('articles', ({ data }) => {
  return data.category === category && (import.meta.env.PROD ? !data.draft : true);
});
---
<div class="articles-grid">
  {categoryArticles.map((a) => <div>{a.data.title}</div>)}
</div>
```

#### Pattern 3: Catch-All Rest Parameters for Root Overview Routes (RULE-ID: ASTRO-ROUTING-02)

##### ❌ Bad Practice / Anti-Pattern: Returning empty strings or slashes for root overview in `[...slug].astro`

```astro
---
// src/pages/resources/[...slug].astro - Broken root path mapping
export async function getStaticPaths() {
  return [
    // Anti-Pattern: Empty string or slash triggers 404 or routing mismatch in Astro SSG
    { params: { slug: '' } },
    { params: { slug: 'whitepapers' } },
  ];
}
---
```

_Why this fails:_ In Astro rest parameters (`[...slug]`), passing an empty string `""` or `"/"` produces undefined routing behavior or silent 404s.

##### ✅ Best Practice / Idiomatic: Returning `{ params: { slug: undefined } }` to match root path

```astro
---
// src/pages/resources/[...slug].astro - Idiomatic catch-all root resolution
export async function getStaticPaths() {
  return [
    // Idiomatic: params: { slug: undefined } explicitly matches /resources
    { params: { slug: undefined } },
    { params: { slug: 'whitepapers' } },
    { params: { slug: 'guides' } },
  ];
}
---
```

#### Pattern 4: Hydrating React Components for Reading Progress or Share Buttons (RULE-ID: ASTRO-HYDRATION-01)

##### ❌ Bad Practice / Anti-Pattern: Importing a React component with `client:load` for a reading time indicator or share button

```astro
---
// src/features/resources/components/ArticleDetailPage.astro
import ReadingProgress from './ReadingProgress.tsx';
import SocialShare from './SocialShare.tsx';
---
<!-- Anti-Pattern: Hydrating 50KB+ React runtime for trivial DOM scroll and share popups -->
<ReadingProgress client:load />
<SocialShare client:visible url={Astro.url.href} />
```

_Why this fails:_ Reading progress bars and native Web Share API buttons require zero React state management. Hydrating React islands bloats the bundle and wastes main thread execution during critical article reading.

##### ✅ Best Practice / Idiomatic: Native Custom Element `<reading-progress>` or `<share-button>` with bundled `<script>`

```astro
---
// src/features/resources/components/ArticleDetailPage.astro
---
<!-- Idiomatic: Zero-JS runtime using lightweight native custom element -->
<reading-progress class="fixed top-0 left-0 h-1 bg-accent z-50 transition-all"></reading-progress>

<script>
  class ReadingProgress extends HTMLElement {
    connectedCallback() {
      const update = () => {
        const scrolled = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
        this.style.width = `${Math.min(100, Math.max(0, scrolled))}%`;
      };
      window.addEventListener('scroll', update, { passive: true });
    }
  }
  customElements.define('reading-progress', ReadingProgress);
</script>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/01-templates-routing/05-resources-library-and-editorial/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an authoritative Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: ASTRO-ROUTING-04`, `RULE-ID: ASTRO-ROUTING-05`, `RULE-ID: ASTRO-CONTENT-01`, `RULE-ID: ASTRO-CONTENT-02`, `RULE-ID: ASTRO-CONTENT-10`).
   - Findings lacking an explicit `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/01-templates-routing/05-resources-library-and-editorial/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "05-RESOURCES-LIBRARY-AND-EDITORIAL-001",
    "rule_id": "RULE-ID: ASTRO-ROUTING-05 (Optimize Memory in getStaticPaths for High-Scale Static Builds)",
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
   Execute the turnkey publisher script using `node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting, creates the primary issue, spawns linked sub-issues (up to 20) for critical/high defects, and pushes the JSON deliverables to `origin main`:

```bash
# Turnkey Script (node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/01-templates-routing/05-resources-library-and-editorial/issue-body.md" \
  --title "[Audit - Resources Library & Long-Form Editorial Route Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/01-templates-routing/05-resources-library-and-editorial/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification commands to validate audit findings across resources and editorial routes:

1. Scan for collection queries and static path contracts:
   ```bash
   git grep -n "getCollection(" src/pages/
   git grep -n "getStaticPaths" src/pages/
   ```
2. Profile memory usage during large content builds with Node memory flags:
   ```bash
   NODE_OPTIONS="--max-old-space-size=4096" pnpm astro build
   ```
3. Run `git grep -n "client:load\|client:idle" src/features/resources/` to verify zero unnecessary hydration in editorial templates.
4. Run `git grep -n "<style is:global>" src/features/resources/` to detect global typography or layout leaks.
5. Run `git grep -n "onClick=\|onChange=" src/features/resources/` to ensure no illegal JSX event handlers in `.astro` files.
6. Verify `getStaticPaths` in resource routes uses minimal params or pre-resolved props to eliminate redundant collection scans.
7. Check that article headings follow strict sentence case conventions.
8. Check that BookDetailPage does not import client-prohibited assets.
9. Verify `/rss.xml` and `/tr/rss.xml` emit valid XML with proper CDATA and publication dates.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/01-templates-routing/05-resources-library-and-editorial/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Resources Library & Long-Form Editorial Route Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/01-templates-routing/05-resources-library-and-editorial/findings.json` (N defects logged with RULE-ID mapping)
   - `file://docs/audits/results/01-templates-routing/05-resources-library-and-editorial/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/01-templates-routing/05-resources-library-and-editorial/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/01-templates-routing/05-resources-library-and-editorial/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/01-templates-routing/05-resources-library-and-editorial/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
