# Mission Brief: Moving Tickers vs Static Lazy Images Audit

## 3.0 Skills / Tools: view_file, run_command, astro-component-architect.

## 3.1 Context Block

In The project's performance policy and Astro best practice contracts:

1. **Continuous Motion Tracks Must Remain Eager**: Continuously translating logos or ticker assets (such as `AwardsModernizationPilot.astro`, `ProofRail.astro`, `MarqueeRail.tsx`, and `ClientReferenceRail.astro`) must remain EAGER (`loading="eager"`). In Astro applications, applying `loading="lazy"` to elements inside CSS transform tracks causes jarring visual pop-in, dropped animation frames, and GPU pipeline stalls as the browser asynchronously decodes images mid-motion.
2. **Above-the-Fold LCP Priority**: When marquee rails or hero logo tickers reside above the fold, images must be designated with high network priority (`loading="eager"` with `decoding="async"`, or `fetchpriority="high"`) to eliminate LCP paint delays.
3. **Static Content Imagery & LQIP Blur-Up**: Static content imagery (article headers, case study covers, team portraits, long-form editorial) must strictly use `loading="lazy"` paired with inline base64 WebP placeholders from `src/data/assets/image-placeholders.json` following the Gaussian blur-up contract (`filter: blur(12px)`, `transform: scale(1.08)` bleed prevention, `:has(img[data-loaded="true"])` smooth cross-fade).
4. **Strict Intrinsic Dimensions to Eradicate CLS**: Every image element—whether in a moving track or static container—must declare explicit `width` and `height` attributes or responsive aspect-ratio tokens (`aspect-[3/1]`, `aspect-video`) to reserve exact layout boxes before assets arrive.

### Astro Architectural & Best Practice Rules

- [01-prefer-astro-image-over-native-img.md](../../best-practices/07-assets-and-image-pipeline/01-prefer-astro-image-over-native-img.md) — Native `<Image />` component optimization, automatic layout box reservation, and format conversion.
- [08-optimize-lcp-hero-images-with-priority.md](../../best-practices/07-assets-and-image-pipeline/08-optimize-lcp-hero-images-with-priority.md) — Above-the-fold LCP optimization, ensuring marquee tickers and hero assets in the initial viewport use `loading="eager"` and `fetchpriority="high"`, never lazy loading.
- [14-implement-zero-js-lqip-blur-up-placeholders.md](../../best-practices/07-assets-and-image-pipeline/14-implement-zero-js-lqip-blur-up-placeholders.md) — Zero-JS LQIP blur-up placeholders for below-the-fold static content, preventing layout pop-in without client runtime scripts.
- [15-configure-image-services-for-edge-adapters.md](../../best-practices/07-assets-and-image-pipeline/15-configure-image-services-for-edge-adapters.md) — Edge-compatible image pipeline ensuring ticker and content images render consistently across serverless and SSG targets.
- [16-prevent-cumulative-layout-shift-cls.md](../../best-practices/09-performance-prefetch-and-transitions/16-prevent-cumulative-layout-shift-cls.md) — Strict width/height and container aspect ratios (`aspect-[3/1]`) to eradicate Cumulative Layout Shift (CLS) on dynamic tickers and static grids.

Critical files to inspect:

- `src/components/common/MarqueeRail.tsx`:211, 224
- `src/features/homepage/components/AwardsModernizationPilot.astro`
- `src/features/homepage/components/ProofRail.astro`
- `src/components/sections/service-shared/ClientReferenceRail.astro`
- `src/data/assets/image-placeholders.json`
- `src/styles/image-placeholder.css`

## 3.2 Mission Objective

Audit loading attributes, decoding directives, and dimension reservations across all images in continuous motion tracks versus static content.
Outcome: Prove that 100% of moving marquee images use `loading="eager"`, and 100% of static content images use `loading="lazy"` with valid width/height dimensions and LQIP placeholders.
Constraints: Read-only audit; inspect rendered DOM attributes and component templates.
Autonomy Grant: You own this mission end-to-end. Analyze animation smoothness, image loading states, and CLS metrics. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `MarqueeRail.tsx`: ensure both desktop and mobile tracks explicitly specify `loading="eager"` and `decoding="async"`.
2. Inspect `AwardsModernizationPilot.astro` and `ProofRail.astro`: verify logos do not inherit default `loading="lazy"` from shared components.
3. Inspect `ArticleDetailRoute` and `CaseStudyDetailRoute`: verify editorial content imagery uses `loading="lazy"` with LQIP blur-up placeholders.
4. Check for missing intrinsic dimensions (`width`, `height`) that could cause Cumulative Layout Shift during page load or scrolling.

### ❌ Bad Practice / Anti-Pattern (Lazy Loading in Motion Tracks & Missing Dimensions)

```astro
<!-- ❌ Anti-Pattern: Lazy loading inside continuous marquee causes mid-motion pop-in and GPU stalls; missing dimensions triggers CLS -->
<div class="marquee-track flex animate-marquee">
  {logos.map((logo) => (
    <img
      src={logo.src}
      alt={logo.name}
      loading="lazy"
      class="h-12 w-auto"
    />
  ))}
</div>
```

### ✅ Best Practice / Idiomatic (Eager Motion Assets + Sized Container & Lazy Static Content)

```astro
<!-- ✅ Idiomatic: Eager loading with async decoding and explicit aspect ratio prevents animation stalls and CLS -->
<div class="marquee-track flex animate-marquee">
  {logos.map((logo) => (
    <div class="flex-shrink-0 w-36 h-12 flex items-center justify-center aspect-[3/1]">
      <img
        src={logo.src}
        alt={logo.name}
        width="144"
        height="48"
        loading="eager"
        decoding="async"
        class="max-h-full max-w-full object-contain"
      />
    </div>
  ))}
</div>

<!-- ✅ Static Content: Below-fold editorial imagery uses lazy loading with inline LQIP blur-up -->
<div
  class="lqip-container overflow-hidden aspect-video relative"
  style={`background-image: url('${placeholder}');`}
>
  <img
    src={article.coverUrl}
    alt={article.title}
    width="1200"
    height="675"
    loading="lazy"
    decoding="async"
    onload="this.dataset.loaded='true'"
    class="lqip-image w-full h-full object-cover"
  />
</div>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/03-media-pipeline-lqip/22-moving-tickers-vs-static-lazy-images/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Best Practice Rule Mapping**: All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an authoritative Astro best practice (e.g., `RULE-ID: ASTRO-ASSETS-08` for above-fold LCP priority, `RULE-ID: ASTRO-PERF-16` for CLS prevention, or `RULE-ID: ASTRO-ASSETS-14` for static content LQIP blur-up).

You must create and populate the following deliverables in `docs/audits/results/03-media-pipeline-lqip/22-moving-tickers-vs-static-lazy-images/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "22-MOVING-TICKERS-VS-STATIC-LAZY-IMAGES-001",
    "rule_id": "RULE-ID: ASTRO-ASSETS-08",
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
  --body "docs/audits/results/03-media-pipeline-lqip/22-moving-tickers-vs-static-lazy-images/issue-body.md" \
  --title "[Audit - Moving Tickers vs Static Lazy Images Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/03-media-pipeline-lqip/22-moving-tickers-vs-static-lazy-images/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Audit marquee and ticker components to prove zero instances of `loading="lazy"` in motion paths:
   ```bash
   # Scan all marquee, rail, and ticker components for rogue lazy-loading
   git grep -rn 'loading="lazy"' src/components/common/MarqueeRail* src/features/homepage/components/*Rail* src/components/sections/service-shared/*Rail* || echo "Pass: Zero lazy-loading in tickers"

   # Verify explicit eager loading on moving logo elements
   git grep -rn 'loading="eager"' src/components/common/MarqueeRail* src/features/homepage/components/AwardsModernizationPilot.astro

   # Verify async decoding directive across moving tracks
   git grep -rn 'decoding="async"' src/components/common/MarqueeRail* src/features/homepage/components/*Rail*
   ```
2. Audit static content images for proper dimension reservation and LQIP placeholder coverage:
   ```bash
   # Verify 100% placeholder coverage across static raster assets
   pnpm assets:placeholders:check

   # Flag raw <img> tags in content routes lacking explicit width or height attributes
   git grep -n '<img' src/pages/ src/components/ | grep -v -E '(width=|aspect-)' || echo "Pass: All images dimensioned"

   # Audit image-placeholders.json isolation from client islands
   git grep -n "image-placeholders.json" src/
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/03-media-pipeline-lqip/22-moving-tickers-vs-static-lazy-images/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Moving Tickers vs Static Lazy Images Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/03-media-pipeline-lqip/22-moving-tickers-vs-static-lazy-images/findings.json` (N defects logged)
   - `file://docs/audits/results/03-media-pipeline-lqip/22-moving-tickers-vs-static-lazy-images/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/03-media-pipeline-lqip/22-moving-tickers-vs-static-lazy-images/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/03-media-pipeline-lqip/22-moving-tickers-vs-static-lazy-images/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/03-media-pipeline-lqip/22-moving-tickers-vs-static-lazy-images/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
