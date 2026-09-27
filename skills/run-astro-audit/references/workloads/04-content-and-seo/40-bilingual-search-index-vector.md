# Mission Brief: Bilingual Search Index & Vector Embedding Hygiene Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

Site search runs as a client island (`SiteSearch.astro`, `SearchRoute.astro`) backed by a static search index (`search-index/[locale].json`) generated at build time.
Additionally, `workers/ai` provides vector embeddings for semantic search.

### Authoritative Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`11-filter-queries-with-sqlite-query-store.md`](../../best-practices/04-content-layer-and-collections/11-filter-queries-with-sqlite-query-store.md) — High-speed SQLite querying for search indexing, filtering drafts, and projecting compact search records (`RULE-ID: 04-content-layer-and-collections/11-filter-queries-with-sqlite-query-store`).
- [`12-ui-translation-dictionaries-and-type-safety.md`](../../best-practices/08-i18n-and-localization/12-ui-translation-dictionaries-and-type-safety.md) — Type-safe translation dictionaries and search interface localization (`RULE-ID: 08-i18n-and-localization/12-ui-translation-dictionaries-and-type-safety`).
- [`15-content-layer-store-architecture.md`](../../best-practices/01-architecture-and-philosophy/15-content-layer-store-architecture.md) — Content Layer data store architecture for build-time static index generation isolating data fetching from client bundles (`RULE-ID: 01-architecture-and-philosophy/15-content-layer-store-architecture`).
- [`04-define-type-safe-schemas-with-zod.md`](../../best-practices/04-content-layer-and-collections/04-define-type-safe-schemas-with-zod.md) — Type-safe frontmatter schema definitions ensuring clean search metadata (`RULE-ID: 04-content-layer-and-collections/04-define-type-safe-schemas-with-zod`).
- [`09-custom-404-and-500-error-routing.md`](../../best-practices/03-routing-and-pages/09-custom-404-and-500-error-routing.md) — Custom error routing and graceful search degradation when edge workers or queries fail (`RULE-ID: 03-routing-and-pages/09-custom-404-and-500-error-routing`).

Architectural invariants and performance contracts:

- Static Search Index Payload Budget: Static search index files (`search-index/[locale].json`) must remain strictly under 500 KB uncompressed per locale. Full article markdown/HTML bodies and AST nodes must be stripped out; only `{ title, slug, excerpt, tags, category }` are permitted.
- Zero-Eager Hydration Mandate: The search island (`SiteSearch.astro` / `SearchRoute.astro`) must never use `client:load` because it introduces unnecessary JavaScript execution to the critical rendering path. It must use `client:idle` or hydrate on demand upon keyboard trigger (Cmd+K / Ctrl+K) or search button interaction.
- Locale-Specific Character Folding & Stemming: localized primary locale linguistic folding differs fundamentally from standard ASCII lowercasing (localized primary locale dotted `İ`/`i` vs dotless `I`/`ı`). Standard `.toLowerCase()` erroneously turns `İ` into `i\u0307` or `I` into `i`. Search normalization must use localized primary locale-aware collation and case-folding.
- Workers AI / Vectorize Semantic Search Boundary: For semantic search queries handled by `workers/ai`, vector embeddings must be generated against normalized summary chunks, completely isolated from client browser bundles and operating within Cloudflare Workers edge execution limits.

Critical files to inspect:

- `src/features/search/`
- `src/lib/search/`
- `src/pages/search/[...rest].astro`
- `scripts/release/search/`
- `workers/ai/`

## 3.2 Mission Objective

Audit the search index generation pipeline and client search island.
Outcome: Ensure the static search index is compressed, strips HTML tags, supports localized primary locale and English stemming/folding, and loads lazily when the search modal is triggered.
Constraints: Read-only audit; verify search index generators.
Autonomy Grant: You own this mission end-to-end. Benchmark index size, search query latency, and character folding. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect search index builder: verify what fields are indexed (title, excerpt, tags) and confirm full article bodies are excluded to prevent payload bloat.
2. Test localized primary locale character folding (e.g. searching "dijital" matches "Dijital", "ı" matches "i", "ş" matches "s").
3. Ensure SiteSearch island uses `client:idle` or hydrates only when the search shortcut (Ctrl+K / Cmd+K) is pressed.
4. Benchmark search query execution latency: verify in-memory fuzzy/prefix lookups execute in <10ms.
5. Audit `workers/ai` embeddings pipeline: confirm vector embeddings do not leak raw server environment secrets or bloat edge memory.
6. Contrast heavy in-memory client search bundling (>5MB) with static precomputed search vectors and lightweight micro-islands.

### ❌ Bad Practice / Anti-Pattern (Heavy In-Memory Client Bundling >5MB & Eager Hydration)

```astro
---
// src/layouts/Header.astro - Anti-pattern: Bundling heavy in-memory search indexes (>5MB) & eager hydration
import SearchModal from "@/features/search/SearchModal.tsx";
// BAD: Importing entire 5MB+ content index into client JavaScript bundle!
import searchIndexData from "@/data/heavy-uncompressed-search-index.json";
---
<!-- BAD: client:load blocks critical rendering path; executes immediately on page load -->
<SearchModal client:load rawIndex={searchIndexData} />

<script>
// Naive lowercasing breaking localized primary locale dotted/dotless I characters
function naiveSearch(query, items) {
  // BUG: "DİJİTAL".toLowerCase() turns into "di̇jital" with combining dot, failing match with "dijital"
  const q = query.toLowerCase();
  return items.filter(item => item.title.toLowerCase().includes(q));
}
</script>
```

_Why this fails:_ Shipping massive JSON data (>5MB) inside the client JS bundle destroys mobile memory and Core Web Vitals (TBT/INP). Eager `client:load` forces immediate browser hydration on every pageview, even when 95% of users never open search. Naive `toLowerCase()` corrupts localized primary locale collation (`İ`/`i` vs `I`/`ı`).

### ✅ Best Practice / Idiomatic (Static Precomputed Search Vectors & Lazy Micro-Island Hydration)

```astro
---
// src/layouts/Header.astro - Static precomputed search vectors & lazy micro-island hydration
import SearchTrigger from "@/components/search/SearchTrigger.astro";
---
<!-- Zero-JS server-rendered trigger button: no React runtime loaded on initial pageview -->
<SearchTrigger />

<!-- Lazy micro-island: hydrates only when user triggers search shortcut (Cmd+K) or clicks trigger -->
<div id="search-modal-container" data-loaded="false"></div>

<script>
// Lightweight interaction handler loading search micro-island dynamically on demand
const container = document.getElementById("search-modal-container");
async function openSearch() {
  if (container && container.dataset.loaded === "false") {
    container.dataset.loaded = "true";
    // Dynamically import micro-island only when needed (<30 KB chunk)
    const { mountSearchIsland } = await import("@/features/search/mount-search");
    // Queries static precomputed index (<500 KB per locale) or edge workers/ai vector endpoint
    mountSearchIsland(container);
  }
}

window.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "k") {
    e.preventDefault();
    openSearch();
  }
});
</script>
```

```typescript
// scripts/release/search/build-static-index.mjs - Build-time precomputed search vector generator
import { getCollection } from 'astro:content'

export async function generateSearchPayload(locale: 'tr' | 'en') {
  // Query content store via Astro Content Layer: strip heavy Markdown/HTML bodies
  const articles = await getCollection(
    'articles',
    ({ data }) => !data.draft && data.lang === locale,
  )

  return articles.map((article) => ({
    id: article.id,
    title: article.data.title,
    slug: article.data.slug,
    // Truncate excerpt and strip all HTML/Markdown tags; budget < 500 KB total
    excerpt: article.data.description?.slice(0, 160).replace(/<[^>]*>?/gm, '') || '',
    category: article.data.category,
    tags: article.data.tags || [],
  }))
}
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/04-content-and-seo/40-bilingual-search-index-vector/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: 04-content-layer-and-collections/11-filter-queries-with-sqlite-query-store`, `RULE-ID: 08-i18n-and-localization/12-ui-translation-dictionaries-and-type-safety`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/04-content-and-seo/40-bilingual-search-index-vector/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "40-BILINGUAL-SEARCH-INDEX-VECTOR-001",
    "rule_id": "RULE-ID: 04-content-layer-and-collections/11-filter-queries-with-sqlite-query-store",
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
  --body "docs/audits/results/04-content-and-seo/40-bilingual-search-index-vector/issue-body.md" \
  --title "[Audit - Bilingual Search Index & Vector Embedding Hygiene Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/04-content-and-seo/40-bilingual-search-index-vector/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Verify static search index file sizes are strictly under 500 KB per locale:
   ```bash
   ls -lh dist/search-index/*.json 2>/dev/null || ls -lh public/search-index/*.json
   ```
2. Run unit tests for localized primary locale character folding and query normalization:
   ```bash
   pnpm vitest run tests/unit/search-folding.test.ts
   ```
3. Audit templates to confirm search island uses `client:idle` or deferred hydration:
   ```bash
   grep -rn 'SearchModal' src/ | grep -E 'client:(load|idle)'
   ```
4. Verify search index contains zero raw HTML tags in excerpt fields:
   ```bash
   node -e "const fs = require('fs'); const file = 'public/search-index/tr.json'; if (fs.existsSync(file)) { const idx = JSON.parse(fs.readFileSync(file)); const hasHtml = idx.some(item => /<[a-z][\s\S]*>/i.test(item.excerpt || '')); console.log('HTML detected:', hasHtml); } else { console.log('Index file not yet built'); }"
   ```
5. Audit edge semantic search vector embedding pipeline in `workers/ai`:
   ```bash
   git grep -n "Vectorize" workers/ai/
   ```
6. Confirm sub-10ms search query response times in client search benchmark tests.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/04-content-and-seo/40-bilingual-search-index-vector/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Bilingual Search Index & Vector Embedding Hygiene Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/04-content-and-seo/40-bilingual-search-index-vector/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/04-content-and-seo/40-bilingual-search-index-vector/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/04-content-and-seo/40-bilingual-search-index-vector/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/04-content-and-seo/40-bilingual-search-index-vector/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/04-content-and-seo/40-bilingual-search-index-vector/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
