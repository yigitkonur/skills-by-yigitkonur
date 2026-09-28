# Mission Brief: CSP Level 3 & Edge Security Hardening Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

Security headers are injected by `src/worker.ts` and Cloudflare delivery policies:

- Content-Security-Policy (CSP Level 3) using Astro finer-grained directives
- Strict-Transport-Security (`HSTS: max-age=63072000; includeSubDomains; preload`)
- X-Content-Type-Options: `nosniff`
- X-Frame-Options: `DENY` / `frame-ancestors 'none'`
- Referrer-Policy: `strict-origin-when-cross-origin`
- Permissions-Policy restricting `camera=(), microphone=(), geolocation=()`
- Middleware Interception Contract: In Astro, security headers must be applied to outgoing responses in post-execution middleware (`const response = await next()`). Augmenting existing response headers on `text/html` responses ensures all routes adhere to security baselines without stripping downstream headers (such as `Set-Cookie`, `Cache-Control`, or custom status codes).
- Zero-Secret Leakage Mandate: Emitted client JavaScript chunks, source maps, and static assets in `dist/` must remain completely free of server runtime secrets, private API tokens, or `.env` credentials.

### Authoritative Astro Architectural & Best Practice Rules

Every finding, security header directive, and edge middleware rule in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`10-inject-security-headers-and-csp.md`](../../best-practices/06-middleware-and-auth/10-inject-security-headers-and-csp.md) — Injecting security headers and CSP in post-execution middleware without dropping existing headers or cookies (`RULE-ID: 06-middleware-and-auth/10-inject-security-headers-and-csp`).
- [`11-server-secrets-astro-env.md`](../../best-practices/06-middleware-and-auth/11-server-secrets-astro-env.md) — Access server secrets in middleware via `astro:env/server` with schema validation, preventing leaked API tokens in client bundles (`RULE-ID: 06-middleware-and-auth/11-server-secrets-astro-env`).
- [`19-avoid-consuming-streaming-response-body-in-middleware.md`](../../best-practices/06-middleware-and-auth/19-avoid-consuming-streaming-response-body-in-middleware.md) — Mutating headers directly on outgoing responses without consuming streaming response bodies (`RULE-ID: 06-middleware-and-auth/19-avoid-consuming-streaming-response-body-in-middleware`).
- [`06-enforce-astro-check-quality-gate-in-ci.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/06-enforce-astro-check-quality-gate-in-ci.md) — Enforce `astro check` in CI to validate middleware types and edge environment contracts (`RULE-ID: 10-auditing-testing-and-nextjs-migration/06-enforce-astro-check-quality-gate-in-ci`).
- [`05-run-built-in-a11y-audits-with-dev-toolbar.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/05-run-built-in-a11y-audits-with-dev-toolbar.md) — Ensuring developer toolbar and local auditing assets are safely isolated from production CSP policies (`RULE-ID: 10-auditing-testing-and-nextjs-migration/05-run-built-in-a11y-audits-with-dev-toolbar`).

Critical files to inspect:

- `src/worker.ts`
- `edge/policy/`
- `astro.config.mjs`
- `package.json`

## 3.2 Mission Objective

Audit all HTTP response security headers and CSP Level 3 directives.
Outcome: Prove A+ security posture on Mozilla Observatory and SecurityHeaders.com, zero unsafe-inline in script-src without strict hashes/nonces, proper isolation of external APIs, and execute a Secret Sentinel scan proving zero .env variables, private emails, or API tokens leak into emitted bundles or source maps.
Constraints: Read-only audit; inspect header injection logic and middleware pipelines.
Autonomy Grant: You own this mission end-to-end. Analyze CSP directives, SRI hash generation, and frame restrictions. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `src/worker.ts` `setSecurityHeaders()`: verify all required OWASP secure headers.
2. Check CSP directives: ensure `connect-src` permits only Cloudflare, Sentry, Turnstile, and forms satellite endpoints.
3. Verify that `frame-ancestors 'none'` prevents iframe clickjacking sitewide.
4. Run Secret Sentinel audit: scan `dist/` output for leaked private keys, API secrets, or unmasked credentials.
5. Verify middleware body handling: ensure `response.body` stream is never consumed with `response.text()` or `response.json()` during header decoration.

### Executable AST & Grep Audit Commands

Run these commands to inspect middleware security and CSP injection:

```bash
# Audit middleware for fresh Response instantiation that drops downstream headers:
git grep -rn "new Response(response.body" src/
# Audit for streaming body consumption (response.text/json) in middleware:
git grep -rnE "response\.(text|json)\(\)" src/
# Audit for server secret exposure via PUBLIC_ prefix:
git grep -rnE "PUBLIC_.*(SECRET|TOKEN|API_KEY|PRIVATE|KEY)" src/
# Audit CSP header injection in worker and edge middleware:
git grep -rn "Content-Security-Policy" src/ worker.ts edge/
# Inspect CSP headers on live or preview server:
curl -sI http://localhost:4321/ | grep -Ei "(content-security-policy|x-frame-options|strict-transport|x-content-type)"
```

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Fresh Response Discarding Downstream Headers (RULE-ID: 06-middleware-and-auth/10-inject-security-headers-and-csp)

##### ❌ Bad Practice / Anti-Pattern

```typescript
// src/worker.ts or src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next()
  // BAD: Fresh Response wipes out downstream Set-Cookie and status codes!
  // Insecure wildcard CSP permits arbitrary script injection and inline scripts without nonces
  return new Response(response.body, {
    headers: {
      'Content-Security-Policy': "default-src * 'unsafe-inline' 'unsafe-eval';",
    },
  })
})
```

_Why this fails:_ Re-instantiating `new Response()` breaks session management, cookie authentication, and form redirection. Permissive CSP policies defeat defense-in-depth, leaving users vulnerable to XSS and clickjacking.

##### ✅ Best Practice / Idiomatic

```typescript
// src/worker.ts or src/middleware.ts
import { defineMiddleware } from 'astro:middleware'

const SECURITY_HEADERS: Record<string, string> = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  'Content-Security-Policy':
    "default-src 'self'; script-src 'self' https://challenges.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://*.ingest.sentry.io https://challenges.cloudflare.com; frame-ancestors 'none'; base-uri 'self'; object-src 'none';",
}

export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next()
  const contentType = response.headers.get('Content-Type') || ''

  // Apply strict security headers to HTML documents while preserving downstream cookies & status
  if (contentType.includes('text/html')) {
    for (const [key, value] of Object.entries(SECURITY_HEADERS)) {
      if (!response.headers.has(key)) {
        response.headers.set(key, value)
      }
    }
  }
  return response
})
```

#### Pattern 2: Consuming Streaming Response Bodies in Middleware (RULE-ID: 06-middleware-and-auth/19-avoid-consuming-streaming-response-body-in-middleware)

##### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts - Consuming response body breaks chunked HTML streaming
export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next()

  // FATAL: Consuming response.text() permanently exhausts the stream and buffers entire HTML in RAM!
  if (response.headers.get('content-type')?.includes('text/html')) {
    const html = await response.text() // Exhausts stream!
    const modified = html.replace('</body>', "<script src='/security-tag.js'></script></body>")
    return new Response(modified, response)
  }
  return response
})
```

_Why this fails:_ `response.body` is a single-consumption `ReadableStream`. Awaiting `response.text()` buffers the entire document in memory, spikes V8 memory, delays TTFB, and throws `TypeError: Body has already been consumed`.

##### ✅ Best Practice / Idiomatic

```typescript
// src/middleware.ts - Mutate headers without consuming stream body
export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next()

  // Mutate headers directly on active streaming response without touching response.body
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('X-Frame-Options', 'DENY')

  // If HTML rewriting is required, pipe through TransformStream or HTMLRewriter
  return response
})
```

#### Pattern 3: Exposing Server Secrets via PUBLIC_ Prefixes (RULE-ID: 06-middleware-and-auth/11-server-secrets-astro-env)

##### ❌ Bad Practice / Anti-Pattern

```typescript
// src/middleware.ts - Exposing secrets with PUBLIC_ naming convention
export const onRequest = defineMiddleware((context, next) => {
  // CRITICAL SECURITY RISK: PUBLIC_ prefix exposes secret to browser bundles!
  const secretKey = import.meta.env.PUBLIC_JWT_SECRET
  context.locals.secretToken = secretKey
  return next()
})
```

_Why this fails:_ Next.js-style `PUBLIC_` conventions leak credentials into client-side bundles and source maps, exposing API secrets to external inspection.

##### ✅ Best Practice / Idiomatic

```typescript
// astro.config.mjs
import { defineConfig, envField } from 'astro/config'

export default defineConfig({
  env: {
    schema: {
      AUTH_SECRET: envField.string({ context: 'server', access: 'secret' }),
    },
    validateSecrets: true,
  },
})

// src/middleware.ts
import { AUTH_SECRET } from 'astro:env/server'

export const onRequest = defineMiddleware(async (context, next) => {
  // Secret is type-safe, validated at startup, and never bundled to client
  return next()
})
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/05-edge-workers-and-qa/45-csp-level-3-security-headers/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g., `RULE-ID: 06-middleware-and-auth/10-inject-security-headers-and-csp`, `RULE-ID: 06-middleware-and-auth/11-server-secrets-astro-env`, `RULE-ID: 06-middleware-and-auth/19-avoid-consuming-streaming-response-body-in-middleware`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/05-edge-workers-and-qa/45-csp-level-3-security-headers/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "45-CSP-LEVEL-3-SECURITY-HEADERS-001",
    "rule_id": "RULE-ID: 06-middleware-and-auth/10-inject-security-headers-and-csp",
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
  --body "docs/audits/results/05-edge-workers-and-qa/45-csp-level-3-security-headers/issue-body.md" \
  --title "[Audit - CSP Level 3 & Edge Security Hardening Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/05-edge-workers-and-qa/45-csp-level-3-security-headers/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Audit HTTP headers on rendered HTML responses to confirm all security headers are present:
   ```bash
   curl -sI http://localhost:4321/ | grep -Ei "(Content-Security-Policy|X-Content-Type-Options|X-Frame-Options|Referrer-Policy|Permissions-Policy|Strict-Transport-Security)"
   ```
2. Verify type safety and middleware contracts with `astro check`:
   ```bash
   pnpm exec astro check --minimumFailingSeverity error
   ```
3. Run security headers vitest suite to ensure automated checks pass:
   ```bash
   pnpm vitest run tests/int/security-headers.test.ts
   ```
4. Confirm zero console errors regarding blocked CSP resources during normal user navigation in browser tests.
5. Execute Secret Sentinel audit across production output:
   ```bash
   grep -rEi "(sk_live|private_key|AWS_SECRET|CLOUDFLARE_API_KEY)" dist/ || echo "PASS: No leaked secrets"
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/05-edge-workers-and-qa/45-csp-level-3-security-headers/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** CSP Level 3 & Edge Security Hardening Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/05-edge-workers-and-qa/45-csp-level-3-security-headers/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/05-edge-workers-and-qa/45-csp-level-3-security-headers/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/05-edge-workers-and-qa/45-csp-level-3-security-headers/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/05-edge-workers-and-qa/45-csp-level-3-security-headers/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/05-edge-workers-and-qa/45-csp-level-3-security-headers/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
