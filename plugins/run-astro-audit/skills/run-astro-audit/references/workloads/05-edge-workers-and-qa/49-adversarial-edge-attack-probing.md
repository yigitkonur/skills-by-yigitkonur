# Mission Brief: Adversarial Edge Attack & Robustness Probing Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

Production websites face adversarial edge traffic:

- Malicious query strings and path traversal attempts (e.g. `/../../etc/passwd`, `%00` null byte injections, `%2e%2e` dot encodings).
- XSS and prototype pollution payloads in search queries and form fields.
- Abnormally large headers or cookies (>16 KB).
- Denial of Service via recursive regex evaluation (ReDoS).
- Edge Rate Limiting Law: Storing request counters in global JavaScript in-memory `Map` objects fails in distributed edge runtimes (where workers execute in isolated memory spaces) and introduces unbounded memory leaks in persistent processes. Rate limiting on sensitive mutation endpoints (forms capture, inquiries) must use distributed token buckets returning HTTP 429 with `Retry-After: 60`.
- Fail-Closed Routing Invariant: The edge worker entrypoint `src/worker.ts` must fail closed, wrap URI decoding in `try/catch` to prevent unhandled `URIError` 500 crashes, and sanitize all URL paths before routing.

### Authoritative Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`15-stateless-edge-rate-limiting.md`](../../best-practices/06-middleware-and-auth/15-stateless-edge-rate-limiting.md) — Stateless, distributed rate limiting on Cloudflare Workers edge using distributed token buckets (`RULE-ID: 06-middleware-and-auth/15-stateless-edge-rate-limiting`).
- [`07-path-canonicalization-auth-bypass.md`](../../best-practices/06-middleware-and-auth/07-path-canonicalization-auth-bypass.md) — Path canonicalization, null byte normalization, and directory traversal defense (`RULE-ID: 06-middleware-and-auth/07-path-canonicalization-auth-bypass`).
- [`14-global-error-handling-in-middleware.md`](../../best-practices/06-middleware-and-auth/14-global-error-handling-in-middleware.md) — Global fail-closed error handling in edge middleware and intercepting malformed URI errors (`RULE-ID: 06-middleware-and-auth/14-global-error-handling-in-middleware`).
- [`10-inject-security-headers-and-csp.md`](../../best-practices/06-middleware-and-auth/10-inject-security-headers-and-csp.md) — Injecting edge security headers, CSP, and framing defenses (`RULE-ID: 06-middleware-and-auth/10-inject-security-headers-and-csp`).
- [`07-request-body-parsing-and-validation.md`](../../best-practices/05-data-fetching-and-endpoints/07-request-body-parsing-and-validation.md) — Safe request body parsing, payload size bounding, and schema validation (`RULE-ID: 05-data-fetching-and-endpoints/07-request-body-parsing-and-validation`).
- [`12-structured-error-handling-and-http-status-codes.md`](../../best-practices/05-data-fetching-and-endpoints/12-structured-error-handling-and-http-status-codes.md) — Structured error handling and correct HTTP status codes (400, 403, 429) without leaking stack traces (`RULE-ID: 05-data-fetching-and-endpoints/12-structured-error-handling-and-http-status-codes`).
- [`07-scoped-styles-encapsulation.md`](../../best-practices/01-architecture-and-philosophy/07-scoped-styles-encapsulation.md) — Scoped CSS encapsulation and avoiding global style leaks (`RULE-ID: 01-architecture-and-philosophy/07-scoped-styles-encapsulation`).
- [`09-enforce-component-scoped-css.md`](../../best-practices/09-performance-prefetch-and-transitions/09-enforce-component-scoped-css.md) — Enforcing component-scoped CSS architecture (`RULE-ID: 09-performance-prefetch-and-transitions/09-enforce-component-scoped-css`).
- [`13-migrate-to-tailwind-v4-vite-plugin.md`](../../best-practices/09-performance-prefetch-and-transitions/13-migrate-to-tailwind-v4-vite-plugin.md) — Tailwind v4 CSS-first design token architecture (`RULE-ID: 09-performance-prefetch-and-transitions/13-migrate-to-tailwind-v4-vite-plugin`).
- [`01-audit-against-production-preview-never-dev.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/01-audit-against-production-preview-never-dev.md) — Testing and visual QA against production builds (`astro preview`), never dev server (`RULE-ID: 10-auditing-testing-and-nextjs-migration/01-audit-against-production-preview-never-dev`).
- [`04-audit-island-boundaries-with-dev-toolbar-inspect.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/04-audit-island-boundaries-with-dev-toolbar-inspect.md) — Inspecting island boundaries and container render fidelity (`RULE-ID: 10-auditing-testing-and-nextjs-migration/04-audit-island-boundaries-with-dev-toolbar-inspect`).

Critical files to inspect:

- `src/worker.ts`
- `edge/policy/`
- `src/lib/redirects/`
- `tests/int/astro-pages-edge-policy.test.ts`

## 3.2 Mission Objective

Perform an adversarial robustness and boundary audit against edge routing and query processing.
Outcome: Prove that invalid, malformed, or malicious URL requests fail closed (returning clean 400 Bad Request or 404 Not Found) without throwing unhandled 500 errors or leaking stack traces.
Constraints: Read-only audit; simulate malformed path inputs in offline test suites.
Autonomy Grant: You own this mission end-to-end. Probe edge edge-cases, path normalizers, and regex safety. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Test edge URL normalizer: verify that multiple slashes (`///`), backslashes (`\`), and encoded dots (`%2e%2e`) are handled securely.
2. Inspect search query sanitization: ensure HTML tags (`<script>`) in `?q=` parameters are escaped before rendering.
3. Check ReDoS risks in regex patterns across markdown plugins and redirect matchers.
4. Audit rate limiting: verify distributed rate limiting on form capture endpoints rather than in-memory Maps.
5. Verify edge worker entrypoint catches malformed percent encoding before calling router logic.

### ❌ Bad Practice / Anti-Pattern (In-Memory Rate Limiting & Naked decodeURIComponent)

```typescript
// src/worker.ts - Edge Vulnerability Anti-patterns
// Common blunder: Carrying stateful Node/Express idioms into edge serverless
const ipRequestMap = new Map<string, number>() // ❌ BAD: Leaks memory and fails in distributed isolates

export default {
  async fetch(request: Request) {
    const url = new URL(request.url)

    // ❌ BAD: Unhandled decodeURIComponent throws unhandled URIError (500 crash) on malformed UTF-8!
    const pathname = decodeURIComponent(url.pathname)

    // ❌ BAD: Blindly trusting path without sanitizing path traversal (../)
    return handleRoute(pathname)
  },
}
```

_Why this fails:_ Malformed percent-encoded sequences (like `%a0%a1` or `%00`) cause `decodeURIComponent` to throw, yielding an unhandled 500 server crash and leaking edge internals. Unbounded in-memory Maps leak memory and leave edge nodes completely open to distributed credential stuffing.

### ✅ Best Practice / Idiomatic (Fail-Closed Edge Routing & Distributed Rate Limiting)

```typescript
// src/worker.ts - Resilient fail-closed edge routing
// Idiomatic Astro / Cloudflare Workers: Web standard fail-closed pattern
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    let pathname: string
    try {
      // ✅ Handle malformed percent encoding gracefully with clean 400 response
      pathname = decodeURIComponent(new URL(request.url).pathname)
    } catch {
      return new Response('Bad Request: Malformed URI encoding', { status: 400 })
    }

    // ✅ Reject null bytes and path traversal attempts immediately (fail closed)
    if (pathname.includes('\0') || /(\/|\\)\.\.(\/|\\)/.test(pathname)) {
      return new Response('Forbidden: Invalid path traversal', { status: 403 })
    }

    // ✅ Distributed rate limiting on sensitive mutation routes using Cloudflare binding
    if (pathname.startsWith('/api/forms/')) {
      const clientIp = request.headers.get('cf-connecting-ip') ?? '127.0.0.1'
      const rateLimit = await env.RATE_LIMITER.limit({ key: clientIp })
      if (!rateLimit.success) {
        return new Response(JSON.stringify({ error: 'Rate limit exceeded' }), {
          status: 429,
          headers: { 'Content-Type': 'application/json', 'Retry-After': '60' },
        })
      }
    }

    return handleRoute(pathname)
  },
}
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/05-edge-workers-and-qa/49-adversarial-edge-attack-probing/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: 06-middleware-and-auth/15-stateless-edge-rate-limiting`, `RULE-ID: 06-middleware-and-auth/07-path-canonicalization-auth-bypass`, `RULE-ID: 06-middleware-and-auth/14-global-error-handling-in-middleware`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/05-edge-workers-and-qa/49-adversarial-edge-attack-probing/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "49-ADVERSARIAL-EDGE-ATTACK-PROBING-001",
    "rule_id": "RULE-ID: 06-middleware-and-auth/15-stateless-edge-rate-limiting",
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
  --body "docs/audits/results/05-edge-workers-and-qa/49-adversarial-edge-attack-probing/issue-body.md" \
  --title "[Audit - Adversarial Edge Attack & Robustness Probing Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/05-edge-workers-and-qa/49-adversarial-edge-attack-probing/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Run `pnpm vitest run tests/int/astro-pages-edge-policy.test.ts` to verify edge failure modes.
2. Confirm zero unhandled exceptions when passing malformed UTF-8 sequences to edge router:
   `curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:4321/%a0%a1"` (Expects 400).
3. Probe path traversal sequences to verify fail-closed responses:
   `curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:4321/../../etc/passwd"` (Expects 400 or 403).
4. Verify distributed rate limiting returns HTTP 429 with `Retry-After: 60`:
   `for i in {1..12}; do curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:4321/api/forms/capture; done`
5. Audit worker source for stateful in-memory maps or unhandled decoding:
   `git grep -n "new Map<" src/worker.ts edge/`
   `git grep -n "decodeURIComponent" src/worker.ts`
6. Audit for synthetic pulsing badges or arbitrary border radius tokens:
   `git grep -n "animate-pulse" src/`
   `git grep -n "rounded-lg\|rounded-xl\|rounded-2xl" src/`
7. Verify documentation integrity:
   `pnpm check:doc-integrity`

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/05-edge-workers-and-qa/49-adversarial-edge-attack-probing/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Adversarial Edge Attack & Robustness Probing Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/05-edge-workers-and-qa/49-adversarial-edge-attack-probing/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/05-edge-workers-and-qa/49-adversarial-edge-attack-probing/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/05-edge-workers-and-qa/49-adversarial-edge-attack-probing/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/05-edge-workers-and-qa/49-adversarial-edge-attack-probing/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/05-edge-workers-and-qa/49-adversarial-edge-attack-probing/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
