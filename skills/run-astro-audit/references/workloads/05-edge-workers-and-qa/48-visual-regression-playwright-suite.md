# Mission Brief: Visual Regression Playwright Suite & Frame Comparison Audit

## 3.0 Skills / Tools: view_file, run_command, audit-ui-ux.

## 3.1 Context Block

Visual iteration requires real browser frame captures across standard viewports:

- Desktop: 1280x900
- Mobile: 393x851
- Themes: Light (`[data-theme="light"]`) and Dark (`[data-theme="dark"]`).
- Production Preview vs Dev Server Law: Visual audits must execute against the production preview server (`pnpm build && pnpm preview`), NEVER against `astro dev`. Vite's dev server injects unbundled ESM, HMR WebSocket listeners (`/@vite/client`), unminified markup, and the Astro Dev Toolbar runtime (`astro/toolbar`). These dev-only injections alter layout geometry and trigger massive false-positive visual regressions.
- Container Automation Disciplines:
  1. NEVER use `waitUntil: 'networkidle'` (Vite's persistent HMR WebSocket prevents network idle). Always use `waitUntil: 'domcontentloaded'` and wait for specific DOM selectors.
  2. Always pass container-resilient flags (`--no-sandbox`, `--disable-setuid-sandbox`, `--disable-dev-shm-usage`, `--disable-gpu`).
  3. Freeze moving tickers (`*, *::before, *::after { animation: none !important; transition: none !important; }`) before taking screenshots to prevent diff false-positives.
  4. Enforce strict 60s global timeouts and explicit `process.exit(0)` / `process.exit(1)` handlers so background agent tasks never hang.

### Authoritative Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`01-audit-against-production-preview-never-dev.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/01-audit-against-production-preview-never-dev.md) — Auditing visual performance and layout strictly against production preview builds, never dev server (`RULE-ID: 10-auditing-testing-and-nextjs-migration/01-audit-against-production-preview-never-dev`).
- [`04-audit-island-boundaries-with-dev-toolbar-inspect.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/04-audit-island-boundaries-with-dev-toolbar-inspect.md) — Inspecting island boundaries and container render fidelity without layout shifts (`RULE-ID: 10-auditing-testing-and-nextjs-migration/04-audit-island-boundaries-with-dev-toolbar-inspect`).
- [`16-prevent-cumulative-layout-shift-cls.md`](../../best-practices/09-performance-prefetch-and-transitions/16-prevent-cumulative-layout-shift-cls.md) — Preventing cumulative layout shift across media, tickers, and hydrated islands (`RULE-ID: 09-performance-prefetch-and-transitions/16-prevent-cumulative-layout-shift-cls`).
- [`21-unit-test-components-with-astro-container-api.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/21-unit-test-components-with-astro-container-api.md) — Testing component render output and layout DOM in isolation using the Astro Container API (`RULE-ID: 10-auditing-testing-and-nextjs-migration/21-unit-test-components-with-astro-container-api`).
- [`07-scoped-styles-encapsulation.md`](../../best-practices/01-architecture-and-philosophy/07-scoped-styles-encapsulation.md) — Scoped CSS encapsulation and avoiding global style leaks affecting visual baselines (`RULE-ID: 01-architecture-and-philosophy/07-scoped-styles-encapsulation`).
- [`09-enforce-component-scoped-css.md`](../../best-practices/09-performance-prefetch-and-transitions/09-enforce-component-scoped-css.md) — Enforcing component-scoped CSS over loose utility classes (`RULE-ID: 09-performance-prefetch-and-transitions/09-enforce-component-scoped-css`).
- [`13-migrate-to-tailwind-v4-vite-plugin.md`](../../best-practices/09-performance-prefetch-and-transitions/13-migrate-to-tailwind-v4-vite-plugin.md) — Tailwind v4 CSS-first design token architecture (`RULE-ID: 09-performance-prefetch-and-transitions/13-migrate-to-tailwind-v4-vite-plugin`).

Critical files to inspect:

- `scripts/checks/qa/`
- `tests/visual/`
- `droid-wiki/agent-tools/09-visual-iteration-loop.md`
- `playwright.config.ts`

## 3.2 Mission Objective

Audit and calibrate the automated visual regression test suite.
Outcome: Ensure robust Playwright screenshot captures across all core page types in both themes and viewports, with zero flakiness from marquee animations or HMR WebSockets.
Constraints: Read-only audit; verify test scripts and container resilience.
Autonomy Grant: You own this mission end-to-end. Calibrate visual test timeouts, screenshot masks, and animation freezing styles. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect visual test scripts: verify that animation freezing CSS is injected before `page.screenshot()`.
2. Verify production preview target: ensure tests point to compiled preview servers (`port 8788`), not dev servers.
3. Ensure explicit timeouts (60s) and clean `process.exit(0)` handlers prevent background task hangs.
4. Check screenshot diffing thresholds (tolerance: 0.02) to ignore minor sub-pixel antialiasing differences.
5. Verify absence of `waitUntil: 'networkidle'` across all Playwright and test scripts.

### ❌ Bad Practice / Anti-Pattern (Testing Dev Server with networkidle & Unfrozen Marquees)

```typescript
// tests/visual/capture.test.ts - Flawed Playwright visual test
// Common blunder: Carrying over Next.js dev server testing patterns
import { test } from '@playwright/test'

test('audit homepage visual layout', async ({ page }) => {
  // ❌ BAD: Targeting dev server causes HMR and dev toolbar layout shifts
  // ❌ BAD: networkidle hangs indefinitely due to Vite WebSocket connection!
  await page.goto('http://localhost:4321/', { waitUntil: 'networkidle' })

  // ❌ BAD: Moving marquees/tickers cause unpredictable screenshot diffs
  // ❌ BAD: No animation freeze results in random false-positive regressions
  await page.screenshot({ path: 'homepage.png' })
})
```

_Why this fails:_ `networkidle` hangs background workers until timeout because Vite's WebSocket never closes. Dev toolbar elements inject into `<body>`, skewing layout baselines, and active CSS animations produce random diff noise.

### ✅ Best Practice / Idiomatic (Production Preview with Frozen Animations & DOM Wait)

```typescript
// tests/visual/capture.test.ts - Container-resilient production preview test
// Idiomatic Astro: Test against production preview artifacts (port 8788)
import { test } from '@playwright/test'

test('audit homepage visual layout', async ({ page }) => {
  // ✅ BEST PRACTICE: Target production preview server running compiled artifacts
  // ✅ Wait for domcontentloaded and specific semantic selector, NEVER networkidle
  await page.goto('http://localhost:8788/', { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('main', { state: 'visible' })

  // ✅ Freeze all animations, transitions, and marquees sitewide
  await page.addStyleTag({
    content: '*, *::before, *::after { animation: none !important; transition: none !important; }',
  })

  // ✅ Take screenshot with disabled animations and fixed viewport
  await page.screenshot({
    path: 'homepage.png',
    animations: 'disabled',
  })
})
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/05-edge-workers-and-qa/48-visual-regression-playwright-suite/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: 10-auditing-testing-and-nextjs-migration/01-audit-against-production-preview-never-dev`, `RULE-ID: 10-auditing-testing-and-nextjs-migration/04-audit-island-boundaries-with-dev-toolbar-inspect`, `RULE-ID: 09-performance-prefetch-and-transitions/16-prevent-cumulative-layout-shift-cls`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/05-edge-workers-and-qa/48-visual-regression-playwright-suite/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "48-VISUAL-REGRESSION-PLAYWRIGHT-SUITE-001",
    "rule_id": "RULE-ID: 10-auditing-testing-and-nextjs-migration/01-audit-against-production-preview-never-dev",
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
  --body "docs/audits/results/05-edge-workers-and-qa/48-visual-regression-playwright-suite/issue-body.md" \
  --title "[Audit - Visual Regression Playwright Suite & Frame Comparison Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/05-edge-workers-and-qa/48-visual-regression-playwright-suite/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Verify the production preview server serves clean HTML without Vite HMR or dev toolbar scripts:
   `curl -s http://localhost:8788/ | grep -E "(@vite/client|astro/toolbar)" || echo "PASS: Clean production HTML"`
2. Verify zero tests use `networkidle` across test suites:
   `git grep -n "networkidle" tests/ scripts/`
3. Audit for synthetic pulsing badges or arbitrary border radius tokens in tested components:
   `git grep -n "animate-pulse" src/`
   `git grep -n "rounded-lg\|rounded-xl\|rounded-2xl" src/`
4. Verify that Playwright runs in the headless Linux container without crashing:
   `pnpm vitest run tests/int/visual-regression.test.ts`
5. Prove that visual diffs reliably flag intentional UI changes while ignoring ticker movement.
6. Confirm test scripts enforce a 60-second timeout and exit cleanly with code 0 or 1.
7. Verify documentation integrity:
   `pnpm check:doc-integrity`

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/05-edge-workers-and-qa/48-visual-regression-playwright-suite/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Visual Regression Playwright Suite & Frame Comparison Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/05-edge-workers-and-qa/48-visual-regression-playwright-suite/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/05-edge-workers-and-qa/48-visual-regression-playwright-suite/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/05-edge-workers-and-qa/48-visual-regression-playwright-suite/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/05-edge-workers-and-qa/48-visual-regression-playwright-suite/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/05-edge-workers-and-qa/48-visual-regression-playwright-suite/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
