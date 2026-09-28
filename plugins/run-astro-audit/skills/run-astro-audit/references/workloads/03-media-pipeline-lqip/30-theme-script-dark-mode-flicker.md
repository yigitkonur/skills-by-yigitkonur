# Mission Brief: Dark Mode Flicker Prevention & ThemeScript Purity Audit

## 3.0 Skills / Tools: view_file, run_command, dark-mode-orchestrator.

## 3.1 Context Block

The application supports both Light and Dark modes seamlessly across all 3,897 routes.
To eliminate Flash of Unstyled Theme (FOUT / blinding white flash on dark mode reload), a synchronous inline script in `<head>` (`ThemeScript.astro`) reads `localStorage` and the `prefers-color-scheme` media query, applying the `[data-theme]` attribute and `.dark` class to `document.documentElement` BEFORE the body paints.

Key Astro Best Practice contracts for theme initialization:

1. **Synchronous Inline Script in `<head>`**: In Astro, client scripts (`<script>`) are bundled and deferred by default. Theme initialization MUST use `<script is:inline>` to execute synchronously during initial `<head>` parsing before CSS paints the first frame.
2. **Paired Tag Syntax**: In Astro 7, `ThemeScript.astro` must strictly use paired `<script is:inline>...</script>` tags to avoid parser serialization glitches.
3. **Zero Runtime Dependencies**: The inline script must have zero external imports, zero framework runtime overhead, and execute synchronously without waiting for `DOMContentLoaded` or `load` events.
4. **Cross-Tab & System Event Synchronization**: Storage events (`window.addEventListener('storage', ...)`) and system color scheme changes (`matchMedia('(prefers-color-scheme: dark)').addEventListener('change', ...)`) keep active tabs and OS toggles in sync.

Astro Architectural & Best Practice Rules:

- **Client Scripts & Synchronous Inline Execution ([08-client-scripts-over-ui-frameworks.md](../../best-practices/01-architecture-and-philosophy/08-client-scripts-over-ui-frameworks.md))**: Standard Astro `<script>` tags are bundled, deferred, and executed asynchronously. Early DOM initialization—specifically theme determination and dark mode class application—MUST use a synchronous, unbundled `<script is:inline>` in `<head>` before any stylesheet or body markup is processed, eliminating Flash of Unstyled Theme (FOUT) and white flash on reload.
- **Optimize Largest Contentful Paint (LCP) with Static Heroes ([14-optimize-largest-contentful-paint-lcp.md](../../best-practices/09-performance-prefetch-and-transitions/14-optimize-largest-contentful-paint-lcp.md))**: Theme initialization must never depend on React islands or client framework runtimes (`client:load`). Rendering the initial DOM and dark mode colors synchronously drives LCP below 1.2s with zero layout or style flashing.
- **Prevent Cumulative Layout Shift (CLS) Across Media and Islands ([16-prevent-cumulative-layout-shift-cls.md](../../best-practices/09-performance-prefetch-and-transitions/16-prevent-cumulative-layout-shift-cls.md))**: Theme transitions must alter color tokens without modifying font metrics, padding, or container dimensions that induce layout shifts.
- **Self-Host Web Fonts and Preload Critical Above-the-Fold WOFF2 ([09-self-host-and-preload-critical-web-fonts.md](../../best-practices/07-assets-and-image-pipeline/09-self-host-and-preload-critical-web-fonts.md))**: Ensure `<head>` script execution order does not interfere with critical font preloads.
- **Eradicate Font CLS with size-adjust and Metric Overrides ([10-eliminate-font-cls-with-metric-overrides.md](../../best-practices/07-assets-and-image-pipeline/10-eliminate-font-cls-with-metric-overrides.md))**: Confirm that theme switches do not alter font fallback metrics or cause font swaps.

Critical files to inspect:

- `src/components/ThemeScript.astro`
- `src/components/chrome/ThemeToggle.astro`
- `src/styles/globals.css` ([data-theme="dark"])
- `src/layouts/SiteLayout.astro`

## 3.2 Mission Objective

Audit `ThemeScript.astro`, the `ThemeToggle` component, and CSS custom property theme token cascades.
Outcome: Prove zero dark mode flicker on page reload, verify paired `<script is:inline></script>` syntax, and confirm smooth CSS color transitions without blocking page render.
Constraints: Read-only audit; test theme switching in both local storage states.
Autonomy Grant: You own this mission end-to-end. Profile early head script execution, theme storage keys, and CSS variables. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `ThemeScript.astro`: ensure it executes synchronously in `<head>` with zero external dependencies.
2. Verify that `[data-theme="dark"]` CSS custom properties cascade cleanly to all background and text colors without layout shifts.
3. Test theme toggle state synchronization across multiple open browser tabs and system preference shifts.
4. Contrast Next.js client-side theme providers (which flash white on SSR/hydration) with Astro's synchronous inline script architecture.

### ❌ Bad Practice / Anti-Pattern (Deferred Bundled Script or React useEffect Causing Dark Mode Flash)

```astro
---
// ❌ Anti-Pattern: Hydrating React or using deferred bundled script for theme
import ThemeProvider from '@/components/ThemeProvider.tsx';
---
<!-- React useEffect runs after paint: user sees jarring white flash in dark mode! -->
<ThemeProvider client:load />

<script>
  // Vite bundles this script into a deferred chunk executed asynchronously on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', () => {
    const theme = localStorage.getItem('theme') || 'light';
    document.documentElement.dataset.theme = theme;
  });
</script>
```

### ✅ Best Practice / Idiomatic (Synchronous is:inline Head Execution with Zero Framework Overhead)

```astro
---
// src/components/ThemeScript.astro (Canonical Astro synchronous inline head script)
---
<script is:inline>
  (function () {
    try {
      const stored = localStorage.getItem('theme');
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const theme = stored ? stored : (prefersDark ? 'dark' : 'light');
      document.documentElement.dataset.theme = theme;
      document.documentElement.classList.toggle('dark', theme === 'dark');
    } catch (_) {}
  })();
</script>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/03-media-pipeline-lqip/30-theme-script-dark-mode-flicker/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Rule ID Mapping**: All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an authoritative Astro best practice rule (e.g. `ASTRO-BP-01-08`, `ASTRO-BP-09-14`, `ASTRO-BP-09-16`, `ASTRO-BP-07-09`, `ASTRO-BP-07-10`).

You must create and populate the following deliverables in `docs/audits/results/03-media-pipeline-lqip/30-theme-script-dark-mode-flicker/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "30-THEME-SCRIPT-DARK-MODE-FLICKER-001",
    "rule_id": "RULE-ID (e.g. ASTRO-BP-01-08 / ASTRO-BP-09-14 / ASTRO-BP-09-16 / ASTRO-BP-07-09 / ASTRO-BP-07-10)",
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
  --body "docs/audits/results/03-media-pipeline-lqip/30-theme-script-dark-mode-flicker/issue-body.md" \
  --title "[Audit - Dark Mode Flicker Prevention & ThemeScript Purity Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/03-media-pipeline-lqip/30-theme-script-dark-mode-flicker/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Verify `ThemeScript.astro` carries paired `<script is:inline></script>` tags without bundling directives:
   ```bash
   grep -A 15 "<script is:inline>" src/components/ThemeScript.astro
   ```
2. Confirm `ThemeScript.astro` is positioned before stylesheets in `<head>` in `src/layouts/SiteLayout.astro`.
3. Audit layout script and preloading directives:
   ```bash
   # Confirm synchronous inline execution in head
   git grep -n "is:inline" src/layouts/
   # Confirm preload directives in layouts
   git grep -n "preload" src/layouts/
   ```
4. Verify CSS custom properties under `[data-theme="dark"]` in `src/styles/globals.css`:
   ```bash
   grep -rn '\[data-theme="dark"\]' src/styles/
   ```
5. Confirm zero white flash when reloading a dark-mode page on a fresh browser instance:
   ```bash
   pnpm vitest run tests/int/theme-script.test.ts || npx playwright test tests/e2e/dark-mode-flicker.spec.ts
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/03-media-pipeline-lqip/30-theme-script-dark-mode-flicker/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Dark Mode Flicker Prevention & ThemeScript Purity Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/03-media-pipeline-lqip/30-theme-script-dark-mode-flicker/findings.json` (N defects logged)
   - `file://docs/audits/results/03-media-pipeline-lqip/30-theme-script-dark-mode-flicker/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/03-media-pipeline-lqip/30-theme-script-dark-mode-flicker/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/03-media-pipeline-lqip/30-theme-script-dark-mode-flicker/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/03-media-pipeline-lqip/30-theme-script-dark-mode-flicker/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
