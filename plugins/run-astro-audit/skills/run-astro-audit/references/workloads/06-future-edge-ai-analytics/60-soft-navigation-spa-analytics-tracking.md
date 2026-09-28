# Mission Brief: Soft-Navigation Analytics & SPA Tracking Parity Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

When Astro's `<ClientRouter />` executes a soft navigation (SPA transition), the browser replaces the page DOM without reloading the document or re-executing `<head>` tracking scripts:

- Astro Lifecycle Events: The transition engine fires `astro:before-preparation`, `astro:after-preparation`, `astro:before-swap`, `astro:after-swap`, and `astro:page-load`.
- Analytics Failure Modes: Standard Google Analytics 4 (GA4), Google Tag Manager (GTM), Meta Pixel, and LinkedIn Insight tags rely on full page reloads (`window.onload` / `DOMContentLoaded`). Without explicit integration with `astro:page-load`, subsequent page views are dropped, artificially inflating bounce rates to 100% and breaking multi-step conversion funnels.
- Prefetch Isolation: Speculative prefetching (`data-astro-prefetch="hover"` or Speculation Rules API) fetches or renders pages in the background. Background prefetch requests must NEVER emit virtual `page_view` events, which would corrupt visitor counts. Tracking must bind strictly to navigation commit on `astro:page-load`.
- Referrer & Title Accuracy: In an SPA context, `document.referrer` remains frozen to the initial external entrypoint. Lifecycle scripts must track internal referrers, extract updated `document.title`, and push canonical `page_location` into `dataLayer`.

### Astro Architectural & Best Practice Rules

All analytics tracking scripts, tag managers, and telemetry integrations must adhere to the authoritative best practices:

- [21-track-pageviews-in-client-router-with-astro-page-load.md](../../best-practices/03-routing-and-pages/21-track-pageviews-in-client-router-with-astro-page-load.md) — Reliable pageview tracking under ClientRouter with `astro:page-load`, disabling initial automatic page_view to prevent double counting.
- [14-script-execution-mechanics-and-data-astro-rerun.md](../../best-practices/03-routing-and-pages/14-script-execution-mechanics-and-data-astro-rerun.md) — Script execution mechanics, differentiating bundled module scripts from `is:inline` and `data-astro-rerun`.
- [15-astro-page-load-vs-domcontentloaded-and-listener-leaks.md](../../best-practices/03-routing-and-pages/15-astro-page-load-vs-domcontentloaded-and-listener-leaks.md) — Lifecycle event listener leak prevention on `astro:before-swap`.
- [13-client-router-lifecycle-events-sequence.md](../../best-practices/03-routing-and-pages/13-client-router-lifecycle-events-sequence.md) — Client router lifecycle event sequence (`before-preparation` -> `after-preparation` -> `before-swap` -> `after-swap` -> `page-load`).
- [17-leverage-speculation-rules-client-prerendering.md](../../best-practices/09-performance-prefetch-and-transitions/17-leverage-speculation-rules-client-prerendering.md) — Isolating speculative prerenders from emitting virtual pageviews before navigation commit.
- [01-avoid-blanket-viewport-prefetching.md](../../best-practices/09-performance-prefetch-and-transitions/01-avoid-blanket-viewport-prefetching.md) — Avoiding blanket viewport prefetching to prevent unneeded analytics or network traffic.
- [03-configure-native-prefetch-engine.md](../../best-practices/09-performance-prefetch-and-transitions/03-configure-native-prefetch-engine.md) — Configuring native prefetch engine in `astro.config.mjs`.

Critical files to inspect:

- src/layouts/SiteLayout.astro
- src/components/TransitionLifecycle.astro
- scripts/dev/

## 3.2 Mission Objective

Audit SPA soft-navigation analytics tracking across all marketing routes.
Outcome: Ensure that GA4, Google Tag Manager, and conversion pixels record an accurate `page_view` event on every `astro:page-load`, reporting accurate canonical paths, page titles, and referrers without duplicate firings or prefetch pollutions.
Constraints: Read-only audit; inspect analytics event listener hooks.
Autonomy Grant: You own this mission end-to-end. Trace analytics dispatchers, dataLayer pushes, and SPA navigation hooks. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect SiteLayout.astro: check how GTM or GA4 is initialized and whether it listens to document.addEventListener('astro:page-load', ...).
2. Verify that dataLayer.push({ event: 'page_view', page_location: ... }) fires on soft navigations without double-counting initial loads.
3. Check scroll depth tracking: verify that scroll listeners re-initialize on each new page view and tear down cleanly in astro:before-swap.
4. Verify that prefetch triggers do not emit premature tracking hits.

### ❌ Bad Practice / Anti-Pattern

```html
<!-- SiteLayout.astro: Legacy static script tags and firing on astro:after-swap -->
<script is:inline>
  window.dataLayer = window.dataLayer || []
  function gtag() {
    dataLayer.push(arguments)
  }
  gtag('js', new Date())
  gtag('config', 'G-XXXXXXXXXX')
  // ❌ Fails: Standard snippet only fires on initial load; blind to SPA navigations!
  // Subsequent article reads or service views are invisible in analytics.
</script>

<script>
  // ❌ Bad Practice: Dispatching analytics on astro:after-swap before document.title and canonical metadata update!
  // At after-swap time, document.title still reflects the OLD page or remains empty,
  // creating race conditions and logging corrupted page titles and wrong URLs.
  document.addEventListener('astro:after-swap', () => {
    gtag('event', 'page_view', {
      page_title: document.title, // ❌ STALE: Returns previous page's title!
      page_location: window.location.href,
    })
  })
</script>
```

### ✅ Best Practice / Idiomatic

```astro
<!-- src/components/TransitionLifecycle.astro - Idiomatic Astro lifecycle tracking -->
<script is:inline define:vars={{ gaId: "G-XXXXXXXXXX" }}>
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  gtag('js', new Date());
  // ✅ Best Practice: Disable automatic page_view to prevent double counting on initial load
  gtag('config', gaId, { send_page_view: false });

  let lastPath = window.location.pathname;

  // ✅ Best Practice: Listen to astro:page-load where DOM, document.title, and canonical URL are fully committed
  document.addEventListener('astro:page-load', () => {
    const currentPath = window.location.pathname;
    const pageTitle = document.title;
    const pageLocation = window.location.href;

    if (typeof window.dataLayer !== 'undefined') {
      window.dataLayer.push({
        event: 'page_view',
        page_location: pageLocation,
        page_path: currentPath,
        page_title: pageTitle,
        page_referrer: lastPath !== currentPath ? lastPath : document.referrer,
      });
    }

    lastPath = currentPath;
  });

  // Clean up observers or timers before new page swap to prevent memory leaks
  document.addEventListener('astro:before-swap', () => {
    // Teardown scroll listeners or active tracking timers
  });
</script>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/06-future-edge-ai-analytics/60-soft-navigation-spa-analytics-tracking/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Best Practice Mapping Requirement**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule (e.g. `RULE-ID: 03-21-track-pageviews-in-client-router-with-astro-page-load`, `RULE-ID: 03-14-script-execution-mechanics-and-data-astro-rerun`, `RULE-ID: 03-15-astro-page-load-vs-domcontentloaded-and-listener-leaks`, `RULE-ID: 03-13-client-router-lifecycle-events-sequence`, `RULE-ID: 09-17-leverage-speculation-rules-client-prerendering`, `RULE-ID: 09-01-avoid-blanket-viewport-prefetching`, or `RULE-ID: 09-03-configure-native-prefetch-engine`).

You must create and populate the following deliverables in `docs/audits/results/06-future-edge-ai-analytics/60-soft-navigation-spa-analytics-tracking/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "60-SOFT-NAVIGATION-SPA-ANALYTICS-TRACKING-001",
    "rule_id": "RULE-ID (e.g. 03-21-track-pageviews-in-client-router-with-astro-page-load)",
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
  --body "docs/audits/results/06-future-edge-ai-analytics/60-soft-navigation-spa-analytics-tracking/issue-body.md" \
  --title "[Audit - Soft-Navigation Analytics & SPA Tracking Parity Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/06-future-edge-ai-analytics/60-soft-navigation-spa-analytics-tracking/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Verify that simulated soft navigation between 3 pages fires exactly 3 page_view analytics events.
2. Confirm that page_location matches the updated window.location.pathname.
3. Audit soft-navigation analytics implementation and prefetch interactions via terminal commands:

```bash
# 1. Audit layout files for astro:page-load event listener bindings
grep -rn 'astro:page-load' src/layouts/ src/components/

# 2. Inspect dataLayer.push and gtag calls for soft-navigation hooks
grep -rnE '(dataLayer\.push|gtag\()' src/

# 3. Check for astro:before-swap cleanup handlers
grep -rn 'astro:before-swap' src/

# 4. Search for legacy inline analytics scripts missing lifecycle integration
grep -rn 'is:inline' src/layouts/ src/components/ | grep -iE '(analytics|gtm|tag|pixel)'

# 5. Audit for speculation rules and prefetch directives in templates
git grep -n "speculationrules" src/
git grep -n "data-astro-prefetch" src/
```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/06-future-edge-ai-analytics/60-soft-navigation-spa-analytics-tracking/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Soft-Navigation Analytics & SPA Tracking Parity Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/06-future-edge-ai-analytics/60-soft-navigation-spa-analytics-tracking/findings.json` (N defects logged)
   - `file://docs/audits/results/06-future-edge-ai-analytics/60-soft-navigation-spa-analytics-tracking/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/06-future-edge-ai-analytics/60-soft-navigation-spa-analytics-tracking/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/06-future-edge-ai-analytics/60-soft-navigation-spa-analytics-tracking/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/06-future-edge-ai-analytics/60-soft-navigation-spa-analytics-tracking/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
