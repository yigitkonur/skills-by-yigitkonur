# Mission Brief: WebMCP Browser-Agent Integration Audit

## 3.0 Skills / Tools: view_file, run_command, astro-webmcp.

## 3.1 Context Block

The application implements the W3C ModelContext WebMCP protocol for AI browser agents, registering 4 live tools in `window.modelContext`:

1. `match_site_offering`
2. `filter_case_studies`
3. `submit_service_inquiry`
4. `find_site_content`
   These tools run directly in the browser environment, allowing AI agents to query site capabilities and submit inquiries programmatically.

Astro best practices and WebMCP invariants mandate:

1. **Client-Only Execution & Zero SSR Hydration Tax**: WebMCP scripts must never execute at module evaluation time during SSR (preventing `window is not defined` crashes) and must load asynchronously via `type="module"` to avoid delaying DOMContentLoaded or First Contentful Paint (FCP).
2. **Strict Schema Validation & Input Sanitization**: All incoming tool arguments must be strictly parsed against JSON Schema / Zod contracts to prevent prompt injection attacks and invalid payloads.
3. **Information Barrier & Security Scoping**: Tools must operate strictly within public capability scopes; never expose private CV documents, internal admin endpoints, or bypass CSRF protections.

### Astro Architectural & Best Practice Rules

All WebMCP implementations and agent tools must adhere to the authoritative best practices:

- [08-actions-vs-endpoints-mutations.md](../../best-practices/05-data-fetching-and-endpoints/08-actions-vs-endpoints-mutations.md) — Prefer Astro Actions over custom REST POST endpoints for internal client mutations and agent tool handlers.
- [13-handle-csrf-and-check-origin-on-external-endpoints.md](../../best-practices/05-data-fetching-and-endpoints/13-handle-csrf-and-check-origin-on-external-endpoints.md) — Handle CSRF origin checks and distinguish browser agent submissions from external webhooks.
- [14-progressive-enhancement-with-astro-actions.md](../../best-practices/05-data-fetching-and-endpoints/14-progressive-enhancement-with-astro-actions.md) — Progressive enhancement baseline ensuring tools and forms function cleanly without unneeded client runtime tax.
- [15-stateless-edge-rate-limiting.md](../../best-practices/06-middleware-and-auth/15-stateless-edge-rate-limiting.md) — Stateless edge rate limiting to prevent automated agent inquiry abuse.
- [21-track-pageviews-in-client-router-with-astro-page-load.md](../../best-practices/03-routing-and-pages/21-track-pageviews-in-client-router-with-astro-page-load.md) — Lifecycle coordination with `astro:page-load` for client router transitions.

Critical files to inspect:

- src/scripts/*-webmcp.ts
- src/lib/tools/
- src/features/company/components/SubmitServiceInquiryWebMcp.astro
- .claude/skills/astro-webmcp/

## 3.2 Mission Objective

Audit all 4 live WebMCP browser agent tools for security, schema correctness, and zero-tax runtime impact.
Outcome: Verify that tool schemas match W3C ModelContext specifications, execution does not leak sensitive memory or trigger CSRF bypasses, and script initialization does not delay FCP or trigger SSR hydration errors.
Constraints: Read-only audit; verify security threat models and tool return types.
Autonomy Grant: You own this mission end-to-end. Test tool execution, validate JSON schemas, and audit memory limits. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Audit WebMCP registration points for SSR safety and deferred initialization:
   - ❌ Bad Practice / Anti-Pattern (Unsafe Global & Unvalidated Handler):
     ```typescript
     // Anti-Pattern: Unchecked window access and raw unvalidated payload pass-through
     window.modelContext.registerTool({
       name: 'submit_service_inquiry',
       handler: async (args) => fetch('/api/forms/proposal', { body: JSON.stringify(args) }),
     })
     ```
   - ✅ Best Practice / Idiomatic (SSR-Safe Guard & Zod Schema Validation):
     ```typescript
     // Idiomatic: Guarded client execution with strict schema validation
     if (typeof window !== 'undefined' && 'modelContext' in window) {
       window.modelContext.registerTool({
         name: 'submit_service_inquiry',
         parameters: inquirySchema,
         execute: async (args) => {
           const clean = inquirySchema.parse(args)
           return await submitInquiryAction(clean)
         },
       })
     }
     ```

2. Contrast ad-hoc client fetch mutations against type-safe Astro Actions:
   - ❌ Bad Practice / Anti-Pattern (Ad-Hoc Untyped Fetch Endpoint):
     ```typescript
     // Legacy Next.js pattern: Unsafe manual POST fetch lacking centralized type-safety
     const res = await fetch('/api/inquiry', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify(args),
     })
     ```
   - ✅ Best Practice / Idiomatic (Centralized Astro Actions Mutation):
     ```typescript
     // Astro 5 Idiomatic: Type-safe action call with structured ActionError handling
     import { actions } from 'astro:actions'
     const { data, error } = await actions.submitServiceInquiry(cleanArgs)
     if (error) throw new Error(error.message)
     ```

3. Audit external agent webhook endpoints for CSRF checkOrigin mismatches:
   - ❌ Bad Practice / Anti-Pattern (Global checkOrigin Failure on Webhooks):
     ```typescript
     // astro.config.mjs: Default checkOrigin: true causes external agent webhooks to fail with 403 Forbidden!
     export default defineConfig({ output: 'server' })
     ```
   - ✅ Best Practice / Idiomatic (Granular CSRF & Signature Validation):
     ```typescript
     // astro.config.mjs: Disable checkOrigin selectively and authenticate callers cryptographically via HMAC signatures
     export default defineConfig({
       output: 'server',
       security: { checkOrigin: false },
     })
     ```

4. Verify that `window.modelContext` registration scripts are non-blocking (`type="module"` in layout).
5. Validate return payload schemas against W3C ModelContext JSON Schema definitions.

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/02-zero-js-hydration/18-webmcp-browser-agent-tools/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Best Practice Mapping Requirement**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule (e.g. `RULE-ID: 05-08-actions-vs-endpoints-mutations`, `RULE-ID: 05-13-handle-csrf-check-origin`, `RULE-ID: 05-14-progressive-enhancement`, `RULE-ID: 06-15-stateless-edge-rate-limiting`, or `RULE-ID: 03-21-track-pageviews-astro-page-load`).

You must create and populate the following deliverables in `docs/audits/results/02-zero-js-hydration/18-webmcp-browser-agent-tools/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "18-WEBMCP-BROWSER-AGENT-TOOLS-001",
    "rule_id": "RULE-ID (e.g. 05-08-actions-vs-endpoints-mutations)",
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
  --body "docs/audits/results/02-zero-js-hydration/18-webmcp-browser-agent-tools/issue-body.md" \
  --title "[Audit - WebMCP Browser-Agent Integration Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/02-zero-js-hydration/18-webmcp-browser-agent-tools/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Execute CLI checks on WebMCP registrations, schemas, and Astro action wiring:
   ```bash
   # 1. Audit WebMCP script references in layouts for non-blocking attributes
   git grep -n "webmcp" src/layouts/ src/components/
   # 2. Check for unguarded window.modelContext calls in scripts
   git grep -n "modelContext" src/scripts/ | grep -v "typeof window" || echo "Verify window guards"
   # 3. Verify Astro Actions usage for internal mutations vs legacy fetch
   git grep -n "actions\." src/scripts/ src/components/
   # 4. Check client router lifecycle hooks for agent tool re-registration
   git grep -n "astro:page-load" src/
   # 5. Run WebMCP unit tests and schema verification
   pnpm vitest run tests/unit/webmcp/ || pnpm check:doc-integrity
   ```
2. Verify that all 4 tools execute and return structured JSON in under 50ms without leaking private CV data or admin routes.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/02-zero-js-hydration/18-webmcp-browser-agent-tools/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** WebMCP Browser-Agent Integration Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/02-zero-js-hydration/18-webmcp-browser-agent-tools/findings.json` (N defects logged)
   - `file://docs/audits/results/02-zero-js-hydration/18-webmcp-browser-agent-tools/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/02-zero-js-hydration/18-webmcp-browser-agent-tools/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/02-zero-js-hydration/18-webmcp-browser-agent-tools/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/02-zero-js-hydration/18-webmcp-browser-agent-tools/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
