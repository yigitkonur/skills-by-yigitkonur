# Mission Brief: Middleware Static Asset Bypass & Edge CPU Preservation Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

In Astro SSR and Cloudflare Workers runtime environments, every incoming HTTP request traverses the edge delivery and middleware pipeline.
Unlike Next.js which utilizes an engine-level `config.matcher` export to exclude static files before executing middleware, Astro requires programmatic filtering via `context.url.pathname`.
If middleware or worker handlers lack an immediate early return bypass for static assets (`/_astro/*`, `/assets/*`, `/fonts/*`, `/favicon.ico`, `/robots.txt`, images, and hashed JS/CSS bundles), heavy operations (cookie parsing, session lookups, header decoration) execute on every single static asset request. In edge environments with strict CPU limits (Cloudflare Workers 50ms limit), this causes edge compute exhaustion, worker throttles, and degraded Time to First Byte (TTFB).
Furthermore, when inspecting routes for protection or authentication, path canonicalization (CVE-2026-59731 / GHSA-vj59-8hwv-xxmv) is required: naive `.startsWith()` checks can be bypassed by percent-encoded slashes (`%252fadmin`), duplicate slashes (`//admin`), or directory traversal (`/admin/..%2fadmin`).

### Authoritative Astro Architectural & Best Practice Rules

Auditors must inspect, evaluate, and verify all code patterns against the repository's authoritative Astro best practices:

- **Primary Contract**: [05-filter-static-asset-requests.md](../../best-practices/06-middleware-and-auth/05-filter-static-asset-requests.md) — Filter out static assets before executing heavy middleware logic (`/_astro/`, images, fonts, `favicon.ico`).
- **Middleware State Contract**: [04-mutate-locals-never-reassign.md](../../best-practices/06-middleware-and-auth/04-mutate-locals-never-reassign.md) — Mutate `context.locals` properties; never overwrite the object.
- **Streaming Pipeline Contract**: [19-avoid-consuming-streaming-response-body-in-middleware.md](../../best-practices/06-middleware-and-auth/19-avoid-consuming-streaming-response-body-in-middleware.md) — Avoid consuming streaming response bodies in post-execution middleware.
- **Frontmatter Security Contract**: [03-frontmatter-security-boundary.md](../../best-practices/01-architecture-and-philosophy/03-frontmatter-security-boundary.md) — Isolate secrets and database calls in frontmatter without leaking to client bundles.
- **Server Islands Architecture**: [11-defer-personalized-content-with-server-islands.md](../../best-practices/02-islands-and-hydration/11-defer-personalized-content-with-server-islands.md) — Defer personalized content with Server Islands (`server:defer`).
- **Island URL Boundary**: [12-keep-server-island-props-under-url-limit.md](../../best-practices/02-islands-and-hydration/12-keep-server-island-props-under-url-limit.md) — Keep Server Island props lightweight and under URL length limits (< 2048 bytes).
- **Headless Unit Testing**: [21-unit-test-components-with-astro-container-api.md](../../best-practices/10-auditing-testing-and-nextjs-migration/21-unit-test-components-with-astro-container-api.md) — Unit test `.astro` components headlessly with the Astro Container API.

Critical files to inspect:

- `src/worker.ts`
- `src/middleware.ts` (if present)
- `edge/policy/asset-paths.mjs`
- `edge/policy/classify.mjs`
- `edge/policy/decorate.mjs`

## 3.2 Mission Objective

Audit all edge middleware, delivery policies, and worker entrypoints to verify strict static asset filtering, early return execution, and path canonicalization.
Outcome: Guarantee zero unnecessary middleware execution cycles for static assets, saving 100% of edge CPU quota for dynamic routes, and ensure zero auth bypass gaps.
Constraints: Read-only audit; do not alter production code.
Autonomy Grant: You own this mission end-to-end. Inspect middleware entrypoints, check regex patterns, and measure edge bypass efficiency. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `src/worker.ts`, `edge/policy/asset-paths.mjs`, and `edge/policy/classify.mjs`.
2. Verify that static prefixes (`/_astro/`, `/assets/`, `/fonts/`, `/favicon.ico`, `/robots.txt`) and file extension patterns (`\.(svg|png|jpg|webp|avif|woff2|css|js|ico|xml|txt)$`) immediately bypass processing and return without overhead.
3. Check whether `context.isPrerendered` is utilized to bypass dynamic session verification on statically generated routes.
4. Verify that authorization guards apply path canonicalization (`decodeURIComponent(pathname).replace(/\/+/g, '/').toLowerCase()`) rather than raw `.startsWith()` comparisons.

### ❌ Bad Practice / Anti-Pattern (Next.js Legacy Assumption & Unfiltered Static Execution)

```typescript
// src/middleware.ts (Heavy lookups on static assets & naive auth guard)
// Next.js developers often rely on config.matcher; omitting programmatic checks in Astro runs on ALL requests!
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  // ❌ Burns edge CPU on /_astro/style.css, /assets/hero.webp, /favicon.ico, and fonts!
  // In Cloudflare Workers, this triggers CPU time-limit throttles (50ms quota).
  const sessionToken = context.cookies.get('session')?.value
  context.locals.user = await db.verifySession(sessionToken)

  // ❌ Vulnerable to %2fadmin or //admin auth bypass (GHSA-vj59-8hwv-xxmv)
  if (context.url.pathname.startsWith('/admin') && !context.locals.user) {
    return context.redirect('/login')
  }

  return next()
})
```

### ✅ Best Practice / Idiomatic (Astro Programmatic Fast-Path Regex & Path Canonicalization)

```typescript
// src/middleware.ts (Fast static bypass + canonicalized path protection)
// Bound to RULE-ID: 06-middleware-and-auth/05-filter-static-asset-requests
import { defineMiddleware } from 'astro:middleware'

const STATIC_PREFIXES = ['/_astro/', '/assets/', '/fonts/', '/favicon.ico', '/robots.txt']
const STATIC_EXTENSION_REGEX =
  /\.(css|js|webp|avif|svg|png|jpg|jpeg|gif|woff2?|ttf|eot|ico|xml|txt|webmanifest)$/i

function getCanonicalPath(pathname: string): string {
  try {
    return decodeURIComponent(pathname).replace(/\/+/g, '/').toLowerCase()
  } catch {
    return pathname.toLowerCase()
  }
}

export const onRequest = defineMiddleware(async (context, next) => {
  const { pathname } = context.url

  // ✅ Immediately bypass middleware for static bundles, public prefixes, and asset extensions
  if (
    STATIC_PREFIXES.some((prefix) => pathname.startsWith(prefix)) ||
    STATIC_EXTENSION_REGEX.test(pathname)
  ) {
    return next()
  }

  // ✅ Skip prerendered pages if dynamic session checks are not required
  if (context.isPrerendered) {
    return next()
  }

  // ✅ Protect routes using canonicalized paths against directory traversal & encoded slashes
  const canonicalPath = getCanonicalPath(pathname)
  if (canonicalPath === '/admin' || canonicalPath.startsWith('/admin/')) {
    const user = context.locals.user
    if (!user) return context.redirect('/login', 302)
  }

  return next()
})
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/07-migration-and-core-contracts/66-middleware-static-asset-bypass-cpu/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Rule-ID Mapping**: Every item in `findings.json` MUST explicitly map to an authoritative Astro best practice rule ID (e.g. `RULE-ID: 06-middleware-and-auth/05-filter-static-asset-requests`).

You must create and populate the following deliverables in `docs/audits/results/07-migration-and-core-contracts/66-middleware-static-asset-bypass-cpu/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "66-MIDDLEWARE-STATIC-ASSET-BYPASS-CPU-001",
    "rule_id": "RULE-ID: 06-middleware-and-auth/05-filter-static-asset-requests",
    "file": "src/worker.ts",
    "line": 42,
    "severity": "critical" | "high" | "medium" | "low",
    "category": "performance" | "security" | "syntax" | "hydration" | "parity",
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
  --body "docs/audits/results/07-migration-and-core-contracts/66-middleware-static-asset-bypass-cpu/issue-body.md" \
  --title "[Audit - Middleware Static Asset Bypass & Edge CPU Preservation Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/07-migration-and-core-contracts/66-middleware-static-asset-bypass-cpu/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Run `git grep -n "defineMiddleware" src/` and `git grep -n "STATIC_PREFIXES\|startsWith('/_astro')\|pageAssetCandidate" src/ edge/` to audit static asset bypass routes.
2. Run `git grep -n "isPrerendered" src/ edge/` to verify prerender bypass logic.
3. Run `git grep -n "server:defer" src/` to verify coexistence with Server Island routes.
4. Execute headless component and middleware unit tests with Vitest using `experimental_AstroContainer` from `astro/container`:
   ```bash
   pnpm exec vitest run tests/edge/ tests/middleware/ --run
   ```
5. Test static asset response headers and timing:
   ```bash
   curl -I http://localhost:4321/_astro/client.bundle.js
   ```
   (Static response should be served immediately with minimal latency (<5ms) and without session query overhead).
6. Run adversarial path tests to verify canonicalization:
   ```bash
   curl -i http://localhost:4321/%2fadmin
   curl -i http://localhost:4321//admin/dashboard
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/07-migration-and-core-contracts/66-middleware-static-asset-bypass-cpu/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Middleware Static Asset Bypass & Edge CPU Preservation Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/07-migration-and-core-contracts/66-middleware-static-asset-bypass-cpu/findings.json` (N defects logged with RULE-ID mappings)
   - `file://docs/audits/results/07-migration-and-core-contracts/66-middleware-static-asset-bypass-cpu/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/07-migration-and-core-contracts/66-middleware-static-asset-bypass-cpu/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/07-migration-and-core-contracts/66-middleware-static-asset-bypass-cpu/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/07-migration-and-core-contracts/66-middleware-static-asset-bypass-cpu/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
