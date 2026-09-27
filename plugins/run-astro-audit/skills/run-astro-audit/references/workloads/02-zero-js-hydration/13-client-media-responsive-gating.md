# Mission Brief: client:media Responsive Island Gating Audit

## 3.0 Skills / Tools: view_file, run_command, react-doctor.

## 3.1 Context Block

Astro provides the `client:media="(media query)"` directive, ensuring that an island is only downloaded and hydrated when the user's viewport matches the media query.
Currently, `MegaMenu.astro`:186 and `RailPanel.astro`:182 use `client:media="(min-width: 992px)"` for desktop navigation faces.
However, other desktop-only features (such as large matrix toolbars or desktop hover cards) may be needlessly downloading JavaScript on mobile viewports.

### Astro Architectural & Best Practice Rules

Every finding, responsive budget calculation, and recommended gating directive in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`01-prefer-static-leaf-islands-over-mega-islands.md`](../../best-practices/02-islands-and-hydration/01-prefer-static-leaf-islands-over-mega-islands.md) — Keeping islands small, pushing static layout up to `.astro`, and eliminating mega-islands (`RULE-ID: ASTRO-HYDRATION-01`).
- [`02-never-default-blindly-to-client-load.md`](../../best-practices/02-islands-and-hydration/02-never-default-blindly-to-client-load.md) — Eradicating `client:load` for below-the-fold content and non-critical widgets (`RULE-ID: ASTRO-HYDRATION-02`).
- [`03-use-client-visible-with-root-margin-for-below-fold.md`](../../best-practices/02-islands-and-hydration/03-use-client-visible-with-root-margin-for-below-fold.md) — Deferred hydration using `client:visible={{ rootMargin: '200px' }}` (`RULE-ID: ASTRO-HYDRATION-03`).
- [`04-use-client-media-for-responsive-interactive-elements.md`](../../best-practices/02-islands-and-hydration/04-use-client-media-for-responsive-interactive-elements.md) — Responsive hydration gating via `client:media="(max-width: 1024px)"` (`RULE-ID: ASTRO-HYDRATION-04`).
- [`05-use-client-only-for-browser-dependent-widgets.md`](../../best-practices/02-islands-and-hydration/05-use-client-only-for-browser-dependent-widgets.md) — Bypassing server SSR errors with `client:only="react"` and fallback slots (`RULE-ID: ASTRO-HYDRATION-05`).

- Architecture Rule: Pre-Request Media Gating vs CSS Hiding. In standard React and Next.js, conditional rendering based on screen size (e.g. `useMediaQuery` or CSS `hidden lg:block`) still bundles the component code into the client JavaScript payload. Astro's `client:media="(media query)"` evaluates `window.matchMedia()` at the `<astro-island>` boundary _before_ making any network request for the component script chunk. If the viewport does not match, ZERO bytes of JavaScript are downloaded or executed.
- Responsive Navigation Symmetry: Desktop mega-menus (`MegaMenu.astro`, `RailPanel.astro`) and mobile navigation drawers must use symmetric media queries. Desktop components should be gated with `client:media="(min-width: 1024px)"`, while mobile drawers should be gated with `client:media="(max-width: 1023px)"`.
- Design System Token Alignment: Media queries in `client:media` directives must strictly synchronize with Tailwind v4 breakpoints (`md: 768px`, `lg: 1024px`, `xl: 1280px`). Inconsistent breakpoint values (e.g. `992px` vs `1024px`) risk hydration dead-zones where neither mobile nor desktop islands hydrate.

Critical files to inspect:

- `src/components/chrome/MegaMenu.astro`
- `src/components/chrome/megamenu/RailPanel.astro`
- `src/features/tools/components/MarketingToolsRoute.astro`:177
- `src/components/chrome/SiteHeader.astro`
- `src/styles/tokens.css`

## 3.2 Mission Objective

Examine the entire UI for desktop-exclusive and mobile-exclusive components.
Outcome: Identify heavy desktop islands that currently download on mobile devices, and prescribe `client:media` gating to achieve zero-JS delivery on handheld screens while ensuring strict alignment with Tailwind v4 breakpoints.
Constraints: Read-only audit; verify that responsive CSS breakpoints match Tailwind v4 design tokens.
Autonomy Grant: You own this mission end-to-end. Analyze responsive breakpoints, media queries, and device budgets. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Check all navigation, drawer, and table islands across desktop and mobile.
2. Verify that mobile devices (393px width) do not download desktop mega-menu bundles.
3. Validate breakpoint parity: ensure `(min-width: 992px)` or `(min-width: 1024px)` aligns with Tailwind v4 screens.
4. Audit mobile-only widgets (e.g. mobile bottom sheets, touch swipers) to ensure they do not hydrate on desktop screens.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Desktop-Only Mega-Menus Leaking to Mobile (RULE-ID: ASTRO-HYDRATION-04)

##### ❌ Bad Practice / Anti-Pattern: Desktop-only mega-menus shipping 50KB mobile JS without media gating

```astro
---
// src/components/chrome/SiteHeader.astro - CSS hiding without media gating
import MegaMenu from "./MegaMenu.tsx";
import MobileDrawer from "./MobileDrawer.tsx";
---
<header>
  <!-- Anti-Pattern: Downloaded and hydrated on mobile even though CSS hides it! -->
  <div class="hidden lg:block">
    <MegaMenu client:load />
  </div>
  <!-- Anti-Pattern: Downloaded and hydrated on desktop even though CSS hides it! -->
  <div class="block lg:hidden">
    <MobileDrawer client:load />
  </div>
</header>
```

_Why this fails:_ CSS utility classes (`hidden`, `block`) only affect element visibility in the rendered layout. Astro still compiles `<astro-island>` scripts for both components, forcing mobile users to download 70+ KB of desktop mega-menu JS and desktop users to download mobile drawer code.

##### ✅ Best Practice / Idiomatic: `<MobileDrawer client:media="(max-width: 1024px)" />` and `<MegaMenu client:media="(min-width: 1024px)" />`

```astro
---
// src/components/chrome/SiteHeader.astro - Pre-request client:media gating
import MegaMenu from "./MegaMenu.tsx";
import MobileDrawer from "./MobileDrawer.tsx";
---
<header>
  <!-- Zero JS requested on mobile viewports (< 1024px) -->
  <div class="hidden lg:block">
    <MegaMenu client:media="(min-width: 1024px)" />
  </div>
  <!-- Zero JS requested on desktop viewports (>= 1024px) -->
  <div class="block lg:hidden">
    <MobileDrawer client:media="(max-width: 1023px)" />
  </div>
</header>
```

#### Pattern 2: Immediate Load on Non-Critical Navigation (RULE-ID: ASTRO-HYDRATION-02)

##### ❌ Bad Practice / Anti-Pattern: `<NavigationMenu client:load />` blocking main thread during initial page load

```astro
---
// src/components/chrome/Header.astro - Unconditionally executing JS on initial paint
import NavigationMenu from "./NavigationMenu.tsx";
---
<header>
  <!-- Anti-Pattern: Downloads, parses, and reconciles JS on load -->
  <NavigationMenu client:load />
</header>
```

_Why this fails:_ Blocks the browser's main thread during critical HTML rendering and delays First Contentful Paint.

##### ✅ Best Practice / Idiomatic: `<NavigationMenu client:idle />` or pure CSS dropdown in `.astro`

```astro
---
// src/components/chrome/Header.astro - Deferred or zero-JS dropdown
import NavigationMenu from "./NavigationMenu.tsx";
---
<header>
  <!-- Idiomatic: Defers until idle or leverages zero-JS CSS hover/focus-within -->
  <NavigationMenu client:idle={{ timeout: 500 }} />
</header>
```

#### Pattern 3: Mega-Islands & Static Presentation Markup (RULE-ID: ASTRO-HYDRATION-01)

##### ❌ Bad Practice / Anti-Pattern: Rendering static presentation markup inside React client components

```astro
---
// src/components/ServiceCardWrapper.astro - Contaminating client bundle with static copy
import ServiceCard from "./ServiceCard.tsx";
const { title, description, iconSvg } = Astro.props;
---
<!-- Hydrated as client:visible even though layout and text are static -->
<ServiceCard
  title={title}
  description={description}
  iconSvg={iconSvg}
  client:visible
/>
```

_Why this fails:_ Bloats client bundles by serializing static props and pulling React runtime into pages that only need HTML.

##### ✅ Best Practice / Idiomatic: Converting static wrappers to `.astro` and isolating islands strictly to interactive leafs

```astro
---
// src/components/ServiceCardWrapper.astro - Pure static HTML with isolated leaf island
import ShareButton from "./ShareButton.tsx";
const { title, description, iconSvg } = Astro.props;
---
<!-- Pure static HTML structure with zero client JS overhead -->
<article class="service-card">
  <div class="icon" set:html={iconSvg} />
  <h3>{title}</h3>
  <p>{description}</p>

  <!-- Hydration strictly pushed down to interactive leaf button -->
  <ShareButton url={`/services/${title}`} client:idle />
</article>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/02-zero-js-hydration/13-client-media-responsive-gating/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/02-islands-and-hydration/` (e.g., `RULE-ID: ASTRO-HYDRATION-01` through `RULE-ID: ASTRO-HYDRATION-05`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/02-zero-js-hydration/13-client-media-responsive-gating/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "13-CLIENT-MEDIA-RESPONSIVE-GATING-001",
    "rule_id": "RULE-ID: ASTRO-HYDRATION-04 (Use client:media for Viewport-Specific Interactive Elements)",
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
# Turnkey Script (node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/02-zero-js-hydration/13-client-media-responsive-gating/issue-body.md" \
  --title "[Audit - client:media Responsive Island Gating Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/02-zero-js-hydration/13-client-media-responsive-gating/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification commands to validate audit findings and responsive gating candidates:

1. Scan for all active `client:media` directives across templates:
   ```bash
   git grep -n "client:media" src/
   ```
2. Scan specifically for `client:load` and `client:visible` to identify ungated responsive candidates:
   ```bash
   git grep -n "client:load" src/
   git grep -n "client:visible" src/
   ```
3. Run bundle analysis to inspect client JavaScript chunks:
   ```bash
   pnpm build && ls -lh dist/_astro/
   ```
4. Cross-reference media queries against Tailwind v4 breakpoint definitions in `tokens.css`.
5. Verify that mobile viewport requests (393px) never trigger bundle downloads for desktop mega-menu islands.
6. Verify that desktop viewport requests (1280px) never trigger bundle downloads for mobile navigation drawer islands.
7. Confirm that browser viewport resize crossing the 1024px threshold initiates on-demand script download smoothly without runtime errors.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/02-zero-js-hydration/13-client-media-responsive-gating/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** client:media Responsive Island Gating Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/02-zero-js-hydration/13-client-media-responsive-gating/findings.json` (N defects logged with RULE-ID mapping)
   - `file://docs/audits/results/02-zero-js-hydration/13-client-media-responsive-gating/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/02-zero-js-hydration/13-client-media-responsive-gating/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/02-zero-js-hydration/13-client-media-responsive-gating/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/02-zero-js-hydration/13-client-media-responsive-gating/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
