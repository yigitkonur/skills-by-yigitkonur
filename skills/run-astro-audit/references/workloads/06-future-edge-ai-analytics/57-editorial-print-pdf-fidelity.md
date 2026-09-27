# Mission Brief: Editorial & Case Study Print / PDF Mode (@media print) Audit

## 3.0 Skills / Tools: view_file, run_command, craft-brand-theme.

## 3.1 Context Block

In enterprise B2B sales, executives, procurement officers, and technical leads frequently print (Cmd+P) or save articles, case studies, and service pillar pages as PDF to review internally.
Without dedicated print stylesheets, browsers attempt to print screen-oriented layouts:

- When Dark theme (`[data-theme="dark"]`) is active, background fills print as solid black/navy ink blocks, draining printer toner and destroying contrast.
- Fixed/sticky navigation headers, mega menus, search modals, cookie consent banners, and floating CTA buttons clutter the paper layout.
- Metric grids, quotes, and diagrams awkwardly slice across page boundaries when `break-inside: avoid` is omitted.
- Links lack target transparency unless expanded inline via `a[href^="http"]::after`.
  The application requires crisp Swiss monochrome print fidelity across editorial and proof surfaces.

### Astro Architectural & Best Practice Rules

All print media implementations, stylesheet bundles, and client lifecycle integrations must adhere to the authoritative best practices:

- [14-script-execution-mechanics-and-data-astro-rerun.md](../../best-practices/03-routing-and-pages/14-script-execution-mechanics-and-data-astro-rerun.md) — Script execution mechanics, bundled module scripts vs inline, and `data-astro-rerun` handling under ClientRouter navigation.
- [21-track-pageviews-in-client-router-with-astro-page-load.md](../../best-practices/03-routing-and-pages/21-track-pageviews-in-client-router-with-astro-page-load.md) — Reliable pageview tracking under ClientRouter, ensuring print dialog triggers or PDF export actions do not corrupt navigation analytics.
- [01-avoid-blanket-viewport-prefetching.md](../../best-practices/09-performance-prefetch-and-transitions/01-avoid-blanket-viewport-prefetching.md) — Avoiding blanket viewport prefetching on heavy routes and editorial archives.
- [03-configure-native-prefetch-engine.md](../../best-practices/09-performance-prefetch-and-transitions/03-configure-native-prefetch-engine.md) — Configuring native `prefetch` engine in `astro.config.mjs` (`prefetchAll: false`, `defaultStrategy: 'hover'`).
- [17-leverage-speculation-rules-client-prerendering.md](../../best-practices/09-performance-prefetch-and-transitions/17-leverage-speculation-rules-client-prerendering.md) — Speculation Rules API for sub-second client prerendering without memory limit exhaustion.
- [09-enforce-component-scoped-css.md](../../best-practices/09-performance-prefetch-and-transitions/09-enforce-component-scoped-css.md) — Enforcing component-scoped CSS while centralizing global `@media print` resets in `src/styles/globals.css`.
- [12-tune-css-bundle-control-and-asset-inlining.md](../../best-practices/09-performance-prefetch-and-transitions/12-tune-css-bundle-control-and-asset-inlining.md) — Tuning CSS bundle output to ensure critical print styles are bundled cleanly without render-blocking overhead.

Critical files to inspect:

- src/styles/globals.css (@media print)
- src/features/resources/components/ArticleDetailPage.astro
- src/features/proof/components/CaseStudyDetailPage.astro
- src/components/service-hierarchy/detail/ServiceDetailTemplate.astro

## 3.2 Mission Objective

Audit and design @media print stylesheets across editorial, case study, and service pages.
Outcome: Ensure that printing (Cmd+P) hides navigation, search, and footers, removes dark background fills, prints high-contrast typography on white paper, prevents page breaks inside metric cards, and displays external link URLs inline.
Constraints: Read-only audit; verify CSS print rules.
Autonomy Grant: You own this mission end-to-end. Design print media rules, page-break properties, and paper margins. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect src/styles/globals.css: search for existing @media print blocks and reset coverage.
2. Ensure header, footer, contact drawer, and floating buttons carry @media print { display: none !important; }.
3. Verify page-break-inside / break-inside: avoid on case study metrics cards, callouts, and figures.
4. Verify link URL expansion logic: ensure external links print destinations while internal fragments (#) are suppressed.

### ❌ Bad Practice / Anti-Pattern

```css
/* Missing print reset: dark theme background prints solid black ink; nav & buttons waste paper */
[data-theme='dark'] body {
  background: #0f111a;
  color: #fff;
}
/* No @media print rules or partial overrides leaving sticky nav visible */
.site-header {
  position: sticky;
  top: 0;
}
.metric-card {
  break-inside: auto; /* Slices metric numbers across page breaks */
}
/* Blanket link printing exposing internal anchors and JS stubs */
a::after {
  content: ' (' attr(href) ')';
} /* Prints: (#overview) or (javascript:void(0)) */
```

### ✅ Best Practice / Idiomatic

```css
/* src/styles/globals.css - Swiss monochrome print stylesheet */
@media print {
  *,
  *::before,
  *::after {
    background: transparent !important;
    color: #000 !important;
    box-shadow: none !important;
    text-shadow: none !important;
  }
  header,
  nav,
  footer,
  .sticky-nav,
  .cookie-banner,
  .floating-cta,
  [data-island],
  button {
    display: none !important;
  }
  article,
  .case-study-content {
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  .metric-card,
  .callout-box,
  blockquote,
  figure {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  h1,
  h2,
  h3 {
    break-after: avoid;
    page-break-after: avoid;
  }
  a[href^='http']::after {
    content: ' (' attr(href) ')';
    font-size: 0.85em;
    font-weight: normal;
  }
  a[href^='#']::after,
  a[href^='javascript:']::after {
    content: '';
  }
}
```

```astro
---
// src/components/PrintAction.astro - Print triggers respecting ClientRouter and prefetch invariants
---
<button id="print-article-btn" class="print-trigger" data-astro-prefetch="false">
  Print Article
</button>

<script>
  // Attach on astro:page-load so listener survives soft client navigations
  document.addEventListener('astro:page-load', () => {
    const printBtn = document.getElementById('print-article-btn');
    printBtn?.addEventListener('click', () => {
      window.print();
    });
  });
</script>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/06-future-edge-ai-analytics/57-editorial-print-pdf-fidelity/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Best Practice Mapping Requirement**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule (e.g. `RULE-ID: 03-14-script-execution-mechanics-and-data-astro-rerun`, `RULE-ID: 03-21-track-pageviews-in-client-router-with-astro-page-load`, `RULE-ID: 09-01-avoid-blanket-viewport-prefetching`, `RULE-ID: 09-03-configure-native-prefetch-engine`, `RULE-ID: 09-09-enforce-component-scoped-css`, `RULE-ID: 09-12-tune-css-bundle-control`, or `RULE-ID: 09-17-leverage-speculation-rules-client-prerendering`).

You must create and populate the following deliverables in `docs/audits/results/06-future-edge-ai-analytics/57-editorial-print-pdf-fidelity/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "57-EDITORIAL-PRINT-PDF-FIDELITY-001",
    "rule_id": "RULE-ID (e.g. 03-14-script-execution-mechanics-and-data-astro-rerun)",
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
   Execute the turnkey publisher script using `node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting (max 200 items, <= 3 levels deep), creates the primary issue, spawns linked sub-issues (up to 20) for critical/high defects, and pushes the JSON deliverables directly to `origin main` without PR:

```bash
# Turnkey Script (node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/06-future-edge-ai-analytics/57-editorial-print-pdf-fidelity/issue-body.md" \
  --title "[Audit - Editorial & Case Study Print / PDF Mode (@media print) Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/06-future-edge-ai-analytics/57-editorial-print-pdf-fidelity/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Verify that simulated print rendering produces a clean, readable A4 layout with zero clipped text.
2. Confirm zero black background blocks printed when Dark theme is active.
3. Audit print stylesheet coverage and prefetch interactions via terminal commands:

```bash
# Check existing print stylesheets in styles directory
grep -rn "@media print" src/styles/
# Audit components for unhidden interactive chrome in print mode
grep -rnE '(sticky|fixed|drawer|cookie|modal)' src/components/ src/layouts/
# Check page-break or break-inside rules on card components
grep -rnE '(break-inside|page-break-inside)' src/
# Audit for speculation rules and prefetch directives in templates
git grep -n "speculationrules" src/
git grep -n "data-astro-prefetch" src/
```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/06-future-edge-ai-analytics/57-editorial-print-pdf-fidelity/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Editorial & Case Study Print / PDF Mode (@media print) Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/06-future-edge-ai-analytics/57-editorial-print-pdf-fidelity/findings.json` (N defects logged)
   - `file://docs/audits/results/06-future-edge-ai-analytics/57-editorial-print-pdf-fidelity/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/06-future-edge-ai-analytics/57-editorial-print-pdf-fidelity/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/06-future-edge-ai-analytics/57-editorial-print-pdf-fidelity/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/06-future-edge-ai-analytics/57-editorial-print-pdf-fidelity/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
