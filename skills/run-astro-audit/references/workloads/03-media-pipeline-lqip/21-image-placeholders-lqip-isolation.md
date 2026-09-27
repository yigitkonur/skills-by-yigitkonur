# Mission Brief: Image Placeholders & LQIP Server-Only Isolation Audit

## 3.0 Skills / Tools: view_file, run_command, image-pipeline-runtime.

## 3.1 Context Block

All raster illustrations and covers on the Astro application provide an inline base64 WebP placeholder in `src/data/assets/image-placeholders.json` (a 13 MB dictionary).
Astro and The application design system invariants strictly enforce:

1. **Strict Server-Only Boundary**: `src/lib/assets/image-placeholders.ts` and `image-placeholders.json` are **strictly server-only**. They must NEVER be imported into React client islands, client scripts, or browser bundles. Always use the server helper `resolveIllustrationPlaceholder()` in `.astro` components for atomic resolution.
2. **Zero-JS CSS Blur-Up Contract**: Placeholders must strictly follow the Gaussian blur-up CSS contract in `src/styles/image-placeholder.css`: `filter: blur(12px)`, `transform: scale(1.08)` bleed prevention, `overflow: hidden`, and `:has(img[data-loaded="true"])` zero-JS smooth cross-fade transition without shipping React image fading runtimes.
3. **Moving Tickers vs Content Imagery**: Continuously translating logos or ticker assets (such as `AwardsModernizationPilot.astro`) must remain eager (`loading="eager"`). Only static content imagery uses `loading="lazy"` with LQIP.

### Astro Architectural & Best Practice Rules

- [01-prefer-astro-image-over-native-img.md](../../best-practices/07-assets-and-image-pipeline/01-prefer-astro-image-over-native-img.md) — Native `<Image />` optimization, automatic layout box reservation, and format conversion.
- [08-optimize-lcp-hero-images-with-priority.md](../../best-practices/07-assets-and-image-pipeline/08-optimize-lcp-hero-images-with-priority.md) — LCP priority, eager loading, and avoiding lazy loading on above-the-fold hero assets.
- [14-implement-zero-js-lqip-blur-up-placeholders.md](../../best-practices/07-assets-and-image-pipeline/14-implement-zero-js-lqip-blur-up-placeholders.md) — Zero-JS LQIP blur-up implementation using `:has(img[data-loaded="true"])` and inline base64 WebP previews without client hydration.
- [15-configure-image-services-for-edge-adapters.md](../../best-practices/07-assets-and-image-pipeline/15-configure-image-services-for-edge-adapters.md) — Edge-compatible image services (`passthroughImageService()` vs build-time Sharp) avoiding native C++ libvips crashes on Cloudflare Workers.
- [16-prevent-cumulative-layout-shift-cls.md](../../best-practices/09-performance-prefetch-and-transitions/16-prevent-cumulative-layout-shift-cls.md) — Explicit width/height and aspect ratios preventing Cumulative Layout Shift (CLS) across media containers.

Critical files to inspect:

- `src/data/assets/image-placeholders.json`
- `src/lib/assets/image-placeholders.ts`
- `src/styles/image-placeholder.css`
- `scripts/checks/astro/validate-image-placeholders.mjs`
- `src/components/molecules/Book.tsx`

## 3.2 Mission Objective

Perform an exhaustive audit of image placeholder references across the entire codebase.
Outcome: Prove 100% server-only isolation (zero imports of `image-placeholders.json` in client islands or browser bundles) and 100% placeholder coverage across all 3,897 routes.
Constraints: Read-only audit; inspect import graphs and bundle manifests.
Autonomy Grant: You own this mission end-to-end. Trace asset hashing, Sharp WebP generation, and CSS blur-up transitions. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

### ❌ Bad Practice / Anti-Pattern (Leaking 13MB Dictionary into Client Island)

```tsx
// Anti-Pattern: Injects 13MB JSON into client bundle Book.tsx!
import placeholders from '../../data/assets/image-placeholders.json'
```

### ❌ Bad Practice / Anti-Pattern (Hydrating React Island for Blur Cross-Fade)

```astro
---
// Anti-Pattern: Hydrates a 45KB React bundle solely for image fading
import ReactBlurImage from '../components/ReactBlurImage.jsx';
---
<ReactBlurImage client:visible src="/heavy-hero.jpg" placeholder="/placeholder.jpg" />
```

### ✅ Best Practice / Idiomatic (Server-Only Resolution & Zero-JS Blur-Up)

```astro
---
// Idiomatic: Resolved strictly on server; only tiny base64 string rendered to HTML
import { resolveIllustrationPlaceholder } from '~/lib/assets/image-placeholders';
const { placeholder } = resolveIllustrationPlaceholder(slug, 'light');
---
<div class="lqip-container overflow-hidden" style={`background-image: url('${placeholder}');`}>
  <img
    src={src}
    alt={alt}
    width="600"
    height="400"
    loading="lazy"
    decoding="async"
    onload="this.dataset.loaded='true'"
    class="lqip-image"
  />
</div>
```

2. Inspect `src/styles/image-placeholder.css`: verify `:has(img[data-loaded="true"])` zero-JS selector transitions and bleed prevention (`transform: scale(1.08)`).
3. Audit how localized secondary locale routes (`/ar/*`) and localized covers are mapped in asset resolution scripts.
4. Verify server-only boundary enforcement in build tooling and CI scripts.

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/03-media-pipeline-lqip/21-image-placeholders-lqip-isolation/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Best Practice Rule Mapping**: All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an authoritative Astro best practice (e.g., `RULE-ID: ASTRO-ASSETS-14` for zero-JS LQIP blur-up, `RULE-ID: ASTRO-ASSETS-01` for native Image component, or `RULE-ID: ASTRO-PERF-16` for CLS prevention).

You must create and populate the following deliverables in `docs/audits/results/03-media-pipeline-lqip/21-image-placeholders-lqip-isolation/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "21-IMAGE-PLACEHOLDERS-LQIP-ISOLATION-001",
    "rule_id": "RULE-ID: ASTRO-ASSETS-14",
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
  --body "docs/audits/results/03-media-pipeline-lqip/21-image-placeholders-lqip-isolation/issue-body.md" \
  --title "[Audit - Image Placeholders & LQIP Server-Only Isolation Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/03-media-pipeline-lqip/21-image-placeholders-lqip-isolation/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Execute canonical placeholder and isolation CLI audits:
   ```bash
   # 1. Run canonical placeholder verification across all 3,897 routes
   pnpm assets:placeholders:check

   # 2. Strict audit proving ZERO client island imports of image-placeholders.json
   git grep -n "image-placeholders.json" src/components/ | grep -E "\.(tsx|jsx|ts|js)" | grep -v "\.astro" || echo "Clean: Zero client island imports"

   # 3. Direct grep ensuring image-placeholders.json is only referenced in server-only modules
   git grep -n "image-placeholders.json" src/

   # 4. Verify dist/_astro client bundle does NOT contain image-placeholders.json content or keys
   grep -ro "image-placeholders.json" dist/_astro/ || echo "Clean: Zero placeholder leaks in client bundle"

   # 5. Verify CSS blur-up contract in src/styles/image-placeholder.css
   git grep -n -E "(scale\(1\.08\)|blur\(12px\)|data-loaded)" src/styles/

   # 6. Check for image loading attributes in static content vs ticker components
   git grep -rn 'loading="lazy"' src/pages/ src/components/
   ```
2. Verify that no file under `src/components/` with `client:*` directives imports image-placeholders.
3. Confirm that blur-up CSS prevents edge bleeding with `transform: scale(1.08)` and `overflow: hidden`.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/03-media-pipeline-lqip/21-image-placeholders-lqip-isolation/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Image Placeholders & LQIP Server-Only Isolation Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/03-media-pipeline-lqip/21-image-placeholders-lqip-isolation/findings.json` (N defects logged)
   - `file://docs/audits/results/03-media-pipeline-lqip/21-image-placeholders-lqip-isolation/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/03-media-pipeline-lqip/21-image-placeholders-lqip-isolation/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/03-media-pipeline-lqip/21-image-placeholders-lqip-isolation/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/03-media-pipeline-lqip/21-image-placeholders-lqip-isolation/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
