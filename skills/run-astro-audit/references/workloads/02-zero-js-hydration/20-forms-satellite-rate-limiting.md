# Mission Brief: Forms Satellite Pipeline & Rate Limiting Audit

## 3.0 Skills / Tools: view_file, run_command, form-capture.

## 3.1 Context Block

The forms pipeline connects the Astro frontend to the `workers/forms` Cloudflare Worker satellite.
It handles proposal inquiries, career applications with private CV uploads, and newsletter subscriptions.

Astro best practices and forms architecture mandate:

1. **Progressive Enhancement Baseline**: Forms must provide a functional HTML `<form action="..." method="POST">` baseline that submits reliably without client JavaScript, enhanced progressively by client islands without SSR hydration mismatches.
2. **Turnstile & Edge Rate-Limiting**: Every form submission must validate a Cloudflare Turnstile cryptographic token at the satellite edge, with IP/token rate-limiting returning 429 status codes upon threshold violations.
3. **Private Encrypted CV Storage**: Uploaded candidate CVs must be validated for MIME type (`application/pdf`, `.docx`) and size (<10 MiB), and stored strictly in a private Cloudflare R2 bucket with zero public URL exposure.
4. **Structured Bilingual Contracts**: Responses must adhere strictly to the shared `FormActionResult` schema with localized error messaging across TR, EN, and AR locales.

### Astro Architectural & Best Practice Rules

All forms pipelines, rate limiting policies, and satellite mutations must adhere to the authoritative best practices:

- [08-actions-vs-endpoints-mutations.md](../../best-practices/05-data-fetching-and-endpoints/08-actions-vs-endpoints-mutations.md) — Prefer Astro Actions over custom REST POST endpoints for internal form mutations.
- [14-progressive-enhancement-with-astro-actions.md](../../best-practices/05-data-fetching-and-endpoints/14-progressive-enhancement-with-astro-actions.md) — Progressive enhancement baseline using `<form method="POST" action={actions.submit}>` with `isInputError()`.
- [13-handle-csrf-and-check-origin-on-external-endpoints.md](../../best-practices/05-data-fetching-and-endpoints/13-handle-csrf-and-check-origin-on-external-endpoints.md) — Handling CSRF and `security.checkOrigin` for external webhooks vs internal actions.
- [15-stateless-edge-rate-limiting.md](../../best-practices/06-middleware-and-auth/15-stateless-edge-rate-limiting.md) — Distributed stateless rate limiting avoiding unbounded in-memory Maps across edge worker isolates.
- [21-track-pageviews-in-client-router-with-astro-page-load.md](../../best-practices/03-routing-and-pages/21-track-pageviews-in-client-router-with-astro-page-load.md) — Coordinating form confirmation views with `astro:page-load` client transitions.

Critical files to inspect:

- workers/forms/
- workers/forms/wrangler.toml
- src/actions/index.ts
- src/lib/forms/form-result.ts
- tests/int/form-result-receiver.test.ts

## 3.2 Mission Objective

Audit the end-to-end forms satellite architecture, submission schemas, and edge rate-limiting policies.
Outcome: Ensure Turnstile verification cannot be bypassed, private CV uploads are written strictly to encrypted private R2 storage, rate-limiting triggers appropriate 429 status codes, and error returns conform to `FormActionResult`.
Constraints: Read-only audit; do not tamper with live satellite secrets.
Autonomy Grant: You own this mission end-to-end. Trace request lifecycles, cryptographic token verification, and payload boundaries. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Audit forms frontend and endpoints for progressive enhancement vs heavy client JS:
   - ❌ Bad Practice / Anti-Pattern (Heavy React Island Solely for Form Validation):
     ```astro
     ---
     // Heavy React island imported solely for form validation and state
     import ContactFormReact from "../components/ContactFormReact.jsx";
     ---
     <!-- Bloats page bundle with React runtime and Zod validator on client -->
     <ContactFormReact client:load />
     ```
   - ✅ Best Practice / Idiomatic (Astro Actions Progressive Enhancement & Zero-JS):
     ```astro
     ---
     // src/pages/contact.astro
     import { actions, isInputError } from 'astro:actions';

     export const prerender = false;

     const result = Astro.getActionResult(actions.submitContact);
     const inputErrors = isInputError(result?.error) ? result.error.fields : {};
     ---
     <!-- Pure HTML form with progressive enhancement and zero client JS -->
     <form method="POST" action={actions.submitContact}>
       <label for="email">Email</label>
       <input id="email" name="email" type="email" required />
       {inputErrors.email && <span class="error">{inputErrors.email.join(", ")}</span>}

       <label for="message">Message</label>
       <textarea id="message" name="message" required></textarea>
       {inputErrors.message && <span class="error">{inputErrors.message.join(", ")}</span>}

       <button type="submit">Send Message</button>
       {result?.data?.success && <p class="success">Message sent successfully!</p>}
     </form>
     ```

2. Contrast stateful in-memory maps against distributed edge rate limiting:
   - ❌ Bad Practice / Anti-Pattern (Unbounded In-Memory Map on Edge Worker):
     ```typescript
     // MEMORY LEAK & DISTRIBUTED BLIND SPOT:
     // Unbounded Map leaks memory and fails across multi-worker edge isolates!
     const requestCounts = new Map<string, number>()

     export const onRequest = async (context) => {
       const ip = context.request.headers.get('cf-connecting-ip') || 'unknown'
       const count = (requestCounts.get(ip) || 0) + 1
       requestCounts.set(ip, count)
       if (count > 100) return new Response('Too Many Requests', { status: 429 })
       return next()
     }
     ```
   - ✅ Best Practice / Idiomatic (Stateless Edge Rate Limiter with Retry-After):
     ```typescript
     // Idiomatic: Atomic rate limit via Cloudflare binding, returning standardized 429 & Retry-After
     export async function onRequestPost({ request, env }) {
       const clientIp = request.headers.get('cf-connecting-ip') ?? '127.0.0.1'
       const { success } = await env.RATE_LIMITER.limit({ key: clientIp })

       if (!success) {
         return new Response(JSON.stringify({ error: 'Rate limit exceeded' }), {
           status: 429,
           headers: {
             'Content-Type': 'application/json',
             'Retry-After': '60',
           },
         })
       }

       const verified = await verifyTurnstile(token, env.TURNSTILE_SECRET_KEY)
       if (!verified) return errorResult('TURNSTILE_FAILED', 403)
       return successResult({ submissionId })
     }
     ```

3. Audit webhook and external API endpoints for origin checking and CSRF handling:
   - ❌ Bad Practice / Anti-Pattern (Global checkOrigin Failure on Webhooks):
     ```typescript
     // astro.config.mjs
     export default defineConfig({
       output: 'server',
       // Default checkOrigin: true rejects external webhook notifications with 403 Forbidden!
     })
     ```
   - ✅ Best Practice / Idiomatic (Granular CSRF & Signature Validation):
     ```typescript
     // astro.config.mjs
     export default defineConfig({
       output: 'server',
       security: {
         checkOrigin: false, // Bypassed for verified webhooks authenticated via HMAC signature
       },
     })
     ```

4. Verify CV upload handling: ensure files are strictly validated for MIME type and file size (<10 MiB) before writing to private R2.
5. Validate error response contracts: verify that forms return structured JSON matching `FormActionResult`.

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/02-zero-js-hydration/20-forms-satellite-rate-limiting/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Best Practice Mapping Requirement**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule (e.g. `RULE-ID: 05-08-actions-vs-endpoints-mutations`, `RULE-ID: 05-14-progressive-enhancement`, `RULE-ID: 06-15-stateless-edge-rate-limiting`, `RULE-ID: 05-13-handle-csrf-check-origin`, or `RULE-ID: 03-21-track-pageviews-astro-page-load`).

You must create and populate the following deliverables in `docs/audits/results/02-zero-js-hydration/20-forms-satellite-rate-limiting/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "20-FORMS-SATELLITE-RATE-LIMITING-001",
    "rule_id": "RULE-ID (e.g. 05-14-progressive-enhancement-with-astro-actions)",
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
  --body "docs/audits/results/02-zero-js-hydration/20-forms-satellite-rate-limiting/issue-body.md" \
  --title "[Audit - Forms Satellite Pipeline & Rate Limiting Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/02-zero-js-hydration/20-forms-satellite-rate-limiting/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Execute test suite and static checks for forms contracts and edge configuration:
   ```bash
   # 1. Run integration tests for forms satellite contracts
   pnpm vitest run tests/int/form-result-receiver.test.ts
   # 2. Audit rate limiting and Turnstile validation in workers/forms
   git grep -n "turnstile" workers/forms/
   git grep -n "rateLimit" workers/forms/
   # 3. Check for Astro Actions usage and progressive enhancement
   git grep -n "actions\." src/
   # 4. Check for client router pageview events on form pages
   git grep -n "astro:page-load" src/
   # 5. Verify private R2 bucket bindings in wrangler.toml (ensure no public bucket exposure)
   git grep -n "r2_buckets" workers/forms/wrangler.toml
   # 6. Check FormActionResult type adherence in frontend actions
   git grep -n "FormActionResult" src/actions/ src/lib/forms/
   # 7. Test forms submission endpoints with curl and verify rate-limiting headers (HTTP 429 & Retry-After)
   curl -i -X POST http://localhost:8787/api/forms/proposal -H "Content-Type: application/json" -d '{"email":"test@example.com"}'
   ```
2. Verify that rate limiting triggers and returns localized error messages across EN, TR, and AR.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/02-zero-js-hydration/20-forms-satellite-rate-limiting/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Forms Satellite Pipeline & Rate Limiting Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/02-zero-js-hydration/20-forms-satellite-rate-limiting/findings.json` (N defects logged)
   - `file://docs/audits/results/02-zero-js-hydration/20-forms-satellite-rate-limiting/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/02-zero-js-hydration/20-forms-satellite-rate-limiting/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/02-zero-js-hydration/20-forms-satellite-rate-limiting/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/02-zero-js-hydration/20-forms-satellite-rate-limiting/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
