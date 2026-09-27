# Mission Brief: WCAG 2.2 AAA Accessibility & Windows Forced Colors Audit

## 3.0 Skills / Tools: view_file, run_command, accessibility.

## 3.1 Context Block

The application adheres to WCAG 2.2 accessibility standards:

- Keyboard navigation: visible focus rings (`:focus-visible`), skip-to-content links (`SkipLink.astro`), and escape key drawer closing.
- Screen reader landmarks: proper `<main>`, `<header>`, `<footer>`, `<nav>`, and `role="dialog"` with `aria-modal="true"` and `aria-labelledby`.
- Color contrast: minimum 4.5:1 for normal text (AA) and 7:1 (AAA) across both Light and Dark themes.
- Windows High Contrast / Forced Colors: Enterprise clients on corporate Windows machines frequently use Forced Colors mode. Custom CSS custom properties are overridden by system colors, so backgrounds, borders, and button labels must remain fully legible under `@media (forced-colors: active)`.
- Production Preview Audit Rule: Automated accessibility scans (`@axe-core/cli`, Pa11y, Playwright) must run exclusively against the production preview server (`pnpm build && pnpm preview`), NEVER against `astro dev`. Vite's dev server injects unminified HMR scripts and the Astro Dev Toolbar DOM overlay, generating false-positive accessibility failures and DOM hierarchy violations.
- Dev Toolbar Audit Feedback: During local development, the built-in Astro Dev Toolbar Audit app provides immediate feedback for missing `alt` attributes, heading hierarchy errors, and broken links, complementing CI-based axe scans.

### Authoritative Astro Architectural & Best Practice Rules

Every finding, keyboard navigation contract, and ARIA state audit in this mission must strictly align with the authoritative rules in `../../best-practices`:

- [`05-run-built-in-a11y-audits-with-dev-toolbar.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/05-run-built-in-a11y-audits-with-dev-toolbar.md) — Built-in Dev Toolbar accessibility audits and keyboard focus order (`RULE-ID: 10-auditing-testing-and-nextjs-migration/05-run-built-in-a11y-audits-with-dev-toolbar`).
- [`06-enforce-astro-check-quality-gate-in-ci.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/06-enforce-astro-check-quality-gate-in-ci.md) — Enforcing `astro check` type validation and template linting in CI (`RULE-ID: 10-auditing-testing-and-nextjs-migration/06-enforce-astro-check-quality-gate-in-ci`).
- [`10-inject-security-headers-and-csp.md`](../../best-practices/06-middleware-and-auth/10-inject-security-headers-and-csp.md) — Enforcing CSP Level 3 compatibility with focus rings, high-contrast style fallbacks, and dialog modals (`RULE-ID: 06-middleware-and-auth/10-inject-security-headers-and-csp`).
- [`11-server-secrets-astro-env.md`](../../best-practices/06-middleware-and-auth/11-server-secrets-astro-env.md) — Type-safe server secrets via `astro:env/server`, ensuring interactive accessibility widgets do not leak environment secrets (`RULE-ID: 06-middleware-and-auth/11-server-secrets-astro-env`).
- [`19-avoid-consuming-streaming-response-body-in-middleware.md`](../../best-practices/06-middleware-and-auth/19-avoid-consuming-streaming-response-body-in-middleware.md) — Preserving streaming HTML so assistive technologies and screen readers receive early page landmarks without buffering delays (`RULE-ID: 06-middleware-and-auth/19-avoid-consuming-streaming-response-body-in-middleware`).

Critical files to inspect:

- `src/components/SkipLink.astro`
- `src/components/chrome/SiteHeader.astro`
- `src/components/chrome/ContactDrawer.astro`
- `src/components/chrome/MegaMenu.astro`
- `src/styles/globals.css` (`:focus-visible` and `forced-colors` styling)
- `astro.config.mjs`
- `package.json`

## 3.2 Mission Objective

Execute an exhaustive accessibility audit across core layouts, interactive navigation surfaces, and high-contrast modes.
Outcome: Prove zero keyboard traps, 100% accessible modal focus management, valid ARIA labels on all icon buttons, compliant color contrast in both themes, full legibility in Windows Forced Colors mode, body scroll lock during open modals, and minimum 48x48px mobile touch targets.
Constraints: Read-only audit; inspect DOM attributes, focus listeners, and keyboard event handling.
Autonomy Grant: You own this mission end-to-end. Test keyboard tab sequences, screen reader trees, and contrast ratios. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `SkipLink.astro`: ensure it is the very first focusable element on every page and moves focus to `#main-content`.
2. Inspect `ContactDrawer.astro` and `MegaMenu.astro`: ensure opening locks background scroll and traps keyboard Tab navigation within the modal.
3. Check `@media (forced-colors: active)` rules: ensure borders, buttons, and icons remain visible with `CanvasText` and `ButtonText` system colors.
4. Audit mobile tap targets: ensure all navigation links, buttons, and drawer icons meet Apple/Google 48x48px minimum hit target size.
5. Verify `astro.config.mjs`: confirm `devToolbar` is enabled for local developer auditing.

### Executable AST & Grep Audit Commands

Run these commands to inspect accessibility attributes, keyboard handlers, and toolbar settings:

```bash
# Audit for non-semantic clickable elements lacking keyboard accessibility:
git grep -rnE "on(click|keydown)=" src/components/ | grep -vE "(<button|<a|<input)"
# Audit for icon buttons missing aria-label:
git grep -rn "<button" src/components/ | grep -v "aria-label"
# Check devToolbar configuration in astro.config.mjs:
git grep -n "devToolbar" astro.config.mjs
# Audit skip link presence and target ID in layout files:
git grep -n "SkipLink" src/layouts/
git grep -n 'id="main-content"' src/
# Run axe-core CLI accessibility scan against production preview:
npx @axe-core/cli http://localhost:8788 --exit
# Run Playwright accessibility tests:
pnpm exec playwright test tests/e2e/a11y.spec.ts
```

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Non-Semantic Interactive Triggers vs Native Accessible Buttons (RULE-ID: 10-auditing-testing-and-nextjs-migration/05-run-built-in-a11y-audits-with-dev-toolbar)

##### ❌ Bad Practice / Anti-Pattern

```astro
<!-- src/components/chrome/SiteHeader.astro - Accessibility Anti-patterns -->
<!-- BAD: Non-semantic div, missing keyboard listener, missing ARIA state, focus outline stripped -->
<div class="nav-toggle" onclick="toggleMenu()">
  <svg class="h-6 w-6"><path d="M4 6h16M4 12h16M4 18h16"></path></svg>
</div>

<style>
  /* BAD: Removing focus ring breaks keyboard navigation completely */
  .nav-toggle:focus { outline: none; }
</style>
```

_Why this fails:_ Non-semantic `<div>` elements are invisible to screen reader tab orders, cannot be activated via Enter or Space, lack `aria-expanded` state communication, and stripping focus rings strands keyboard users.

##### ✅ Best Practice / Idiomatic

```astro
<!-- src/components/chrome/SiteHeader.astro - Accessible interactive trigger -->
<button
  type="button"
  aria-label="Toggle navigation menu"
  aria-expanded="false"
  aria-controls="mobile-menu"
  class="inline-flex min-h-[48px] min-w-[48px] items-center justify-center rounded focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
>
  <svg aria-hidden="true" focusable="false" class="h-6 w-6"><path d="M4 6h16M4 12h16M4 18h16"></path></svg>
</button>

<style>
  /* Windows Forced Colors mode fallback */
  @media (forced-colors: active) {
    button {
      border: 1px solid ButtonText;
    }
  }
</style>
```

#### Pattern 2: Disabling Astro Dev Toolbar Globally (RULE-ID: 10-auditing-testing-and-nextjs-migration/05-run-built-in-a11y-audits-with-dev-toolbar)

##### ❌ Bad Practice / Anti-Pattern

```javascript
// astro.config.mjs - Disabling dev toolbar globally hides instant a11y audits
import { defineConfig } from 'astro/config'

export default defineConfig({
  devToolbar: {
    // BAD: Completely disables Audit and Inspect apps during development
    enabled: false,
  },
})
```

_Why this fails:_ Disabling the Dev Toolbar eliminates the fastest developer feedback loop for template-level a11y defects (missing image alt text, heading hierarchy violations, empty links).

##### ✅ Best Practice / Idiomatic

```javascript
// astro.config.mjs - Keep devToolbar enabled; configure per-user via preferences
import { defineConfig } from 'astro/config'

export default defineConfig({
  // Dev toolbar remains active for real-time Audit and Inspect feedback
  devToolbar: {
    enabled: true,
  },
})
```

#### Pattern 3: Skipping astro check in CI Pipelines (RULE-ID: 10-auditing-testing-and-nextjs-migration/06-enforce-astro-check-quality-gate-in-ci)

##### ❌ Bad Practice / Anti-Pattern

```json
// package.json - INCORRECT: tsc ignores .astro files, leaving broken a11y props
{
  "scripts": {
    "typecheck": "tsc --noEmit",
    "build": "astro build",
    "ci": "npm run typecheck && npm run build"
  }
}
```

_Why this fails:_ `tsc --noEmit` ignores `.astro` component files. Template prop errors, missing mandatory ARIA props, or invalid element attributes pass silently into production.

##### ✅ Best Practice / Idiomatic

```json
// package.json - CORRECT: astro check validates .astro files and catches template defects
{
  "scripts": {
    "typecheck": "astro check --minimumFailingSeverity error",
    "build": "astro check && astro build",
    "ci": "astro check --minimumFailingSeverity error && astro build"
  }
}
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/05-edge-workers-and-qa/46-wcag-22-aaa-accessibility/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g., `RULE-ID: 10-auditing-testing-and-nextjs-migration/05-run-built-in-a11y-audits-with-dev-toolbar`, `RULE-ID: 10-auditing-testing-and-nextjs-migration/06-enforce-astro-check-quality-gate-in-ci`, `RULE-ID: 06-middleware-and-auth/10-inject-security-headers-and-csp`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/05-edge-workers-and-qa/46-wcag-22-aaa-accessibility/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "46-WCAG-22-AAA-ACCESSIBILITY-001",
    "rule_id": "RULE-ID: 10-auditing-testing-and-nextjs-migration/05-run-built-in-a11y-audits-with-dev-toolbar",
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
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/05-edge-workers-and-qa/46-wcag-22-aaa-accessibility/issue-body.md" \
  --title "[Audit - WCAG 2.2 AAA Accessibility & Windows Forced Colors Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/05-edge-workers-and-qa/46-wcag-22-aaa-accessibility/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Run `astro check` to validate template accessibility attributes and prop typing:
   ```bash
   pnpm exec astro check --minimumFailingSeverity error
   ```
2. Audit the production preview build using axe-core CLI to ensure zero automated violations:
   ```bash
   pnpm build && npx @axe-core/cli http://localhost:8788 --exit
   ```
3. Run Playwright accessibility tests for keyboard navigation and modal focus trapping:
   ```bash
   pnpm exec playwright test tests/e2e/a11y.spec.ts
   ```
4. Verify CSP headers on preview server do not block accessibility styles or inline focus rings:
   ```bash
   curl -I http://localhost:4321/
   ```
5. Verify zero missing `aria-label` errors on interactive buttons and icon triggers:
   ```bash
   git grep -rn '<button' src/components/ | grep -v 'aria-label'
   ```
6. Confirm contrast ratios meet WCAG 2.2 AA (and AAA where applicable) in both Light and Dark themes, as well as Windows Forced Colors mode (`@media (forced-colors: active)`).
7. Verify that Tab navigation from page top lands directly on `SkipLink.astro` and skips to `#main-content`.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/05-edge-workers-and-qa/46-wcag-22-aaa-accessibility/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** WCAG 2.2 AAA Accessibility & Windows Forced Colors Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/05-edge-workers-and-qa/46-wcag-22-aaa-accessibility/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/05-edge-workers-and-qa/46-wcag-22-aaa-accessibility/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/05-edge-workers-and-qa/46-wcag-22-aaa-accessibility/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/05-edge-workers-and-qa/46-wcag-22-aaa-accessibility/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/05-edge-workers-and-qa/46-wcag-22-aaa-accessibility/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
