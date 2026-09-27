# Mission Brief: Hreflang Cluster & Bidirectional Return-Tag Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

Google's international SEO ranking algorithm enforces the strict return-tag rule:
If page A links to page B as an alternate hreflang, page B MUST link back to page A as its alternate. If any target 404s or redirects, the entire cluster is discarded by Google search crawlers.

- Return-Tag & Google Search Central Standards: Every localized variant must be linked with fully qualified absolute URLs via `getAbsoluteLocaleUrl()` from `astro:i18n`, never relative paths.
- Reciprocity Requirement: If `/en/services/seo` links to `/tr/hizmetler/seo`, `/tr/hizmetler/seo` must link back to `/en/services/seo`.
- Self-Referencing Requirement: Every page MUST include a self-referencing `hreflang` tag for its own locale.
- Language-Neutral Fallback: `hreflang="x-default"` must point to the default locale (English `/en/`) to handle unmatched user locales without redirect loops.
- Sitemap Synchronization: `@astrojs/sitemap` must configure `i18n` mapping (`en: "en-US"`, `tr: "tr-TR"`, `ar: "ar-AE"`) generating `<xhtml:link rel="alternate">` inside `<url>` tags in `dist/sitemap-0.xml`.
- Content Parity Constraint: Pages with `fallbackType: "rewrite"` or missing translations must not emit dangling alternates that 404 or redirect.

### Authoritative Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`08-multilingual-seo-hreflang-and-canonical.md`](../../best-practices/08-i18n-and-localization/08-multilingual-seo-hreflang-and-canonical.md) — Generating complete self-referencing hreflang clusters, reciprocal return tags, and `x-default` meta tags (`RULE-ID: 08-i18n-and-localization/08-multilingual-seo-hreflang-and-canonical`).
- [`03-type-safe-url-helpers.md`](../../best-practices/08-i18n-and-localization/03-type-safe-url-helpers.md) — Using `getAbsoluteLocaleUrl()` from `astro:i18n` to produce fully qualified absolute alternate URLs (`RULE-ID: 08-i18n-and-localization/03-type-safe-url-helpers`).
- [`01-native-i18n-configuration.md`](../../best-practices/08-i18n-and-localization/01-native-i18n-configuration.md) — Native i18n routing configuration in `astro.config.mjs` ensuring consistent locale route resolution (`RULE-ID: 08-i18n-and-localization/01-native-i18n-configuration`).
- [`09-localized-sitemap-generation.md`](../../best-practices/08-i18n-and-localization/09-localized-sitemap-generation.md) — Synchronizing on-page alternate links with `@astrojs/sitemap` XML alternate clusters (`RULE-ID: 08-i18n-and-localization/09-localized-sitemap-generation`).
- [`08-redirects-and-rewrites.md`](../../best-practices/03-routing-and-pages/08-redirects-and-rewrites.md) — Preventing hreflang alternates from targeting redirect sources or rewriting endpoints (`RULE-ID: 03-routing-and-pages/08-redirects-and-rewrites`).
- [`07-bidirectional-rtl-ltr-handling.md`](../../best-practices/08-i18n-and-localization/07-bidirectional-rtl-ltr-handling.md) — Pairing bidirectional localized secondary locale (RTL) alternate links with English and localized primary locale (LTR) equivalents (`RULE-ID: 08-i18n-and-localization/07-bidirectional-rtl-ltr-handling`).
- [`15-cross-language-content-linking.md`](../../best-practices/08-i18n-and-localization/15-cross-language-content-linking.md) — Cross-language slug mapping and paired alternate resolution without dangling links (`RULE-ID: 08-i18n-and-localization/15-cross-language-content-linking`).

Critical files to inspect:

- `src/lib/routing/enumerate.ts` (`pairedAlternate`, `computeHreflangAlternates`)
- `src/lib/routing/category-references.ts`
- `src/layouts/SiteLayout.astro` (`<link rel="alternate" hreflang="...">`)
- `astro.config.mjs` (`i18n` config & `@astrojs/sitemap` integration)

## 3.2 Mission Objective

Audit all hreflang tags emitted across the site.
Outcome: Prove 100% bidirectional return-tag integrity across all 3,900+ routes, zero hreflang links pointing to 404s or redirect sources, and valid x-default canonical tags.
Constraints: Read-only audit; verify hreflang graphs and sitemap data.
Autonomy Grant: You own this mission end-to-end. Traverse the alternate URL graph, check status codes, and validate language codes (en, tr, ar). The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `pairedAlternate()` in `enumerate.ts`: ensure retired team members or redirect sources never emit hreflang alternates.
2. Inspect `SiteLayout.astro`: verify canonical link tag format and hreflang alternate link generation using `getAbsoluteLocaleUrl()`.
3. Validate that `x-default` points to the English primary URL (`https://example.com/en/...`).
4. Inspect `dist/sitemap-0.xml`: verify XML sitemap `<xhtml:link rel="alternate">` tags match on-page HTML alternate tags 1:1.
5. Audit pagination tails (`/blog/page/2/`): ensure alternates correctly reflect paginated siblings rather than collapsing onto page 1.
6. Verify reciprocity: verify that for any page pairing (e.g. EN <-> TR <-> AR), each variant reciprocates all others.

### ❌ Bad Practice / Anti-Pattern (One-Way Relative Hreflang & Missing Reciprocity)

```astro
---
// ❌ Anti-Pattern: Relative paths, one-way links, missing self-ref and x-default
// Common migration blunder from Next.js where metadata is built via ad-hoc string concatenation
const { pathname } = Astro.url;
---
<head>
  <!-- BUG: Relative paths violate search engine specs; Google Search Console drops the cluster -->
  <link rel="canonical" href={pathname} />
  <!-- BUG: One-way link: /tr equivalent might not link back to /en, breaking reciprocity -->
  <link rel="alternate" hreflang="tr" href={`/tr${pathname}`} />
  <!-- BUG: Missing self-referencing hreflang="en" and missing hreflang="x-default" fallback! -->
  <!-- BUG: Dangerously points to /tr/ even if /tr/ equivalent 404s or 301 redirects -->
</head>
```

### ✅ Best Practice / Idiomatic (Full Cluster Hreflang with Self-Ref & x-default)

```astro
---
// ✅ Idiomatic Astro: Fully compliant, reciprocal absolute hreflang cluster
import { getAbsoluteLocaleUrl } from "astro:i18n";
import { computeHreflangAlternates } from "@/lib/routing/enumerate";

interface Props {
  subpath?: string;
}
const { subpath = Astro.url.pathname } = Astro.props;

// Invariant: Only active, non-redirecting, reciprocal variants are emitted
const alternates = computeHreflangAlternates(subpath);
const canonicalURL = new URL(Astro.url.pathname, Astro.site);
---
<head>
  <!-- Self-referencing canonical URL -->
  <link rel="canonical" href={canonicalURL.href} />

  <!-- Reciprocal language alternates (including self-referencing locale) -->
  {alternates.map(({ lang, url }) => (
    <link rel="alternate" hreflang={lang} href={url} />
  ))}

  <!-- Language-neutral fallback to default locale -->
  <link
    rel="alternate"
    hreflang="x-default"
    href={getAbsoluteLocaleUrl("en", subpath)}
  />
</head>
```

### ❌ Bad Practice / Anti-Pattern (Dangling Alternate to Redirect Source)

```html
<!-- ❌ Emitting alternate links pointing to redirect sources or 404s -->
<!-- On https://example.com/en/services/seo -->
<link rel="alternate" hreflang="tr" href="https://example.com/tr/seo" />
<!-- BUG: https://example.com/tr/seo 301-redirects to https://example.com/tr/hizmetler/seo!
     Google discards the hreflang annotation because it targets a non-200 redirect URL. -->
```

### ✅ Best Practice / Idiomatic (Canonical Direct Target in Alternates)

```html
<!-- ✅ Direct canonical target resolving in a single 200 OK hop -->
<link rel="alternate" hreflang="tr" href="https://example.com/tr/hizmetler/seo" />
<link rel="alternate" hreflang="en" href="https://example.com/en/services/seo" />
<link rel="alternate" hreflang="ar" href="https://example.com/ar/services/seo" />
<link rel="alternate" hreflang="x-default" href="https://example.com/en/services/seo" />
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/04-content-and-seo/36-hreflang-cluster-return-tags/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: 08-i18n-and-localization/08-multilingual-seo-hreflang-and-canonical`, `RULE-ID: 08-i18n-and-localization/03-type-safe-url-helpers`, `RULE-ID: 08-i18n-and-localization/09-localized-sitemap-generation`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/04-content-and-seo/36-hreflang-cluster-return-tags/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "36-HREFLANG-CLUSTER-RETURN-TAGS-001",
    "rule_id": "RULE-ID: 08-i18n-and-localization/08-multilingual-seo-hreflang-and-canonical",
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
  --body "docs/audits/results/04-content-and-seo/36-hreflang-cluster-return-tags/issue-body.md" \
  --title "[Audit - Hreflang Cluster & Bidirectional Return-Tag Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/04-content-and-seo/36-hreflang-cluster-return-tags/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Audit codebase for absolute locale URL helpers in head tags:
   ```bash
   git grep -n "getAbsoluteLocaleUrl" src/
   ```
2. Audit layout templates for hreflang tag declarations:
   ```bash
   git grep -n "hreflang" src/layouts/
   ```
3. Audit rendered HTML for absolute hreflang and reciprocal tags:
   ```bash
   curl -s http://localhost:4321/en/ | grep -E 'rel="(canonical|alternate)"'
   curl -s http://localhost:4321/tr/ | grep -E 'rel="(canonical|alternate)"'
   ```
4. Verify XML sitemap alternate links across all generated shards:
   ```bash
   grep -A 5 "xhtml:link" dist/sitemap-*.xml | head -n 30
   ```
5. Audit templates for relative hreflang links or raw string concatenation:
   ```bash
   grep -rn 'rel="alternate"' src/ | grep -v 'getAbsoluteLocaleUrl'
   ```
6. Run integration tests to prove 100% cluster integrity:
   ```bash
   pnpm vitest run tests/int/crawl-click-depth.test.ts
   pnpm vitest run tests/int/seo-meta.test.ts
   ```
7. Confirm zero orphaned hreflang tags across all emitted static HTML pages.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/04-content-and-seo/36-hreflang-cluster-return-tags/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Hreflang Cluster & Bidirectional Return-Tag Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/04-content-and-seo/36-hreflang-cluster-return-tags/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/04-content-and-seo/36-hreflang-cluster-return-tags/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/04-content-and-seo/36-hreflang-cluster-return-tags/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/04-content-and-seo/36-hreflang-cluster-return-tags/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/04-content-and-seo/36-hreflang-cluster-return-tags/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
