# Mission Brief: Commercial Services Hierarchy Tier 3 Task Offerings Audit

## 3.0 Skills / Tools: view_file, run_command, astro-component-architect.

## 3.1 Context Block

Tier 3 represents granular Task Offerings and Method Dossiers (`TaskOfferingTemplate.astro`), comprising 62+ specialized deliverables (e.g. log analysis, crawl budget, entity optimization, prompt auditing).
A previous defect occurred where empty slot wrappers (`<div class="proof-band-wrapper">`) rendered unconditional 500px empty spacing even when no proof band was supplied, causing severe Cumulative Layout Shift (CLS).

### Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`04-getstaticpaths-contract-params-vs-props.md`](../../best-practices/03-routing-and-pages/04-getstaticpaths-contract-params-vs-props.md) — Passing pre-computed props vs refetching inside components (`RULE-ID: ASTRO-ROUTING-04`).
- [`05-large-build-memory-optimization-in-getstaticpaths.md`](../../best-practices/03-routing-and-pages/05-large-build-memory-optimization-in-getstaticpaths.md) — Avoiding massive memory retention in `getStaticPaths` across thousands of pages (`RULE-ID: ASTRO-ROUTING-05`).
- [`01-content-layer-architecture-v5.md`](../../best-practices/04-content-layer-and-collections/01-content-layer-architecture-v5.md) — Astro 5 Content Layer store and collection definitions (`RULE-ID: ASTRO-CONTENT-01`).
- [`02-sqlite-backed-content-store.md`](../../best-practices/04-content-layer-and-collections/02-sqlite-backed-content-store.md) — High-speed SQLite-backed cache vs repetitive disk reads (`RULE-ID: ASTRO-CONTENT-02`).
- [`03-custom-loaders-over-filesystem.md`](../../best-practices/04-content-layer-and-collections/03-custom-loaders-over-filesystem.md) — Using custom loaders for API/CMS integration (`RULE-ID: ASTRO-CONTENT-06`).
- [`11-filter-queries-with-sqlite-query-store.md`](../../best-practices/04-content-layer-and-collections/11-filter-queries-with-sqlite-query-store.md) — Efficient filtering of references and case studies (`RULE-ID: ASTRO-CONTENT-10`).

Invariants:

- **Zero-JS Compilation Across Task Offerings**: All 62+ Task Offering pages (`TaskOfferingTemplate.astro`, `TaskFaqSection.astro`, `TaskArtFigure.astro`) must render 100% static HTML with zero client JavaScript runtime.
- **Defensive Slot Guarding & CLS Elimination**: Wrapper elements around optional slots must strictly be guarded with `Astro.slots.has('slotName')`. Rendering empty wrapper elements without slotted content creates phantom padding, margins, and severe CLS.
- **getStaticPaths Memory & Query Hygiene**: For 62+ granular deliverables, avoid loading heavy unneeded payloads or monolithic collection graphs into heap memory. Return minimal parameters and identifiers or targeted pre-fetched data, avoiding redundant collection scans.
- **Client Scripts Over UI Frameworks**: In `TaskFaqSection.astro`, accordion expand/collapse toggles must use native semantic HTML `<details><summary>` or native Web Components (`HTMLElement`), never pulling a heavy React accordion island (`client:visible`) that ships 45KB+ framework runtime.
- **Scoped Style Encapsulation**: Task chrome, badge pills, and methodology cards must use scoped `<style>` (`[data-astro-cid-*]`) to prevent leaking styles into sibling service templates.

Critical files to inspect:

- src/components/service-hierarchy/task/TaskOfferingTemplate.astro
- src/components/service-hierarchy/task/TaskFaqSection.astro
- src/components/service-hierarchy/task/TaskArtFigure.astro
- src/components/service-hierarchy/task/chrome.ts
- src/lib/task-offerings/make-page.tsx
- src/content/taskOfferings/
- src/pages/services/

## 3.2 Mission Objective

Examine all 62+ Tier 3 Task Offering pages and TaskOfferingTemplate.astro.
Outcome: Prove zero layout jumps, zero unconditioned wrapper divs, complete multilingual metadata and breadcrumb hierarchy, robust slot fallbacks, and zero client JS runtime bloat.
Constraints: Read-only inspection; verify prop contracts and slot emptiness checks.
Autonomy Grant: You own this mission end-to-end. Audit template slots, responsive art wrappers, and dossier metadata. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `TaskOfferingTemplate.astro` lines 90-130: ensure `Astro.slots.has('proofBand')` and `Astro.slots.has('tools')` guard wrapper elements.
2. Verify `TASK_CHROME` localization in `chrome.ts` across 'en', 'tr', and 'ar'.
3. Inspect `TaskFaqSection.astro`: ensure FAQ schema JSON-LD is generated deterministically without unescaped quote syntax.
4. Verify dynamic route decoding: Ensure task slugs handle URL decoding properly via `decodeURI(task)`.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Monolithic Props in getStaticPaths vs Memory Optimization (RULE-ID: ASTRO-ROUTING-05)

##### ❌ Bad Practice / Anti-Pattern: Passing entire monolithic collection arrays as props in `getStaticPaths()`, retaining gigabytes of AST memory during sharded builds

```astro
---
// src/pages/services/[tier1]/[tier2]/[task].astro - Leaking full collection ASTs in memory
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  const allTasks = await getCollection('taskOfferings');
  // Anti-Pattern: Retaining heavy monolithic task dossiers & ASTs in memory across all routes
  return allTasks.map((entry) => ({
    params: { tier1: entry.data.tier1, tier2: entry.data.tier2, task: entry.id },
    props: { fullEntry: entry }, // 62+ heavy objects with ASTs held in heap throughout build
  }));
}

const { fullEntry } = Astro.props;
---
<h1>{fullEntry.data.title}</h1>
```

_Why this fails:_ Passing monolithic objects and heavy AST graphs inside `props` retains them in Node.js heap memory throughout the entire static build cycle. On large content collections, this triggers heap out-of-memory (`ERR_WORKER_OUT_OF_MEMORY`) crashes.

##### ✅ Best Practice / Idiomatic: Returning minimal `{ params: { slug: entry.id } }` and fetching lightweight records via `getEntry()` in page frontmatter

```astro
---
// src/pages/services/[tier1]/[tier2]/[task].astro - Minimal params with targeted on-demand fetch
import { getCollection, getEntry, render } from 'astro:content';

export async function getStaticPaths() {
  const allTasks = await getCollection('taskOfferings');
  // Idiomatic: Return only lightweight routing parameters
  return allTasks.map((entry) => ({
    params: { tier1: entry.data.tier1, tier2: entry.data.tier2, task: entry.id },
  }));
}

const { task } = Astro.params;
// Resolve lightweight record on-demand during page render, garbage collected immediately after
const entry = await getEntry('taskOfferings', task!);
if (!entry) return Astro.redirect('/404');
const { Content } = await render(entry);
---
<h1>{entry.data.title}</h1>
<Content />
```

#### Pattern 2: In-Memory Filtering vs Content Layer Predicates & SQLite Query Store (RULE-ID: ASTRO-CONTENT-10)

##### ❌ Bad Practice / Anti-Pattern: In-memory JavaScript `.filter()` over thousands of entries inside UI components

```astro
---
// src/components/service-hierarchy/task/RelatedTasks.astro - Wasteful full collection pull
import { getCollection } from 'astro:content';

interface Props {
  tier2: string;
}
const { tier2 } = Astro.props;

// Anti-Pattern: Loads all 62+ tasks from disk/Vite and filters in JavaScript memory
const allTasks = await getCollection('taskOfferings');
const filtered = allTasks.filter((t) => t.data.tier2 === tier2 && !t.data.draft);
---
<ul>
  {filtered.map((item) => <li>{item.data.title}</li>)}
</ul>
```

_Why this fails:_ Running unbounded `.filter()` inside page components duplicates memory allocations, re-evaluates filters for every route rendered, and ignores Astro 5's Content Layer query optimizations.

##### ✅ Best Practice / Idiomatic: Targeted Content Layer queries and SQLite indexing via predicate parameter

```astro
---
// src/components/service-hierarchy/task/RelatedTasks.astro - Upstream filtered query
import { getCollection } from 'astro:content';

interface Props {
  tier2: string;
}
const { tier2 } = Astro.props;

// Idiomatic: Predicate filters at query time using the Content Layer DataStore
const filtered = await getCollection('taskOfferings', ({ data }) => {
  return data.tier2 === tier2 && (import.meta.env.PROD ? !data.draft : true);
});
---
<ul>
  {filtered.map((item) => <li>{item.data.title}</li>)}
</ul>
```

#### Pattern 3: Defensive Slot Guarding to Prevent Layout Shift (RULE-ID: ASTRO-ROUTING-11)

##### ❌ Bad Practice / Anti-Pattern: Unconditioned slot wrapper rendering 500px empty box causing severe CLS

```astro
---
// src/components/service-hierarchy/task/TaskOfferingTemplate.astro
---
<article class="task-offering">
  <!-- Anti-Pattern: Renders wrapper with padding/margin even when no proof band is passed -->
  <div class="proof-band-wrapper">
    <slot name="proofBand" />
  </div>
</article>
```

_Why this fails:_ An empty `<div class="proof-band-wrapper">` with layout styles (height, margins, padding) creates phantom space, displacing subsequent content and introducing severe Cumulative Layout Shift (CLS > 0.1).

##### ✅ Best Practice / Idiomatic: Defensive slot guarding with `Astro.slots.has()`

```astro
---
// src/components/service-hierarchy/task/TaskOfferingTemplate.astro
---
<article class="task-offering">
  <!-- Idiomatic: Defensive check guarantees zero empty DOM nodes and zero CLS -->
  {Astro.slots.has('proofBand') && (
    <div class="proof-band-wrapper">
      <slot name="proofBand" />
    </div>
  )}
</article>
```

#### Pattern 4: Heavy React FAQ Accordions vs Zero-JS Semantic HTML (RULE-ID: ASTRO-HYDRATION-01)

##### ❌ Bad Practice / Anti-Pattern: Importing React accordion islands for static FAQ content

```astro
---
// src/components/service-hierarchy/task/TaskFaqSection.astro
import ReactAccordion from './ReactAccordion.tsx';
const { faqs } = Astro.props;
---
<!-- Anti-Pattern: Ships 45KB+ React runtime for simple click-to-expand text -->
<ReactAccordion client:visible faqs={faqs} />
```

_Why this fails:_ Presentational accordions do not require Virtual DOM, state reconcilers, or JavaScript bundles. Hydrating React for static text incurs unnecessary main-thread blocking and increases INP.

##### ✅ Best Practice / Idiomatic: Semantic HTML `<details><summary>` with scoped CSS

```astro
---
// src/components/service-hierarchy/task/TaskFaqSection.astro
const { faqs } = Astro.props;
---
<!-- Idiomatic: Zero-JS native disclosure widget with instant interaction -->
<div class="faq-list">
  {faqs.map(({ question, answer }) => (
    <details class="faq-item">
      <summary class="faq-question font-gilroy font-semibold">{question}</summary>
      <div class="faq-answer font-akagi text-neutral-600 dark:text-neutral-300">
        <p>{answer}</p>
      </div>
    </details>
  ))}
</div>

<style>
  .faq-item {
    border-bottom: 1px solid var(--color-border);
    padding: 1rem 0;
  }
  .faq-question {
    cursor: pointer;
    list-style: none;
  }
</style>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/01-templates-routing/04-services-hierarchy-tier3-task-offerings/`

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

You must create and populate the following deliverables in `docs/audits/results/01-templates-routing/04-services-hierarchy-tier3-task-offerings/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "04-SERVICES-HIERARCHY-TIER3-TASK-OFFERINGS-001",
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
  --body "docs/audits/results/01-templates-routing/04-services-hierarchy-tier3-task-offerings/issue-body.md" \
  --title "[Audit - Commercial Services Hierarchy Tier 3 Task Offerings Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/01-templates-routing/04-services-hierarchy-tier3-task-offerings/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification commands to validate audit findings across task offering routes:

1. Scan for collection queries and static path contracts:
   ```bash
   git grep -n "getCollection(" src/pages/
   git grep -n "getStaticPaths" src/pages/
   ```
2. Profile memory usage during full static build to ensure no linear heap growth or worker OOM:
   ```bash
   NODE_OPTIONS="--max-old-space-size=4096" pnpm astro build
   ```
3. Run `git grep -n "Astro.slots.has" src/components/service-hierarchy/task/TaskOfferingTemplate.astro` to verify conditional rendering of slot wrappers.
4. Run `git grep -n "client:" src/components/service-hierarchy/task/` to prove zero client directives in task templates.
5. Run `git grep -n "<style is:global>" src/components/service-hierarchy/task/` to confirm zero cascading style leaks.
6. Run `git grep -n "onClick=\|onChange=" src/components/service-hierarchy/task/` to ensure no illegal JSX event handlers in `.astro` files.
7. Verify `getStaticPaths` in task offering routes passes minimal parameters or pre-resolved props to eliminate redundant build-time content lookups.
8. Check that all task offering routes emit valid canonical URLs without trailing slashes.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/01-templates-routing/04-services-hierarchy-tier3-task-offerings/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Commercial Services Hierarchy Tier 3 Task Offerings Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/01-templates-routing/04-services-hierarchy-tier3-task-offerings/findings.json` (N defects logged with RULE-ID mapping)
   - `file://docs/audits/results/01-templates-routing/04-services-hierarchy-tier3-task-offerings/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/01-templates-routing/04-services-hierarchy-tier3-task-offerings/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/01-templates-routing/04-services-hierarchy-tier3-task-offerings/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/01-templates-routing/04-services-hierarchy-tier3-task-offerings/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
