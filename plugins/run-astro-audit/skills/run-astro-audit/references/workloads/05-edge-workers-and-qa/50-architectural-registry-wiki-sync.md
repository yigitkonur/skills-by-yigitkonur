# Mission Brief: Architectural Registry & Documentation Synchronization Audit

## 3.0 Skills / Tools: view_file, run_command, writing-for-agents.

## 3.1 Context Block

Durable project documentation belongs in droid-wiki/ (00-index.md).
Any changes to system behavior, build pipelines, or routing contracts must update the relevant wiki page.
pnpm check:doc-integrity audits 390 doc files, 655 paths, and 140 pnpm package scripts to ensure zero stale links or outdated documentation.

Key Astro Best Practice contracts that documentation must faithfully record:

1. **Dynamic Endpoints & Prerender Boundary**: In `output: 'static'` builds, dynamic mutation/API endpoints must explicitly declare `export const prerender = false;`. Omitting this causes endpoints to execute once at build time into static files.
2. **APIRoute Signature & Standard Web Responses**: Endpoints must be typed with `APIRoute` from `astro`, accepting `{ request, locals, cookies, params }`, and returning standard Web API `Response` or `Response.json(...)`. Returning raw JS objects throws fatal runtime errors.
3. **SPA Navigation Architecture**: Astro 5 replaces legacy `<ViewTransitions />` with `<ClientRouter fallback="animate" />` from `astro:transitions`. Per-link navigation controls must use `data-astro-reload` and `data-astro-history="replace"`.
4. **Response Header Immutability**: In SSR streaming, HTTP headers and status commit at the route root before HTML streaming begins. Child components or layouts cannot alter headers or status.
5. **Multi-Domain Routing**: Multi-TLD routing via `i18n.domains` requires `output: "server"` with an adapter. In static mode, it throws `NoPrerenderedRoutesWithDomains`.

### Authoritative Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`02-prerender-boundary-dynamic-endpoints.md`](../../best-practices/05-data-fetching-and-endpoints/02-prerender-boundary-dynamic-endpoints.md) — Explicit `export const prerender = false;` boundaries on dynamic mutation endpoints in static builds (`RULE-ID: 05-data-fetching-and-endpoints/02-prerender-boundary-dynamic-endpoints`).
- [`03-apiroute-signature-and-web-response.md`](../../best-practices/05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response.md) — Standard `APIRoute` signatures and Web standard `Response` contracts (`RULE-ID: 05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response`).
- [`10-response-headers-immutability-and-html-streaming.md`](../../best-practices/05-data-fetching-and-endpoints/10-response-headers-immutability-and-html-streaming.md) — Response header immutability during SSR HTML streaming (`RULE-ID: 05-data-fetching-and-endpoints/10-response-headers-immutability-and-html-streaming`).
- [`14-i18n-domains-multidomain-routing.md`](../../best-practices/08-i18n-and-localization/14-i18n-domains-multidomain-routing.md) — Multi-domain i18n routing constraints requiring server adapter (`RULE-ID: 08-i18n-and-localization/14-i18n-domains-multidomain-routing`).
- [`06-audit-client-router-default-prefetch-all.md`](../../best-practices/09-performance-prefetch-and-transitions/06-audit-client-router-default-prefetch-all.md) — Astro 5 `<ClientRouter />` architecture replacing deprecated `<ViewTransitions />` (`RULE-ID: 09-performance-prefetch-and-transitions/06-audit-client-router-default-prefetch-all`).
- [`06-enforce-astro-check-quality-gate-in-ci.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/06-enforce-astro-check-quality-gate-in-ci.md) — Enforcing `astro check` and documentation integrity gates in CI (`RULE-ID: 10-auditing-testing-and-nextjs-migration/06-enforce-astro-check-quality-gate-in-ci`).
- [`07-scoped-styles-encapsulation.md`](../../best-practices/01-architecture-and-philosophy/07-scoped-styles-encapsulation.md) — Scoped CSS encapsulation and avoiding global style leaks (`RULE-ID: 01-architecture-and-philosophy/07-scoped-styles-encapsulation`).
- [`09-enforce-component-scoped-css.md`](../../best-practices/09-performance-prefetch-and-transitions/09-enforce-component-scoped-css.md) — Enforcing component-scoped CSS over loose utility classes (`RULE-ID: 09-performance-prefetch-and-transitions/09-enforce-component-scoped-css`).
- [`13-migrate-to-tailwind-v4-vite-plugin.md`](../../best-practices/09-performance-prefetch-and-transitions/13-migrate-to-tailwind-v4-vite-plugin.md) — Tailwind v4 CSS-first design token architecture (`RULE-ID: 09-performance-prefetch-and-transitions/13-migrate-to-tailwind-v4-vite-plugin`).
- [`01-audit-against-production-preview-never-dev.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/01-audit-against-production-preview-never-dev.md) — Testing and visual QA against production builds (`astro preview`), never dev server (`RULE-ID: 10-auditing-testing-and-nextjs-migration/01-audit-against-production-preview-never-dev`).
- [`04-audit-island-boundaries-with-dev-toolbar-inspect.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/04-audit-island-boundaries-with-dev-toolbar-inspect.md) — Inspecting island boundaries and container render fidelity (`RULE-ID: 10-auditing-testing-and-nextjs-migration/04-audit-island-boundaries-with-dev-toolbar-inspect`).

Critical files to inspect:

- `droid-wiki/00-index.md`
- `droid-wiki/routing/06-page-types-inventory.md`
- `droid-wiki/content/03-markdown-mdx-processing.md`
- `AGENTS.md` and `.agents/AGENTS.md`
- `src/pages/api/` (verify APIRoute and prerender boundaries match docs)

## 3.2 Mission Objective

Audit all architectural documentation, wiki references, and agent guidelines.
Outcome: Ensure 100% synchronization between codebase reality and droid-wiki/, prove 0 doc integrity errors, eliminate deprecated Astro 4 / Next.js syntax from guides, and maintain a unified source of truth for future AI agents.
Constraints: Read-only audit; verify documentation links, script targets, and architectural conventions.
Autonomy Grant: You own this mission end-to-end. Trace doc paths, cross-references, and command definitions. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Run `pnpm check:doc-integrity` to verify all documented file paths and pnpm scripts exist.
2. Verify that `droid-wiki/content/03-markdown-mdx-processing.md` accurately documents the Sätteri Rust processor and 7 HAST/MDAST plugins.
3. Check `AGENTS.md`: ensure rules regarding zero-copying to user MacBook and Cloudflare Tunnel review protocols are clearly documented.
4. Audit documentation for architectural anti-patterns, stale syntax, and Next.js legacy baggage:

### ❌ Bad Practice / Anti-Pattern (Stale Registry & Deprecated Syntax)

```astro
---
// Outdated Astro 4 documentation snippet in wiki or agent guides:
// ❌ Deprecated in Astro 5; triggers runtime warnings and lacks modern lifecycle events
import { ViewTransitions } from "astro:transitions";
---
<head>
  <ViewTransitions />
</head>
```

```ts
// Outdated or non-standard API route documentation (Next.js baggage):
// ❌ Missing export const prerender = false; runs at build time into static JSON!
// ❌ Returning raw object throws "The endpoint did not return a Response"
export async function POST(context: any) {
  return { success: true }
}
```

_Why this fails:_ Documenting deprecated imports like `ViewTransitions` misleads agents and developers into writing obsolete syntax. Omitting `prerender = false` on mutation endpoints bakes static responses during `astro build`, causing runtime mutation endpoints to 405 or serve stale data.

### ✅ Best Practice / Idiomatic (Canonical Astro 5 Documentation Standards)

```astro
---
// Canonical Astro 5 ClientRouter documentation:
// ✅ Idiomatic Astro 5 SPA router with animation fallback and history management
import { ClientRouter } from "astro:transitions";
---
<head>
  <ClientRouter fallback="animate" />
</head>
```

```ts
// Canonical API route contract matching documented architecture:
import type { APIRoute } from 'astro'

// ✅ Required for dynamic on-demand mutation in output: 'static' builds
export const prerender = false

export const POST: APIRoute = async ({ request }) => {
  const body = await request.json()
  // ✅ Web standard Response object with explicit status
  return Response.json({ success: true, data: body }, { status: 200 })
}
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/05-edge-workers-and-qa/50-architectural-registry-wiki-sync/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: 05-data-fetching-and-endpoints/02-prerender-boundary-dynamic-endpoints`, `RULE-ID: 05-data-fetching-and-endpoints/03-apiroute-signature-and-web-response`, `RULE-ID: 09-performance-prefetch-and-transitions/06-audit-client-router-default-prefetch-all`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/05-edge-workers-and-qa/50-architectural-registry-wiki-sync/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "50-ARCHITECTURAL-REGISTRY-WIKI-SYNC-001",
    "rule_id": "RULE-ID: 05-data-fetching-and-endpoints/02-prerender-boundary-dynamic-endpoints",
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
  --body "docs/audits/results/05-edge-workers-and-qa/50-architectural-registry-wiki-sync/issue-body.md" \
  --title "[Audit - Architectural Registry & Documentation Synchronization Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/05-edge-workers-and-qa/50-architectural-registry-wiki-sync/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Run `pnpm check:doc-integrity` and confirm 0 errors across all 390 doc files, 655 paths, and 140 scripts.
2. Run `pnpm check:boundaries` and confirm 0 workspace boundary violations.
3. Grep documentation and code for deprecated syntax:
   ```bash
   # Confirm zero occurrences of deprecated ViewTransitions in docs and components
   git grep -n "ViewTransitions" src/ droid-wiki/
   # Confirm all API routes adhere to APIRoute standard and declare prerender boundary
   git grep -n "export const prerender = false" src/pages/api/
   ```
4. Audit for synthetic pulsing badges or arbitrary border radius tokens:
   `git grep -n "animate-pulse" src/`
   `git grep -n "rounded-lg\|rounded-xl\|rounded-2xl" src/`
5. Verify Playwright visual testing config:
   `pnpm vitest run tests/int/visual-regression.test.ts`

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/05-edge-workers-and-qa/50-architectural-registry-wiki-sync/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Architectural Registry & Documentation Synchronization Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/05-edge-workers-and-qa/50-architectural-registry-wiki-sync/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/05-edge-workers-and-qa/50-architectural-registry-wiki-sync/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/05-edge-workers-and-qa/50-architectural-registry-wiki-sync/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/05-edge-workers-and-qa/50-architectural-registry-wiki-sync/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/05-edge-workers-and-qa/50-architectural-registry-wiki-sync/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
