# Mission Brief: INP (Interaction to Next Paint) 200ms Latency & Thread Responsiveness Audit

## 3.0 Skills / Tools: view_file, run_command, react-doctor.

## 3.1 Context Block

Interaction to Next Paint (INP) is Google's Core Web Vital measuring responsiveness to all user interactions (clicks, taps, key presses) throughout the entire page lifecycle.
Google requires an INP under 200ms for a "Good" rating.
While Astro's Zero-JS architecture provides 0ms Total Blocking Time (TBT) by default, loading un-deferred framework islands with `client:load` saturates the main browser thread during initial hydration, creating Long Tasks (>50ms) that delay paint updates and fail the 200ms INP threshold.

Key Astro Best Practice contracts for INP & TBT Optimization:

1. **Hydration Deferral Discipline**: Never use `client:load` on below-the-fold or non-critical components.
   - Use `client:idle` for above-the-fold interactive accessories (e.g., currency selector, search bar, language switch).
   - Use `client:visible={{ rootMargin: '200px' }}` for below-the-fold content (e.g., FAQ accordions, matrix tables, contact forms) so framework code parses only when approaching viewport.
2. **Main Thread Yielding in React Islands**: Heavy UI updates (such as table filters in `MatrixPage.tsx` or search keystrokes) must yield to the main thread via `scheduler.yield()`, `React.startTransition()`, or `requestAnimationFrame()` to avoid input delays > 50ms.
3. **ClientRouter Soft Navigation Responsiveness**: In `astro:page-load`, defer non-critical widget initialization to `requestIdleCallback` to ensure page navigation paints immediately.
4. **Layout Containment & Visual Stability**: Avoid layout shifts during interaction feedback by establishing reserved bounding boxes, preventing cumulative recalculations.

Astro Architectural & Best Practice Rules:

- **Eliminate Total Blocking Time (TBT) and Optimize INP Under 200ms ([15-eliminate-total-blocking-time-tbt-and-optimize-inp.md](../../best-practices/09-performance-prefetch-and-transitions/15-eliminate-total-blocking-time-tbt-and-optimize-inp.md))**: Never saturate the main thread with eager `client:load` islands. Deferring framework execution with `client:idle` and `client:visible={{ rootMargin: '200px' }}` guarantees 0ms TBT and keeps INP comfortably below the strict 200ms threshold (`ASTRO-BP-09-15`).
- **Prevent Cumulative Layout Shift (CLS) Across Media and Islands ([16-prevent-cumulative-layout-shift-cls.md](../../best-practices/09-performance-prefetch-and-transitions/16-prevent-cumulative-layout-shift-cls.md))**: Every interactive component wrapper and dynamic feed container must declare explicit dimensions or CSS aspect-ratio tokens (`aspect-[16/9]`, `aspect-square`) to prevent layout shifts when islands hydrate or paint state updates (`ASTRO-BP-09-16`).
- **Execute Site-Wide Performance Audits Using Unlighthouse Against Preview Server ([08-site-wide-crawling-with-unlighthouse.md](../../best-practices/10-auditing-testing-and-nextjs-migration/08-site-wide-crawling-with-unlighthouse.md))**: Audit site-wide INP, TBT, and Core Web Vitals across all pre-rendered HTML routes using headless parallel Lighthouse workers against `dist/sitemap-index.xml` on the preview server (`ASTRO-BP-10-08`).
- **Protect Authenticated Routes Server-Side via `context.cookies` and `context.redirect` ([06-auth-guard-session-validation.md](../../best-practices/06-middleware-and-auth/06-auth-guard-session-validation.md))**: Interactive routes requiring session validation must be protected at the edge/middleware boundary before HTML rendering or island execution occurs (`ASTRO-BP-06-06`).
- **Compose i18n Routing Before Auth Guards to Handle Localized Protected Paths ([16-i18n-and-multilingual-auth-composition.md](../../best-practices/06-middleware-and-auth/16-i18n-and-multilingual-auth-composition.md))**: Multilingual route handling must evaluate localized paths before route interception to ensure zero thread-blocking client redirects (`ASTRO-BP-06-16`).

Critical files to inspect:

- src/components/chrome/SiteHeader.astro
- src/components/chrome/ContactDrawer.astro
- src/features/tools/components/matrix/MatrixPage.tsx
- src/components/common/MarqueeRail.tsx
- src/pages/ (scan for un-deferred `client:load` usage)

## 3.2 Mission Objective

Profile user interaction latency across mobile and desktop viewports.
Outcome: Prove that all button clicks, drawer toggles, and filter selections trigger visual feedback in under 200ms (INP < 200ms), eliminate unthrottled `client:load` directives, and ensure zero blocking tasks exceeding 50ms during continuous logo marquee motion.
Constraints: Read-only audit; profile main-thread execution timing and hydration strategies.
Autonomy Grant: You own this mission end-to-end. Profile event handler runtimes, requestAnimationFrame queues, and microtask delays. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Audit Contact Drawer toggle and Mobile Menu button: measure time from pointerdown to DOM mutation.
2. Check matrix table filters: verify that filter state updates yield to the main thread via `startTransition`, `requestAnimationFrame`, or `scheduler.yield()`.
3. Verify that marquee continuous scroll does not trigger layout recalculation during user taps.
4. Audit island hydration directives across pages for anti-patterns:

### ❌ Bad Practice / Anti-Pattern (Heavy Synchronous Event Handlers Blocking Main Thread)

```tsx
// ❌ Heavy synchronous computation executed in event handler:
// Blocks the main thread for 250ms+ upon user click, failing the 200ms INP threshold
function SearchFilterMatrix({ items }: { items: MatrixItem[] }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(items)

  const handleFilterClick = (tag: string) => {
    // Synchronously filtering 5,000 items directly blocks browser paint:
    const filtered = items.filter((item) => {
      return item.tags.includes(tag) && expensiveLevenshteinDistance(item.name, query)
    })
    setResults(filtered) // Triggers synchronous re-render and long task (>150ms)
  }

  return (
    <div>
      {TAGS.map((tag) => (
        <button key={tag} onClick={() => handleFilterClick(tag)}>
          {tag}
        </button>
      ))}
    </div>
  )
}
```

### ✅ Best Practice / Idiomatic (Yielding to Main Thread with scheduler.yield() & startTransition)

```tsx
// ✅ Idiomatic: Yielding to main thread provides immediate visual feedback (<50ms INP)
import { startTransition, useState } from 'react'

function SearchFilterMatrix({ items }: { items: MatrixItem[] }) {
  const [activeTag, setActiveTag] = useState('')
  const [results, setResults] = useState(items)

  const handleFilterClick = async (tag: string) => {
    // 1. Immediately update active UI state for instant paint feedback
    setActiveTag(tag)

    // 2. Yield to browser main thread to allow paint frame to land
    if ('scheduler' in window && 'yield' in (window as any).scheduler) {
      await (window as any).scheduler.yield()
    } else {
      await new Promise((resolve) => requestAnimationFrame(resolve))
    }

    // 3. Defer non-urgent state calculation via startTransition
    startTransition(() => {
      const filtered = items.filter((item) => item.tags.includes(tag))
      setResults(filtered)
    })
  }

  return (
    <div>
      {TAGS.map((tag) => (
        <button
          key={tag}
          className={activeTag === tag ? 'active' : ''}
          onClick={() => handleFilterClick(tag)}
        >
          {tag}
        </button>
      ))}
    </div>
  )
}
```

### ❌ Bad Practice / Anti-Pattern (Unthrottled Hydration Saturating Main Thread)

```astro
---
// src/pages/tools/matrix.astro
import SiteHeader from '../../components/chrome/SiteHeader.astro';
import MatrixPage from '../../features/tools/components/matrix/MatrixPage.tsx';
import FAQAccordion from '../../components/FAQAccordion.tsx';
import ContactForm from '../../components/ContactForm.tsx';
---
<!-- ❌ All islands hydrate simultaneously on page load: -->
<!-- Main thread locks up for 350ms, causing high TBT and INP > 400ms -->
<header>
  <SiteHeader />
</header>
<main>
  <MatrixPage client:load /> <!-- Heavy table locks main thread! -->
  <FAQAccordion client:load />  <!-- Below the fold: unnecessary eager load! -->
</main>
<footer>
  <ContactForm client:load />   <!-- Bottom of page: blocks initial tap inputs! -->
</footer>
```

### ✅ Best Practice / Idiomatic (Deferred Hydration & Main Thread Yielding)

```astro
---
// src/pages/tools/matrix.astro
import SiteHeader from '../../components/chrome/SiteHeader.astro';
import MatrixPage from '../../features/tools/components/matrix/MatrixPage.tsx';
import FAQAccordion from '../../components/FAQAccordion.tsx';
import ContactForm from '../../components/ContactForm.tsx';
---
<!-- ✅ Strategic hydration eliminates main-thread contention: -->
<header>
  <SiteHeader />
</header>
<main>
  <!-- Hydrate matrix when idle -->
  <MatrixPage client:idle />
  <!-- Hydrates strictly when scrolled into view (pre-warmed 200px before viewport) -->
  <FAQAccordion client:visible={{ rootMargin: '200px' }} />
</main>
<footer>
  <!-- Hydrates strictly when visible at the bottom of the page -->
  <ContactForm client:visible />
</footer>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/06-future-edge-ai-analytics/54-inp-interaction-to-next-paint-audit/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Rule ID Mapping**: All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an authoritative Astro best practice rule (e.g. `ASTRO-BP-09-15`, `ASTRO-BP-09-16`, `ASTRO-BP-10-08`, `ASTRO-BP-06-06`, `ASTRO-BP-06-16`).

You must create and populate the following deliverables in `docs/audits/results/06-future-edge-ai-analytics/54-inp-interaction-to-next-paint-audit/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "54-INP-INTERACTION-TO-NEXT-PAINT-AUDIT-001",
    "rule_id": "RULE-ID (e.g. ASTRO-BP-09-15 / ASTRO-BP-09-16 / ASTRO-BP-10-08)",
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
  --body "docs/audits/results/06-future-edge-ai-analytics/54-inp-interaction-to-next-paint-audit/issue-body.md" \
  --title "[Audit - INP (Interaction to Next Paint) 200ms Latency & Thread Responsiveness Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/06-future-edge-ai-analytics/54-inp-interaction-to-next-paint-audit/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Scan for un-deferred `client:load` directives on non-critical islands:
   ```bash
   rg "client:load" src/pages/ src/components/
   ```
2. Execute site-wide performance and responsiveness audit against production preview server:
   ```bash
   pnpm exec unlighthouse --site http://localhost:8788
   ```
3. Run automated responsiveness and thread contention tests:
   ```bash
   pnpm vitest run test/performance/inp-thread-responsiveness.test.ts
   ```
4. Verify that simulated click/tap events produce next-frame paint in <100ms under 4x CPU throttling.
5. Confirm zero JavaScript long tasks exceeding 50ms during continuous logo marquee animation.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/06-future-edge-ai-analytics/54-inp-interaction-to-next-paint-audit/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** INP (Interaction to Next Paint) 200ms Latency & Thread Responsiveness Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/06-future-edge-ai-analytics/54-inp-interaction-to-next-paint-audit/findings.json` (N defects logged)
   - `file://docs/audits/results/06-future-edge-ai-analytics/54-inp-interaction-to-next-paint-audit/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/06-future-edge-ai-analytics/54-inp-interaction-to-next-paint-audit/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/06-future-edge-ai-analytics/54-inp-interaction-to-next-paint-audit/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/06-future-edge-ai-analytics/54-inp-interaction-to-next-paint-audit/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
