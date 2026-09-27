# Mission Brief: Edge Cache & Stale-While-Revalidate Policy Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

Astro stabilizes Cloudflare Edge CDN cache providers via Cloudflare Workers adapter bindings.
Static assets in `dist/client/` are served with immutable long-term caching (`max-age=31536000, immutable`).
HTML pages use short edge TTLs with stale-while-revalidate to ensure instant delivery while refreshing in the background.
Architectural facts and caching tiers:

- Tiered Caching Taxonomy: Cloudflare edge responses must be partitioned into strict caching tiers:
  1. Static Immutable Assets (`dist/client/_astro/*`): Content-hashed JavaScript, CSS, and optimized images must specify `Cache-Control: public, max-age=31536000, immutable`.
  2. Marketing HTML Documents: Prerendered static pages must specify short browser TTL with edge stale-while-revalidate (`Cache-Control: public, max-age=0, s-maxage=3600, stale-while-revalidate=86400, stale-if-error=604800`) to guarantee instant edge cache delivery while revalidating asynchronously in background.
  3. On-Demand Dynamic Routes (`/form-result`, satellite API proxies): Must explicitly set `Cache-Control: private, no-store, no-cache, must-revalidate` to prevent edge caching of personalized or session data.
- Conditional Requests & ETags: The worker must evaluate `If-None-Match` request headers against entity tags, returning `HTTP 304 Not Modified` to eliminate payload transfer.
- Cloudflare Edge Early Hints (103): Emitting `103 Early Hints` for critical CSS chunks and preloaded Gilroy fonts (`Link: </_astro/...css>; rel=preload; as=style`) dramatically improves First Contentful Paint (FCP).
- Stale-If-Error Edge Resilience: When backend satellites (forms, AI, search) experience transient latency or 5xx outages, the edge worker must serve stale cached marketing HTML rather than failing hard with a 500 error.

### Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`10-response-headers-immutability-and-html-streaming.md`](../../best-practices/05-data-fetching-and-endpoints/10-response-headers-immutability-and-html-streaming.md) — Configuring response headers at the route root before HTML streaming begins, edge Cache-Control headers, and stale-while-revalidate policy (`RULE-ID: ASTRO-DATA-10`).
- [`11-server-adapters-and-runtime-environment.md`](../../best-practices/05-data-fetching-and-endpoints/11-server-adapters-and-runtime-environment.md) — Cloudflare Workers adapter caching interfaces, prerender boundary separation, and dynamic vs. static route execution (`RULE-ID: ASTRO-DATA-11`).
- [`02-mpa-memory-lifecycle.md`](../../best-practices/01-architecture-and-philosophy/02-mpa-memory-lifecycle.md) — MPA clean memory lifecycle, client-side document teardown, and deterministic cache invalidation on page navigation (`RULE-ID: ASTRO-ARCH-02`).
- [`10-vite-build-pipeline-and-tree-shaking.md`](../../best-practices/01-architecture-and-philosophy/10-vite-build-pipeline-and-tree-shaking.md) — Vite build pipeline, content-hashed asset emits in `dist/client/_astro/`, and immutable cache targeting (`RULE-ID: ASTRO-ARCH-10`).
- [`16-isolate-vite-cache-across-concurrent-dev-instances.md`](../../best-practices/01-architecture-and-philosophy/16-isolate-vite-cache-across-concurrent-dev-instances.md) — Isolating cache directories across dev and edge preview servers to prevent stale cache contamination (`RULE-ID: ASTRO-ARCH-16`).

Critical files to inspect:

- `src/worker.ts` (`handleRequest` & cache header injector)
- `edge/policy/`
- `astro.config.mjs`
- `tests/int/edge-caching-policy.test.ts`

## 3.2 Mission Objective

Audit edge response headers, Cache-Control directives, and Cloudflare CDN caching rules.
Outcome: Ensure static assets are cached permanently, HTML pages serve instant edge responses with stale-while-revalidate, HTTP 103 Early Hints emission is evaluated for critical CSS/fonts, dynamic form-result pages carry no-store headers, and transient satellite outages fall back gracefully to stale cache.
Constraints: Read-only audit; verify HTTP headers.
Autonomy Grant: You own this mission end-to-end. Trace response headers, CDN cache HIT/MISS behavior, and edge bypass conditions. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `src/worker.ts` `handleRequest()`: verify `Cache-Control` header assignments based on asset type.
2. Verify that on-demand SSR routes (`/form-result`, `/api/*`) never set immutable or long-lived cache headers.
3. Test ETags and `304 Not Modified` responses for revalidated content.
4. Check Cloudflare Worker Early Hints (103): test if preloading critical stylesheets via Early Hints accelerates First Contentful Paint.
5. Test edge resilience: verify that a satellite timeout serves cached marketing content rather than a 500 error.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Omitting `stale-while-revalidate` on Edge Cache-Control Headers Causing Cold Start Latencies (RULE-ID: ASTRO-DATA-10)

##### ❌ Bad Practice / Anti-Pattern: Omitting `stale-while-revalidate` on edge cache-control headers, causing cold start latencies

```typescript
// src/worker.ts - Omitting stale-while-revalidate on marketing HTML
export function applyEdgeCachePolicy(pathname: string, headers: Headers): void {
  if (pathname.endsWith('/') || pathname.endsWith('.html')) {
    // ❌ Anti-Pattern: No SWR directive forces cache misses to block requests and hit origin
    headers.set('Cache-Control', 'public, max-age=0, must-revalidate')
  }
}
```

_Why this fails:_ When the CDN edge cache expires or encounters a miss, omitting `stale-while-revalidate` forces the edge proxy to block the incoming client request while re-fetching from origin or re-executing SSR, introducing severe latency spikes and cold-start delays.

##### ✅ Best Practice / Idiomatic: Setting `Cache-Control: public, max-age=3600, stale-while-revalidate=86400`

```typescript
// src/worker.ts - Tiered edge caching strategy with SWR and dynamic protection
export function applyEdgeCachePolicy(pathname: string, headers: Headers): void {
  // ✅ Best Practice: Setting public cache with stale-while-revalidate
  // Instant edge delivery with background revalidation and stale-if-error resilience
  headers.set(
    'Cache-Control',
    'public, max-age=3600, stale-while-revalidate=86400, stale-if-error=604800',
  )
}
```

#### Pattern 2: Modifying Cache Headers in Child Components After HTML Streaming Commences (RULE-ID: ASTRO-DATA-10)

##### ❌ Bad Practice / Anti-Pattern: Mutating response headers inside nested child components

```astro
---
// src/components/MarketingSection.astro (Nested Child Component)
// ❌ FAILS IN ON-DEMAND SSR: HTTP header block already closed by the time child renders!
Astro.response.headers.set(
  "Cache-Control",
  "public, max-age=3600, stale-while-revalidate=86400"
);
---
<section class="marketing-band">...</section>
```

_Why this fails:_ Astro streams HTML chunks progressively to the client in SSR mode. HTTP status codes and response headers are committed immediately when the top-level route begins output. Modifying headers inside child components triggers console warnings and has zero effect on the emitted edge HTTP response.

##### ✅ Best Practice / Idiomatic: Configuring headers at the route root or edge entrypoint

```astro
---
// src/pages/services/[slug].astro (Top-Level Page Route)
export const prerender = false;

// ✅ Set response headers at the PAGE ROOT before HTML streaming commences:
Astro.response.headers.set(
  "Cache-Control",
  "public, max-age=3600, stale-while-revalidate=86400"
);
---
<Layout>
  <MarketingSection />
</Layout>
```

#### Pattern 3: Overly Broad Caching Leaking Dynamic Form Results vs. Strict Tiered Cache Partitioning (RULE-ID: ASTRO-DATA-10, RULE-ID: ASTRO-DATA-11)

##### ❌ Bad Practice / Anti-Pattern: Overly broad caching leaking dynamic data or serving stale HTML indefinitely

```typescript
// src/worker.ts - Overly broad caching leaking dynamic data or serving stale HTML indefinitely
export default {
  async fetch(request: Request, env: any) {
    const response = await handleRequest(request, env)
    // ❌ BAD: Blindly setting public immutable cache on ALL responses!
    // Dynamic form results and CSRF tokens get cached at Cloudflare edge CDN.
    response.headers.set('Cache-Control', 'public, max-age=31536000, immutable')
    return response
  },
}
```

_Why this fails:_ Caching dynamic routes at the edge causes privacy leaks, CSRF verification failures, and outdated transactional states. Omitting `stale-while-revalidate` on HTML forces cache misses to block the user.

##### ✅ Best Practice / Idiomatic: Three-tier edge caching strategy

```typescript
// src/worker.ts - Tiered edge caching strategy with SWR and dynamic protection
export function applyEdgeCachePolicy(pathname: string, headers: Headers): void {
  // Tier 1: Content-hashed static assets (never change)
  if (pathname.startsWith('/_astro/') || pathname.startsWith('/assets/')) {
    headers.set('Cache-Control', 'public, max-age=31536000, immutable')
    return
  }

  // Tier 2: Dynamic / On-Demand / Form submissions (never cache)
  if (pathname.startsWith('/api/') || pathname === '/form-result') {
    headers.set('Cache-Control', 'private, no-store, no-cache, must-revalidate')
    return
  }

  // Tier 3: Marketing HTML - Instant edge delivery with async revalidation
  headers.set(
    'Cache-Control',
    'public, max-age=0, s-maxage=3600, stale-while-revalidate=86400, stale-if-error=604800',
  )
}
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/05-edge-workers-and-qa/42-edge-cache-stale-while-revalidate/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: ASTRO-DATA-10`, `RULE-ID: ASTRO-DATA-11`, `RULE-ID: ASTRO-ARCH-02`, `RULE-ID: ASTRO-ARCH-10`, `RULE-ID: ASTRO-ARCH-16`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/05-edge-workers-and-qa/42-edge-cache-stale-while-revalidate/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "42-EDGE-CACHE-STALE-WHILE-REVALIDATE-001",
    "rule_id": "RULE-ID: ASTRO-DATA-10 (Configure Response Headers at Route Root Before HTML Streaming Commences)",
    "file": "src/worker.ts",
    "line": 42,
    "severity": "critical",
    "category": "performance",
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
   Execute the turnkey publisher script using `node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting (max 200 items, 3 levels deep), creates the primary issue, spawns linked sub-issues (capped at 20) for critical and high severity defects, and pushes the JSON deliverables to `origin main` directly:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/05-edge-workers-and-qa/42-edge-cache-stale-while-revalidate/issue-body.md" \
  --title "[Audit - Edge Cache & Stale-While-Revalidate Policy Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/05-edge-workers-and-qa/42-edge-cache-stale-while-revalidate/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Confirm that `/_astro/*.css` and `/_astro/*.js` responses carry `max-age=31536000, immutable`:
   ```bash
   curl -sI http://localhost:4321/_astro/test.css | grep -i "cache-control"
   ```
2. Confirm that `/form-result` and API endpoints carry `Cache-Control: private, no-store`:
   ```bash
   curl -sI http://localhost:4321/form-result | grep -i "cache-control"
   ```
3. Verify marketing HTML serves `stale-while-revalidate`:
   ```bash
   curl -sI http://localhost:4321/en/ | grep -i "cache-control"
   ```
4. Test conditional requests return 304 Not Modified:
   ```bash
   ETAG=$(curl -sI http://localhost:4321/ | grep -i "etag" | awk '{print $2}' | tr -d '\r'); if [ -n "$ETAG" ]; then curl -sI -H "If-None-Match: $ETAG" http://localhost:4321/ | grep -E "HTTP/.* 304"; fi
   ```
5. Audit Cache-Control directives and headers in edge worker source:
   ```bash
   git grep -n "Cache-Control" src/worker.ts edge/
   ```
6. Run edge caching policy integration tests:
   ```bash
   pnpm vitest run tests/int/edge-caching-policy.test.ts
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/05-edge-workers-and-qa/42-edge-cache-stale-while-revalidate/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Edge Cache & Stale-While-Revalidate Policy Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/05-edge-workers-and-qa/42-edge-cache-stale-while-revalidate/findings.json` (N defects logged with RULE-ID mapping)
   - `file://docs/audits/results/05-edge-workers-and-qa/42-edge-cache-stale-while-revalidate/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/05-edge-workers-and-qa/42-edge-cache-stale-while-revalidate/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/05-edge-workers-and-qa/42-edge-cache-stale-while-revalidate/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/05-edge-workers-and-qa/42-edge-cache-stale-while-revalidate/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
