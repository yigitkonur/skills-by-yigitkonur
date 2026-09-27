# Mission Brief: Content Collection Build-Time Memory Deferral Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

In Astro 5's Content Layer, `glob()` and custom loaders eagerly compile Markdown/MDX entries into HTML during content synchronization (`astro sync`) by default, retaining compiled HTML and full Abstract Syntax Trees (ASTs) in the Content Layer DataStore in memory.
For large, body-rich collections (e.g. hundreds of articles, 199+ updates in `algorithmUpdates`, dictionary entries), storing pre-rendered HTML in memory exhausts Node.js heap space, triggering `JavaScript heap out of memory` (OOM) build crashes on memory-capped CI runners and developer hosts.
Astro best practices establish two non-negotiable memory boundaries:

1. **Loader Memory Optimization:** Set `deferRender: true` and `retainBody: false` on loaders for large collections to defer HTML compilation until individual routes request rendering and drop raw source bodies from RAM.
2. **Template Render Deferral:** Listing, catalog, and archive pages (e.g. `/blog`, `/tr/blog`, `/resources`, `/glossary`) must NEVER invoke `await render(entry)` inside loops or overview components. Listing templates must strictly read metadata from `entry.data` (title, excerpt, pubDate, coverImage). `render(entry)` is strictly deferred to the individual detail route (`[...id].astro`).

### Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`13-defer-markdown-rendering-on-large-collections.md`](../../best-practices/04-content-layer-and-collections/13-defer-markdown-rendering-on-large-collections.md) — Deferring markdown rendering on large collections with `deferRender: true` and `retainBody: false` (`RULE-ID: ASTRO-COLLECT-13`).
- [`04-leverage-builtin-glob-loader.md`](../../best-practices/04-content-layer-and-collections/04-leverage-builtin-glob-loader.md) — Configuring built-in `glob()` loader memory settings and patterns (`RULE-ID: ASTRO-COLLECT-04`).
- [`10-filter-drafts-and-query-collections.md`](../../best-practices/04-content-layer-and-collections/10-filter-drafts-and-query-collections.md) — Lightweight querying and filtering of content collections without pulling rendered AST into memory (`RULE-ID: ASTRO-COLLECT-10`).
- [`05-render-entry-content-via-rendered-object.md`](../../best-practices/04-content-layer-and-collections/05-render-entry-content-via-rendered-object.md) — Rendering entry content via rendered object (`RULE-ID: ASTRO-COLLECT-05`).

Critical files to inspect:

- `src/content.config.ts`
- `src/content/collections/*.ts`
- `src/pages/blog/` and `src/pages/tr/blog/`
- `src/features/resources/` and `src/features/glossary/`
- `src/lib/collection-kit.ts`

## 3.2 Mission Objective

Perform a memory footprint and render deferral audit across all collection loaders and listing templates to ensure `deferRender: true` is configured for large collections and `render(entry)` is strictly deferred to single-entry detail routes.
Outcome: Eliminate build-time memory bloat and guarantee lightweight heap utilization during sharded builds.
Constraints: Read-only audit; do not alter production code.
Autonomy Grant: You own this mission end-to-end. Audit template loops, check memory allocations, and enforce deferral boundaries. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Search for `render(` calls across `src/pages/`, `src/features/`, and `src/components/`.
2. Verify that `render(entry)` is called exclusively in single-entry detail templates and never inside listing, card, or filter components.
3. Check `getStaticPaths` implementations to ensure large collections pass minimal props (`params: { id: entry.id }` or minimal metadata) rather than bulky AST structures.
4. Verify that collection loaders in `src/content/collections/*.ts` use `deferRender: true` and `retainBody: false` for high-volume content collections.
5. Ensure summary text on listing cards is derived from `entry.data.description` or `entry.data.excerpt` rather than rendered HTML.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Eager Compilation & Loop Rendering vs. Deferred Compilation (RULE-ID: ASTRO-COLLECT-13)

##### ❌ Bad Practice / Anti-Pattern: Eager loader compilation and rendering inside listing loops

```ts
// src/content/collections/articles.ts & src/pages/blog/index.astro
// Eager compilation + rendering in listing loop exhausts Node heap!
export const articles = defineCollection({
  // ❌ Default deferRender: false compiles all entries eagerly into RAM
  loader: glob({ pattern: '**/*.md', base: './content/articles' }),
  schema: articleSchema,
})

// src/pages/blog/index.astro
const posts = await getCollection('articles')
// ❌ Fatal OOM: rendering every entry during listing generation!
const rendered = await Promise.all(posts.map(async (p) => ({ ...p, rendered: await render(p) })))
```

_Why this fails:_ Eagerly compiling thousands of markdown documents stores entire rendered HTML strings and syntax trees in the Node.js memory DataStore. Invoking `render(p)` inside collection loops forces concurrent parsing of every single document, triggering `JavaScript heap out of memory` (OOM) build crashes on memory-capped hosts and CI workers.

##### ✅ Best Practice / Idiomatic: Deferred rendering with metadata-only listing loops

```ts
// src/content/collections/articles.ts & src/pages/blog/index.astro
// Deferred compilation + metadata-only listing loop
export const articles = defineCollection({
  // ✅ Defers compilation until individual detail routes call render(entry)
  loader: glob({
    pattern: '**/*.md',
    base: './content/articles',
    deferRender: true,
    retainBody: false, // Drops raw source body from memory store
  }),
  schema: articleSchema,
});

// src/pages/blog/index.astro
// ✅ Listing page reads strictly from lightweight entry.data; zero render() calls
const posts = await getCollection('articles');
---
<ul>
  {posts.map((post) => (
    <li>
      <a href={`/blog/${post.id}`}>{post.data.title}</a>
      <p>{post.data.excerpt}</p>
    </li>
  ))}
</ul>
```

#### Pattern 2: Passing Bulky AST Trees via getStaticPaths vs. Minimal Identifiers (RULE-ID: ASTRO-COLLECT-10)

##### ❌ Bad Practice / Anti-Pattern: Passing full rendered objects through static route props

```astro
---
// ❌ Anti-Pattern: Bloats memory by retaining full rendered bodies across static paths
export async function getStaticPaths() {
  const posts = await getCollection('articles');
  return Promise.all(posts.map(async (post) => ({
    params: { id: post.id },
    props: { post, rendered: await render(post) },
  })));
}
---
```

##### ✅ Best Practice / Idiomatic: Passing lightweight entry references and rendering on demand

```astro
---
// ✅ Idiomatic: getStaticPaths returns lightweight props; render() is deferred to route execution
export async function getStaticPaths() {
  const posts = await getCollection('articles');
  return posts.map((post) => ({
    params: { id: post.id },
    props: { post },
  }));
}

const { post } = Astro.props;
const { Content } = await render(post);
---
<article>
  <h1>{post.data.title}</h1>
  <Content />
</article>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/07-migration-and-core-contracts/65-content-collection-build-memory-deferral/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: ASTRO-COLLECT-13`, `RULE-ID: ASTRO-COLLECT-04`, `RULE-ID: ASTRO-COLLECT-10`, `RULE-ID: ASTRO-COLLECT-05`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/07-migration-and-core-contracts/65-content-collection-build-memory-deferral/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "65-CONTENT-COLLECTION-BUILD-MEMORY-DEFERRAL-001",
    "rule_id": "RULE-ID: ASTRO-COLLECT-13 (Defer Markdown Rendering on Large Collections)",
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
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/07-migration-and-core-contracts/65-content-collection-build-memory-deferral/issue-body.md" \
  --title "[Audit - Content Collection Build-Time Memory Deferral Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/07-migration-and-core-contracts/65-content-collection-build-memory-deferral/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Run `git grep -n "render(" src/pages/ src/features/ src/components/` to isolate all render call sites.
2. Confirm zero listing templates compile markdown bodies during index or archive generation.
3. Run `git grep -n "deferRender" src/content/` and `git grep -n "retainBody" src/content/` to inspect loader memory flags.
4. Verify memory bounds during content sync: `node --max-old-space-size=2048 ./node_modules/.bin/astro sync`.
5. Audit memory deferral boundaries via terminal commands:

```bash
# 1. Search for render() calls in listing and archive page components
git grep -n "render(" src/pages/blog/ src/pages/tr/blog/ src/features/resources/

# 2. Check collection loader configurations for deferRender flag
git grep -n "deferRender" src/content/ src/content.config.ts

# 3. Check collection loader configurations for retainBody flag
git grep -n "retainBody" src/content/ src/content.config.ts

# 4. Verify astro sync runs within memory limits
node --max-old-space-size=2048 ./node_modules/.bin/astro sync
```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/07-migration-and-core-contracts/65-content-collection-build-memory-deferral/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Content Collection Build-Time Memory Deferral Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/07-migration-and-core-contracts/65-content-collection-build-memory-deferral/findings.json` (N defects logged)
   - `file://docs/audits/results/07-migration-and-core-contracts/65-content-collection-build-memory-deferral/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/07-migration-and-core-contracts/65-content-collection-build-memory-deferral/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/07-migration-and-core-contracts/65-content-collection-build-memory-deferral/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/07-migration-and-core-contracts/65-content-collection-build-memory-deferral/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
