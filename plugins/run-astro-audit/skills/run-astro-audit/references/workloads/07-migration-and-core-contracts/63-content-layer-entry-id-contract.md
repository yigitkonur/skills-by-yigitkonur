# Mission Brief: Content Layer entry.id vs entry.slug Contract Audit

## 3.0 Skills / Tools: view_file, run_command, astro-component-architect.

## 3.1 Context Block

Astro 5 and Astro 7 introduced the unified Content Layer API (`src/content.config.ts`) backed by a reactive SQLite DataStore:

- Unified ID Architecture: In legacy Astro 4 collections, Markdown/MDX entries had a generated `slug` property, while data collections used `id`. In the modern Content Layer, all collections are unified: every entry, regardless of loader (`glob`, `file`, custom loaders), uses `entry.id` as its authoritative primary unique identifier.
- Deprecation of `entry.slug`: The reserved `slug` property has been completely removed from Content Layer entries. Accessing `entry.slug` returns `undefined`.
- Routing Hazards: Using `entry.slug` inside `getStaticPaths()` silently generates broken routes containing `/undefined/` or causes fatal static path generation failures at build time.
- Modern `render(entry)` API: Rendering content entries now imports `render(entry)` from `astro:content` (`const { Content, headings } = await render(entry);`), deprecating legacy `await entry.render()`.
- Deterministic Routing: If specific URL slugs are required, route parameters should map directly to `entry.id`, or customize `generateId` inside the collection loader configuration.

### Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`14-handle-breaking-changes-from-legacy-collections.md`](../../best-practices/04-content-layer-and-collections/14-handle-breaking-changes-from-legacy-collections.md) — Upgrading legacy `entry.slug` to Astro 5 `entry.id` across Content Layer queries (`RULE-ID: ASTRO-COLLECT-14`).
- [`02-use-entry-id-instead-of-slug.md`](../../best-practices/04-content-layer-and-collections/02-use-entry-id-instead-of-slug.md) — Query and route by `entry.id` instead of legacy `slug` (`RULE-ID: ASTRO-COLLECT-02`).
- [`03-use-render-function-from-astro-content.md`](../../best-practices/04-content-layer-and-collections/03-use-render-function-from-astro-content.md) — Using the standalone `render(entry)` function from `astro:content` instead of legacy `entry.render()` (`RULE-ID: ASTRO-COLLECT-03`).
- [`01-migrate-to-content-config.md`](../../best-practices/04-content-layer-and-collections/01-migrate-to-content-config.md) — Migrating to modern `src/content.config.ts` Content Layer architecture (`RULE-ID: ASTRO-COLLECT-01`).

Critical files to inspect:

- `src/content.config.ts`
- `src/features/resources/`
- `src/features/proof/`
- `src/pages/`
- `src/lib/`

## 3.2 Mission Objective

Perform a site-wide audit across all content collection queries to verify strict adherence to the Content Layer `entry.id` contract and modern `render(entry)` API.
Outcome: Ensure zero broken `entry.slug` references, confirm all `getStaticPaths` mappings use `entry.id`, and verify that collections use standard loader patterns (`glob`, `file`) without legacy deprecation warnings.
Constraints: Read-only audit; do not edit production code.
Autonomy Grant: You own this mission end-to-end. Inspect collection schemas, trace query call sites, and verify ID-based routing contracts. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Audit `src/content.config.ts` to verify collection definitions and loader configurations.
2. Search for `entry.slug` across all `.astro` and `.ts` files and verify whether `entry.id` should be used instead.
3. Check calls to `render(entry)` from `'astro:content'` to ensure proper AST compilation.
4. Verify that `getStaticPaths` parameter contracts use `params: { id: entry.id }` or `params: { slug: entry.id }`.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Accessing Deprecated entry.slug vs. Canonical entry.id (RULE-ID: ASTRO-COLLECT-14, RULE-ID: ASTRO-COLLECT-02)

##### ❌ Bad Practice / Anti-Pattern: Accessing entry.slug in Astro 5 Content Layer

```astro
---
// src/pages/case-studies/[slug].astro (Legacy Astro 4 collection query)
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  const studies = await getCollection('caseStudies');
  return studies.map((entry) => ({
    // ❌ entry.slug is undefined in Content Layer! Generates /case-studies/undefined
    params: { slug: entry.slug },
    props: { entry },
  }));
}

const { entry } = Astro.props;
// ❌ Deprecated legacy rendering method:
const { Content } = await entry.render();
---
```

_Why this fails:_ In Astro 5 Content Layer, the `slug` property was removed in favor of a unified `id` identifier across all loaders. Accessing `entry.slug` evaluates to `undefined`, silently generating broken URLs like `/case-studies/undefined/` or failing route build validation.

##### ✅ Best Practice / Idiomatic: Direct entry.id routing and standalone render(entry) API

```astro
---
// src/pages/case-studies/[id].astro (Idiomatic Astro Content Layer)
import { getCollection, render } from 'astro:content';

export async function getStaticPaths() {
  const studies = await getCollection('caseStudies');
  return studies.map((entry) => ({
    // ✅ entry.id is the authoritative identifier across all loaders
    params: { id: entry.id },
    props: { entry },
  }));
}

const { entry } = Astro.props;
// ✅ Idiomatic Content Layer render API
const { Content, headings } = await render(entry);
---
<article>
  <h1>{entry.data.title}</h1>
  <Content />
</article>
```

#### Pattern 2: Deprecated entry.render() Method vs. Standalone render(entry) (RULE-ID: ASTRO-COLLECT-03)

##### ❌ Bad Practice / Anti-Pattern: Calling entry.render() method on collection entries

```astro
---
// ❌ Anti-Pattern: Invoking legacy method directly on entry object
const { Content } = await entry.render();
---
```

##### ✅ Best Practice / Idiomatic: Importing standalone render() from astro:content

```astro
---
// ✅ Idiomatic: Standalone render function with headings extraction
import { render } from 'astro:content';
const { Content, headings } = await render(entry);
---
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/07-migration-and-core-contracts/63-content-layer-entry-id-contract/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: ASTRO-COLLECT-14`, `RULE-ID: ASTRO-COLLECT-02`, `RULE-ID: ASTRO-COLLECT-03`, `RULE-ID: ASTRO-COLLECT-01`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/07-migration-and-core-contracts/63-content-layer-entry-id-contract/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "63-CONTENT-LAYER-ENTRY-ID-CONTRACT-001",
    "rule_id": "RULE-ID: ASTRO-COLLECT-14 (Handle Breaking Changes From Legacy Collections: entry.id)",
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
  --body "docs/audits/results/07-migration-and-core-contracts/63-content-layer-entry-id-contract/issue-body.md" \
  --title "[Audit - Content Layer entry.id vs entry.slug Contract Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/07-migration-and-core-contracts/63-content-layer-entry-id-contract/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Run `git grep -n "\.slug\b" src/pages/ src/features/` to isolate legacy slug property accesses.
2. Confirm all collection entry accesses are verified for Astro 5/7 Content Layer compliance.
3. Audit Content Layer contracts via terminal commands:

```bash
# 1. Audit codebase for deprecated .slug property access on collection entries
git grep -n "\.slug\b" src/pages/ src/features/ src/components/

# 2. Check getStaticPaths param definitions for slug: entry.slug
git grep -n "params:\s*\{\s*slug:\s*[^}]*\.slug" src/pages/

# 3. Detect deprecated entry.render() method calls
git grep -n "\.render()" src/

# 4. Check for deprecated getEntryBySlug helper imports
git grep -n "getEntryBySlug" src/

# 5. Verify loader definitions in src/content.config.ts
git grep -nE "(glob|file)\(" src/content.config.ts
```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/07-migration-and-core-contracts/63-content-layer-entry-id-contract/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Content Layer entry.id vs entry.slug Contract Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/07-migration-and-core-contracts/63-content-layer-entry-id-contract/findings.json` (N defects logged)
   - `file://docs/audits/results/07-migration-and-core-contracts/63-content-layer-entry-id-contract/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/07-migration-and-core-contracts/63-content-layer-entry-id-contract/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/07-migration-and-core-contracts/63-content-layer-entry-id-contract/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/07-migration-and-core-contracts/63-content-layer-entry-id-contract/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
