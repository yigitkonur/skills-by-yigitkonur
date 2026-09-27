# Mission Brief: Multilingual Commercial Parity (EN / TR / AR) Audit

## 3.0 Skills / Tools: view_file, run_command, multilingual-locale-manager.

## 3.1 Context Block

The application enforces strict commercial parity across English, localized primary locale, and localized secondary locale:

- 7 Core Services (SEO, GEO, Content Marketing, Performance, Analytics, Gen AI Consultancy, Gen AI Training)
- 62 Service Details
- 238 Customer References
- 37 Case Studies
- 34 Team Specialists
- Single Pages (About, Contact, Brand Assets, Hello Funnel)
  Repetitive historical archives (blog posts, past webinars) are intentionally excluded from localized secondary locale parity per the B2B Commercial Core blueprint.

### Authoritative Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`01-native-i18n-configuration.md`](../../best-practices/08-i18n-and-localization/01-native-i18n-configuration.md) — Declarative native i18n routing configuration in `astro.config.mjs` with compile-time locale validation (`RULE-ID: 08-i18n-and-localization/01-native-i18n-configuration`).
- [`03-type-safe-url-helpers.md`](../../best-practices/08-i18n-and-localization/03-type-safe-url-helpers.md) — Computing localized routes with `getRelativeLocaleUrl()` and `getAbsoluteLocaleUrl()` over raw string concatenation (`RULE-ID: 08-i18n-and-localization/03-type-safe-url-helpers`).
- [`07-bidirectional-rtl-ltr-handling.md`](../../best-practices/08-i18n-and-localization/07-bidirectional-rtl-ltr-handling.md) — Enforcing bidirectional (RTL/LTR) HTML root attributes and CSS logical properties (`RULE-ID: 08-i18n-and-localization/07-bidirectional-rtl-ltr-handling`).
- [`08-multilingual-seo-hreflang-and-canonical.md`](../../best-practices/08-i18n-and-localization/08-multilingual-seo-hreflang-and-canonical.md) — Full reciprocal hreflang clusters and localized canonical tags across all commercial pages (`RULE-ID: 08-i18n-and-localization/08-multilingual-seo-hreflang-and-canonical`).
- [`08-redirects-and-rewrites.md`](../../best-practices/03-routing-and-pages/08-redirects-and-rewrites.md) — Differentiating static URL migrations from transparent language fallbacks via `Astro.rewrite()` (`RULE-ID: 03-routing-and-pages/08-redirects-and-rewrites`).
- [`09-custom-404-and-500-error-routing.md`](../../best-practices/03-routing-and-pages/09-custom-404-and-500-error-routing.md) — Dedicated localized error routing and localized secondary locale 404 shells preserving commercial navigation (`RULE-ID: 03-routing-and-pages/09-custom-404-and-500-error-routing`).
- [`12-ui-translation-dictionaries-and-type-safety.md`](../../best-practices/08-i18n-and-localization/12-ui-translation-dictionaries-and-type-safety.md) — Type-safe translation dictionaries avoiding untranslated English token leaks on localized secondary locale surfaces (`RULE-ID: 08-i18n-and-localization/12-ui-translation-dictionaries-and-type-safety`).

Key Astro Best Practice contracts for bidirectional i18n & localization:

1. **Dynamic Bidirectional HTML Attributes**: Root layouts must compute `dir` dynamically (`const RTL_LOCALES = new Set(["ar", "he", "fa", "ur"]); const dir = RTL_LOCALES.has(locale) ? "rtl" : "ltr";`) and set `<html lang={locale} dir={dir}>`. Hardcoding `dir="ltr"` breaks browser layout engines and screen readers.
2. **CSS Logical Properties**: Physical coordinates (`margin-left`, `padding-right`, `left-4`, `text-left`) break symmetry in RTL. Templates must use CSS logical properties: `ms-` (`margin-inline-start`), `me-` (`margin-inline-end`), `ps-` (`padding-inline-start`), `pe-` (`padding-inline-end`), `border-s`, `border-e`, `text-start`, `text-end`, and `inset-inline-start-0`.
3. **Directional Icon Mirroring**: Directional navigational glyphs (arrows, chevrons, steps) must mirror automatically using utility classes (`rtl:rotate-180` or `rtl:scale-x-[-1]`).
4. **Localized Number & Date Formatting**: Dates and currencies must use native `Intl.DateTimeFormat` and `Intl.NumberFormat` rather than hardcoded Western month names or currency positions.
5. **Dedicated localized secondary locale 404 Shell**: `/ar/404` must render a fully localized localized secondary locale error layout, preserving commercial header navigation.
6. **Type-Safe Route Generation**: Navigation links must use `getRelativeLocaleUrl(locale, path)` from `astro:i18n` rather than string interpolation (`/${locale}/${path}`), respecting `prefixDefaultLocale` and base routing invariants.

Critical files to inspect:

- `src/lib/routes/public.ts` (`PUBLIC_ROUTE_REGISTRY`)
- `src/lib/routing/enumerate.ts`
- `src/layouts/SiteLayout.astro`
- `src/pages/ar/`
- `edge/policy/runtime-routes.mjs`
- `astro.config.mjs`

## 3.2 Mission Objective

Perform a comprehensive parity audit across English, localized primary locale, and localized secondary locale commercial surfaces.
Outcome: Ensure zero missing routes, zero 404 links on commercial surfaces, complete metadata translations, full RTL (Right-to-Left) BiDi mirroring (chevron icons, padding-inline, logical CSS), localized `Intl.DateTimeFormat` date formatting, localized currency symbols (USD, EUR, TRY, AED), and dedicated localized secondary locale 404 error page parity.
Constraints: Read-only audit; verify data sets against the B2B Commercial Core specification.
Autonomy Grant: You own this mission end-to-end. Cross-reference route registries, translation keys, and RTL CSS rules. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Check all 7 services in `PUBLIC_ROUTE_REGISTRY`: ensure en, tr, and ar paths exist and map to active route files.
2. Inspect `src/layouts/SiteLayout.astro`: verify dynamic `dir={dir}` computation based on current locale.
3. Audit `src/pages/ar/` and shared components for physical CSS classes (`ml-`, `mr-`, `pl-`, `pr-`, `left-`, `right-`, `text-left`).
4. Verify icon mirroring: ensure directional icons (arrows, chevrons) reverse direction under RTL.
5. Verify `/ar/404` parity: ensure non-existent localized secondary locale URLs render a fully translated localized secondary locale 404 shell.
6. Audit date and number formatting: ensure native `Intl.DateTimeFormat` is used for localized secondary locale publication dates.
7. Audit all internal links to ensure usage of `getRelativeLocaleUrl()` over hardcoded template strings.

### ❌ Bad Practice / Anti-Pattern (Hardcoded URL Strings & Broken Locales)

```astro
---
// ❌ Anti-Pattern: Hardcoded locale URL strings from Next.js / legacy routing
// Breaks when routing.prefixDefaultLocale changes or base path shifts
const { locale } = Astro.params;
const targetSlug = "services/seo";
---
<!-- BUG: Hardcoded template literal produces double slashes or invalid paths if prefixDefaultLocale is false -->
<a href={`/${locale}/${targetSlug}`}>SEO Services</a>
<a href={`/${locale}/services/geo/`}>GEO Strategy</a>
```

### ✅ Best Practice / Idiomatic (Type-Safe Astro i18n URL Helpers)

```astro
---
// ✅ Idiomatic Astro: Using type-safe getRelativeLocaleUrl from astro:i18n
import { getRelativeLocaleUrl } from "astro:i18n";

const currentLocale = Astro.currentLocale ?? "en";
---
<!-- Emits "/services/seo" if default locale without prefix, or "/ar/services/seo", respecting trailingSlash -->
<a href={getRelativeLocaleUrl(currentLocale, "services/seo")}>
  SEO Services
</a>
<a href={getRelativeLocaleUrl(currentLocale, "services/geo")}>
  GEO Strategy
</a>
```

### ❌ Bad Practice / Anti-Pattern (Hardcoded LTR & Directional Physical CSS)

```astro
---
// ❌ Anti-Pattern: Hardcoded ltr and directional physical CSS classes
// Breaks localized secondary locale layout symmetry, alignment, and reading flow
const locale = Astro.currentLocale ?? "en";
---
<html lang={locale} dir="ltr">
  <body class="text-left">
    <!-- BUG: pl-4, mr-6, and left-0 push elements to the wrong side in RTL -->
    <div class="mr-6 pl-4 left-0 border-l-2">
      <slot />
      <!-- Arrow points right, clashing with RTL backward navigation -->
      <span>→</span>
    </div>
  </body>
</html>
```

### ✅ Best Practice / Idiomatic (Dynamic BiDi Root & CSS Logical Properties)

```astro
---
// ✅ Idiomatic Astro: Dynamic bidirectional root attributes and CSS logical properties
const locale = Astro.currentLocale ?? "en";
const RTL_LOCALES = new Set(["ar", "he", "fa", "ur"]);
const dir = RTL_LOCALES.has(locale) ? "rtl" : "ltr";
---
<html lang={locale} dir={dir}>
  <body class="text-start">
    <!-- Uses CSS logical properties: me-6, ps-4, inset-inline-start-0, border-s-2 -->
    <div class="me-6 ps-4 inset-inline-start-0 border-s-2">
      <slot />
      <!-- Reverses navigational icon orientation only under RTL reading order -->
      <span class="inline-block rtl:rotate-180">→</span>
    </div>
  </body>
</html>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/04-content-and-seo/35-multilingual-commercial-parity-en-tr-ar/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: 08-i18n-and-localization/01-native-i18n-configuration`, `RULE-ID: 08-i18n-and-localization/03-type-safe-url-helpers`, `RULE-ID: 08-i18n-and-localization/07-bidirectional-rtl-ltr-handling`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/04-content-and-seo/35-multilingual-commercial-parity-en-tr-ar/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "35-TRILINGUAL-COMMERCIAL-PARITY-EN-TR-AR-001",
    "rule_id": "RULE-ID: 08-i18n-and-localization/07-bidirectional-rtl-ltr-handling",
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
  --body "docs/audits/results/04-content-and-seo/35-multilingual-commercial-parity-en-tr-ar/issue-body.md" \
  --title "[Audit - Multilingual Commercial Parity (EN / TR / AR) Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/04-content-and-seo/35-multilingual-commercial-parity-en-tr-ar/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Audit codebase for type-safe Astro i18n URL helper usage:
   ```bash
   git grep -n "getRelativeLocaleUrl" src/
   ```
2. Audit templates for hardcoded physical CSS coordinates and directional classes:
   ```bash
   git grep -nE '(text-left|text-right|\bml-[0-9]|\bmr-[0-9]|\bpl-[0-9]|\bpr-[0-9]|\bleft-[0-9]|\bright-[0-9])' src/pages/ar/ src/components/
   ```
3. Audit for CSS logical property adoption (`ps-`, `pe-`, `ms-`, `me-`, `text-start`, `text-end`, `inset-inline`):
   ```bash
   git grep -nE '(\bps-[0-9]|\bpe-[0-9]|\bms-[0-9]|\bme-[0-9]|text-start|text-end|inset-inline-start)' src/components/
   ```
4. Verify dynamic bidirectional attributes in root layout:
   ```bash
   git grep -n 'dir=' src/layouts/
   ```
5. Verify that `enumerateAllPages()` lists identical commercial service counts across all 3 locales:
   ```bash
   pnpm vitest run tests/int/routes-parity.test.ts
   ```
6. Confirm zero visual clipping or horizontal scrollbars in localized secondary locale RTL layouts across desktop and mobile.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/04-content-and-seo/35-multilingual-commercial-parity-en-tr-ar/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Multilingual Commercial Parity (EN / TR / AR) Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/04-content-and-seo/35-multilingual-commercial-parity-en-tr-ar/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/04-content-and-seo/35-multilingual-commercial-parity-en-tr-ar/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/04-content-and-seo/35-multilingual-commercial-parity-en-tr-ar/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/04-content-and-seo/35-multilingual-commercial-parity-en-tr-ar/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/04-content-and-seo/35-multilingual-commercial-parity-en-tr-ar/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
