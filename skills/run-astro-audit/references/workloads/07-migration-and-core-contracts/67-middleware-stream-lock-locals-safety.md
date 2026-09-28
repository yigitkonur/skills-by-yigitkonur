# Mission Brief: Middleware Stream Lock & context.locals Mutation Safety Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

Four critical failure modes exist in Astro middleware request and response handling:

1. **ReadableStream Lock:** Under the WHATWG Streams API, `Request.body` is a `ReadableStream` that can only be locked and consumed once. Invoking `request.json()`, `request.text()`, or `request.formData()` directly in middleware permanently consumes the stream. Subsequent reads by downstream Astro Actions, API endpoints, or template forms will fail catastrophically with `TypeError: Body has already been consumed`. If request body inspection is necessary, `context.request.clone()` must be called before consumption.
2. **Streaming Response Body Consumption:** Astro renders on-demand pages using chunked HTML streaming via WHATWG `ReadableStream` for fast TTFB. Calling `await response.text()` or `await response.json()` in post-execution middleware permanently locks and exhausts the stream, forcing the server to buffer the entire HTML document in RAM before flushing. This destroys chunked streaming, triggers severe memory pressure on edge workers, and throws `TypeError: Body has already been consumed`. Header mutation must occur directly on `response.headers`, and any body transformation must utilize `TransformStream` or Cloudflare `HTMLRewriter`.
3. **Locals Reassignment & State Obliteration:** Assigning `context.locals = { ... }` wipes out properties pre-populated by upstream integrations, i18n middleware, and hosting adapter runtimes (e.g. `context.locals.runtime.env` on Cloudflare Workers). Assigning a primitive throws `LocalsNotAnObject`. Middleware must strictly mutate properties (`context.locals.user = ...`) or use `Object.assign(context.locals, ...)`.
4. **Response Resolution (`next()` Return):** Every branch in Astro middleware must resolve to a valid `Response`. Omitting `return` before `next()` (a common habit from Express) returns `undefined`, triggering runtime error `MiddlewareNoDataOrNextCalled`.

### Authoritative Astro Architectural & Best Practice Rules

Auditors must inspect, evaluate, and verify all middleware patterns against the repository's authoritative Astro best practices:

- **Primary Streaming Contract**: [19-avoid-consuming-streaming-response-body-in-middleware.md](../../best-practices/06-middleware-and-auth/19-avoid-consuming-streaming-response-body-in-middleware.md) — Avoid consuming streaming response bodies in post-execution middleware (`response.text()` / `response.json()`).
- **Primary Locals Contract**: [04-mutate-locals-never-reassign.md](../../best-practices/06-middleware-and-auth/04-mutate-locals-never-reassign.md) — Mutate `context.locals` properties; never overwrite the object.
- **Static Asset Bypass**: [05-filter-static-asset-requests.md](../../best-practices/06-middleware-and-auth/05-filter-static-asset-requests.md) — Filter out static assets before executing heavy middleware logic.
- **Frontmatter Security Contract**: [03-frontmatter-security-boundary.md](../../best-practices/01-architecture-and-philosophy/03-frontmatter-security-boundary.md) — Isolate secrets and database calls in frontmatter without leaking to client bundles.
- **Server Islands Architecture**: [11-defer-personalized-content-with-server-islands.md](../../best-practices/02-islands-and-hydration/11-defer-personalized-content-with-server-islands.md) — Defer personalized content with Server Islands (`server:defer`).
- **Island URL Boundary**: [12-keep-server-island-props-under-url-limit.md](../../best-practices/02-islands-and-hydration/12-keep-server-island-props-under-url-limit.md) — Keep Server Island props lightweight and under URL length limits (< 2048 bytes).
- **Headless Unit Testing**: [21-unit-test-components-with-astro-container-api.md](../../best-practices/10-auditing-testing-and-nextjs-migration/21-unit-test-components-with-astro-container-api.md) — Unit test `.astro` components headlessly with the Astro Container API.

Critical files to inspect:

- `src/middleware.ts`
- `src/worker.ts`
- `src/actions/`
- `src/env.d.ts` / `src/types/`

## 3.2 Mission Objective

Perform a rigorous audit of middleware request and response handling to ensure zero stream consumption locks, strict `context.locals` mutation safety, and complete response returns across all execution branches.
Outcome: Prevent downstream API and Astro Action request body read failures, eliminate `response.text()` streaming bottlenecks, preserve type-safe `App.Locals` chaining, and eliminate `MiddlewareNoDataOrNextCalled` errors.
Constraints: Read-only audit; do not alter production code.
Autonomy Grant: You own this mission end-to-end. Trace middleware execution order, verify stream handling, and check locals contracts. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect all middleware handlers in `src/middleware.ts`, `src/worker.ts`, and `sequence()` chains.
2. Check for any direct reading of `request.body` (`request.json()`, `request.text()`, `request.formData()`) without `request.clone()`.
3. Search for post-execution `await response.text()` or `await response.json()` that destroys chunk streaming.
4. Search for `context.locals = ...` full reassignments and verify that `context.locals.prop = ...` or `Object.assign(context.locals, ...)` is exclusively used.
5. Verify that every conditional branch (logging, metrics, auth bypass) explicitly returns `return next()` or a custom `Response`.
6. Check `App.Locals` TypeScript interface definitions in `src/env.d.ts` or `src/types/` for contract integrity.

### ❌ Bad Practice / Anti-Pattern (Stream Exhaustion, Response Buffering & Locals Obliteration)

```typescript
// src/middleware.ts (Stream exhaustion, response buffer lock, locals wipe, unreturned next)
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  if (context.request.method === 'POST') {
    // ❌ FATAL: Consumes stream; downstream Astro Action throws "TypeError: Body already consumed"
    const rawPayload = await context.request.text()
    console.log('Incoming payload:', rawPayload)
  }

  // ❌ FATAL: Reassigning context.locals wipes out Cloudflare runtime & adapter bindings!
  context.locals = { user: { id: '123' } }

  if (context.url.pathname.startsWith('/api/public')) {
    // ❌ FATAL: Missing return; resolves to undefined -> MiddlewareNoDataOrNextCalled
    next()
  } else {
    const response = await next()

    // ❌ FATAL: Calling response.text() destroys chunked HTML streaming and buffers entire page in RAM!
    if (response.headers.get('content-type')?.includes('text/html')) {
      const html = await response.text() // Permanently locks response stream!
      const modified = html.replace('</body>', "<script src='/track.js'></script></body>")
      return new Response(modified, response)
    }

    return response
  }
})
```

### ✅ Best Practice / Idiomatic (Cloned Request Inspection, Direct Header Mutation & Safe Locals Merge)

```typescript
// src/middleware.ts (Cloned stream inspection, locals mutation, streaming preservation, guaranteed return)
// Bound to RULE-ID: 06-middleware-and-auth/19-avoid-consuming-streaming-response-body-in-middleware
// Bound to RULE-ID: 06-middleware-and-auth/04-mutate-locals-never-reassign
import { defineMiddleware } from 'astro:middleware'

export const onRequest = defineMiddleware(async (context, next) => {
  // ✅ Clone request before reading stream to keep original body untouched for downstream actions
  if (context.request.method === 'POST' && shouldInspect(context)) {
    const clone = context.request.clone()
    const raw = await clone.text()
    console.log('Safe inspection:', raw)
  }

  // ✅ Mutate existing context.locals without destroying adapter bindings or Cloudflare env
  context.locals.user = { id: '123' }
  Object.assign(context.locals, {
    tenantId: 'tenant_123',
    featureFlags: { modernUI: true },
  })

  // ✅ Explicitly return next() or Response from every branch
  if (context.url.pathname.startsWith('/api/public')) {
    return next()
  }

  const response = await next()

  // ✅ Mutate headers directly on active streaming response without consuming body
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('X-Frame-Options', 'DENY')

  // ✅ If body transformation is required, use streaming TransformStream or HTMLRewriter, NOT response.text()
  return response
})
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/07-migration-and-core-contracts/67-middleware-stream-lock-locals-safety/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Rule-ID Mapping**: Every item in `findings.json` MUST explicitly map to an authoritative Astro best practice rule ID (e.g. `RULE-ID: 06-middleware-and-auth/19-avoid-consuming-streaming-response-body-in-middleware` or `RULE-ID: 06-middleware-and-auth/04-mutate-locals-never-reassign`).

You must create and populate the following deliverables in `docs/audits/results/07-migration-and-core-contracts/67-middleware-stream-lock-locals-safety/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "67-MIDDLEWARE-STREAM-LOCK-LOCALS-SAFETY-001",
    "rule_id": "RULE-ID: 06-middleware-and-auth/19-avoid-consuming-streaming-response-body-in-middleware",
    "file": "src/middleware.ts",
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
  --body "docs/audits/results/07-migration-and-core-contracts/67-middleware-stream-lock-locals-safety/issue-body.md" \
  --title "[Audit - Middleware Stream Lock & context.locals Mutation Safety Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/07-migration-and-core-contracts/67-middleware-stream-lock-locals-safety/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Run `git grep -n "defineMiddleware" src/` to isolate all middleware entrypoints.
2. Run `git grep -n "request\.text(\|request\.json(\|request\.formData(" src/` to isolate all request body consumption sites.
3. Run `git grep -n "response\.text(\|response\.json(" src/` to check for streaming response body consumption.
4. Run `git grep -n "context\.locals\s*=" src/` to verify zero full object reassignments.
5. Run `git grep -n "server:defer" src/` to verify compatibility with Server Island deferred stream chunks.
6. Execute headless component and middleware unit tests with Vitest using `experimental_AstroContainer` from `astro/container`:
   ```bash
   pnpm exec vitest run tests/middleware/ --run
   ```
7. Verify POST action stability with middleware active:
   ```bash
   curl -X POST http://localhost:4321/_actions/submitForm -H "Content-Type: application/json" -d '{"name":"test"}'
   ```
   (Must succeed with HTTP 200, never throwing "Body has already been consumed").

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/07-migration-and-core-contracts/67-middleware-stream-lock-locals-safety/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Middleware Stream Lock & context.locals Mutation Safety Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/07-migration-and-core-contracts/67-middleware-stream-lock-locals-safety/findings.json` (N defects logged with RULE-ID mappings)
   - `file://docs/audits/results/07-migration-and-core-contracts/67-middleware-stream-lock-locals-safety/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/07-migration-and-core-contracts/67-middleware-stream-lock-locals-safety/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/07-migration-and-core-contracts/67-middleware-stream-lock-locals-safety/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/07-migration-and-core-contracts/67-middleware-stream-lock-locals-safety/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
