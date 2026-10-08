# Mission Brief: Swiss Design System Tokens & Anti-Slop Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

Non-negotiable design system invariants:

- Zero synthetic pulsing-dot pill badges (`animate-pulse`).
- Zero glowing status dot chips.
- Zero developer monospace fonts (`font-mono`) on marketing surfaces.
- Zero boxed quote/text wrappers (`border border-...`).
- Strictly TWO border-radius tokens: `rounded` (4px) and `rounded-full` (9999px). Any `rounded-md`, `rounded-lg`, `rounded-xl`, `rounded-2xl`, or `rounded-3xl` is a direct violation.
- Understated Swiss typographic hierarchy (`font-gilroy`, `font-akagi`) and deliberate negative space.
- Tailwind CSS v4 Engine: Powered by `@tailwindcss/vite` native compiler plugin without legacy `@astrojs/tailwind` or PostCSS wrappers. All tokens are defined CSS-first via `@theme` in `src/styles/globals.css`.
- Scoped Styling Purity: Component styles in `.astro` files must rely on Astro's zero-runtime `data-astro-cid-[hash]` build-time scoping. Unscoped `<style is:global>` in leaf components is strictly prohibited to prevent site-wide CSS cascade pollution; child slot styling must use the `:global()` pseudo-selector nested within a scoped selector.

### Authoritative Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`07-scoped-styles-encapsulation.md`](../../best-practices/01-architecture-and-philosophy/07-scoped-styles-encapsulation.md) — Build-time scoped CSS encapsulation and preventing global style cascading leaks sitewide (`RULE-ID: 01-architecture-and-philosophy/07-scoped-styles-encapsulation`).
- [`09-enforce-component-scoped-css.md`](../../best-practices/09-performance-prefetch-and-transitions/09-enforce-component-scoped-css.md) — Enforcing component-scoped CSS over runtime CSS-in-JS and loose utility classes (`RULE-ID: 09-performance-prefetch-and-transitions/09-enforce-component-scoped-css`).
- [`10-isolate-is-global-and-use-global-pseudo-selector.md`](../../best-practices/09-performance-prefetch-and-transitions/10-isolate-is-global-and-use-global-pseudo-selector.md) — Isolating `:global()` pseudo-selectors within component roots instead of `<style is:global>` (`RULE-ID: 09-performance-prefetch-and-transitions/10-isolate-is-global-and-use-global-pseudo-selector`).
- [`13-migrate-to-tailwind-v4-vite-plugin.md`](../../best-practices/09-performance-prefetch-and-transitions/13-migrate-to-tailwind-v4-vite-plugin.md) — Tailwind v4 CSS-first design token architecture via `@tailwindcss/vite` (`RULE-ID: 09-performance-prefetch-and-transitions/13-migrate-to-tailwind-v4-vite-plugin`).
- [`15-migrate-css-in-js-to-scoped-css-and-tailwind.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/15-migrate-css-in-js-to-scoped-css-and-tailwind.md) — Eliminating CSS-in-JS runtimes and migrating Next.js styling to static Tailwind/scoped CSS (`RULE-ID: 10-auditing-testing-and-nextjs-migration/15-migrate-css-in-js-to-scoped-css-and-tailwind`).
- [`01-audit-against-production-preview-never-dev.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/01-audit-against-production-preview-never-dev.md) — Auditing layout and visual design tokens against production builds, never dev server (`RULE-ID: 10-auditing-testing-and-nextjs-migration/01-audit-against-production-preview-never-dev`).
- [`04-audit-island-boundaries-with-dev-toolbar-inspect.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/04-audit-island-boundaries-with-dev-toolbar-inspect.md) — Inspecting island boundaries and container render fidelity (`RULE-ID: 10-auditing-testing-and-nextjs-migration/04-audit-island-boundaries-with-dev-toolbar-inspect`).

Critical files to inspect:

- `src/styles/globals.css`
- `src/components/`
- `src/features/`
- `astro.config.mjs`
- `package.json`

## 3.2 Mission Objective

Scan the entire codebase for design system token purity and anti-slop violations.
Outcome: Prove zero prohibited utility classes (animate-pulse, arbitrary border-radius, font-mono), verifying that all marketing surfaces adhere strictly to Swiss design purity, Tailwind v4 native Vite compilation, and encapsulated CSS scoping.
Constraints: Read-only audit; search CSS classes across all components.
Autonomy Grant: You own this mission end-to-end. Audit utility classes, token mappings, and typographic hierarchy. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Run `git grep -n "animate-pulse" src/` to prove zero instances.
2. Run `git grep -n "rounded-lg\|rounded-xl\|rounded-2xl" src/` and `git grep -rn -E "rounded-(md|lg|xl|2xl|3xl)" src/` to flag prohibited border-radius classes.
3. Check `font-mono` usage: ensure it is strictly confined to developer debug tools and code blocks.
4. Audit `<style is:global>`: ensure leaf components do not leak unscoped CSS into global stylesheets.
5. Verify that `@tailwindcss/vite` is wired directly into `astro.config.mjs` and `@astrojs/tailwind` is removed.

### ❌ Bad Practice / Anti-Pattern (Arbitrary Border-Radius, Pulsing Dots & Monospace Slop)

```astro
<!-- src/components/FeatureCard.astro - Slop Anti-patterns from Next.js / Generic SaaS -->
<!-- ❌ BAD: Prohibited rounded-2xl, border-box wrapper, font-mono, and animate-pulse dot -->
<div class="rounded-2xl border border-slate-700 p-6 font-mono">
  <span class="inline-flex items-center gap-2 rounded-lg bg-pink-500/10 px-3 py-1">
    <span class="h-2 w-2 rounded-full bg-pink-500 animate-pulse"></span>
    LIVE PILOT
  </span>
  <h2 class="mt-4 font-mono text-xl text-slate-100">AI Analytics Matrix</h2>
</div>

<!-- ❌ BAD: Leaking global h2 styles across the entire application -->
<style is:global>
  h2 { font-size: 2rem; color: #f5265e; }
</style>
```

_Why this fails:_ Pulsing dots, arbitrary border-radius tokens (`rounded-2xl`, `rounded-lg`), and monospace fonts on marketing cards violate understated Swiss aesthetics. `<style is:global>` leaks rules sitewide, mutating unrelated page typography and breaking component encapsulation.

### ✅ Best Practice / Idiomatic (Strict Swiss Tokens & Scoped Styles)

```astro
---
// src/components/FeatureCard.astro - Swiss Design System Purity
interface Props {
  badge: string;
  title: string;
}
const { badge, title } = Astro.props;
---
<!-- ✅ BEST PRACTICE: Strictly 2 radius tokens (rounded = 4px, rounded-full = 9999px), understated typography -->
<div class="rounded bg-surface-subtle p-8 font-gilroy text-text-primary">
  <span class="inline-flex items-center rounded-full bg-surface-contrast px-3 py-1 text-xs tracking-tight">
    {badge}
  </span>
  <h2 class="mt-4 font-akagi text-2xl font-bold tracking-tight">{title}</h2>
  <slot />
</div>

<!-- Scoped CSS with zero runtime JS; using :global() nested strictly within component root -->
<style>
  div :global(p) {
    line-height: 1.6;
    color: var(--color-text-secondary);
  }
</style>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/05-edge-workers-and-qa/47-swiss-design-tokens-purity/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: 01-architecture-and-philosophy/07-scoped-styles-encapsulation`, `RULE-ID: 09-performance-prefetch-and-transitions/09-enforce-component-scoped-css`, `RULE-ID: 09-performance-prefetch-and-transitions/13-migrate-to-tailwind-v4-vite-plugin`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/05-edge-workers-and-qa/47-swiss-design-tokens-purity/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "47-SWISS-DESIGN-TOKENS-PURITY-001",
    "rule_id": "RULE-ID: 01-architecture-and-philosophy/07-scoped-styles-encapsulation",
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
   Execute the turnkey publisher script `scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting (<= 200 items, max 3 levels deep), creates the primary issue, spawns linked sub-issues (up to 20) for critical and high severity defects, and commits/pushes results directly to `main` without PR:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
# node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/05-edge-workers-and-qa/47-swiss-design-tokens-purity/issue-body.md" \
  --title "[Audit - Swiss Design System Tokens & Anti-Slop Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/05-edge-workers-and-qa/47-swiss-design-tokens-purity/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Run `git grep -n "animate-pulse" src/` to prove zero pulsing badges across marketing surfaces.
2. Run `git grep -n "rounded-lg\|rounded-xl\|rounded-2xl" src/` and `git grep -rn -E "rounded-(md|lg|xl|2xl|3xl)" src/` to verify compliance with the 2-radius scale.
3. Run `grep -rn '<style is:global>' src/components/` to verify zero unscoped global styles in leaf components.
4. Run `git grep -rn "font-mono" src/components/ src/pages/` to confirm monospace font is absent from marketing surfaces.
5. Verify `@tailwindcss/vite` is in `package.json` and `@astrojs/tailwind` is completely removed:
   `grep -E '@(astrojs/tailwind|tailwindcss/vite)' package.json`
6. Verify documentation and design system integrity:
   `pnpm check:doc-integrity`
7. Run visual regression check against preview server:
   `pnpm vitest run tests/int/visual-regression.test.ts`

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/05-edge-workers-and-qa/47-swiss-design-tokens-purity/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Swiss Design System Tokens & Anti-Slop Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/05-edge-workers-and-qa/47-swiss-design-tokens-purity/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/05-edge-workers-and-qa/47-swiss-design-tokens-purity/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/05-edge-workers-and-qa/47-swiss-design-tokens-purity/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/05-edge-workers-and-qa/47-swiss-design-tokens-purity/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/05-edge-workers-and-qa/47-swiss-design-tokens-purity/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
