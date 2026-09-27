# Mission Brief: Speculative Rules API & 0ms Instant Prerender Navigation Audit

## 3.0 Skills / Tools: view_file, run_command, react-doctor.

## 3.1 Context Block

Astro 7 supports Chrome's native Speculation Rules API and built-in client prefetching via the native prefetch engine:

- Astro replaced legacy `@astrojs/prefetch` with a built-in prefetch runtime (<1KB) configured via `prefetch` in `astro.config.mjs` (`prefetchAll: false`, `defaultStrategy: 'hover'`).
- `data-astro-prefetch="hover"`: captures user intent on desktop during the 100–300ms cursor dwell with a ~65ms debounce window.
- `data-astro-prefetch="tap"`: prefetches on `touchstart`/`pointerdown` (50–100ms head start), eliminating false-positive downloads on mobile.
- `data-astro-prefetch="viewport"`: downloads HTML when links enter the viewport. Blanket usage across grids of 50+ links saturates mobile cellular bandwidth, spikes device CPU, and triggers excessive origin requests.
- Speculation Rules API (`experimental.clientPrerender: true`): Supporting browsers (Chrome 121+) fully pre-render targeted pages in an invisible background tab for 0ms perceived latency. Eagerness must be calibrated (`moderate` or targeted `immediate`) to avoid memory limit eviction (`Failure: Memory limit exceeded`).
- Network Guards: Astro respects `navigator.connection.saveData` and 2G/3G `effectiveType`, downgrading prefetch strategies automatically. Bypassing checks via `{ ignoreSlowConnection: true }` must be restricted to critical single conversion steps.
- Sensitive Routes: State-mutating endpoints (`/api/auth/signout`), heavy SSR database queries, or uncacheable checkout funnels must explicitly opt out via `data-astro-prefetch="false"`.

### Astro Architectural & Best Practice Rules

All prefetching configurations, Speculation Rules integrations, and link tiering must adhere to the authoritative best practices:

- [17-leverage-speculation-rules-client-prerendering.md](../../best-practices/09-performance-prefetch-and-transitions/17-leverage-speculation-rules-client-prerendering.md) — Speculation Rules API for sub-second client prerendering without memory limit exhaustion.
- [03-configure-native-prefetch-engine.md](../../best-practices/09-performance-prefetch-and-transitions/03-configure-native-prefetch-engine.md) — Configuring native `prefetch` engine in `astro.config.mjs` (`prefetchAll: false`, `defaultStrategy: 'hover'`).
- [01-avoid-blanket-viewport-prefetching.md](../../best-practices/09-performance-prefetch-and-transitions/01-avoid-blanket-viewport-prefetching.md) — Avoiding blanket viewport prefetching on large link collections to prevent network congestion.
- [02-prefer-hover-or-tap-prefetch-strategies.md](../../best-practices/09-performance-prefetch-and-transitions/02-prefer-hover-or-tap-prefetch-strategies.md) — Preferring hover or tap prefetch strategies to eliminate false-positive downloads.
- [04-opt-out-heavy-or-dynamic-routes-from-prefetch.md](../../best-practices/09-performance-prefetch-and-transitions/04-opt-out-heavy-or-dynamic-routes-from-prefetch.md) — Explicitly opting out heavy, state-mutating, or dynamic routes with `data-astro-prefetch="false"`.
- [05-respect-save-data-and-slow-connections.md](../../best-practices/09-performance-prefetch-and-transitions/05-respect-save-data-and-slow-connections.md) — Enforcing `saveData` and 2G/3G connection respect without unauthorized bypasses.
- [14-script-execution-mechanics-and-data-astro-rerun.md](../../best-practices/03-routing-and-pages/14-script-execution-mechanics-and-data-astro-rerun.md) — Script execution mechanics under ClientRouter.
- [21-track-pageviews-in-client-router-with-astro-page-load.md](../../best-practices/03-routing-and-pages/21-track-pageviews-in-client-router-with-astro-page-load.md) — Reliable pageview tracking under ClientRouter, isolating background speculative prerendering from analytics emissions.

Critical files to inspect:

- astro.config.mjs (native prefetch & experimental.clientPrerender settings)
- src/layouts/SiteLayout.astro (<ClientRouter />)
- src/components/atoms/SmartLink.tsx
- src/components/chrome/MegaMenu.astro

## 3.2 Mission Objective

Audit and calibrate speculative prefetching and ClientRouter configuration across the entire site.
Outcome: Implement tiered speculative prefetching (`tap` on mobile, `hover` on desktop, `data-astro-prefetch="false"` on sensitive/heavy routes) with strict `saveData` adherence, native Speculation Rules API pre-rendering, and zero legacy `@astrojs/prefetch` remnants.
Constraints: Read-only audit; verify prefetch attributes, config flags, and network triggers.
Autonomy Grant: You own this mission end-to-end. Analyze network prefetch waterfalls, cache storage, and mobile data budgets. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect SmartLink.tsx & MegaMenu.astro: verify how data-astro-prefetch is applied and ensure external links never prefetch.
2. Check astro.config.mjs: verify native prefetch configuration (`prefetchAll: false`, `defaultStrategy: 'hover'`) and client prerender flags.
3. Audit catalog and archive listings for blanket viewport prefetching.
4. Verify sensitive endpoint protection: ensure logout, signout, and heavy SSR routes have `data-astro-prefetch="false"`.
5. Check programmatic prefetch call sites for unauthorized `ignoreSlowConnection: true` or over-speculation (`eagerness: 'immediate'` on bulk URLs).

### ❌ Bad Practice / Anti-Pattern

```astro
---
// astro.config.mjs & template anti-patterns
import prefetch from '@astrojs/prefetch'; // DEPRECATED: Do not use legacy prefetch package

// ❌ Blanket viewport prefetch on 50+ catalog links floods origin & drains mobile batteries
// Next.js developers migrating to Astro often apply viewport prefetching indiscriminately,
// failing to realize Astro downloads full HTML documents rather than partial JSON diffs.
---
<div class="grid">
  {products.map(p => (
    <a href={`/services/${p.id}`} data-astro-prefetch="viewport">View</a>
  ))}
  <!-- Accidental signout triggered by cursor hover! -->
  <a href="/api/auth/signout">Sign Out</a>
</div>

<script>
  import { prefetch } from 'astro:prefetch';
  // ❌ Over-speculation and ignoring slow connections
  document.querySelectorAll('a').forEach(a => prefetch(a.href, { eagerness: 'immediate', ignoreSlowConnection: true }));
</script>
```

### ✅ Best Practice / Idiomatic

```javascript
// astro.config.mjs - Central native prefetch & client prerender configuration
import { defineConfig } from 'astro/config'

export default defineConfig({
  prefetch: {
    prefetchAll: false, // Explicit opt-in prevents runaway download waterfalls
    defaultStrategy: 'hover', // 100-300ms desktop intent buffer
  },
  experimental: {
    clientPrerender: true, // Leverages native Speculation Rules API safely
  },
})
```

```astro
---
// src/components/Navigation.astro - Calibrated prefetch tiering & sensitive opt-outs
---
<nav>
  <!-- Hover strategy for primary navigation; tap fallback on mobile -->
  <a href="/services" data-astro-prefetch="hover">Services</a>
  <a href="/case-studies" data-astro-prefetch="tap">Case Studies</a>
  <!-- Explicit opt-out for heavy SSR queries and auth actions -->
  <a href="/dashboard/analytics" data-astro-prefetch="false">Deep Analytics</a>
  <a href="/api/auth/signout" data-astro-prefetch="false">Sign Out</a>
</nav>

<script>
  import { prefetch } from 'astro:prefetch';

  // Immediate eagerness strictly for high-probability conversion path
  prefetch('/contact', { eagerness: 'immediate' });

  // Moderate eagerness allows browser FIFO heuristics to manage memory safely
  prefetch('/services', { eagerness: 'moderate' });
</script>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/06-future-edge-ai-analytics/58-speculative-rules-prerender-navigation/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Best Practice Mapping Requirement**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule (e.g. `RULE-ID: 09-17-leverage-speculation-rules-client-prerendering`, `RULE-ID: 09-03-configure-native-prefetch-engine`, `RULE-ID: 09-01-avoid-blanket-viewport-prefetching`, `RULE-ID: 09-02-prefer-hover-or-tap-prefetch-strategies`, `RULE-ID: 09-04-opt-out-heavy-or-dynamic-routes-from-prefetch`, `RULE-ID: 09-05-respect-save-data-and-slow-connections`, `RULE-ID: 03-14-script-execution-mechanics-and-data-astro-rerun`, or `RULE-ID: 03-21-track-pageviews-in-client-router-with-astro-page-load`).

You must create and populate the following deliverables in `docs/audits/results/06-future-edge-ai-analytics/58-speculative-rules-prerender-navigation/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "58-SPECULATIVE-RULES-PRERENDER-NAVIGATION-001",
    "rule_id": "RULE-ID (e.g. 09-17-leverage-speculation-rules-client-prerendering)",
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
  --body "docs/audits/results/06-future-edge-ai-analytics/58-speculative-rules-prerender-navigation/issue-body.md" \
  --title "[Audit - Speculative Rules API & 0ms Instant Prerender Navigation Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/06-future-edge-ai-analytics/58-speculative-rules-prerender-navigation/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Verify that hovering over a navigation link triggers an instant background prefetch.
2. Confirm that devices with saveData: true enabled disable automatic viewport prefetching.
3. Audit prefetch configuration, speculation rules, and attributes using terminal commands:

```bash
# 1. Audit for Speculation Rules API scripts and JSON tags
git grep -n "speculationrules" src/

# 2. Audit for native prefetch directives across templates
git grep -n "data-astro-prefetch" src/

# 3. Audit for deprecated @astrojs/prefetch package
grep -n "@astrojs/prefetch" package.json

# 4. Detect unbounded viewport prefetching on link collections
grep -rn 'data-astro-prefetch="viewport"' src/pages src/components

# 5. Detect eager load prefetching saturating initial bandwidth
grep -rn 'data-astro-prefetch="load"' src/

# 6. Check for un-opted sensitive endpoints (logout, auth, heavy downloads)
grep -rnE 'href="[^"]*(signout|logout|checkout|download)' src/ | grep -v 'data-astro-prefetch="false"'

# 7. Detect reckless bypass of slow connection safeguards
grep -rn 'ignoreSlowConnection:\s*true' src/

# 8. Verify native prefetch script presence in server-rendered output
curl -s http://localhost:4321 | grep -i 'astro-prefetch'
```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/06-future-edge-ai-analytics/58-speculative-rules-prerender-navigation/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Speculative Rules API & 0ms Instant Prerender Navigation Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/06-future-edge-ai-analytics/58-speculative-rules-prerender-navigation/findings.json` (N defects logged)
   - `file://docs/audits/results/06-future-edge-ai-analytics/58-speculative-rules-prerender-navigation/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/06-future-edge-ai-analytics/58-speculative-rules-prerender-navigation/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/06-future-edge-ai-analytics/58-speculative-rules-prerender-navigation/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/06-future-edge-ai-analytics/58-speculative-rules-prerender-navigation/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
