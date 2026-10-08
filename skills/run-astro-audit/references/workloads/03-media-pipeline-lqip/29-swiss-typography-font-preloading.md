# Mission Brief: Swiss Typography, localized secondary locale Fonts & Unicode-Range Slicing Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

The project's visual identity is strictly grounded in understated Swiss typographic hierarchy:

- Primary Sans: font-gilroy (Gilroy Bold, SemiBold, Medium, Regular).
- Secondary Sans: font-akagi (Akagi Pro).
- Zero developer monospace fonts (font-mono) on marketing surfaces.
  Fonts are self-hosted in WOFF2 format with immutable caching (`Cache-Control: public, max-age=31536000, immutable`).

Key Astro Best Practice contracts for typography and performance:

1. **Critical Font Preloading**: Preload strictly the single critical 400-weight WOFF2 file required for above-the-fold body text. Preloading multiple font weights (400, 600, 700, italics) saturates network pipelines and starves critical HTML/CSS execution.
2. **Eradicate Font CLS with Metric Overrides**: When custom web fonts load with `font-display: swap`, fallback fonts cause severe Cumulative Layout Shift (CLS). Calibrated `@font-face` fallbacks using `size-adjust`, `ascent-override`, `descent-override`, and `line-gap-override` force system fallbacks (e.g. Arial) to match the custom font's exact bounding box.
3. **Unicode-Range Slicing**: With localized secondary locale language support (`/ar/*`), localized secondary locale font glyphs must be served efficiently using CSS `unicode-range` slicing (`U+0600-06FF` for localized secondary locale, `U+0100-017F` for localized primary locale Latin-Extended), preventing English visitors from downloading unnecessary glyph bytes.

Astro Architectural & Best Practice Rules:

- **Self-Host Web Fonts and Preload Critical Above-the-Fold WOFF2 ([09-self-host-and-preload-critical-web-fonts.md](../../best-practices/07-assets-and-image-pipeline/09-self-host-and-preload-critical-web-fonts.md))**: Preload strictly the single critical 400-weight WOFF2 file required for above-the-fold body text in `<head>`. Preloading multiple font weights (400, 600, 700, italics) saturates network queues and delays critical CSS/HTML execution. External font CDNs (Google Fonts) are strictly prohibited.
- **Eradicate Font CLS with size-adjust and Metric Overrides ([10-eliminate-font-cls-with-metric-overrides.md](../../best-practices/07-assets-and-image-pipeline/10-eliminate-font-cls-with-metric-overrides.md))**: Custom web fonts with `font-display: swap` must define fallback `@font-face` rules with calibrated metric overrides (`size-adjust`, `ascent-override`, `descent-override`, `line-gap-override`) so system fallbacks (Arial) match the custom font bounding box with zero layout reflow (CLS = 0).
- **Optimize Largest Contentful Paint (LCP) with Static Heroes ([14-optimize-largest-contentful-paint-lcp.md](../../best-practices/09-performance-prefetch-and-transitions/14-optimize-largest-contentful-paint-lcp.md))**: Critical typography and headings in hero sections must render as pure zero-JS static HTML, enabling instant browser font shaping and sub-1.2s LCP.
- **Prevent Cumulative Layout Shift (CLS) Across Media and Islands ([16-prevent-cumulative-layout-shift-cls.md](../../best-practices/09-performance-prefetch-and-transitions/16-prevent-cumulative-layout-shift-cls.md))**: Typography containers and text wrappers must preserve exact layout dimensions across hydration and font swaps.

Critical files to inspect:

- `config/fonts.mjs`
- `src/styles/globals.css`
- `src/layouts/SiteLayout.astro`
- `public/fonts/`

## 3.2 Mission Objective

Audit font definitions, @font-face declarations, preload links, and typographic token usage.
Outcome: Ensure self-hosted WOFF2 fonts load with zero layout shift (CLS: 0), preload links strictly prioritize the single critical body font weight, localized secondary locale glyphs are cleanly subsetted with `unicode-range` to save bandwidth on non-localized secondary locale pages, and no marketing surface uses `font-mono`.
Constraints: Read-only audit; inspect CSS font stacks, `@font-face` rules, and network waterfalls.
Autonomy Grant: You own this mission end-to-end. Analyze font metrics, unicode ranges, and preload headers. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `config/fonts.mjs` and `src/layouts/SiteLayout.astro`: verify font preloading configuration and ensure only the primary body font is preloaded.
2. Audit `src/styles/globals.css`: verify metric-override `@font-face` rules matching Gilroy and Akagi dimensions.
3. Run `git grep "font-mono" src/` and verify it appears only in developer debug tools, never in marketing copy.
4. Check font subsetting: verify that Latin, Latin-Extended (localized primary locale), and localized secondary locale character sets are cleanly separated by `unicode-range`.

### ❌ Bad Practice / Anti-Pattern (External Google Fonts & Multi-Weight Preloading)

```html
<!-- ❌ Anti-Pattern: External font CDN with render-blocking CSS and multiple preloaded weights -->
<head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link
    rel="stylesheet"
    href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap"
  />
  <link rel="preload" href="/fonts/Gilroy-Regular.woff2" as="font" type="font/woff2" crossorigin />
  <link rel="preload" href="/fonts/Gilroy-Bold.woff2" as="font" type="font/woff2" crossorigin />
  <link rel="preload" href="/fonts/Gilroy-SemiBold.woff2" as="font" type="font/woff2" crossorigin />
</head>
```

### ✅ Best Practice / Idiomatic (Self-Hosted WOFF2 with Single Critical Preload)

```html
<!-- ✅ Idiomatic: Self-hosted WOFF2 preloading strictly the single 400-weight body font -->
<head>
  <link rel="preload" href="/fonts/Gilroy-Regular.woff2" as="font" type="font/woff2" crossorigin />
</head>
```

### ❌ Bad Practice / Anti-Pattern (Uncalibrated System Fallback Causing Font CLS)

```css
/* ❌ Anti-Pattern: Uncalibrated system fallback triggers severe layout shifts upon font arrival */
@font-face {
  font-family: 'Gilroy';
  src: url('/fonts/Gilroy-Regular.woff2') format('woff2');
  font-display: swap;
}
body {
  font-family: 'Gilroy', Arial, sans-serif; /* Jarring reflow when Gilroy swaps! */
}
```

### ✅ Best Practice / Idiomatic (Calibrated Metric-Override Fallback Matching Custom Font Bounding Box)

```css
/* ✅ Calibrated fallback font matches Gilroy bounding box to achieve 0 CLS */
@font-face {
  font-family: 'Gilroy-Fallback';
  src: local('Arial');
  ascent-override: 92.5%;
  descent-override: 23.1%;
  line-gap-override: 0%;
  size-adjust: 104.2%;
}
@font-face {
  font-family: 'Gilroy';
  src: url('/fonts/Gilroy-Regular.woff2') format('woff2');
  font-display: swap;
  unicode-range: U+0000-00FF, U+0100-017F; /* Latin + localized primary locale Latin-Extended */
}
body {
  font-family: 'Gilroy', 'Gilroy-Fallback', sans-serif;
}
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/03-media-pipeline-lqip/29-swiss-typography-font-preloading/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Rule ID Mapping**: All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an authoritative Astro best practice rule (e.g. `ASTRO-BP-07-09`, `ASTRO-BP-07-10`, `ASTRO-BP-09-14`, `ASTRO-BP-09-16`).

You must create and populate the following deliverables in `docs/audits/results/03-media-pipeline-lqip/29-swiss-typography-font-preloading/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "29-SWISS-TYPOGRAPHY-FONT-PRELOADING-001",
    "rule_id": "RULE-ID (e.g. ASTRO-BP-07-09 / ASTRO-BP-07-10 / ASTRO-BP-09-14 / ASTRO-BP-09-16)",
    "file": "path/to/file.ext",
    "line": 42,
    "severity": "critical" | "high" | "medium" | "low",
    "category": "syntax" | "hydration" | "parity" | "performance" | "security",
    "defect": "Precise description of what is broken or violating invariants (must reference RULE-ID)",
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
   Execute the turnkey publisher script using `node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting, creates the primary issue, spawns linked sub-issues (up to 20) for critical and high severity defects, and pushes the JSON deliverables directly to `origin main` without PR:

```bash
# Turnkey Script (node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/03-media-pipeline-lqip/29-swiss-typography-font-preloading/issue-body.md" \
  --title "[Audit - Swiss Typography, localized secondary locale Fonts & Unicode-Range Slicing Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/03-media-pipeline-lqip/29-swiss-typography-font-preloading/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Audit `<head>` preload hints: confirm strictly 1 critical WOFF2 font request is initiated (`grep -rn 'rel="preload"' src/layouts/SiteLayout.astro`).
2. Verify metric-override `@font-face` fallback definitions in `src/styles/globals.css` with `size-adjust` to eliminate CLS:
   ```bash
   grep -rn "size-adjust" src/styles/
   ```
3. Audit layout script and preloading directives:
   ```bash
   # Confirm preload directives in layouts
   git grep -n "preload" src/layouts/
   # Confirm synchronous inline execution in head
   git grep -n "is:inline" src/layouts/
   ```
4. Verify WOFF2 fonts are served with immutable cache headers (`Cache-Control: public, max-age=31536000, immutable`).
5. Confirm zero instances of `font-mono` on marketing surfaces:
   ```bash
   git grep "font-mono" src/pages/ src/components/
   ```
6. Confirm localized secondary locale unicode ranges (`U+0600-06FF`) are cleanly isolated in `@font-face` declarations.
7. Run automated font waterfall and layout stability checks:
   ```bash
   npx playwright test tests/e2e/font-waterfall.spec.ts || pnpm vitest run tests/int/font-preloads.test.ts
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/03-media-pipeline-lqip/29-swiss-typography-font-preloading/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Swiss Typography, localized secondary locale Fonts & Unicode-Range Slicing Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/03-media-pipeline-lqip/29-swiss-typography-font-preloading/findings.json` (N defects logged)
   - `file://docs/audits/results/03-media-pipeline-lqip/29-swiss-typography-font-preloading/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/03-media-pipeline-lqip/29-swiss-typography-font-preloading/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/03-media-pipeline-lqip/29-swiss-typography-font-preloading/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/03-media-pipeline-lqip/29-swiss-typography-font-preloading/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
