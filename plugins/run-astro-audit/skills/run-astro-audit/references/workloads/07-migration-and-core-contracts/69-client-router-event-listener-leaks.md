# Mission Brief: ClientRouter Lifecycle & Event Listener Leak Eliminator Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

Astro's `<ClientRouter />` provides seamless SPA-like page transitions without full browser reloads.
Under `<ClientRouter />`, client script execution mechanics differ fundamentally from classic multi-page applications:

1. **Bundled Module Scripts:** Standard `<script>` tags are bundled as ES modules, deduplicated, and evaluated **once per session** upon initial download. Navigating to secondary pages does NOT re-run top-level module code.
2. **`DOMContentLoaded` Inactivity:** `DOMContentLoaded` fires strictly on the initial hard page load. Scripts relying on it remain completely inert on subsequent client navigations.
3. **Listener Accumulation & Memory Leaks:** Attaching event handlers via `document.addEventListener("astro:page-load", ...)` re-executes on every navigation. However, registering persistent `window` listeners (`scroll`, `resize`, `keydown`) or `setInterval` timers inside `astro:page-load` without teardown stacks duplicate callbacks on every navigation (e.g. 10 scroll listeners after 10 navigations), causing severe memory leaks and CPU degradation.
4. **Teardown Discipline:** Unlike React's `useEffect` cleanup hook, Astro client scripts require manual teardown via `AbortController` and `astro:before-swap` (`{ once: true }`).
5. **Inline Script Re-execution:** Standalone tracking beacons or widget scripts requiring fresh evaluation on every route must explicitly declare `<script is:inline data-astro-rerun>`.

### Authoritative Astro Architectural & Best Practice Rules

Auditors must inspect, evaluate, and verify all client lifecycle bindings against the repository's authoritative Astro best practices:

- **Primary Lifecycle Cleanup Contract**: [03-frontmatter-security-boundary.md](../../best-practices/01-architecture-and-philosophy/03-frontmatter-security-boundary.md) — Isolate secrets and database calls in frontmatter without leaking to client bundles.
- **Server Islands Architecture**: [11-defer-personalized-content-with-server-islands.md](../../best-practices/02-islands-and-hydration/11-defer-personalized-content-with-server-islands.md) — Defer personalized content with Server Islands (`server:defer`).
- **Island URL Boundary**: [12-keep-server-island-props-under-url-limit.md](../../best-practices/02-islands-and-hydration/12-keep-server-island-props-under-url-limit.md) — Keep Server Island props lightweight and under URL length limits (< 2048 bytes).
- **Middleware State Contract**: [04-mutate-locals-never-reassign.md](../../best-practices/06-middleware-and-auth/04-mutate-locals-never-reassign.md) — Mutate `context.locals` properties; never overwrite the object.
- **Static Asset Bypass**: [05-filter-static-asset-requests.md](../../best-practices/06-middleware-and-auth/05-filter-static-asset-requests.md) — Filter out static assets before executing heavy middleware logic.
- **Streaming Pipeline Contract**: [19-avoid-consuming-streaming-response-body-in-middleware.md](../../best-practices/06-middleware-and-auth/19-avoid-consuming-streaming-response-body-in-middleware.md) — Avoid consuming streaming response bodies in post-execution middleware.
- **Headless Unit Testing**: [21-unit-test-components-with-astro-container-api.md](../../best-practices/10-auditing-testing-and-nextjs-migration/21-unit-test-components-with-astro-container-api.md) — Unit test `.astro` components headlessly with the Astro Container API.

Critical files to inspect:

- `src/layouts/`
- `src/components/chrome/`
- `src/components/TransitionLifecycle.astro`
- `src/scripts/`

## 3.2 Mission Objective

Audit all client-side scripts, event listeners, and router lifecycle bindings to guarantee clean teardown, prevent listener accumulation across soft navigations, and ensure proper re-execution with `data-astro-rerun`.
Outcome: Guarantee zero memory leaks across navigations and ensure dynamic scripts properly re-initialize on `astro:page-load`.
Constraints: Read-only audit; do not alter production code.
Autonomy Grant: You own this mission end-to-end. Trace lifecycle events, inspect script tags, and verify cleanup handlers. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Search for `addEventListener('astro:page-load'` and `addEventListener('DOMContentLoaded'` across all components and scripts.
2. Verify that listeners registered on `window` or `document` inside `astro:page-load` utilize an `AbortController` with `{ signal }` or clean up on `astro:before-swap`.
3. Check for orphaned `setInterval` or `setTimeout` timers that persist across client navigations.
4. Audit third-party widgets and analytics scripts to ensure `<script is:inline data-astro-rerun>` is used where route-level re-execution is required.
5. Verify that `transition:persist` is applied appropriately for persistent UI islands (e.g. search bars, audio players, theme controls).

### ❌ Bad Practice / Anti-Pattern (Inert DOMContentLoaded & Exponential Listener Leaks)

```html
<!-- src/components/HeaderNav.astro (Inert scripts & exponential listener leaks) -->
<script>
  // ❌ TRAP 1: Never fires on client-side SPA navigation!
  document.addEventListener('DOMContentLoaded', () => {
    initHeader()
  })

  // ❌ TRAP 2: Memory leak! Stacks a new window scroll listener and interval on every navigation
  document.addEventListener('astro:page-load', () => {
    window.addEventListener('scroll', () => {
      console.log('Scrolled!') // Fires N times after N navigations!
    })
    setInterval(() => syncTimer(), 1000) // Orphaned intervals accumulate indefinitely!
  })
</script>
```

### ✅ Best Practice / Idiomatic (Leak-Free AbortController Pattern & Explicit Re-runs)

```html
<!-- src/components/HeaderNav.astro (Leak-free AbortController pattern) -->
<!-- Bound to RULE-ID: 02-islands-and-hydration/client-router-lifecycle-cleanup -->
<script>
  let pageAbortController

  document.addEventListener('astro:page-load', () => {
    // ✅ Abort previous page listeners before registering new ones
    pageAbortController?.abort()
    pageAbortController = new AbortController()
    const { signal } = pageAbortController

    // ✅ Attach listeners bound to the abort signal
    window.addEventListener('scroll', handleScroll, { signal })
    window.addEventListener('keydown', handleKeydown, { signal })

    const timer = setInterval(syncTimer, 5000)

    // ✅ Clean up timers and abort listeners immediately before DOM swap
    document.addEventListener(
      'astro:before-swap',
      () => {
        clearInterval(timer)
        pageAbortController?.abort()
      },
      { once: true },
    )
  })

  function handleScroll() {
    /* ... */
  }
  function handleKeydown() {
    /* ... */
  }
  function syncTimer() {
    /* ... */
  }
</script>

<!-- ✅ Standalone scripts that must re-evaluate on every transition -->
<script is:inline data-astro-rerun>
  window.dataLayer = window.dataLayer || []
  window.dataLayer.push({ event: 'pageview', path: window.location.pathname })
</script>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/07-migration-and-core-contracts/69-client-router-event-listener-leaks/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Rule-ID Mapping**: Every item in `findings.json` MUST explicitly map to an authoritative Astro best practice rule ID (e.g. `RULE-ID: 02-islands-and-hydration/client-router-lifecycle-cleanup` or `RULE-ID: 01-architecture-and-philosophy/03-frontmatter-security-boundary`).

You must create and populate the following deliverables in `docs/audits/results/07-migration-and-core-contracts/69-client-router-event-listener-leaks/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "69-CLIENT-ROUTER-EVENT-LISTENER-LEAKS-001",
    "rule_id": "RULE-ID: 02-islands-and-hydration/client-router-lifecycle-cleanup",
    "file": "src/components/chrome/HeaderNav.astro",
    "line": 42,
    "severity": "critical" | "high" | "medium" | "low",
    "category": "performance" | "syntax" | "hydration" | "parity" | "security",
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
   Execute the turnkey publisher script `scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting (<=200 items, max 3 levels), creates the primary issue, spawns linked sub-issues (capped at 20) for critical/high defects, and pushes the JSON deliverables to `origin main`:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/07-migration-and-core-contracts/69-client-router-event-listener-leaks/issue-body.md" \
  --title "[Audit - ClientRouter Lifecycle & Event Listener Leak Eliminator Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/07-migration-and-core-contracts/69-client-router-event-listener-leaks/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Run `git grep -n "astro:page-load" src/` to isolate all navigation event bindings.
2. Run `git grep -n "DOMContentLoaded" src/` to identify inert event bindings.
3. Run `git grep -n "astro:before-swap" src/` to confirm cleanup routines exist.
4. Run `git grep -n "data-astro-rerun" src/` to verify inline script re-run directives.
5. Run `git grep -n "defineMiddleware" src/` and `git grep -n "server:defer" src/` to check router coexistence.
6. Execute headless component testing with Vitest using `experimental_AstroContainer` from `astro/container` to render layout chrome components and verify script tags:
   ```bash
   pnpm exec vitest run tests/components/ --run
   ```
7. In browser console, verify listener count stability after 5 navigations:
   `getEventListeners(window).scroll?.length` (must remain 1, never accumulating).

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/07-migration-and-core-contracts/69-client-router-event-listener-leaks/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** ClientRouter Lifecycle & Event Listener Leak Eliminator Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/07-migration-and-core-contracts/69-client-router-event-listener-leaks/findings.json` (N defects logged with RULE-ID mappings)
   - `file://docs/audits/results/07-migration-and-core-contracts/69-client-router-event-listener-leaks/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/07-migration-and-core-contracts/69-client-router-event-listener-leaks/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/07-migration-and-core-contracts/69-client-router-event-listener-leaks/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/07-migration-and-core-contracts/69-client-router-event-listener-leaks/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
