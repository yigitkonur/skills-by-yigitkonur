# Mission Brief: Server Islands (server:defer) URL Limit & Key Profiler Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

Astro Server Islands (`<Component server:defer />`) enable on-demand deferred rendering for personalized or dynamic content while keeping the host page statically cached at the CDN edge.
Three critical architectural pillars govern Server Island reliability and performance:

1. **URL Limit & HTTP Caching Boundary (<2048 bytes):** Astro encrypts component props into a URL query parameter on an HTTP `GET` request. Standard browser and CDN edge caches store HTTP `GET` responses via standard `Cache-Control` headers. If serialized props exceed 2048 bytes, Astro falls back to an uncacheable HTTP `POST` request with props in the body, completely destroying edge caching benefits. Props must be restricted to minimal scalar identifiers (e.g. `id`, `slug`), fetching rich data inside the island.
2. **Layout Shift Prevention (`slot="fallback"`):** Omitting fallback UI causes severe Cumulative Layout Shift (CLS) when deferred HTML swaps into the DOM. Every server island must provide a statically rendered, layout-stable skeleton inside `<slot="fallback">` adhering to The project's Swiss typography standards.
3. **Persistent Distributed Key (`ASTRO_KEY`):** By default, Astro generates an ephemeral encryption key at build time. In distributed multi-region or rolling deployment environments (such as Cloudflare Workers), client HTML served with one build key will fail to decrypt on an edge worker running a different key, returning fatal HTTP 500 errors (`Failed to decrypt server island props`). A persistent secret key (`ASTRO_KEY`) must be generated via `astro create-key` and passed through environment secrets.

### Authoritative Astro Architectural & Best Practice Rules

Auditors must inspect, evaluate, and verify all deferred server component implementations against the repository's authoritative Astro best practices:

- **Primary Deferral Contract**: [11-defer-personalized-content-with-server-islands.md](../../best-practices/02-islands-and-hydration/11-defer-personalized-content-with-server-islands.md) — Defer personalized content with Server Islands (`server:defer`).
- **Primary URL Length Contract**: [12-keep-server-island-props-under-url-limit.md](../../best-practices/02-islands-and-hydration/12-keep-server-island-props-under-url-limit.md) — Keep Server Island props lightweight and under URL length limits (< 2048 bytes).
- **Frontmatter Security Boundary**: [03-frontmatter-security-boundary.md](../../best-practices/01-architecture-and-philosophy/03-frontmatter-security-boundary.md) — Isolate secrets and database calls in frontmatter without leaking to client bundles.
- **Middleware State Contract**: [04-mutate-locals-never-reassign.md](../../best-practices/06-middleware-and-auth/04-mutate-locals-never-reassign.md) — Mutate `context.locals` properties; never overwrite the object.
- **Static Asset Bypass**: [05-filter-static-asset-requests.md](../../best-practices/06-middleware-and-auth/05-filter-static-asset-requests.md) — Filter out static assets before executing heavy middleware logic.
- **Streaming Pipeline Contract**: [19-avoid-consuming-streaming-response-body-in-middleware.md](../../best-practices/06-middleware-and-auth/19-avoid-consuming-streaming-response-body-in-middleware.md) — Avoid consuming streaming response bodies in post-execution middleware.
- **Headless Unit Testing**: [21-unit-test-components-with-astro-container-api.md](../../best-practices/10-auditing-testing-and-nextjs-migration/21-unit-test-components-with-astro-container-api.md) — Unit test `.astro` components headlessly with the Astro Container API.

Critical files to inspect:

- `src/components/`
- `src/pages/`
- `astro.config.mjs`
- `wrangler.jsonc` / `.env`

## 3.2 Mission Objective

Audit current and candidate Server Island usage across the codebase, ensuring prop payloads remain well under the 2048-byte limit, stable fallback skeletons prevent CLS, and `ASTRO_KEY` is properly configured for distributed edge execution.
Outcome: Establish complete Server Island architectural compliance, eliminating payload bloat, cache degradation, and edge decryption errors.
Constraints: Read-only audit; do not alter production code.
Autonomy Grant: You own this mission end-to-end. Profile island props, inspect server deferral points, and verify edge environment configuration. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Search for `server:defer` across all `.astro` components and templates.
2. Inspect prop signatures of deferred components to verify only primitive scalar IDs are passed (never 50+ field database entities or large JSON blobs).
3. Verify that every `server:defer` component defines a `slot="fallback"` with an understated, layout-stable skeleton matching Swiss typography standards.
4. Audit environment configuration (`ASTRO_KEY`) in `.env`, `wrangler.jsonc`, and CI/CD secret managers to verify encryption key stability across rolling deployments.
5. Identify candidates for Server Island deferral (e.g. personalized proposals, dynamic greetings, cart summaries) currently forcing pages into dynamic SSR.

### ❌ Bad Practice / Anti-Pattern (Bloated Props, Missing Fallbacks & Ephemeral Keys)

```astro
---
// src/pages/services/[slug].astro (Bloated props + missing fallback + ephemeral key)
// In Next.js RSC, server data streams over a persistent HTTP payload stream;
// in Astro, Server Islands are discrete REST endpoints where oversized props destroy caching!
import DynamicProposal from '../../components/DynamicProposal.astro';
const fullLead = await getFullLeadContext(Astro.params.slug); // 50+ fields, history, analytics
---
<!-- ❌ FATAL: Exceeds 2048 bytes! Forces uncacheable HTTP POST request fallback -->
<!-- ❌ FATAL: Missing fallback slot causes jarring Cumulative Layout Shift (CLS) -->
<DynamicProposal server:defer lead={fullLead} />
<!-- ❌ FATAL: Relying on auto-generated ephemeral key throws HTTP 500 across rolling deployments -->
```

### ✅ Best Practice / Idiomatic (Scalar IDs, Stable Fallbacks & Durable ASTRO_KEY)

```astro
---
// src/pages/services/[slug].astro (Minimal scalar ID + layout-stable fallback)
// Bound to RULE-ID: 02-islands-and-hydration/12-keep-server-island-props-under-url-limit
// Bound to RULE-ID: 02-islands-and-hydration/11-defer-personalized-content-with-server-islands
import DynamicProposal from '../../components/DynamicProposal.astro';
import ProposalSkeleton from '../../components/ProposalSkeleton.astro';
const leadId = Astro.params.slug;
---
<!-- ✅ Small query string preserves cacheable GET request under 2048 bytes -->
<DynamicProposal server:defer leadId={leadId}>
  <!-- ✅ Layout-stable skeleton renders instantly; prevents CLS -->
  <ProposalSkeleton slot="fallback" />
</DynamicProposal>
```

In `DynamicProposal.astro`:

```astro
---
const { leadId } = Astro.props;
const lead = await fetchLeadById(leadId);
// Enable edge/browser caching on the server island endpoint
Astro.response.headers.set('Cache-Control', 'public, max-age=300, stale-while-revalidate=600');
---
<div class="proposal-card">{lead.title}</div>
```

Persistent key configuration:

```bash
# Generate durable key once:
npx astro create-key
# Set in .env / CI secret manager:
# ASTRO_KEY="d7a9b0c1e8f2345a90123456789abcdef0123456789abcdef0123456789abcdef"
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/07-migration-and-core-contracts/70-server-islands-defer-url-limit-profiler/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Rule-ID Mapping**: Every item in `findings.json` MUST explicitly map to an authoritative Astro best practice rule ID (e.g. `RULE-ID: 02-islands-and-hydration/12-keep-server-island-props-under-url-limit` or `RULE-ID: 02-islands-and-hydration/11-defer-personalized-content-with-server-islands`).

You must create and populate the following deliverables in `docs/audits/results/07-migration-and-core-contracts/70-server-islands-defer-url-limit-profiler/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "70-SERVER-ISLANDS-DEFER-URL-LIMIT-PROFILER-001",
    "rule_id": "RULE-ID: 02-islands-and-hydration/12-keep-server-island-props-under-url-limit",
    "file": "src/pages/services/[slug].astro",
    "line": 42,
    "severity": "critical" | "high" | "medium" | "low",
    "category": "performance" | "syntax" | "hydration" | "parity" | "security",
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
  --body "docs/audits/results/07-migration-and-core-contracts/70-server-islands-defer-url-limit-profiler/issue-body.md" \
  --title "[Audit - Server Islands (server:defer) URL Limit & Key Profiler Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/07-migration-and-core-contracts/70-server-islands-defer-url-limit-profiler/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Run `git grep -n "server:defer" src/` to identify all server island implementations.
2. Run `git grep -n "slot=\"fallback\"" src/` to verify presence of layout-stable fallback slots.
3. Run `git grep -n "defineMiddleware" src/` to verify compatibility with edge middleware routing.
4. Execute headless component testing with Vitest using `experimental_AstroContainer` from `astro/container` to render Server Island host components and fallback slots:
   ```bash
   pnpm exec vitest run tests/islands/ --run
   ```
5. Inspect network requests to `/_server-islands/[ComponentName]` in Chrome DevTools to confirm HTTP `GET` (status 200), not `POST`.
6. Verify `ASTRO_KEY` environment configuration:
   ```bash
   node -e "if (!process.env.ASTRO_KEY) console.warn('ASTRO_KEY not set in local env');"
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/07-migration-and-core-contracts/70-server-islands-defer-url-limit-profiler/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Server Islands (server:defer) URL Limit & Key Profiler Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/07-migration-and-core-contracts/70-server-islands-defer-url-limit-profiler/findings.json` (N defects logged with RULE-ID mappings)
   - `file://docs/audits/results/07-migration-and-core-contracts/70-server-islands-defer-url-limit-profiler/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/07-migration-and-core-contracts/70-server-islands-defer-url-limit-profiler/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/07-migration-and-core-contracts/70-server-islands-defer-url-limit-profiler/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/07-migration-and-core-contracts/70-server-islands-defer-url-limit-profiler/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
