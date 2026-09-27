# Mission Brief: Proof, Case Studies & References Showcase Audit

## 3.0 Skills / Tools: view_file, run_command, brand-logo-normalizer, astro-component-architect.

## 3.1 Context Block

Social proof is central to The project's enterprise authority. The site showcases 238 vetted customer references (market leaders across 24 industry sectors) and 37 published case studies.
Customer reference marquees (`ProofRail.astro`, `MarqueeRail.tsx`) must strictly adhere to Swiss understated motion: zero media-player controls (`showControls={false}`), continuous CSS translation, transparent logo backgrounds, and Light/Dark parity.

### Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`04-getstaticpaths-contract-params-vs-props.md`](../../best-practices/03-routing-and-pages/04-getstaticpaths-contract-params-vs-props.md) — Passing pre-computed props vs refetching inside components (`RULE-ID: ASTRO-ROUTING-04`).
- [`05-large-build-memory-optimization-in-getstaticpaths.md`](../../best-practices/03-routing-and-pages/05-large-build-memory-optimization-in-getstaticpaths.md) — Avoiding massive memory retention in `getStaticPaths` across thousands of pages (`RULE-ID: ASTRO-ROUTING-05`).
- [`01-content-layer-architecture-v5.md`](../../best-practices/04-content-layer-and-collections/01-content-layer-architecture-v5.md) — Astro 5 Content Layer store and collection definitions (`RULE-ID: ASTRO-CONTENT-01`).
- [`02-sqlite-backed-content-store.md`](../../best-practices/04-content-layer-and-collections/02-sqlite-backed-content-store.md) — High-speed SQLite-backed cache vs repetitive disk reads (`RULE-ID: ASTRO-CONTENT-02`).
- [`03-custom-loaders-over-filesystem.md`](../../best-practices/04-content-layer-and-collections/03-custom-loaders-over-filesystem.md) — Using custom loaders for API/CMS integration (`RULE-ID: ASTRO-CONTENT-06`).
- [`11-filter-queries-with-sqlite-query-store.md`](../../best-practices/04-content-layer-and-collections/11-filter-queries-with-sqlite-query-store.md) — Efficient filtering of references and case studies (`RULE-ID: ASTRO-CONTENT-10`).

Invariants:

- **Zero-JS Compilation & Strict Island Containment**: Case study articles, reference grids, and testimonial bands must compile to static HTML. Only interactive marquees or dynamic facet search islands should hydrate; surrounding layouts, quote cards, and metric callouts must remain 100% static zero-JS.
- **Slots Over Render Props**: Components such as `ProofRail.astro` and reference cards must pass logos, captions, and metrics as slotted children (`<slot />`, `<slot name="..." />`) or serializable JSON props. Passing function render props (`renderItem={(ref) => ...}`) across the Astro-to-React boundary fails serialization and is strictly prohibited.
- **Scoped Style Encapsulation**: Hover-zoom effects, logo opacity transitions, and case study grid styles must be scoped via Astro `<style>` (`[data-astro-cid-*]`). Never use `<style is:global>` inside proof components, which can corrupt sitewide image rules.
- **getStaticPaths Memory & Query Balance**: Case study detail routes (`src/pages/case-studies/[slug].astro`) and sector pages must inject minimal route parameters or targeted pre-resolved entities via `props: { study }` in `getStaticPaths()`, avoiding redundant collection queries during static build without retaining massive ASTs in heap.
- **Dynamic Route Param Decoding**: Dynamic parameters in `Astro.params` are raw strings. Decode sector names and case study slugs with `decodeURI(slug)` to ensure special characters resolve cleanly.

Critical files to inspect:

- src/features/proof/components/CaseStudyDetailPage.astro
- src/features/proof/components/CaseStudyListingPage.astro
- src/features/proof/components/ReferencesIndexPage.astro
- src/features/proof/components/ReferencesArchivePage.astro
- src/components/common/ProofRail.astro
- src/components/common/MarqueeRail.tsx
- src/components/sections/service-shared/ClientReferenceRail.astro
- src/pages/case-studies/
- src/pages/references/

## 3.2 Mission Objective

Perform an exhaustive audit of all Case Study and Reference surfaces.
Outcome: Prove 100% adherence to the showControls={false} mandate, verify zero hover-jump in reference logos, confirm locale-aware counter text in CaseStudyListingPage, validate 238-brand reference counts, and confirm zero-JS compilation on proof articles.
Constraints: Read-only audit. Check tokens, aspects, and multi-locale filters.
Autonomy Grant: You own this mission end-to-end. Test facet filters, inspect SVG/PNG silhouettes, and verify translation maps. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `MarqueeRail.tsx`: ensure `showControls={false}` is respected sitewide and no `'|| < >'` media buttons render.
2. Inspect `CaseStudyListingPage.astro`: verify countText logic correctly handles TR ("X / Y vaka") and AR ("X من Y") without digit inversion.
3. Check `ClientReferenceRail.astro`: verify all rail labels, subtitles, and fallbacks exist multilingually.
4. Dynamic Route Decoding: Ensure sector and case study slugs are decoded with `decodeURI(slug)`.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Monolithic Props in getStaticPaths vs Memory Optimization (RULE-ID: ASTRO-ROUTING-05)

##### ❌ Bad Practice / Anti-Pattern: Passing entire monolithic collection arrays as props in `getStaticPaths()`, retaining gigabytes of AST memory during sharded builds

```astro
---
// src/pages/case-studies/[slug].astro - Retaining full case study ASTs across all routes
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  // Anti-Pattern: Loading all case studies with full rich text ASTs into memory props
  const allStudies = await getCollection('caseStudies');
  return allStudies.map((study) => ({
    params: { slug: study.id },
    props: { study }, // Retained in heap during the entire sharded build
  }));
}

const { study } = Astro.props;
---
<article>
  <h1>{study.data.title}</h1>
</article>
```

_Why this fails:_ Keeping dozens of rich case study dossiers and their parsed AST trees in heap memory throughout the static generation cycle causes excessive memory footprint and risk of worker OOM.

##### ✅ Best Practice / Idiomatic: Returning minimal `{ params: { slug: entry.id } }` and fetching lightweight records via `getEntry()` in page frontmatter

```astro
---
// src/pages/case-studies/[slug].astro - Lightweight route params with on-demand retrieval
import { getCollection, getEntry, render } from 'astro:content';

export async function getStaticPaths() {
  const allStudies = await getCollection('caseStudies');
  // Idiomatic: Only return lightweight routing identifiers
  return allStudies.map((study) => ({
    params: { slug: study.id },
  }));
}

const { slug } = Astro.params;
// Resolve the single case study record on-demand; garbage-collected immediately after render
const study = await getEntry('caseStudies', slug!);
if (!study) return Astro.redirect('/404');
const { Content } = await render(study);
---
<article>
  <h1>{study.data.title}</h1>
  <Content />
</article>
```

#### Pattern 2: In-Memory Client Filtering vs Content Layer Predicates & SQLite Query Store (RULE-ID: ASTRO-CONTENT-10)

##### ❌ Bad Practice / Anti-Pattern: In-memory JavaScript `.filter()` over thousands of entries inside UI components

```astro
---
// src/components/proof/SectorReferences.astro - Wasteful array filtering
import { getCollection } from 'astro:content';

interface Props {
  sector: string;
}
const { sector } = Astro.props;

// Anti-Pattern: Reads all 238 references from disk into memory and filters in JavaScript
const allReferences = await getCollection('references');
const sectorRefs = allReferences.filter((ref) => ref.data.sector === sector);
---
<div class="reference-grid">
  {sectorRefs.map((r) => <span>{r.data.brandName}</span>)}
</div>
```

_Why this fails:_ In-memory array filtering forces every sector component to hold and iterate through all 238 customer records, bypassing Content Layer SQLite index speed and wasting CPU time.

##### ✅ Best Practice / Idiomatic: Targeted Content Layer queries and SQLite indexing via predicate parameter

```astro
---
// src/components/proof/SectorReferences.astro - Upstream filtered query
import { getCollection } from 'astro:content';

interface Props {
  sector: string;
}
const { sector } = Astro.props;

// Idiomatic: Filter upstream at collection query time leveraging SQLite DataStore
const sectorRefs = await getCollection('references', ({ data }) => {
  return data.sector === sector;
});
---
<div class="reference-grid">
  {sectorRefs.map((r) => <span>{r.data.brandName}</span>)}
</div>
```

#### Pattern 3: Slots Over Function Render Props Across Astro Boundary (RULE-ID: ASTRO-ROUTING-11)

##### ❌ Bad Practice / Anti-Pattern: Passing function render props across Astro-to-React boundary

```astro
---
// src/components/proof/ProofSection.astro
import MarqueeRail from '../common/MarqueeRail.tsx';
const { logos } = Astro.props;
---
<!-- Anti-Pattern: Function callbacks cannot be serialized across Astro-React boundary -->
<MarqueeRail
  client:visible
  renderLogo={(logo: string) => <img src={logo} alt="Logo" />}
  logos={logos}
/>
```

_Why this fails:_ Astro serializes island props to JSON. Passing functions (`renderLogo`, `renderItem`) across the `.astro` to `.tsx` boundary throws runtime serialization errors or passes undefined.

##### ✅ Best Practice / Idiomatic: Native Astro slots or serializable plain JSON props

```astro
---
// src/components/proof/ProofSection.astro
import ProofRail from '../common/ProofRail.astro';
const { references } = Astro.props;
---
<!-- Idiomatic: Pass markup via native Astro slots or serializable data props -->
<ProofRail references={references} showControls={false}>
  <div slot="caption" class="text-sm font-akagi text-neutral-500">
    Trusted by 238+ enterprise market leaders across 24 sectors.
  </div>
</ProofRail>
```

#### Pattern 4: Media-Player Controls in Continuous Customer Reference Rails (RULE-ID: ASTRO-DESIGN-01)

##### ❌ Bad Practice / Anti-Pattern: Exposing media-player controls on continuous proof marquees

```astro
---
// src/components/common/ProofRail.astro
import MarqueeRail from './MarqueeRail.tsx';
---
<!-- Anti-Pattern: Rendering || < > buttons degrades serene Swiss typographic motion -->
<MarqueeRail client:visible showControls={true} />
```

_Why this fails:_ Violates The project's core Design System Purity rule: Customer reference marquees (`ProofRail.astro`, `MarqueeRail.tsx`) on marketing surfaces must keep media-player controls (`|| < >` pause/step buttons) hidden (`showControls={false}`) to maintain serene, understated Swiss typographic motion.

##### ✅ Best Practice / Idiomatic: Serene Swiss typography with hidden controls and continuous translation

```astro
---
// src/components/common/ProofRail.astro
import MarqueeRail from './MarqueeRail.tsx';
---
<!-- Idiomatic: Strict showControls={false} adhering to The application design system -->
<MarqueeRail client:visible showControls={false} pauseOnHover={true} />
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/01-templates-routing/06-proof-case-studies-references/`

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

You must create and populate the following deliverables in `docs/audits/results/01-templates-routing/06-proof-case-studies-references/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "06-PROOF-CASE-STUDIES-REFERENCES-001",
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
  --body "docs/audits/results/01-templates-routing/06-proof-case-studies-references/issue-body.md" \
  --title "[Audit - Proof, Case Studies & References Showcase Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/01-templates-routing/06-proof-case-studies-references/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification commands to validate audit findings across proof, case study, and reference surfaces:

1. Scan for collection queries and static path contracts:
   ```bash
   git grep -n "getCollection(" src/pages/
   git grep -n "getStaticPaths" src/pages/
   ```
2. Profile memory usage during large static builds with Node memory flags:
   ```bash
   NODE_OPTIONS="--max-old-space-size=4096" pnpm astro build
   ```
3. Run `pnpm vitest run tests/int/reference-facet-copy-contract.test.ts` to verify 238 reference counts.
4. Run `git grep -n "showControls" src/` to prove no instance passes showControls={true} on marketing surfaces.
5. Run `git grep -n "renderRow\|renderItem\|renderLogo" src/features/proof/ src/components/common/` to verify zero render props passed to islands.
6. Run `git grep -n "<style is:global>" src/features/proof/ src/components/common/ProofRail.astro` to confirm style scoping.
7. Run `git grep -n "onClick=\|onChange=" src/features/proof/` to verify zero invalid JSX event handlers in `.astro` templates.
8. Verify `getStaticPaths` in case study routes forwards pre-resolved entity data or minimal identifiers via `props` without build-time re-fetching.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/01-templates-routing/06-proof-case-studies-references/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Proof, Case Studies & References Showcase Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/01-templates-routing/06-proof-case-studies-references/findings.json` (N defects logged with RULE-ID mapping)
   - `file://docs/audits/results/01-templates-routing/06-proof-case-studies-references/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/01-templates-routing/06-proof-case-studies-references/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/01-templates-routing/06-proof-case-studies-references/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/01-templates-routing/06-proof-case-studies-references/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
