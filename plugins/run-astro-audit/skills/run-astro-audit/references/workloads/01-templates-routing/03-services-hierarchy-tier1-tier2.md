# Mission Brief: Commercial Services Hierarchy Tier 1 & Tier 2 Audit

## 3.0 Skills / Tools: view_file, run_command, astro-component-architect.

## 3.1 Context Block

The project's commercial offerings are structured in a 3-tier hierarchy across 7 core services: SEO, GEO, Content Marketing, Performance Marketing, Web Analytics, Generative AI Consultancy, and Generative AI Training.
Tier 1 represents the Service Hub (`ServiceHubTemplate.astro`).
Tier 2 represents the Service Detail / Pillar (`ServiceDetailTemplate.astro`).
Under Astro 7's queued non-recursive rendering engine, deep template nesting and complex slot forwarding must maintain linear dependency trees.

### Authoritative Astro Architectural & Best Practice Rules

- **Zero-JS Compilation Across Services** — [`[01-zero-js-by-default.md]`](../../best-practices/01-architecture-and-philosophy/01-zero-js-by-default.md): Tier 1 (Hub) and Tier 2 (Detail) commercial templates (`ServiceHubTemplate.astro`, `ServiceDetailTemplate.astro`, `HubCardGrid`, `HubProcess`, `DetailProcess`) must compile to 100% static HTML with 0 KB client JavaScript runtime. No presentation components should carry `client:*` directives.
- **Slots Over Render Props in Template Trees** — [`[06-slots-over-render-props.md]`](../../best-practices/01-architecture-and-philosophy/06-slots-over-render-props.md): Deeply nested layouts must pass markup via native Astro slots (`<slot />`, `<slot name="..." />`), never passing render callbacks or closures.
- **Scoped Style Encapsulation** — [`[07-scoped-styles-encapsulation.md]`](../../best-practices/01-architecture-and-philosophy/07-scoped-styles-encapsulation.md): All service tier components must rely on scoped `<style>` (`[data-astro-cid-*]`) to prevent typography, grid layouts, or spacing rules from cascading between Tier 1 hubs and Tier 2 details. `<style is:global>` is strictly banned in service templates.
- **Pure HTML Templates (No Virtual DOM)** — [`[12-no-virtual-dom-in-astro-templates.md]`](../../best-practices/01-architecture-and-philosophy/12-no-virtual-dom-in-astro-templates.md): `.astro` templates compile strictly on the server once per render. Inline JSX handlers (`onClick={...}`) and reactive frontmatter variables are non-functional anti-patterns.
- **Static vs. Dynamic Routing Conventions** — [`[01-static-vs-dynamic-routing-conventions.md]`](../../best-practices/03-routing-and-pages/01-static-vs-dynamic-routing-conventions.md): Commercial service hierarchies are fully static SSG routes built ahead-of-time for instant edge delivery and zero cold-start latency.
- **Catch-All Rest Parameters** — [`[02-rest-parameters-and-catch-all.md]`](../../best-practices/03-routing-and-pages/02-rest-parameters-and-catch-all.md): Multi-tier service slug matching (`[...slug].astro`) must handle both root hub (`{ params: { slug: undefined } }`) and nested details (`{ params: { slug: "tier1/tier2" } }`) without 404s, never returning `""` or `"/"`.
- **getStaticPaths Contract (Params vs Props)** — [`[04-getstaticpaths-contract-params-vs-props.md]`](../../best-practices/03-routing-and-pages/04-getstaticpaths-contract-params-vs-props.md): Service routes (`src/pages/services/[...slug].astro`) must return pre-fetched service data in `props: { service }` within `getStaticPaths()`. Fetching or filtering collections inside per-page frontmatter triggers O(N) redundant lookups at build time.
- **ClientRouter SPA Analytics Tracking** — [`[21-track-pageviews-in-client-router-with-astro-page-load.md]`](../../best-practices/03-routing-and-pages/21-track-pageviews-in-client-router-with-astro-page-load.md): Fire analytics on `astro:page-load` for service hub and detail page navigations to guarantee updated document titles, breadcrumbs, and metadata.

Critical files to inspect:

- `src/components/service-hierarchy/hub/ServiceHubTemplate.astro`
- `src/components/service-hierarchy/hub/HubCardGrid.astro`
- `src/components/service-hierarchy/hub/HubProcess.astro`
- `src/components/service-hierarchy/detail/ServiceDetailTemplate.astro`
- `src/components/service-hierarchy/detail/DetailProcess.astro`
- `src/components/service-hierarchy/detail/DetailChildDirectory.astro`
- `src/lib/service-details/`
- `src/lib/service-hierarchy/`

## 3.2 Mission Objective

Audit all Tier 1 (Hub) and Tier 2 (Detail) commercial templates across all 7 service verticals.
Outcome: Confirm 100% strict JSX tag closure, zero client-side hydration leaks in shared presentation components (ThemedIllustrationBase, HubArgument), zero global style leaks, and complete multilingual route parity.
Constraints: Read-only audit; verify data contracts between content collections and golden templates.
Autonomy Grant: You own this mission end-to-end. Explore template composition, slot delegation, and breadcrumb hierarchies. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Audit `ServiceHubTemplate.astro` and `ServiceDetailTemplate.astro` for slot inheritance.
2. Confirm that all child components (`HubProcess`, `DetailProcess`, `HubStories`) remain pure server-rendered components with NO `client:*` hydration directives.

3. Zero-JS Compilation Across Services:
   Ensure all commercial presentation cards and process lists compile to pure static HTML.

```astro
<!-- ❌ Bad Practice: Wrapping service process steps or cards in React islands -->
<ServiceProcessSteps client:visible steps={service.process} />
<ServiceDeliverablesGrid client:load deliverables={service.deliverables} />

<!-- ✅ Best Practice: Pure .astro components compiling to 100% static HTML (0 KB JS shipped) -->
<HubProcess steps={service.process} />
<HubCardGrid cards={service.cards} />
```

4. getStaticPaths Contract (Params vs Props):
   Inject resolved data directly into `props` within `getStaticPaths()` to eliminate redundant build-time queries.

```astro
---
// src/pages/services/[...slug].astro
export async function getStaticPaths() {
  const allServices = await fetchAllServices();

  // ❌ Bad Practice: Returning only params forces every page to re-fetch/find service in frontmatter
  // return allServices.map(s => ({ params: { slug: s.slug } }));

  // ✅ Best Practice: Pass pre-resolved data in props; frontmatter uses Astro.props directly (O(1) build)
  return allServices.map(service => ({
    params: { slug: service.slug },
    props: { service }
  }));
}

const { service } = Astro.props;
---
```

5. Style Scoping & Isolation:
   Never allow service-specific styles to pollute other marketing tiers.

```astro
<!-- ❌ Bad Practice: <style is:global> leaking service process styling into other site pages -->
<style is:global>
  .process-step { display: flex; gap: 1rem; border-left: 2px solid #F5265E; }
  .step-title { font-weight: 700; color: #1E2038; }
</style>

<!-- ✅ Best Practice: Scoped <style> isolated via [data-astro-cid-*] -->
<style>
  .process-step { display: flex; gap: 1rem; border-left: 2px solid var(--color-pink-500); }
  .step-title { font-weight: 700; color: var(--color-ink); }
</style>
```

6. Dynamic Route Param Decoding:
   Decode URL-encoded characters in route params before looking up content items.

```typescript
// ❌ Bad Practice: Reading raw encoded parameter directly without URI decoding
const rawSlug = Astro.params.slug // e.g. "yapay-zeka-ve-otomasyon%20egitimi"
const service = findService(rawSlug) // Mismatch / 404

// ✅ Best Practice: Explicitly decode dynamic URL segments
const slug = decodeURI(Astro.params.slug ?? '')
const service = findService(slug)
```

7. Rest Catch-All Contract for Services:
   Return `undefined` to match the services overview index route.

```astro
---
// src/pages/services/[...slug].astro
export async function getStaticPaths() {
  return [
    // ❌ Bad Practice: Returning "" or "/" causes routing ambiguity or build-time 404s
    // { params: { slug: "" } },
    // { params: { slug: "/" } },

    // ✅ Best Practice: Explicitly return undefined for the services index overview
    { params: { slug: undefined }, props: { isOverview: true } },
    ...tier1Hubs.map(hub => ({ params: { slug: hub.slug }, props: { hub } })),
    ...tier2Details.map(detail => ({ params: { slug: `${detail.tier1}/${detail.tier2}` }, props: { detail } })),
  ];
}
---
```

8. Pure HTML Templates & Interactive Widgets (No Virtual DOM):
   Avoid inline JSX handlers in `.astro` components; use native semantic elements.

```astro
<!-- ❌ Bad Practice: Inline JSX event handlers in .astro template -->
<button onClick={toggleDetails}>Show More</button>

<!-- ✅ Best Practice: Native HTML <details>/<summary> or custom elements with bundled script -->
<details class="service-faq-item">
  <summary class="cursor-pointer font-bold">What is GEO optimization?</summary>
  <p class="mt-2 text-ink-light">Generative Engine Optimization structures content for LLMs...</p>
</details>
```

9. Verify that all 7 core services have valid EN, TR, and AR hub route definitions in `src/pages/` and `PUBLIC_ROUTE_REGISTRY`.

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/01-templates-routing/03-services-hierarchy-tier1-tier2/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Rule ID Mapping**: Every defect recorded in `findings.json` must explicitly map to an authoritative Astro best practice rule identifier using the `rule_id` field (e.g. `RULE-ID: 03-routing-and-pages/04-getstaticpaths-contract-params-vs-props`, `RULE-ID: 01-architecture-and-philosophy/01-zero-js-by-default`, `RULE-ID: 01-architecture-and-philosophy/07-scoped-styles-encapsulation`, `RULE-ID: 03-routing-and-pages/02-rest-parameters-and-catch-all`).

You must create and populate the following deliverables in `docs/audits/results/01-templates-routing/03-services-hierarchy-tier1-tier2/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps. Every item MUST include a valid `rule_id` linking to `../../best-practices/`:

```json
[
  {
    "id": "03-SERVICES-HIERARCHY-TIER1-TIER2-001",
    "rule_id": "RULE-ID: 03-routing-and-pages/04-getstaticpaths-contract-params-vs-props",
    "file": "src/pages/services/[...slug].astro",
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
  --body "docs/audits/results/01-templates-routing/03-services-hierarchy-tier1-tier2/issue-body.md" \
  --title "[Audit - Commercial Services Hierarchy Tier 1 & Tier 2 Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/01-templates-routing/03-services-hierarchy-tier1-tier2/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Run `git grep -n "client:load\|client:only\|client:idle" src/components/service-hierarchy/` to prove zero client directives in core service templates.
2. Run `git grep -n "<style is:global>" src/components/service-hierarchy/` to verify zero global style leaks.
3. Run `git grep -n "onClick=\|onChange=" src/pages/services/ src/components/service-hierarchy/` to ensure no illegal JSX event handlers in `.astro` files.
4. Run `find dist/ -name "*.js" -size +0c` and verify that static service templates emit zero client JavaScript chunks.
5. Verify `getStaticPaths` in service routes injects data via `props` rather than redundant per-page fetching.
6. Verify that `generative-ai-training` has complete parity in EN, TR, and AR in `src/pages/` and `PUBLIC_ROUTE_REGISTRY`.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/01-templates-routing/03-services-hierarchy-tier1-tier2/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Commercial Services Hierarchy Tier 1 & Tier 2 Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/01-templates-routing/03-services-hierarchy-tier1-tier2/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/01-templates-routing/03-services-hierarchy-tier1-tier2/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/01-templates-routing/03-services-hierarchy-tier1-tier2/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/01-templates-routing/03-services-hierarchy-tier1-tier2/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/01-templates-routing/03-services-hierarchy-tier1-tier2/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
