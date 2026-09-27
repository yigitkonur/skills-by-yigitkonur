# Mission Brief: Central Redirect Table & Loop/Chain Prevention Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

The site maintains a central redirect table (`src/lib/redirects/index.ts`) containing 735+ non-category rules plus thin category redirects (total 836+ rules):

- 138 authored-static
- 71 geo-ia
- 74 ai-consultancy-ia
- 58 content-marketing-legacy
- 18 rewrite-alias
- 96 duplicate-shape
- 280 former-team
- thin-category rules
  Architectural invariants and best practice standards:
- Single-Hop Resolution Invariant: The edge redirect resolver (`src/lib/redirects/index.ts` & `src/worker.ts`) must resolve every rule directly to its canonical destination in exactly one hop (<1ms), completely eliminating multi-hop chains (`A -> B -> C`).
- Strict Loop & Self-Redirect Prohibition: Under no circumstances can a rule redirect to itself (`source === destination`) or cycle back (`A -> B -> A`).
- Trailing Slash Symmetry: Destination paths must strictly conform to the site's trailing slash policy (no trailing slashes, e.g. `/tr/hizmetler` not `/tr/hizmetler/`), preventing an extra hop from edge canonicalization.
- Redirects vs Rewrites: Distinguish permanent URL migrations (HTTP 301/308) from transparent content fallbacks. In Astro 4.15+ / Astro 5, use `routing.fallbackType: "rewrite"` or `Astro.rewrite()` for language fallbacks to avoid visible browser URL jumps and extra network hops.
- Status Code Rigor: Permanent path moves must use HTTP 308 (preserving HTTP method) or 301; temporary routing rules use 307 or 302.

### Authoritative Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`08-redirects-and-rewrites.md`](../../best-practices/03-routing-and-pages/08-redirects-and-rewrites.md) — Declaring static redirects in `astro.config.mjs` vs dynamic `Astro.redirect()` and `Astro.rewrite()`, eliminating multi-hop chains (`RULE-ID: 03-routing-and-pages/08-redirects-and-rewrites`).
- [`01-native-i18n-configuration.md`](../../best-practices/08-i18n-and-localization/01-native-i18n-configuration.md) — Native Astro i18n routing configuration preventing prefix collision loops with redirect tables (`RULE-ID: 08-i18n-and-localization/01-native-i18n-configuration`).
- [`03-type-safe-url-helpers.md`](../../best-practices/08-i18n-and-localization/03-type-safe-url-helpers.md) — Localized destination path validation respecting `trailingSlash` configuration (`RULE-ID: 08-i18n-and-localization/03-type-safe-url-helpers`).
- [`04-fallback-rewrite-vs-redirect.md`](../../best-practices/08-i18n-and-localization/04-fallback-rewrite-vs-redirect.md) — Distinguishing permanent redirects (301/308) from transparent fallback rewrites (`Astro.rewrite()`) (`RULE-ID: 08-i18n-and-localization/04-fallback-rewrite-vs-redirect`).
- [`03-route-priority-and-collision-resolution.md`](../../best-practices/03-routing-and-pages/03-route-priority-and-collision-resolution.md) — Route priority and collision resolution between static endpoints, edge redirects, and dynamic pages (`RULE-ID: 03-routing-and-pages/03-route-priority-and-collision-resolution`).
- [`07-bidirectional-rtl-ltr-handling.md`](../../best-practices/08-i18n-and-localization/07-bidirectional-rtl-ltr-handling.md) — Ensuring localized secondary locale redirected endpoints cleanly land on localized RTL pages without secondary locale-switching hops (`RULE-ID: 08-i18n-and-localization/07-bidirectional-rtl-ltr-handling`).
- [`08-multilingual-seo-hreflang-and-canonical.md`](../../best-practices/08-i18n-and-localization/08-multilingual-seo-hreflang-and-canonical.md) — Canonical self-referencing alignment preventing redirect sources from being indexed as canonical targets (`RULE-ID: 08-i18n-and-localization/08-multilingual-seo-hreflang-and-canonical`).
- [`09-custom-404-and-500-error-routing.md`](../../best-practices/03-routing-and-pages/09-custom-404-and-500-error-routing.md) — Terminating dead paths cleanly at 404 instead of generating endless redirect cycles (`RULE-ID: 03-routing-and-pages/09-custom-404-and-500-error-routing`).

Critical files to inspect:

- `src/lib/redirects/index.ts`
- `src/lib/redirects/redirects.test.ts`
- `tests/int/astro-pages-edge-policy.test.ts`
- `src/worker.ts`
- `astro.config.mjs`

## 3.2 Mission Objective

Audit the central redirect table and edge resolution engine.
Outcome: Prove zero redirect loops, zero redirect chains (A -> B -> C), zero invalid status codes, and 100% test pass on edge policy tests.
Constraints: Read-only audit; execute validation algorithms.
Autonomy Grant: You own this mission end-to-end. Trace destination paths, validate status codes, and test edge rule matching. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Run `validateRedirectTable()` and inspect the returned issues array.
2. Verify that `resolveRedirect()` resolves every rule in a single hop (<1ms).
3. Ensure that redirect destinations never end with trailing slashes.
4. Verify that dynamic redirects in page frontmatter return `Astro.redirect()` immediately before rendering chunks to prevent stream lock issues.
5. Distinguish between URL rewrites (`Astro.rewrite()`) and redirects: ensure rewrites serve status 200 without changing browser URL.
6. Check for static redirect definitions in `astro.config.mjs` to ensure they are flat and non-chained.

### ❌ Bad Practice / Anti-Pattern (Multi-Hop Redirect Chains & Trailing Slash Drift)

```typescript
// ❌ Anti-Pattern: Chained multi-hop redirects with trailing slash drift
// Common in legacy Next.js / Apache migrations where old redirects are stacked on top of each other
export const redirects = [
  { source: '/old-service', destination: '/en/services/legacy/', status: 301 },
  // Trailing slash causes secondary hop: /en/services/legacy/ -> /en/services/legacy
  { source: '/en/services/legacy', destination: '/en/services/modern', status: 301 },
  // Multi-hop chain: /old-service -> /en/services/legacy/ -> /en/services/legacy -> /en/services/modern
  // Result: 3 HTTP roundtrips, crawl budget waste, inflated TTFB
]
```

### ✅ Best Practice / Idiomatic (Flattened Redirect Map in astro.config.mjs)

```javascript
// ✅ Idiomatic Astro: Flattened 301 redirect map declared directly in astro.config.mjs
// Or resolved in a single atomic edge hop in src/lib/redirects/index.ts
import { defineConfig } from 'astro/config'

export default defineConfig({
  redirects: {
    // Both legacy paths resolve directly to the final canonical URL in exactly 1 hop
    '/old-service': { status: 308, destination: '/en/services/modern' },
    '/en/services/legacy': { status: 308, destination: '/en/services/modern' },
  },
})
```

### ❌ Bad Practice / Anti-Pattern (Late Redirects in Nested Components)

```astro
---
// src/components/AuthGate.astro
// ❌ Anti-Pattern: Calling redirect inside child component during HTML streaming
const { user } = Astro.props;
if (!user) {
  // Silent failure or stream corruption: page headers already sent!
  Astro.redirect("/login");
}
---
<div>Protected Content</div>
```

### ✅ Best Practice / Idiomatic (Frontmatter-Level Redirects & Fallback Rewrites)

```astro
---
// src/pages/dashboard.astro
// ✅ Idiomatic Astro: Immediate early return at top of root page frontmatter
const session = Astro.cookies.get("session")?.value;
if (!session) {
  return Astro.redirect("/login", 302);
}
---
<h1>Dashboard</h1>
```

```astro
---
// src/pages/ar/[...slug].astro
// ✅ Idiomatic Astro: Astro.rewrite() serves content transparently without URL jump
if (!haslocalized secondary localeTranslation(Astro.params.slug)) {
  return Astro.rewrite(`/en/${Astro.params.slug}`);
}
---
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/04-content-and-seo/37-central-redirect-table-loops-chains/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: 03-routing-and-pages/08-redirects-and-rewrites`, `RULE-ID: 08-i18n-and-localization/01-native-i18n-configuration`, `RULE-ID: 03-routing-and-pages/03-route-priority-and-collision-resolution`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/04-content-and-seo/37-central-redirect-table-loops-chains/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "37-CENTRAL-REDIRECT-TABLE-LOOPS-CHAINS-001",
    "rule_id": "RULE-ID: 03-routing-and-pages/08-redirects-and-rewrites",
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
  --body "docs/audits/results/04-content-and-seo/37-central-redirect-table-loops-chains/issue-body.md" \
  --title "[Audit - Central Redirect Table & Loop/Chain Prevention Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/04-content-and-seo/37-central-redirect-table-loops-chains/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Run redirect unit test suite:
   ```bash
   pnpm vitest run src/lib/redirects/redirects.test.ts
   ```
2. Run edge policy integration test suite:
   ```bash
   pnpm vitest run tests/int/astro-pages-edge-policy.test.ts
   ```
3. Audit configuration and source files for redirects declaration:
   ```bash
   git grep -n "redirects" astro.config.mjs src/lib/redirects/
   ```
4. Audit the redirect table programmatically for loops, chains, and trailing slashes:
   ```bash
   node -e "import('./src/lib/redirects/index.ts').then(m => { const issues = m.validateRedirectTable ? m.validateRedirectTable() : []; console.log('Issues found:', issues.length); if (issues.length) console.table(issues); })"
   ```
5. Test single-hop edge resolution with curl:
   ```bash
   curl -sI http://localhost:4321/old-service | grep -E "(HTTP/|location:)"
   ```
6. Verify 0 duplicate sources, 0 self-redirects, and 0 chained hops across all 836+ entries.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/04-content-and-seo/37-central-redirect-table-loops-chains/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Central Redirect Table & Loop/Chain Prevention Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/04-content-and-seo/37-central-redirect-table-loops-chains/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/04-content-and-seo/37-central-redirect-table-loops-chains/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/04-content-and-seo/37-central-redirect-table-loops-chains/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/04-content-and-seo/37-central-redirect-table-loops-chains/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/04-content-and-seo/37-central-redirect-table-loops-chains/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
