# Mission Brief: Core Marketing & Homepage Route Controller Audit

## 3.0 Skills / Tools: view_file, run_command, react-doctor, astro-component-architect.

## 3.1 Context Block

The Astro application (Astro 7.3.1, Vite 8.2.2) renders the core marketing surface across 6 primary page types: Homepage (`src/pages/[...home].astro`), About Us (`src/pages/about/[...rest].astro`), Brand Assets (`src/pages/brand-assets/[...rest].astro`), Press (`src/pages/we-in-the-press/[...rest].astro`), Awards (`src/pages/awards/[...rest].astro`), and Reviews (`src/pages/reviews/[...rest].astro`).
`HomepageRoute.astro` mounts exactly five bands in alternating surface/soft tones: `HeroSection`, `ServicesModernizationPilot`, `CaseStudiesShowcase`, `AwardsModernizationPilot`, and `ResourcesSection`.
Under Astro 7's oxc Rust compiler, lenient HTML5 auto-closing is disabled. Any unclosed void tags, illegal self-closing non-void tags (`<span />`, `<button />`, `<template />`), or trailing unescaped characters trigger parsing aborts or excessive backtracking.

### Authoritative Astro Architectural & Best Practice Rules

- **Zero-JS By Default** — [`[01-zero-js-by-default.md]`](../../best-practices/01-architecture-and-philosophy/01-zero-js-by-default.md): Static marketing bands must compile to 100% static HTML with 0 KB client JavaScript. Wrapping static promotional banners or cards in React islands (`client:load`) ships 45KB–100KB+ unnecessary framework runtime.
- **Scoped Style Encapsulation** — [`[07-scoped-styles-encapsulation.md]`](../../best-practices/01-architecture-and-philosophy/07-scoped-styles-encapsulation.md): Component styles in `.astro` files are scoped automatically via `[data-astro-cid-*]`. Indiscriminate `<style is:global>` in marketing components is strictly prohibited as it leaks typography and layout specificity sitewide.
- **Pure HTML Templates (No Virtual DOM)** — [`[12-no-virtual-dom-in-astro-templates.md]`](../../best-practices/01-architecture-and-philosophy/12-no-virtual-dom-in-astro-templates.md): `.astro` templates compile strictly on the server once per render. Inline JSX handlers (`onClick={...}`) and reactive frontmatter variables are non-functional anti-patterns. Use native Web Components (`HTMLElement`) with bundled `<script>` for client-side behaviors.
- **Static vs. Dynamic Routing Conventions** — [`[01-static-vs-dynamic-routing-conventions.md]`](../../best-practices/03-routing-and-pages/01-static-vs-dynamic-routing-conventions.md): Core marketing routes pre-render to static HTML at build time for 0ms TTFB and edge cacheability, preserving edge compute budgets for dynamic search and forms satellites.
- **Catch-All Rest Parameters** — [`[02-rest-parameters-and-catch-all.md]`](../../best-practices/03-routing-and-pages/02-rest-parameters-and-catch-all.md): Root homepage route `src/pages/[...home].astro` and company routes `[...rest].astro` must return `{ params: { home: undefined } }` in `getStaticPaths()` to match the parent/root segment without 404s, never empty string `""` or `"/"`.
- **ClientRouter SPA Analytics Tracking** — [`[21-track-pageviews-in-client-router-with-astro-page-load.md]`](../../best-practices/03-routing-and-pages/21-track-pageviews-in-client-router-with-astro-page-load.md): Tracking pageviews on `astro:page-load` lifecycle event guarantees that `document.title` and canonical URLs are committed before dispatching analytics events, preventing lost SPA transitions.

Critical files to inspect:

- `src/pages/[...home].astro`
- `src/features/homepage/components/HomepageRoute.astro`
- `src/features/homepage/components/HeroSection.astro`
- `src/features/homepage/components/ServicesModernizationPilot.astro`
- `src/features/homepage/components/CaseStudiesShowcase.astro`
- `src/features/homepage/components/AwardsModernizationPilot.astro`
- `src/features/homepage/components/ResourcesSection.astro`
- `src/features/company/components/AboutRoute.astro`
- `src/features/company/components/BrandAssetsRoute.astro`
- `src/features/company/components/PressRoute.astro`

## 3.2 Mission Objective

Execute a rigorous, read-only syntax and architectural audit across all Core Marketing route entrypoints and page bands.
Outcome: Prove zero unclosed tags, zero invalid self-closing elements, zero unescaped JSX characters, zero client-JS bloat on static marketing surfaces, and strict tone alternation (surface/soft) across homepage bands.
Constraints: Read-only audit; do not edit production code. Flag all syntax violations, hydration misalignments, and missing bilingual alternates.
Autonomy Grant: You own this mission end-to-end. Explore freely, analyze DOM structures, inspect component trees, and verify facts directly against source code. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

Focus strictly on Core Marketing templates and homepage bands.
Check each component line-by-line for:

1. Strict tag closure: Ensure all tags like `<span>`, `<button>`, `<div>`, and `<script>` have explicit matching closing tags.
2. Band order & tone mapping: Check against `src/features/homepage/components/layout.ts` (`HOMEPAGE_TONE_CLASS`).

3. Zero-JS & Hydration Pruning:
   Static marketing components must never drag React or framework runtimes to the browser.

```astro
<!-- ❌ Bad Practice: Hydrating static marketing elements with client:load (ships 45KB–100KB+ framework runtime) -->
<MarketingHero client:load title="Enterprise Search" subtitle="Leading Organic Growth" />
<AwardsShowcase client:load />

<!-- ✅ Best Practice: Pure .astro component compiled to static HTML (0 KB client JavaScript shipped) -->
<MarketingHero title="Enterprise Search" subtitle="Leading Organic Growth" />
<AwardsShowcase />
```

4. Style Scoping & Encapsulation:
   Component styles must remain strictly isolated. Do not leak global specificity into unrelated pages.

```astro
<!-- ❌ Bad Practice: Indiscriminate global styles polluting global specificity and other components -->
<style is:global>
  h2 { font-size: 2.5rem; color: #1E2038; margin-bottom: 1.5rem; }
  .card { padding: 2rem; border-radius: 4px; }
</style>

<!-- ✅ Best Practice: Native scoped styles compiled to unique data-astro-cid attributes -->
<style>
  h2 { font-size: 2.5rem; color: var(--color-ink); margin-bottom: 1.5rem; }
  .card { padding: 2rem; border-radius: var(--radius-sm); }
</style>
```

5. Pure HTML Templates & Event Handlers (No Virtual DOM):
   Astro templates run once on the server. JSX event handlers (`onClick`, `onChange`) do not function in `.astro` files.

```astro
<!-- ❌ Bad Practice: Treating .astro like React with inline JSX event handlers or frontmatter state -->
---
let isOpen = false;
function toggleMenu() { isOpen = !isOpen; }
---
<button onClick={toggleMenu}>Menu</button>
{isOpen && <nav>...</nav>}

<!-- ✅ Best Practice: Native Web Component with encapsulated script or pure CSS toggle -->
<site-nav-toggle>
  <button type="button" aria-expanded="false" data-nav-btn>Menu</button>
  <nav hidden data-nav-menu>...</nav>
</site-nav-toggle>
<script>
  class SiteNavToggle extends HTMLElement {
    connectedCallback() {
      const btn = this.querySelector('[data-nav-btn]');
      const menu = this.querySelector('[data-nav-menu]');
      btn?.addEventListener('click', () => {
        const expanded = btn.getAttribute('aria-expanded') === 'true';
        btn.setAttribute('aria-expanded', String(!expanded));
        menu?.toggleAttribute('hidden', expanded);
      });
    }
  }
  customElements.define('site-nav-toggle', SiteNavToggle);
</script>
```

6. Rest Parameter Catch-All Contracts:
   Root and catch-all routes must explicitly return `undefined` to match the root route segment.

```astro
---
// src/pages/[...home].astro
export async function getStaticPaths() {
  return [
    // ❌ Bad Practice: Passing "" or "/" causes routing ambiguity or build-time 404s
    // { params: { home: "" } },
    // { params: { home: "/" } },

    // ✅ Best Practice: Explicitly return undefined to match the root route segment
    { params: { home: undefined }, props: { lang: "tr" } },
    { params: { home: "en" }, props: { lang: "en" } },
    { params: { home: "ar" }, props: { lang: "ar" } },
  ];
}
---
```

7. Client Router SPA Analytics:
   Always track pageviews using the `astro:page-load` lifecycle event.

```html
<!-- ❌ Bad Practice: Standard window load script loses subsequent SPA route changes -->
<script>
  window.addEventListener('load', () => {
    gtag('event', 'page_view', { page_path: window.location.pathname })
  })
</script>

<!-- ✅ Best Practice: Track on astro:page-load lifecycle to ensure title and DOM are committed -->
<script>
  document.addEventListener('astro:page-load', () => {
    gtag('event', 'page_view', {
      page_title: document.title,
      page_location: window.location.href,
      page_path: window.location.pathname,
    })
  })
</script>
```

8. Asset loading: Ensure hero images use responsive presets and background art avoids layout jumps.
9. Multilingual alternates: Verify EN, TR, and AR alternates in `getStaticPaths()` or page props.

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/01-templates-routing/01-core-marketing-and-homepage/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Rule ID Mapping**: Every defect recorded in `findings.json` must explicitly map to an authoritative Astro best practice rule identifier using the `rule_id` field (e.g. `RULE-ID: 01-architecture-and-philosophy/01-zero-js-by-default`, `RULE-ID: 01-architecture-and-philosophy/07-scoped-styles-encapsulation`, `RULE-ID: 01-architecture-and-philosophy/12-no-virtual-dom-in-astro-templates`, `RULE-ID: 03-routing-and-pages/02-rest-parameters-and-catch-all`, `RULE-ID: 03-routing-and-pages/21-track-pageviews-in-client-router-with-astro-page-load`).

You must create and populate the following deliverables in `docs/audits/results/01-templates-routing/01-core-marketing-and-homepage/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps. Every item MUST include a valid `rule_id` linking to `../../best-practices/`:

```json
[
  {
    "id": "01-CORE-MARKETING-AND-HOMEPAGE-001",
    "rule_id": "RULE-ID: 01-architecture-and-philosophy/01-zero-js-by-default",
    "file": "src/features/homepage/components/HeroSection.astro",
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
  --body "docs/audits/results/01-templates-routing/01-core-marketing-and-homepage/issue-body.md" \
  --title "[Audit - Core Marketing & Homepage Route Controller Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/01-templates-routing/01-core-marketing-and-homepage/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Run `pnpm vitest run tests/int/homepage-case-studies-showcase.test.ts` to verify homepage band order invariants.
2. Run `git grep -n "<span[ ]*/>\|<button[ ]*/>\|<template[ ]*/>" src/features/homepage/ src/features/company/` to prove zero illegal self-closing elements.
3. Run `git grep -n "client:load\|client:only\|client:idle" src/features/homepage/ src/features/company/` to verify zero unnecessary client runtime on static marketing bands.
4. Run `git grep -n "<style is:global>" src/features/homepage/ src/features/company/` to audit for global CSS specificity leaks.
5. Run `git grep -n "onClick=\|onChange=" src/pages/ src/features/homepage/ src/features/company/` to flag invalid JSX event handlers in `.astro` templates.
6. Run `find dist/ -name "*.js" -size +0c` and verify that static marketing routes emit zero client JavaScript chunks.
7. Validate that no marketing surface uses `font-mono` or `animate-pulse` badges.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/01-templates-routing/01-core-marketing-and-homepage/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Core Marketing & Homepage Route Controller Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/01-templates-routing/01-core-marketing-and-homepage/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/01-templates-routing/01-core-marketing-and-homepage/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/01-templates-routing/01-core-marketing-and-homepage/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/01-templates-routing/01-core-marketing-and-homepage/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/01-templates-routing/01-core-marketing-and-homepage/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
