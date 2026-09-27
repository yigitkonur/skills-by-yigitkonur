# Mission Brief: client:load Elimination & Progressive Downgrade Audit

## 3.0 Skills / Tools: view_file, run_command, react-doctor.

## 3.1 Context Block

The `client:load` directive instructs the browser to download, parse, and execute component JavaScript immediately on initial page load, competing directly with HTML parsing, stylesheet rendering, and Largest Contentful Paint (LCP).
In Astro best practices, `client:load` is reserved strictly for immediately visible, above-the-fold interactive elements (like a sticky header search trigger or immediate mobile menu toggle).
All below-the-fold or non-urgent components must use `client:visible` with `rootMargin` or `client:idle`.

### Astro Architectural & Best Practice Rules

Every finding, scheduling assessment, and recommended downgrade in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`01-prefer-static-leaf-islands-over-mega-islands.md`](../../best-practices/02-islands-and-hydration/01-prefer-static-leaf-islands-over-mega-islands.md) — Keeping islands small, pushing static layout up to `.astro`, and eliminating mega-islands (`RULE-ID: ASTRO-HYDRATION-01`).
- [`02-never-default-blindly-to-client-load.md`](../../best-practices/02-islands-and-hydration/02-never-default-blindly-to-client-load.md) — Eradicating `client:load` for below-the-fold content and non-critical widgets (`RULE-ID: ASTRO-HYDRATION-02`).
- [`03-use-client-visible-with-root-margin-for-below-fold.md`](../../best-practices/02-islands-and-hydration/03-use-client-visible-with-root-margin-for-below-fold.md) — Deferred hydration using `client:visible={{ rootMargin: '200px' }}` (`RULE-ID: ASTRO-HYDRATION-03`).
- [`04-use-client-media-for-responsive-interactive-elements.md`](../../best-practices/02-islands-and-hydration/04-use-client-media-for-responsive-interactive-elements.md) — Responsive hydration gating via `client:media="(max-width: 1024px)"` (`RULE-ID: ASTRO-HYDRATION-04`).
- [`05-use-client-only-for-browser-dependent-widgets.md`](../../best-practices/02-islands-and-hydration/05-use-client-only-for-browser-dependent-widgets.md) — Bypassing server SSR errors with `client:only="react"` and fallback slots (`RULE-ID: ASTRO-HYDRATION-05`).

- Architecture Rule: Hydration Scheduling Hierarchy. Astro grants fine-grained scheduling control. Slapping `client:load` on every framework component is a legacy habit from SPA frameworks. Running multiple `client:load` islands inflates Total Blocking Time (TBT) and destroys Interaction to Next Paint (INP).
- Viewport Pre-Hydration with `rootMargin`: Plain `client:visible` triggers hydration right when the component boundary enters the viewport. Fast scrolling can result in unresponsive clicks while the script fetches. Adding `client:visible={{ rootMargin: '200px' }}` instructs `IntersectionObserver` to pre-hydrate the component 200px before it enters the viewport.
- Progressive Enhancement for Forms: Contact forms (`HelloBriefFormIsland`) and newsletter subscriptions should render semantic HTML `<form>` tags from the server. Downgrading hydration to `client:visible={{ rootMargin: '200px' }}` or `client:idle={{ timeout: 500 }}` allows native browser autofill to work instantly while freeing the main thread during initial paint.

Critical files to inspect:

- `src/features/company/components/HelloBriefRoute.astro`:90 (`HelloBriefFormIsland`)
- `src/features/academy/components/AcademyHubRoute.astro`:96
- `src/features/academy/components/AcademyModuleRoute.astro`:190 (`ModuleLessonsIsland`)
- `src/features/academy/components/AcademyLessonRoute.astro`:222, 272
- `src/components/chrome/SiteHeader.astro`

## 3.2 Mission Objective

Audit every `client:load` directive currently present in the codebase.
Outcome: Provide a surgical migration roadmap to transition non-critical `client:load` islands to `client:visible={{ rootMargin: '200px' }}` or `client:idle`, minimizing Total Blocking Time (TBT) and optimizing mobile Lighthouse scores.
Constraints: Read-only audit; verify that form prefilling, validation, and deep-linking behaviors are preserved.
Autonomy Grant: You own this mission end-to-end. Trace load event lifecycles, script waterfall traces, and layout timing. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Run `grep -rn "client:load" src/` to extract every instance across pages and components.
2. Analyze `HelloBriefFormIsland`: evaluate transitioning from `client:load` to `client:visible={{ rootMargin: '200px' }}` or `client:idle`.
3. Analyze `AcademyModuleRoute` and `AcademyLessonRoute`: determine why lessons are loaded immediately and measure TBT savings when downgraded to `client:visible`.
4. Check if any pure browser widgets require `client:only="react"` with `<div slot="fallback">` instead of `client:load`.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Blind client:load on Navigation & Below-Fold Widgets (RULE-ID: ASTRO-HYDRATION-02 & ASTRO-HYDRATION-03)

##### ❌ Bad Practice / Anti-Pattern: `<NavigationMenu client:load />` blocking main thread during initial page load

```astro
---
// src/pages/contact.astro - Blindly hydrating navigation and below-fold widgets on initial load
import NavigationMenu from "../components/NavigationMenu.tsx";
import HelloBriefFormIsland from "../components/HelloBriefFormIsland.tsx";
import ReviewCarousel from "../components/ReviewCarousel.tsx";
import FaqAccordion from "../components/FaqAccordion.tsx";
---
<header>
  <!-- Anti-Pattern: Blocks initial parse before user interacts -->
  <NavigationMenu client:load />
</header>
<main>
  <!-- Anti-Pattern: Triggers immediate JS download & main thread blockage on initial paint -->
  <HelloBriefFormIsland client:load />
  <ReviewCarousel client:load />
  <FaqAccordion client:load />
</main>
```

_Why this fails:_ All four components download, parse, and execute JavaScript concurrently during initial load. This blocks the main thread, inflates TBT, delays First Contentful Paint, and wastes mobile data bandwidth on elements the user hasn't scrolled to yet.

##### ✅ Best Practice / Idiomatic: `<NavigationMenu client:idle />` or pure CSS dropdown in `.astro`

```astro
---
// src/pages/contact.astro - Prioritized hydration scheduling hierarchy
import NavigationMenu from "../components/NavigationMenu.tsx";
import HelloBriefFormIsland from "../components/HelloBriefFormIsland.tsx";
import ReviewCarousel from "../components/ReviewCarousel.tsx";
import FaqAccordion from "../components/FaqAccordion.tsx";
---
<header>
  <!-- Deferred until main thread is idle (or pure CSS dropdown in .astro) -->
  <NavigationMenu client:idle={{ timeout: 500 }} />
</header>
<main>
  <!-- Form pre-hydrates 200px before scroll entry; native inputs work immediately -->
  <HelloBriefFormIsland client:visible={{ rootMargin: '200px' }} />
  <!-- Carousel hydrates only when scrolled near viewport -->
  <ReviewCarousel client:visible={{ rootMargin: '200px' }} />
  <!-- Non-urgent accordion hydrates on idle or viewport entry -->
  <FaqAccordion client:idle={{ timeout: 1000 }} />
</main>
```

#### Pattern 2: Mega-Islands & Static Presentation Markup (RULE-ID: ASTRO-HYDRATION-01)

##### ❌ Bad Practice / Anti-Pattern: Rendering static presentation markup inside React client components

```astro
---
// src/components/ServiceCardWrapper.astro - Contaminating client bundle with static copy
import ServiceCard from "./ServiceCard.tsx";
const { title, description, iconSvg } = Astro.props;
---
<!-- Hydrated as client:load or client:visible despite being 95% static layout -->
<ServiceCard
  title={title}
  description={description}
  iconSvg={iconSvg}
  client:load
/>
```

_Why this fails:_ Forces client download of React runtime, virtual DOM reconciliation, and JSON props serialization for static content.

##### ✅ Best Practice / Idiomatic: Converting static wrappers to `.astro` and isolating islands strictly to interactive leafs

```astro
---
// src/components/ServiceCardWrapper.astro - Pure static HTML with isolated leaf island
import ShareButton from "./ShareButton.tsx";
const { title, description, iconSvg } = Astro.props;
---
<!-- Zero KB JavaScript emitted for card layout and typography -->
<article class="service-card">
  <div class="icon" set:html={iconSvg} />
  <h3>{title}</h3>
  <p>{description}</p>

  <!-- Hydration strictly pushed down to interactive leaf button -->
  <ShareButton url={`/services/${title}`} client:idle />
</article>
```

#### Pattern 3: Desktop-Only Mega-Menus Leaking to Mobile (RULE-ID: ASTRO-HYDRATION-04)

##### ❌ Bad Practice / Anti-Pattern: Desktop-only mega-menus shipping 50KB mobile JS without media gating

```astro
---
// src/components/chrome/SiteHeader.astro - CSS hiding without media gating
import MegaMenu from "./MegaMenu.tsx";
import MobileDrawer from "./MobileDrawer.tsx";
---
<header>
  <!-- Both components hydrated on all devices via client:load -->
  <div class="hidden lg:block">
    <MegaMenu client:load />
  </div>
  <div class="block lg:hidden">
    <MobileDrawer client:load />
  </div>
</header>
```

_Why this fails:_ CSS utility classes (`hidden`, `block`) do not stop client script fetching. Mobile users download 70+ KB of desktop mega-menu code over cellular connections.

##### ✅ Best Practice / Idiomatic: `<MobileDrawer client:media="(max-width: 1024px)" />` and `<MegaMenu client:media="(min-width: 1024px)" />`

```astro
---
// src/components/chrome/SiteHeader.astro - Pre-request media gating
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
    <MobileDrawer client:media="(max-width: 1024px)" />
  </div>
</header>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/02-zero-js-hydration/12-client-load-elimination-downgrade/`

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

You must create and populate the following deliverables in `docs/audits/results/02-zero-js-hydration/12-client-load-elimination-downgrade/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "12-CLIENT-LOAD-ELIMINATION-DOWNGRADE-001",
    "rule_id": "RULE-ID: ASTRO-HYDRATION-02 (Never Default Blindly to Client Load)",
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
  --body "docs/audits/results/02-zero-js-hydration/12-client-load-elimination-downgrade/issue-body.md" \
  --title "[Audit - client:load Elimination & Progressive Downgrade Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/02-zero-js-hydration/12-client-load-elimination-downgrade/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification commands to validate audit findings and progressive downgrade candidates:

1. Run a full census of all `client:load` instances with above-the-fold vs below-the-fold classification:
   ```bash
   git grep -n "client:load" src/
   ```
2. Scan specifically for `client:visible` and `client:media` across components:
   ```bash
   git grep -n "client:visible" src/
   git grep -n "client:media" src/
   ```
3. Run bundle analysis to inspect client JavaScript chunks:
   ```bash
   pnpm build && ls -lh dist/_astro/
   ```
4. Measure bundle weight differences and TBT impact for each `client:load` candidate.
5. Run Lighthouse CLI to measure TBT reduction:
   ```bash
   npx lighthouse-ci collect --url="http://localhost:4321"
   ```
6. Verify script loading in browser trace: confirm downgraded chunks are not requested during initial HTML parse.
7. Verify zero breakage in form submission (`HelloBriefFormIsland`) or lesson progress tracking under delayed hydration.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/02-zero-js-hydration/12-client-load-elimination-downgrade/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** client:load Elimination & Progressive Downgrade Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/02-zero-js-hydration/12-client-load-elimination-downgrade/findings.json` (N defects logged with RULE-ID mapping)
   - `file://docs/audits/results/02-zero-js-hydration/12-client-load-elimination-downgrade/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/02-zero-js-hydration/12-client-load-elimination-downgrade/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/02-zero-js-hydration/12-client-load-elimination-downgrade/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/02-zero-js-hydration/12-client-load-elimination-downgrade/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
