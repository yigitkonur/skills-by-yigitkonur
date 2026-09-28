# Mission Brief: Third-Party Scripts & Analytics Loading Discipline Audit

## 3.0 Skills / Tools: view_file, run_command, use-sentry.

## 3.1 Context Block

Third-party scripts (Google Tag Manager, analytics, Sentry error telemetry, Cloudflare Turnstile) can severely degrade Core Web Vitals (FCP, LCP, INP) if loaded synchronously in `<head>`.
Astro architecture and performance guidelines mandate:

1. **Zero Render-Blocking External Scripts**: All non-critical external scripts must specify `defer`, `async`, or load after idle (`requestIdleCallback`). Only minimal, deterministic zero-dependency theme scripts (`ThemeScript.astro`) may execute inline to prevent FOUC.
2. **Prevent Browser API SSR Hydration Hazards**: Analytics initialization and event pushes (`window.dataLayer.push`) must never execute during server-side module evaluation or before client DOM mount.
3. **CSP & Sentry Telemetry Hygiene**: Strict Content Security Policy (CSP) headers must govern script origins. Sentry error tracking must initialize asynchronously, and production sourcemaps must be uploaded to Sentry and stripped from public CDN distribution.

### Astro Architectural & Best Practice Rules

All third-party script integrations, analytics pipelines, and telemetry must adhere to the authoritative best practices:

- [21-track-pageviews-in-client-router-with-astro-page-load.md](../../best-practices/03-routing-and-pages/21-track-pageviews-in-client-router-with-astro-page-load.md) — SPA analytics tracking via `astro:page-load` under ClientRouter navigation (preventing loss of ~70% of pageviews).
- [08-actions-vs-endpoints-mutations.md](../../best-practices/05-data-fetching-and-endpoints/08-actions-vs-endpoints-mutations.md) — Standardized backend communication without ad-hoc tracking endpoints.
- [13-handle-csrf-and-check-origin-on-external-endpoints.md](../../best-practices/05-data-fetching-and-endpoints/13-handle-csrf-and-check-origin-on-external-endpoints.md) — Handling CSRF and origin checks for incoming analytics beacons or external ingestion webhooks.
- [14-progressive-enhancement-with-astro-actions.md](../../best-practices/05-data-fetching-and-endpoints/14-progressive-enhancement-with-astro-actions.md) — Zero-JS progressive enhancement preventing analytics blockers from impeding form submissions.
- [15-stateless-edge-rate-limiting.md](../../best-practices/06-middleware-and-auth/15-stateless-edge-rate-limiting.md) — Edge rate limiting for telemetry and beacon ingestion endpoints.

Critical files to inspect:

- src/layouts/SiteLayout.astro
- src/components/ThemeScript.astro
- scripts/release/sentry/
- astro.config.mjs
- src/worker.ts (CSP header dispatch)

## 3.2 Mission Objective

Audit all third-party script loading, tracking beacons, and error telemetry integrations.
Outcome: Confirm that no third-party script blocks the critical render path, CSP headers authorize all external domains, Sentry telemetry operates asynchronously, and zero SSR hydration mismatches occur.
Constraints: Read-only audit; check script attributes and CSP policies.
Autonomy Grant: You own this mission end-to-end. Inspect network waterfall profiles, async loaders, and CSP hashes. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Audit layout `<head>` tags for blocking script tags and hydration hazards:
   - ❌ Bad Practice / Anti-Pattern (Blocking Script & Unguarded Window Push):
     ```html
     <!-- Anti-Pattern: Blocks HTML parser in <head> and risks SSR failure -->
     <script src="https://www.googletagmanager.com/gtm.js?id=GTM-XXXX"></script>
     <script>
       window.dataLayer = window.dataLayer || []
     </script>
     ```
   - ✅ Best Practice / Idiomatic (Deferred Script & Guarded Client Execution):
     ```astro
     <!-- Idiomatic: Non-blocking deferred loading and guarded client execution -->
     <script is:inline defer src="https://www.googletagmanager.com/gtm.js?id=GTM-XXXX"></script>
     <script>
       if (typeof window !== 'undefined') {
         window.dataLayer = window.dataLayer || [];
       }
     </script>
     ```

2. Contrast client router analytics tracking against legacy static tag insertion:
   - ❌ Bad Practice / Anti-Pattern (Injecting Tracking Scripts Without astro:page-load):
     ```html
     <!-- src/components/Analytics.astro -->
     <!-- Fails: Standard snippet only fires on initial load; misses ~70% of SPA client-side navigations -->
     <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXX"></script>
     <script>
       window.dataLayer = window.dataLayer || []
       function gtag() {
         dataLayer.push(arguments)
       }
       gtag('js', new Date())
       gtag('config', 'G-XXXXX') // Misses all soft client router page transitions!
     </script>
     ```
   - ✅ Best Practice / Idiomatic (SPA-Aware Analytics with astro:page-load):
     ```astro
     <!-- src/components/Analytics.astro -->
     <script is:inline define:vars={{ gaId: "G-XXXXX" }}>
       window.dataLayer = window.dataLayer || [];
       function gtag() { window.dataLayer.push(arguments); }
       gtag('js', new Date());
       // Disable automatic page_view to prevent double counting on initial load
       gtag('config', gaId, { send_page_view: false });

       // Listen to astro:page-load for initial load and all SPA transitions
       document.addEventListener('astro:page-load', () => {
         gtag('event', 'page_view', {
           page_title: document.title,
           page_location: window.location.href,
           page_path: window.location.pathname,
         });
       });
     </script>
     ```

3. Contrast client-side blocking tracking logic on form submissions with progressive enhancement:
   - ❌ Bad Practice / Anti-Pattern (Form Blocked by Analytics JS):
     ```html
     <!-- Form submission completely blocked if analytics script fails to load -->
     <form id="lead-form">
       <input name="email" type="email" required />
       <button type="submit">Submit</button>
     </form>
     <script>
       document.getElementById('lead-form').addEventListener('submit', (e) => {
         e.preventDefault()
         gtag('event', 'lead_submit')
         fetch('/api/lead', { method: 'POST' })
       })
     </script>
     ```
   - ✅ Best Practice / Idiomatic (Progressive Enhancement via Astro Actions):
     ```astro
     ---
     import { actions } from "astro:actions";
     ---
     <form method="POST" action={actions.submitLead}>
       <input name="email" type="email" required />
       <button type="submit">Submit</button>
     </form>
     ```

4. Verify that GTM and analytics do not trigger long tasks (>50ms) during initial interaction.
5. Confirm that Sentry release configuration uploads sourcemaps without shipping unminified `.js.map` files to public CDN.

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/02-zero-js-hydration/19-third-party-scripts-analytics/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Best Practice Mapping Requirement**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule (e.g. `RULE-ID: 03-21-track-pageviews-astro-page-load`, `RULE-ID: 05-08-actions-vs-endpoints-mutations`, `RULE-ID: 05-13-handle-csrf-check-origin`, `RULE-ID: 05-14-progressive-enhancement`, or `RULE-ID: 06-15-stateless-edge-rate-limiting`).

You must create and populate the following deliverables in `docs/audits/results/02-zero-js-hydration/19-third-party-scripts-analytics/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "19-THIRD-PARTY-SCRIPTS-ANALYTICS-001",
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
   - **Outer Tier (localized primary locale): Conversational human summary (1-2 sentences), affected URLs/routes table, surface area table (viewports, themes, components), observed defect vs expected behavior (WITHOUT prescribing code fixes).
   - **Inner Tier (English `<details>`): Collapsed block titled `<details><summary><strong>Agent implementation brief — scope, source map, behavior contracts, and verification</strong></summary>...</details>`. Contains exact `file:line` citations, quoted 3-8 lines of code, defect classification (`bug` | `by-design` | `drift` | `reversal`), required behavioral invariants, known traps, acceptance checklist, and embeds the structured `findings.json` table and `handoff.md` remediation steps.

5. **Publication via GitHub CLI (`gh`) & Sub-Issue Creation**:
   Execute the turnkey publisher script using which automatically verifies the 60,000-char limit, checklist nesting, creates the primary issue, spawns linked sub-issues (up to 20) for critical/high defects, and pushes the JSON deliverables to `origin main`:

```bash
# Turnkey Script (node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/02-zero-js-hydration/19-third-party-scripts-analytics/issue-body.md" \
  --title "[Audit - Third-Party Scripts & Analytics Loading Discipline Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/02-zero-js-hydration/19-third-party-scripts-analytics/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Execute CLI audits on script tags, CSP headers, and sourcemap files:
   ```bash
   # 1. Audit all <script> tags in layouts and components for blocking external scripts
   git grep -n "<script" src/layouts/ src/components/ | grep -v -E "(type=\"module\"|defer|async|is:inline)" || echo "Clean: All scripts use module/defer/async"
   # 2. Check for SPA client router tracking hooks
   git grep -n "astro:page-load" src/
   # 3. Check for Astro Actions usage in form submission flows
   git grep -n "actions\." src/
   # 4. Check CSP header configuration in Cloudflare Worker edge entry
   git grep -n "Content-Security-Policy" src/ edge/ workers/
   # 5. Verify public build output does NOT expose unminified .map files
   find dist/ -name "*.map" | wc -l
   # 6. Check for un-guarded window.dataLayer or analytics references
   git grep -n "dataLayer" src/ | grep -v "typeof window" || echo "Verify window guards on analytics"
   ```
2. Verify that Content Security Policy directives restrict `script-src` strictly to authorized hosts.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/02-zero-js-hydration/19-third-party-scripts-analytics/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Third-Party Scripts & Analytics Loading Discipline Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/02-zero-js-hydration/19-third-party-scripts-analytics/findings.json` (N defects logged)
   - `file://docs/audits/results/02-zero-js-hydration/19-third-party-scripts-analytics/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/02-zero-js-hydration/19-third-party-scripts-analytics/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/02-zero-js-hydration/19-third-party-scripts-analytics/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/02-zero-js-hydration/19-third-party-scripts-analytics/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
