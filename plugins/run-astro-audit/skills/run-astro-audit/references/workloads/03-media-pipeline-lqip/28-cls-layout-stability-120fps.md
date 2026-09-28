# Mission Brief: CLS Layout Stability & 120 FPS Compositor Audit

## 3.0 Skills / Tools: view_file, run_command, audit-ui-and-save-files.

## 3.1 Context Block

Cumulative Layout Shift (CLS) must remain strictly under 0.05 across all 73 page archetypes.
Astro rendering performance and layout stability invariants:

1. **Zero-Jank GPU Compositor (120 FPS)**: Continuous animations (marquees, sliders, transitions) must strictly animate composite-only properties (`transform: translate3d(...)`, `opacity`) with `will-change: transform`. Animating layout or paint properties (`top`, `left`, `width`, `height`, `margin`, `padding`) forces continuous main-thread CPU recalculations, dropping frames below 60/120 FPS.
2. **Explicit Aspect-Ratio & Dimension Reservation**: In accordance with Astro CLS prevention rules, all hero illustrations, figures, embedded media, and React island wrappers must declare explicit aspect-ratio tokens (`aspect-[16/9]`, `aspect-square`, `aspect-[3/1]`) or min-height skeletons before assets or scripts arrive.
3. **Head Resource Balance & DNS Hygiene**: `<head>` preconnect hints must strictly target critical domains (R2 CDN, GTM). Speculative preconnects to non-critical third parties saturate browser connection pools.
4. **Save-Data & Reduced-Motion Respect**: Continuous CSS tickers must observe `@media (prefers-reduced-motion)` and connection constraints (`navigator.connection?.saveData`), pausing infinite animations on low-power or bandwidth-metered mobile devices.

Astro Architectural & Best Practice Rules:

- **Prevent Cumulative Layout Shift (CLS) Across Media and Islands ([16-prevent-cumulative-layout-shift-cls.md](../../best-practices/09-performance-prefetch-and-transitions/16-prevent-cumulative-layout-shift-cls.md))**: Every media element, hero illustration, video embed, and dynamic client island container must declare reserved dimensions or CSS `aspect-ratio` tokens (`aspect-[16/9]`, `aspect-square`, `aspect-[3/1]`) or `contain-intrinsic-size` skeletons to prevent layout shifts (CLS < 0.05) when content or assets stream into the DOM.
- **Optimize Largest Contentful Paint (LCP) with Static Heroes ([14-optimize-largest-contentful-paint-lcp.md](../../best-practices/09-performance-prefetch-and-transitions/14-optimize-largest-contentful-paint-lcp.md))**: Above-the-fold hero banners must render as pure zero-JS static Astro markup with `fetchpriority="high"` and `loading="eager"`. Wrapping heroes in client-hydrated islands introduces hydration delay and layout instability.
- **Eradicate Font CLS with size-adjust and Metric Overrides ([10-eliminate-font-cls-with-metric-overrides.md](../../best-practices/07-assets-and-image-pipeline/10-eliminate-font-cls-with-metric-overrides.md))**: Fallback system fonts must use calibrated `@font-face` metric overrides (`size-adjust`, `ascent-override`, `descent-override`) matching custom Swiss typography (Gilroy, Akagi) to eliminate layout jumps when web fonts swap.
- **Self-Host Web Fonts and Preload Critical Above-the-Fold WOFF2 ([09-self-host-and-preload-critical-web-fonts.md](../../best-practices/07-assets-and-image-pipeline/09-self-host-and-preload-critical-web-fonts.md))**: Preload strictly the single critical body font weight in `<head>` to avoid font loading waterfalls that cause layout reflows.

Critical files to inspect:

- `src/styles/globals.css`
- `src/components/sections/`
- `src/features/homepage/`
- `src/layouts/SiteLayout.astro`
- `droid-wiki/performance/`

## 3.2 Mission Objective

Perform an exhaustive audit of layout stability, CSS animation compositor efficiency, and Core Web Vitals across desktop and mobile viewports.
Outcome: Prove zero layout thrashing (CLS < 0.05 sitewide), verify that all images and media containers have reserved aspect ratios, confirm animations run at 120 FPS on high-refresh displays, audit preconnect/dns-prefetch balance in `<head>`, and ensure Save-Data mode pauses continuous tickers on slow mobile connections.
Constraints: Read-only audit; check CSS properties, animation keyframes, and element dimensions.
Autonomy Grant: You own this mission end-to-end. Inspect CSS rules, layout containment, and animation triggers. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Search for CSS rules animating `margin`, `padding`, `width`, `height`, `top`, `left`, `bottom`, or `right` in keyframe definitions.
2. Verify that all `<img>` elements and video wrappers have corresponding width and height or aspect-ratio styling.
3. Check font loading and ensure metric-override `@font-face` fallbacks prevent layout shifts during font swap.
4. Check `<head>` preconnect: ensure only critical origins (R2 CDN, GTM) are preconnected to avoid DNS queue saturation.
5. Inspect Save-Data and reduced-motion handling: verify whether continuous CSS marquee animations can pause when `saveData` or `prefers-reduced-motion` is active.

### ❌ Bad Practice / Anti-Pattern (Layout Property Animation Forcing Reflow)

```css
/* ❌ Anti-Pattern: Animating margin-left forces continuous CPU reflow; drops frames below 60fps */
@keyframes marquee-scroll {
  0% {
    margin-left: 0;
  }
  100% {
    margin-left: -100%;
  }
}
.marquee-track {
  animation: marquee-scroll 20s linear infinite;
}
```

### ✅ Best Practice / Idiomatic (Hardware-Accelerated Transform & 120 FPS Compositor)

```css
/* ✅ Idiomatic: GPU-composited 3D transform with will-change; 120 FPS smooth playback */
@keyframes marquee-scroll {
  0% {
    transform: translate3d(0, 0, 0);
  }
  100% {
    transform: translate3d(-50%, 0, 0);
  }
}
.marquee-track {
  display: flex;
  width: max-content;
  will-change: transform;
  animation: marquee-scroll 35s linear infinite;
}
@media (prefers-reduced-motion: reduce) {
  .marquee-track {
    animation-play-state: paused;
  }
}
```

### ❌ Bad Practice / Anti-Pattern (Elements Expanding Dynamically Without Reserved Aspect-Ratio)

```astro
---
// ❌ Anti-Pattern: Unreserved island container and unconstrained image cause massive CLS (>0.1)
import FeedIsland from '@/components/FeedIsland.tsx';
---
<div class="feed-container">
  <!-- Missing width/height causes layout push when image loads -->
  <img src="/banner.webp" alt="Promo banner" />

  <!-- Zero reserved height: Expands dynamically by 400px when island mounts, shifting content down -->
  <FeedIsland client:visible />
</div>
```

### ✅ Best Practice / Idiomatic (Reserving Container Dimensions via CSS aspect-ratio & contain-intrinsic-size)

```astro
---
// ✅ Idiomatic: Reserved aspect-ratio container and skeleton wrapper guarantee 0 CLS
import FeedIsland from '@/components/FeedIsland.tsx';
---
<div class="feed-container">
  <!-- Explicit dimensions allow browser to calculate aspect ratio instantly -->
  <img
    src="/banner.webp"
    alt="Promo banner"
    width="1200"
    height="400"
    class="w-full h-auto aspect-[3/1] rounded-[4px]"
  />

  <!-- Reserved min-height skeleton wrapper prevents island mounting shift -->
  <div class="min-h-[400px] w-full contain-intrinsic-size-[auto_400px]">
    <FeedIsland client:visible />
  </div>
</div>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/03-media-pipeline-lqip/28-cls-layout-stability-120fps/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Rule ID Mapping**: All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an authoritative Astro best practice rule (e.g. `ASTRO-BP-09-16`, `ASTRO-BP-09-14`, `ASTRO-BP-07-10`, `ASTRO-BP-07-09`).

You must create and populate the following deliverables in `docs/audits/results/03-media-pipeline-lqip/28-cls-layout-stability-120fps/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "28-CLS-LAYOUT-STABILITY-120FPS-001",
    "rule_id": "RULE-ID (e.g. ASTRO-BP-09-16 / ASTRO-BP-09-14 / ASTRO-BP-07-10 / ASTRO-BP-07-09)",
    "file": "path/to/file.ext",
    "line": 42,
    "severity": "critical" | "high" | "medium" | "low",
    "category": "syntax" | "hydration" | "parity" | "performance" | "security",
    "defect": "Precise description of what is broken or violating invariants (must reference RULE-ID)",
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
   Execute the turnkey publisher script using `node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting, creates the primary issue, spawns linked sub-issues (up to 20) for critical and high severity defects, and pushes the JSON deliverables directly to `origin main` without PR:

```bash
# Turnkey Script (node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/03-media-pipeline-lqip/28-cls-layout-stability-120fps/issue-body.md" \
  --title "[Audit - CLS Layout Stability & 120 FPS Compositor Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/03-media-pipeline-lqip/28-cls-layout-stability-120fps/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Audit CSS keyframes for non-composited property animations:
   ```bash
   # Detect any @keyframes animating layout properties (margin, padding, width, height, top, left)
   git grep -rnE '(left|top|bottom|right|margin|padding|width|height):' src/styles/ | grep -iE 'keyframes|animate' || echo "Pass: Zero layout property animations"
   # Verify will-change: transform is set on moving rails
   git grep -rn "will-change: transform" src/
   ```
2. Verify that CLS scores remain under 0.05 across key page archetypes:
   ```bash
   # Inspect images lacking width, height, or aspect-ratio tokens
   git grep -n '<img' src/features/ src/components/ | grep -v -E 'width=|aspect-|contain-intrinsic-size' || echo "Pass: All components dimensioned"
   # Verify preconnect domains in SiteLayout.astro
   grep -rn 'rel="preconnect"' src/layouts/SiteLayout.astro
   ```
3. Audit layout script and preloading directives:
   ```bash
   # Confirm single critical font preload in SiteLayout
   git grep -n "preload" src/layouts/
   # Confirm synchronous inline execution in head
   git grep -n "is:inline" src/layouts/
   ```
4. Run automated layout stability test suite:
   ```bash
   pnpm vitest run tests/perf/cls.test.ts || npx playwright test tests/e2e/layout-stability.spec.ts
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/03-media-pipeline-lqip/28-cls-layout-stability-120fps/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** CLS Layout Stability & 120 FPS Compositor Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/03-media-pipeline-lqip/28-cls-layout-stability-120fps/findings.json` (N defects logged)
   - `file://docs/audits/results/03-media-pipeline-lqip/28-cls-layout-stability-120fps/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/03-media-pipeline-lqip/28-cls-layout-stability-120fps/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/03-media-pipeline-lqip/28-cls-layout-stability-120fps/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/03-media-pipeline-lqip/28-cls-layout-stability-120fps/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
