# Mission Brief: Reference Logos Dark/Light Silhouette & Hover Jump Audit

## 3.0 Skills / Tools: view_file, run_command, brand-logo-normalizer.

## 3.1 Context Block

The application showcases 238 customer reference logos representing market leaders across 24 industry sectors.
Non-negotiable visual standards and Astro asset architecture:

1. **The Canonical Trio**: Every reference brand must maintain three authentic variants: Original Master, Light Rest Black (`#1E2038`), and Dark Rest White (`#FFFFFF`).
2. **Native Alpha Transparency**: 4 corners must be 100% alpha transparent (`alpha <= 10`). No dirty matte artifacts, white halos, or opaque bounding fills.
3. **Zero Hover Jump & Mathematical Parity**: Logos must maintain identical bounding boxes and normalized `viewBox` coordinates between Light and Dark variants. Hover states must strictly animate GPU transforms (`scale-105`), never manipulating margin, padding, or width/height which triggers browser reflow and layout jumps.
4. **Container Aspect-Ratio Reservation**: In accordance with Astro CLS prevention rules, all logo containers must enforce fixed aspect ratios (e.g. `aspect-[3/1]` with `object-contain`) or explicit width/height to eliminate Cumulative Layout Shift as SVGs or remote WebP assets render.

### Astro Architectural & Best Practice Rules

- [01-prefer-astro-image-over-native-img.md](../../best-practices/07-assets-and-image-pipeline/01-prefer-astro-image-over-native-img.md) — Native `<Image />` optimization, automatic layout box reservation, and format conversion for reference assets.
- [08-optimize-lcp-hero-images-with-priority.md](../../best-practices/07-assets-and-image-pipeline/08-optimize-lcp-hero-images-with-priority.md) — Eager loading and high fetch priority for above-the-fold customer reference rails.
- [14-implement-zero-js-lqip-blur-up-placeholders.md](../../best-practices/07-assets-and-image-pipeline/14-implement-zero-js-lqip-blur-up-placeholders.md) — Zero-JS asset handling avoiding bloated client scripts for logo rendering.
- [15-configure-image-services-for-edge-adapters.md](../../best-practices/07-assets-and-image-pipeline/15-configure-image-services-for-edge-adapters.md) — Edge-compatible asset pipeline for serving remote or CDN-hosted SVG and WebP customer logos across Cloudflare Workers.
- [16-prevent-cumulative-layout-shift-cls.md](../../best-practices/09-performance-prefetch-and-transitions/16-prevent-cumulative-layout-shift-cls.md) — Strict width/height attributes and container aspect-ratio reservation (`aspect-[3/1]`) to eradicate CLS on logo grids and prevent reflow jumps on hover or theme toggling.

Critical files to inspect:

- `public/assets/references/` or R2 reference logos
- `src/data/references/`
- `src/features/proof/data/references-taxonomy.ts`
- `src/components/common/MarqueeRail.tsx`
- `.claude/skills/brand-logo-normalizer/`

## 3.2 Mission Objective

Perform a mathematical and visual audit of all 238 customer reference logos across both themes and animation tracks.
Outcome: Prove 100% alpha transparency, zero contour drift, perfect Light/Dark silhouette matching, and 0-pixel shift on hover and theme toggling.
Constraints: Read-only audit; inspect logo manifest metadata, SVG viewBox attributes, and rendered dimensions.
Autonomy Grant: You own this mission end-to-end. Measure bounding boxes, check transparency pixels, and verify aspect ratios. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Check reference logo manifest for complete Light and Dark variants across all 238 cataloged brands.
2. Verify that logo containers enforce fixed aspect ratios (e.g. `aspect-[3/1]` or fixed height with `object-contain`).
3. Audit SVG viewBox coordinates between paired light and dark silhouettes to ensure matching aspect ratios and alignment.
4. Test hover state transitions in `MarqueeRail.tsx` and static reference grids: ensure scale or opacity transitions do not alter layout flow.

### ❌ Bad Practice / Anti-Pattern (Hardcoding Duplicate DOM Elements & Layout-Thrashing Hover)

```astro
<!-- ❌ Anti-Pattern: Hardcoded duplicate DOM elements; padding on hover causes reflow and shifts neighboring logos; missing container aspect ratio triggers CLS -->
<div class="logo-box hover:p-2 transition-all">
  <img
    src={logo.lightUrl}
    alt={logo.name}
    class="h-8 w-auto dark:hidden"
  />
  <img
    src={logo.darkUrl}
    alt={logo.name}
    class="h-8 w-auto hidden dark:block"
  />
</div>
```

### ✅ Best Practice / Idiomatic (CSS Filter Silhouette Inversion or Normalized Aspect Ratio & GPU Transform)

```astro
<!-- ✅ Idiomatic Pattern A: Single SVG/WebP with CSS filter silhouette inversion (Zero duplicate DOM elements) -->
<div class="relative w-36 h-12 flex items-center justify-center aspect-[3/1] overflow-hidden">
  <img
    src={logo.src}
    alt={`${logo.name} logo`}
    width="144"
    height="48"
    loading="eager"
    decoding="async"
    class="max-h-full max-w-full object-contain transition-transform duration-200 ease-out hover:scale-105 dark:invert dark:brightness-200"
  />
</div>

<!-- ✅ Idiomatic Pattern B: Dedicated dual-silhouette pairing with identical viewBox and GPU transform hover -->
<div class="relative w-36 h-12 flex items-center justify-center aspect-[3/1] overflow-hidden">
  <img
    src={logo.lightUrl}
    alt={`${logo.name} logo`}
    width="144"
    height="48"
    loading="eager"
    decoding="async"
    class="max-h-full max-w-full object-contain transition-transform duration-200 ease-out hover:scale-105 dark:hidden"
  />
  <img
    src={logo.darkUrl}
    alt={`${logo.name} logo`}
    width="144"
    height="48"
    loading="eager"
    decoding="async"
    class="max-h-full max-w-full object-contain transition-transform duration-200 ease-out hover:scale-105 hidden dark:block"
  />
</div>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/03-media-pipeline-lqip/23-reference-logos-dark-light-silhouette/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Best Practice Rule Mapping**: All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an authoritative Astro best practice (e.g., `RULE-ID: ASTRO-PERF-16` for CLS prevention, `RULE-ID: ASTRO-ASSETS-01` for native image sizing, or `RULE-ID: ASTRO-ASSETS-15` for edge asset delivery).

You must create and populate the following deliverables in `docs/audits/results/03-media-pipeline-lqip/23-reference-logos-dark-light-silhouette/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "23-REFERENCE-LOGOS-DARK-LIGHT-SILHOUETTE-001",
    "rule_id": "RULE-ID: ASTRO-PERF-16",
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
   Execute the turnkey publisher script (`node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push`) which automatically verifies the 60,000-char limit, checklist nesting, creates the primary issue, spawns linked sub-issues (up to 20) for critical/high defects, and pushes the JSON deliverables to `origin main`:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/03-media-pipeline-lqip/23-reference-logos-dark-light-silhouette/issue-body.md" \
  --title "[Audit - Reference Logos Dark/Light Silhouette & Hover Jump Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/03-media-pipeline-lqip/23-reference-logos-dark-light-silhouette/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Audit reference taxonomy mapping to confirm all 238 entries have valid definitions:
   ```bash
   # Verify taxonomy count and integrity of customer reference catalog
   pnpm tsx -e "import { referenceTaxonomy } from './src/features/proof/data/references-taxonomy.ts'; const count = Object.keys(referenceTaxonomy).length; console.log('Total references:', count); if (count < 238) process.exit(1);"
   ```
2. Audit logo pair completeness across light and dark variants:
   ```bash
   # Scan reference data directory for unpaired light or dark assets
   pnpm tsx scripts/assets/media/sync-all-references-to-macbook.mjs --dry-run || echo "Reference audit completed"

   # Detect any hover styles modifying layout box properties instead of transform/opacity
   git grep -rn 'hover:p-' src/components/ src/features/proof/ || echo "Pass: Zero hover padding shifts"
   git grep -rn 'hover:m-' src/components/ src/features/proof/ || echo "Pass: Zero hover margin shifts"

   # Verify container aspect-ratio reservation across reference displays
   git grep -n '<img' src/components/common/MarqueeRail.tsx src/features/proof/ | grep -v -E '(width=|aspect-)' || echo "Pass: All reference logos dimensioned"

   # Confirm image-placeholders.json isolation
   git grep -n "image-placeholders.json" src/
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/03-media-pipeline-lqip/23-reference-logos-dark-light-silhouette/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Reference Logos Dark/Light Silhouette & Hover Jump Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/03-media-pipeline-lqip/23-reference-logos-dark-light-silhouette/findings.json` (N defects logged)
   - `file://docs/audits/results/03-media-pipeline-lqip/23-reference-logos-dark-light-silhouette/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/03-media-pipeline-lqip/23-reference-logos-dark-light-silhouette/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/03-media-pipeline-lqip/23-reference-logos-dark-light-silhouette/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/03-media-pipeline-lqip/23-reference-logos-dark-light-silhouette/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
