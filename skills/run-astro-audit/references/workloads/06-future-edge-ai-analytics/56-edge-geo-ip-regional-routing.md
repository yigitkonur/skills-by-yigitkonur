# Mission Brief: Edge Geo-IP Regional Routing & Language Preference Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

Cloudflare Workers provides `request.cf.country` and `request.cf.city` on every incoming HTTP request.
The application operates commercial services across Turkey, UK/Europe, and GCC/Middle East (UAE, Saudi Arabia).
Edge worker `src/worker.ts` and dynamic endpoints can use geolocation to suggest appropriate regional content (e.g. suggesting localized secondary locale to GCC visitors, localized primary locale to TR visitors).

Key Astro Best Practice contracts for Regional Routing & i18n:

1. **Multi-Domain Routing Architectural Gate**: Configuring `i18n.domains` in `astro.config.mjs` strictly requires `output: "server"` with an SSR adapter. Attempting to use `i18n.domains` in `output: "static"` mode triggers the fatal compiler error `NoPrerenderedRoutesWithDomains`. Reverse proxies must pass `Host` and `X-Forwarded-Host` headers so `Astro.currentLocale` and `getAbsoluteLocaleUrl()` resolve correctly.
2. **SEO Crawler Safety & CDN Cache Purity**: NEVER execute hard HTTP 301/302 redirects based on `request.cf.country` on edge requests. Hard geo-redirects break Googlebot/Bingbot indexing (crawlers primarily originate from US IP addresses) and poison Cloudflare CDN edge caches across regions unless expensive custom cache keys are maintained.
3. **Non-Intrusive Regional Discovery**: Serve the canonical URL, and display a non-blocking regional suggestion banner (hydrated with `client:idle`).
4. **Dynamic Preference Endpoints & Root Headers**: Locale preference mutations (setting `user_locale` cookie) must declare `export const prerender = false;` and return standard Web API `Response` instances. In SSR mode, headers and cookies must be committed at the route root before HTML streaming commences.
5. **Zero-JS Edge Geo Inspection**: Inspect `context.request.headers.get('cf-ipcountry')` or `request.cf.country` at the edge to decorate headers without blocking the client or delaying TTFB.

Astro Architectural & Best Practice Rules:

- **Protect Authenticated Routes Server-Side via `context.cookies` and `context.redirect` ([06-auth-guard-session-validation.md](../../best-practices/06-middleware-and-auth/06-auth-guard-session-validation.md))**: Edge middleware and route handlers must inspect session cookies and geolocation headers atomically on the server before dispatching responses, preventing unauthenticated access or leaking localized private data (`ASTRO-BP-06-06`).
- **Compose i18n Routing Before Auth Guards to Handle Localized Protected Paths ([16-i18n-and-multilingual-auth-composition.md](../../best-practices/06-middleware-and-auth/16-i18n-and-multilingual-auth-composition.md))**: Compose regional routing rules and i18n path resolution in middleware so localized paths (`/tr/`, `/en/`, `/ar/`) are normalized before regional policy evaluation (`ASTRO-BP-06-16`).
- **Execute Site-Wide Performance Audits Using Unlighthouse Against Preview Server ([08-site-wide-crawling-with-unlighthouse.md](../../best-practices/10-auditing-testing-and-nextjs-migration/08-site-wide-crawling-with-unlighthouse.md))**: Verify that international visitor routing, hreflang tag parity, and localized routes crawl cleanly without edge redirection loops or CDN cache collisions (`ASTRO-BP-10-08`).
- **Eliminate Total Blocking Time (TBT) and Optimize INP Under 200ms ([15-eliminate-total-blocking-time-tbt-and-optimize-inp.md](../../best-practices/09-performance-prefetch-and-transitions/15-eliminate-total-blocking-time-tbt-and-optimize-inp.md))**: Regional suggestion banners and language switcher dialogs must use deferred hydration (`client:idle`) to guarantee 0ms TBT and responsive interaction (`ASTRO-BP-09-15`).
- **Prevent Cumulative Layout Shift (CLS) Across Media and Islands ([16-prevent-cumulative-layout-shift-cls.md](../../best-practices/09-performance-prefetch-and-transitions/16-prevent-cumulative-layout-shift-cls.md))**: Geo suggestion banners injected at the top of the viewport must reserve explicit layout containers to avoid layout reflows (CLS < 0.05) when rendered (`ASTRO-BP-09-16`).

Critical files to inspect:

- src/worker.ts
- edge/policy/
- src/components/chrome/LanguageSwitchLink.astro
- astro.config.mjs (i18n routing & domains configuration)
- src/pages/api/locale.ts (or dynamic preference handler)

## 3.2 Mission Objective

Audit edge geolocation handling, multi-domain routing configurations, and international visitor routing policies.
Outcome: Ensure that geo-detection does not poison Cloudflare CDN caches, strictly respects search engine crawler integrity, enforces multi-domain SSR contracts, respects manual user language preferences, and provides smooth GCC/TR regional discovery.
Constraints: Read-only audit; verify edge request handlers, cache headers, and i18n domain configurations.
Autonomy Grant: You own this mission end-to-end. Analyze Cloudflare request.cf properties, edge response decorators, and cookie flags. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `src/worker.ts`: check how `request.cf` is utilized and verify no hard redirects target search bots.
2. Verify `astro.config.mjs`: if `i18n.domains` is enabled, confirm `output: "server"` is configured and reverse proxies forward `Host` / `X-Forwarded-Host`.
3. Check `LanguageSwitchLink.astro`: verify that selecting a language sets an explicit cookie (`user_locale`) that overrides geo defaults.
4. Audit multi-domain and geo-routing contracts against anti-patterns:

### ❌ Bad Practice / Anti-Pattern (Blocking Client-Side Geo Redirection & Hard Edge 302s)

```html
<!-- ❌ Blocking Client-Side JS Geolocation Redirection: -->
<!-- Flashes English content, executes expensive navigator.geolocation or third-party IP lookup, -->
<!-- and forces a client-side location.href change causing massive CLS and broken crawler indexing -->
<script>
  fetch('https://ipapi.co/json/')
    .then((res) => res.json())
    .then((data) => {
      if (data.country_code === 'TR' && !window.location.pathname.startsWith('/tr/')) {
        window.location.href = '/tr' + window.location.pathname // Layout flashes and shifts!
      }
    })
</script>
```

```ts
// src/worker.ts (Edge Handler)
// ❌ CATASTROPHIC: Hard redirect destroys SEO and pollutes edge cache:
export default {
  async fetch(request) {
    const country = request.cf?.country
    // Hard redirecting sends Googlebot (US IP) to /en and caches the 302 on CDN!
    if (country === 'TR' && !request.url.includes('/tr/')) {
      return Response.redirect('https://example.com/tr/', 302)
    }
    return fetch(request)
  },
}
```

```js
// astro.config.mjs
// ❌ FAILS: Static mode cannot use i18n.domains; throws NoPrerenderedRoutesWithDomains:
export default defineConfig({
  output: 'static',
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'tr', 'ar'],
    domains: {
      tr: 'https://example.com.tr', // Compiler error in static mode!
    },
  },
})
```

### ✅ Best Practice / Idiomatic (Zero-JS Edge Middleware & Non-Intrusive Banner)

```typescript
// src/middleware.ts - Zero-JS Edge Inspection & Non-Intrusive Decoration
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  // Read geo headers provided by Cloudflare edge without blocking rendering
  const country = context.request.headers.get('cf-ipcountry') || 'US'
  const userLocaleCookie = context.cookies.get('user_locale')?.value

  // Pass geo metadata to locals for zero-JS Astro components:
  context.locals.geoCountry = country
  context.locals.preferredLocale = userLocaleCookie || (country === 'TR' ? 'tr' : 'en')

  const response = await next()

  // Ensure CDN cache respects country variance only if specifically partitioned:
  response.headers.set('Vary', 'Accept-Language, Cookie')
  return response
})
```

```astro
---
// src/components/chrome/GeoSuggestionBanner.astro
// ✅ Non-intrusive suggestion banner hydrated on idle, preserving SEO & zero layout shift:
import { getAbsoluteLocaleUrl } from "astro:i18n";

const country = Astro.locals.geoCountry || Astro.request.headers.get("cf-ipcountry");
const isTargetRegionVisitor = country === "DE" && Astro.currentLocale !== "de";
const targetUrl = getAbsoluteLocaleUrl("de", Astro.url.pathname);
---
{isTargetRegionVisitor && (
  <aside class="geo-banner min-h-[48px] w-full" data-nosnippet>
    <div class="flex items-center justify-between px-4 py-2 text-sm bg-neutral-100 dark:bg-neutral-800">
      <p>Visiting from Germany?</p>
      <a href={targetUrl} class="font-medium underline hover:text-accent">Switch to German version</a>
    </div>
  </aside>
)}
```

```js
// astro.config.mjs - Compliant Multi-Domain SSR
import { defineConfig } from 'astro/config'
import cloudflare from '@astrojs/cloudflare'

export default defineConfig({
  site: 'https://example.com',
  output: 'server', // Mandatory for i18n.domains
  adapter: cloudflare(),
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'tr', 'ar'],
    routing: { prefixDefaultLocale: false },
    domains: {
      tr: 'https://example.com.tr',
      ar: 'https://example.ae',
    },
  },
})
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/06-future-edge-ai-analytics/56-edge-geo-ip-regional-routing/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Rule ID Mapping**: All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an authoritative Astro best practice rule (e.g. `ASTRO-BP-06-06`, `ASTRO-BP-06-16`, `ASTRO-BP-10-08`, `ASTRO-BP-09-15`, `ASTRO-BP-09-16`).

You must create and populate the following deliverables in `docs/audits/results/06-future-edge-ai-analytics/56-edge-geo-ip-regional-routing/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "56-EDGE-GEO-IP-REGIONAL-ROUTING-001",
    "rule_id": "RULE-ID (e.g. ASTRO-BP-06-06 / ASTRO-BP-06-16 / ASTRO-BP-10-08)",
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
  --body "docs/audits/results/06-future-edge-ai-analytics/56-edge-geo-ip-regional-routing/issue-body.md" \
  --title "[Audit - Edge Geo-IP Regional Routing & Language Preference Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/06-future-edge-ai-analytics/56-edge-geo-ip-regional-routing/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Confirm that Cloudflare edge caches remain clean without cache-key collisions between countries.
2. Verify crawler safety by testing requests with Googlebot User-Agent:
   ```bash
   curl -sI -A "Googlebot" -H "CF-IPCountry: TR" http://localhost:8788/ | grep -i "location"
   # Verify output is empty (no 301/302 redirects for crawlers)
   ```
3. Verify simulated regional requests pass CF-IPCountry headers without hard redirects:
   ```bash
   curl -sI -H "CF-IPCountry: TR" http://localhost:8788/
   curl -sI -H "CF-IPCountry: SA" http://localhost:8788/
   ```
4. Verify simulated multi-domain requests pass host headers cleanly:
   ```bash
   curl -sI -H "Host: example.ae" http://localhost:8788/
   ```
5. Run site-wide crawler with Unlighthouse against preview server to detect localized route parity:
   ```bash
   pnpm exec unlighthouse --site http://localhost:8788
   ```
6. Verify dynamic preference endpoints declare `export const prerender = false`:
   ```bash
   rg "export const prerender = false" src/pages/api/
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/06-future-edge-ai-analytics/56-edge-geo-ip-regional-routing/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Edge Geo-IP Regional Routing & Language Preference Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/06-future-edge-ai-analytics/56-edge-geo-ip-regional-routing/findings.json` (N defects logged)
   - `file://docs/audits/results/06-future-edge-ai-analytics/56-edge-geo-ip-regional-routing/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/06-future-edge-ai-analytics/56-edge-geo-ip-regional-routing/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/06-future-edge-ai-analytics/56-edge-geo-ip-regional-routing/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/06-future-edge-ai-analytics/56-edge-geo-ip-regional-routing/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
