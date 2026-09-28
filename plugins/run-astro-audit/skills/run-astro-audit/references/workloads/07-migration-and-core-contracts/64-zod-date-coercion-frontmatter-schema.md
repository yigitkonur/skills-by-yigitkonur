# Mission Brief: Zod Date Coercion (z.coerce.date) & Frontmatter Schema Guard

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

In Markdown, MDX frontmatter (YAML), and JSON content files, date fields are serialized as strings (e.g. `"2026-09-26"` or ISO-8601 timestamps) or parsed by YAML engines into arbitrary Date/string representations.
Using Zod's strict `z.date()` validator expects an existing JavaScript `Date` instance and throws fatal build-time validation crashes: `ZodError: Expected date, received string`.
Astro best practices require using `z.coerce.date()` or dedicated normalizers (such as `dateLike` in `src/content/zod-helpers.ts`) in all Content Layer collection schemas to safely coerce ISO strings, unix timestamps, and YAML date strings into verified native JavaScript `Date` objects or normalized ISO-8601 strings.
Unlike classic React / Next.js where date objects are often avoided across client component boundaries to prevent serialization errors, `.astro` components execute strictly on the server. Having a strongly typed native `Date` object (or canonical ISO string) enables direct invocation of `.toLocaleDateString()` or `.getTime()` without repetitive, fragile `new Date()` wraps in UI templates.

### Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`07-use-zod-date-coercion-for-flexible-metadata.md`](../../best-practices/04-content-layer-and-collections/07-use-zod-date-coercion-for-flexible-metadata.md) — Using `z.coerce.date()` to accept YAML strings and date objects (`RULE-ID: ASTRO-COLLECT-07`).
- [`08-coerce-frontmatter-dates-with-zod.md`](../../best-practices/04-content-layer-and-collections/08-coerce-frontmatter-dates-with-zod.md) — Coercing frontmatter timestamps with `z.coerce.date()` (`RULE-ID: ASTRO-COLLECT-08`).
- [`04-define-type-safe-schemas-with-zod.md`](../../best-practices/04-content-layer-and-collections/04-define-type-safe-schemas-with-zod.md) — Type-safe schema validation in Content Collections with Zod (`RULE-ID: ASTRO-COLLECT-04`).

Critical files to inspect:

- `src/content.config.ts`
- `src/content/collections/*.ts`
- `src/content/schemas/*.ts`
- `src/content/zod-helpers.ts`
- `src/data/` and content directories

## 3.2 Mission Objective

Audit all Content Layer collection schemas in `src/content.config.ts`, `src/content/collections/`, `src/content/schemas/`, and shared zod helpers to ensure every timestamp field uses `z.coerce.date()` or canonical `dateLike` preprocessors.
Outcome: Guarantee zero build-time Zod date validation crashes across all 3,897 routes.
Constraints: Read-only audit; do not alter production code.
Autonomy Grant: You own this mission end-to-end. Inspect all schema definitions, check date format variations in content files, and verify parser resiliency. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect every schema definition in `src/content/collections/*.ts` and `src/content/schemas/*.ts`.
2. Check for any usage of `z.date()` without coercion (e.g. `pubDate: z.date()`, `updatedDate: z.date().optional()`).
3. Verify that all date fields use `z.coerce.date()`, `dateLike`, or `z.preprocess()` to handle both quoted strings (`"2026-09-26"`) and unquoted YAML dates (`2026-09-26T12:00:00Z`).
4. Test schema validation against edge cases: empty strings, null, undefined, and non-standard date formats.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Strict z.date() vs. Resilient z.coerce.date() in Content Schemas (RULE-ID: ASTRO-COLLECT-07, RULE-ID: ASTRO-COLLECT-08)

##### ❌ Bad Practice / Anti-Pattern: Strict z.date() causing build failures on string frontmatter

```ts
// src/content/schemas/post.ts (Strict z.date causes build crashes on strings)
import { defineCollection, z } from 'astro:content'

export const blogSchema = z.object({
  title: z.string(),
  // ❌ Fails with 'ZodError: Expected date, received string' when parsing JSON or YAML strings
  pubDate: z.date(),
  updatedDate: z.date().optional(),
})
```

_Why this fails:_ In YAML frontmatter and JSON content files, dates are frequently authored or parsed as string literals (e.g. `"2026-09-26"`). Zod's `z.date()` expects an existing JavaScript `Date` instance, causing Astro builds to crash during content sync with fatal validation errors.

##### ✅ Best Practice / Idiomatic: Automatic type coercion with z.coerce.date() or dateLike helper

```ts
// src/content/schemas/post.ts (Robust coercion or canonical dateLike)
import { defineCollection, z } from 'astro:content'
import { dateLike } from '../zod-helpers'

export const blogSchema = z.object({
  title: z.string(),
  // ✅ Coerces string, number, or Date into a verified JavaScript Date object
  pubDate: z.coerce.date(),
  // Or uses normalized dateLike for canonical ISO-8601 string consistency
  updatedDate: z.coerce.date().optional(),
})
```

#### Pattern 2: Raw String Dates in Schemas vs. Coerced Server Date Instances (RULE-ID: ASTRO-COLLECT-04)

##### ❌ Bad Practice / Anti-Pattern: Storing dates as unvalidated strings and manually parsing in templates

```astro
---
// Schema defined date as z.string(); UI template forced to manually parse on every render:
const { post } = Astro.props;
// ❌ Fragile manual date instantiation prone to runtime Invalid Date errors
const formattedDate = new Date(post.data.pubDate).toLocaleDateString('tr-TR');
---
<time datetime={post.data.pubDate}>{formattedDate}</time>
```

##### ✅ Best Practice / Idiomatic: Schema-guaranteed Date object directly formatting in template

```astro
---
// ✅ Schema guarantees post.data.pubDate is a valid native Date instance
const { post } = Astro.props;
const formattedDate = post.data.pubDate.toLocaleDateString('tr-TR', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
});
---
<time datetime={post.data.pubDate.toISOString()}>{formattedDate}</time>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/07-migration-and-core-contracts/64-zod-date-coercion-frontmatter-schema/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: ASTRO-COLLECT-07`, `RULE-ID: ASTRO-COLLECT-08`, `RULE-ID: ASTRO-COLLECT-04`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/07-migration-and-core-contracts/64-zod-date-coercion-frontmatter-schema/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "64-ZOD-DATE-COERCION-FRONTMATTER-SCHEMA-001",
    "rule_id": "RULE-ID: ASTRO-COLLECT-07 (Use Zod Date Coercion for Flexible Metadata)",
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
   Execute the turnkey publisher script using `node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting, creates the primary issue, spawns linked sub-issues (up to 20) for critical/high defects, and pushes the JSON deliverables to `origin main`:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/07-migration-and-core-contracts/64-zod-date-coercion-frontmatter-schema/issue-body.md" \
  --title "[Audit - Zod Date Coercion (z.coerce.date) & Frontmatter Schema Guard]: <Concise Defect Summary>" \
  --findings "docs/audits/results/07-migration-and-core-contracts/64-zod-date-coercion-frontmatter-schema/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Run `git grep -n "z\.date()" src/content/` to isolate all uncoerced date validators.
2. Run `git grep -n "z\.coerce\.date(" src/` and `git grep -n "dateLike" src/content/schemas/`.
3. Verify that `pnpm exec astro check` passes with zero schema type or Zod date parsing errors.
4. Document every uncoerced `z.date()` instance and its drop-in `z.coerce.date()` replacement in `handoff.md`.
5. Audit schema date contracts via terminal commands:

```bash
# 1. Search for uncoerced z.date() declarations in content schemas
git grep -n "z\.date()" src/content/

# 2. Search for modern z.coerce.date() usage across codebase
git grep -n "z\.coerce\.date(" src/

# 3. Check for custom date normalizers (e.g. dateLike)
git grep -n "dateLike" src/content/

# 4. Verify TypeScript and Astro Content Layer type-check
pnpm exec astro check
```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/07-migration-and-core-contracts/64-zod-date-coercion-frontmatter-schema/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Zod Date Coercion (z.coerce.date) & Frontmatter Schema Guard
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/07-migration-and-core-contracts/64-zod-date-coercion-frontmatter-schema/findings.json` (N defects logged)
   - `file://docs/audits/results/07-migration-and-core-contracts/64-zod-date-coercion-frontmatter-schema/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/07-migration-and-core-contracts/64-zod-date-coercion-frontmatter-schema/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/07-migration-and-core-contracts/64-zod-date-coercion-frontmatter-schema/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/07-migration-and-core-contracts/64-zod-date-coercion-frontmatter-schema/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
