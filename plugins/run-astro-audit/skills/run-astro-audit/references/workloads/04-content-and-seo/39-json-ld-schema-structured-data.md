# Mission Brief: JSON-LD Schema & Structured Data Rich Results Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

Search engines rely on structured data (JSON-LD) to power rich snippets (breadcrumbs, FAQs, articles, organization profiles).
The Astro application injects schema blocks across multiple templates:

- Organization & WebSite (Homepage)
- Service & ProfessionalService (Service Hubs and Details)
- FAQPage (FAQ sections)
- Article & TechArticle (Blog posts and guides)
- DefinedTerm (Glossary terms)
- BreadcrumbList (All hierarchical pages)

### Authoritative Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`04-define-type-safe-schemas-with-zod.md`](../../best-practices/04-content-layer-and-collections/04-define-type-safe-schemas-with-zod.md) — Type-safe frontmatter schema definitions, validation, and JSON-LD structured data modeling (`RULE-ID: 04-content-layer-and-collections/04-define-type-safe-schemas-with-zod`).
- [`09-custom-404-and-500-error-routing.md`](../../best-practices/03-routing-and-pages/09-custom-404-and-500-error-routing.md) — Custom error routing and HTTP status code fidelity ensuring missing pages or error boundaries never emit misleading schema (`RULE-ID: 03-routing-and-pages/09-custom-404-and-500-error-routing`).
- [`11-filter-queries-with-sqlite-query-store.md`](../../best-practices/04-content-layer-and-collections/11-filter-queries-with-sqlite-query-store.md) — High-speed SQLite querying for content collection records feeding schema generators (`RULE-ID: 04-content-layer-and-collections/11-filter-queries-with-sqlite-query-store`).
- [`12-ui-translation-dictionaries-and-type-safety.md`](../../best-practices/08-i18n-and-localization/12-ui-translation-dictionaries-and-type-safety.md) — Type-safe translation dictionaries and localized metadata (`RULE-ID: 08-i18n-and-localization/12-ui-translation-dictionaries-and-type-safety`).
- [`15-content-layer-store-architecture.md`](../../best-practices/01-architecture-and-philosophy/15-content-layer-store-architecture.md) — Content Layer data store architecture unifying structured data sources (`RULE-ID: 01-architecture-and-philosophy/15-content-layer-store-architecture`).

Architectural facts and structured data invariants:

- Google Search Central & Schema.org Specification Compliance: Every schema block must be valid, well-formed JSON, emitted via `<script type="application/ld+json">` with strict HTML script entity escaping (`replace(/</g, '\\u003c')`) to prevent XSS script breakout.
- Canonical URL & Identity Integrity: Schema `@id`, `url`, and breadcrumb `item` fields must be fully qualified canonical URLs generated via `Astro.site` and `getAbsoluteLocaleUrl()`, never relative paths (`/en/services/...` is invalid).
- Anti-Cloaking & Parity Mandate: `FAQPage` schema must strictly mark up questions and answers visibly present in the DOM. Marking up invisible or suppressed accordion content violates Google Search quality guidelines.
- Multilingual Entity Grounding: Schemas must declare `inLanguage` matching `Astro.currentLocale` (`en-US`, `tr-TR`, `ar-AE`), and organization entities must link to verified Wikidata / social knowledge graph identifiers (`sameAs`).

Critical files to inspect:

- `src/components/seo/` or schema generators in `src/lib/`
- `src/layouts/SiteLayout.astro`
- `src/features/homepage/components/`
- `src/components/service-hierarchy/`
- `src/features/resources/components/`

## 3.2 Mission Objective

Audit all JSON-LD structured data generators across the site.
Outcome: Prove 100% compliance with Google Search Central Structured Data guidelines, zero syntax errors (valid JSON without trailing commas or unescaped quotes), and complete breadcrumb hierarchies.
Constraints: Read-only audit; validate JSON-LD schemas.
Autonomy Grant: You own this mission end-to-end. Extract JSON-LD scripts, validate schema properties against schema.org, and test entity relationships. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Extract JSON-LD blocks from rendered HTML and parse with `JSON.parse()` to catch trailing commas or syntax defects.
2. Verify required schema fields (e.g. headline, author, datePublished, image for Article; provider, serviceType for Service).
3. Ensure `FAQPage` schema only marks up questions that are visibly rendered on the page (anti-cloaking policy).
4. Validate that all schema `@id` and URL properties use absolute canonical URLs (`https://example.com/...`).
5. Check breadcrumb position sequences: verify 1-indexed contiguous numbering without gaps.
6. Contrast naive Next.js / string-interpolated JSON-LD schemas with strongly-typed, Zod-validated Astro schema components.

### ❌ Bad Practice / Anti-Pattern (Unescaped String Interpolation & Relative URLs)

```astro
---
// src/components/seo/ArticleSchema.astro - String template interpolation risking syntax errors & XSS
const { title, date, excerpt, slug } = Astro.props;
---
<!-- BAD: Unescaped string interpolation causes JSON parse errors when title contains quotes or <script> tags -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "datePublished": "{date}",
  "description": "{excerpt}",
  "url": "/blog/{slug}" // BUG: Relative URL violates Google Structured Data specs
}
</script>
```

_Why this fails:_ Manual string templating crashes with invalid JSON whenever content contains unescaped double quotes, unescaped newlines, or HTML characters. Emitting relative URLs violates Google Schema.org specs. Leaving `<script>` unescaped opens severe XSS vulnerabilities.

### ✅ Best Practice / Idiomatic (Strongly-Typed Schema Serialized via JSON.stringify & Validated with Zod)

```astro
---
// src/components/seo/JsonLd.astro - Strongly-typed schema objects serialized via JSON.stringify & validated with Zod
import { z } from "astro:content";
import { getAbsoluteLocaleUrl } from "astro:i18n";

// Zod schema enforcing Google Search Central and Schema.org specifications
export const ArticleSchemaValidator = z.object({
  "@context": z.literal("https://schema.org"),
  "@type": z.literal("Article"),
  headline: z.string().min(1).max(110),
  datePublished: z.string().datetime(),
  description: z.string().min(1),
  url: z.string().url(),
  inLanguage: z.enum(["tr-TR", "en-US", "ar-AE"]),
  author: z.object({
    "@type": z.literal("Person"),
    name: z.string(),
    url: z.string().url(),
  }),
});

export type ArticleSchemaType = z.infer<typeof ArticleSchemaValidator>;

interface Props {
  schema: Record<string, unknown>;
}

const { schema } = Astro.props;

// Type-safe schema validation
const validatedSchema = ArticleSchemaValidator.parse(schema);

// Secure serialization with HTML script tag entity escaping to prevent XSS script breakout
const jsonString = JSON.stringify(validatedSchema, null, 2).replace(/</g, "\\u003c");
---
<script type="application/ld+json" set:html={jsonString} />
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/04-content-and-seo/39-json-ld-schema-structured-data/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: 04-content-layer-and-collections/04-define-type-safe-schemas-with-zod`, `RULE-ID: 03-routing-and-pages/09-custom-404-and-500-error-routing`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/04-content-and-seo/39-json-ld-schema-structured-data/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "39-JSON-LD-SCHEMA-STRUCTURED-DATA-001",
    "rule_id": "RULE-ID: 04-content-layer-and-collections/04-define-type-safe-schemas-with-zod",
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
   Execute the turnkey publisher script `scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting (<= 200 items, max 3 levels deep), creates the primary issue, spawns linked sub-issues (capped at 20) for critical and high severity defects, and commits/pushes results directly to `main` without PR:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/04-content-and-seo/39-json-ld-schema-structured-data/issue-body.md" \
  --title "[Audit - JSON-LD Schema & Structured Data Rich Results Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/04-content-and-seo/39-json-ld-schema-structured-data/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Search for raw unescaped JSON-LD script templates or direct string interpolations across codebase:
   ```bash
   git grep -n "application/ld+json" src/
   grep -rn 'application/ld+json' src/ | grep -v 'JsonLd'
   ```
2. Verify zero schema parse errors across all 73 page archetypes via schema-dts or zod validators:
   ```bash
   pnpm vitest run tests/int/json-ld-schema.test.ts
   ```
3. Audit rendered HTML on key archetypes to confirm valid JSON-LD:
   ```bash
   curl -s http://localhost:4321/en/ | grep -A 25 'type="application/ld+json"'
   ```
4. Audit breadcrumb schema IDs to ensure absolute URLs and sequential indexing:
   ```bash
   curl -s http://localhost:4321/en/services/seo | grep -A 20 'BreadcrumbList'
   ```
5. Confirm that FAQPage schemas match visible DOM content without cloaked entities.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/04-content-and-seo/39-json-ld-schema-structured-data/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** JSON-LD Schema & Structured Data Rich Results Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/04-content-and-seo/39-json-ld-schema-structured-data/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/04-content-and-seo/39-json-ld-schema-structured-data/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/04-content-and-seo/39-json-ld-schema-structured-data/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/04-content-and-seo/39-json-ld-schema-structured-data/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/04-content-and-seo/39-json-ld-schema-structured-data/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
