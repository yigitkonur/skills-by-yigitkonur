# Mission Brief: Hydration Stripper & Static React De-Hydration Audit

## 3.0 Skills / Tools: view_file, run_command, react-doctor.

## 3.1 Context Block

In Astro, importing a React component (`.tsx`) inside an `.astro` template WITHOUT a `client:*` directive renders pure static HTML with ZERO JavaScript sent to the browser.
During migration from Next.js, developers often added `client:*` directives out of habit to components that only accept props and produce static DOM.
Every unnecessary client island incurs bundle size, hydration CPU cycles, and memory overhead.

### Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`01-prefer-static-leaf-islands-over-mega-islands.md`](../../best-practices/02-islands-and-hydration/01-prefer-static-leaf-islands-over-mega-islands.md) — Keeping islands small, pushing static layout up to `.astro`, and eliminating mega-islands (`RULE-ID: ASTRO-HYDRATION-01`).
- [`02-never-default-blindly-to-client-load.md`](../../best-practices/02-islands-and-hydration/02-never-default-blindly-to-client-load.md) — Eradicating `client:load` for below-the-fold content and non-critical widgets (`RULE-ID: ASTRO-HYDRATION-02`).
- [`03-use-client-visible-with-root-margin-for-below-fold.md`](../../best-practices/02-islands-and-hydration/03-use-client-visible-with-root-margin-for-below-fold.md) — Deferred hydration using `client:visible={{ rootMargin: '200px' }}` (`RULE-ID: ASTRO-HYDRATION-03`).
- [`04-use-client-media-for-responsive-interactive-elements.md`](../../best-practices/02-islands-and-hydration/04-use-client-media-for-responsive-interactive-elements.md) — Responsive hydration gating via `client:media="(max-width: 1024px)"` (`RULE-ID: ASTRO-HYDRATION-04`).
- [`05-use-client-only-for-browser-dependent-widgets.md`](../../best-practices/02-islands-and-hydration/05-use-client-only-for-browser-dependent-widgets.md) — Bypassing server SSR errors with `client:only="react"` and fallback slots (`RULE-ID: ASTRO-HYDRATION-05`).

- Architecture Rule: Zero-Runtime Native Compilation. React components imported into `.astro` files without client directives compile to raw HTML strings during the build. No React runtime, virtual DOM reconciliation, or JSON props serialization is delivered to the browser.
- Eliminating "use client" Spillover: In Next.js, adding `'use client'` to a parent component drags all imported child components and icons into the client bundle. Astro eliminates this contagion: passing server-rendered content through `<slot />` into an island preserves the children as 100% static HTML, preventing bundle bloat.
- Static Leaf Island Mandate: Presentational cards, badges, service grids, and marketing blocks must NEVER be hydrated. If an interactive widget (e.g. copy button, filter) is required inside a card, maintain the card as a zero-JS `.astro` template and isolate hydration strictly to the interactive leaf component.

Critical files to inspect:

- All call sites of `client:` in `src/`
- `src/components/sections/service-shared/`
- `src/components/service-hierarchy/`
- `src/features/homepage/components/`
- `src/components/molecules/`

## 3.2 Mission Objective

Inspect every single `client:*` hydration directive across the repository.
Outcome: Identify all "fake islands" (React components lacking `useState`, `useEffect`, `onClick`, or browser APIs) and provide a concrete de-hydration list to eliminate unnecessary client JavaScript, scoping hydration strictly to isolated leaves.
Constraints: Read-only audit. Ensure that true interactive components (search, toggles, form islands) remain functional.
Autonomy Grant: You own this mission end-to-end. Analyze ASTs, state dependencies, and event handlers. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Run `grep -rn "client:" src/` to extract the complete census of all hydrated islands.
2. Inspect the underlying `.tsx` implementation for each match: check for hooks (`useState`, `useReducer`, `useEffect`) and event listeners.
3. Classify each island:
   - (A) Pure Presentational -> Strip directive entirely (Level 1 static, zero client JS).
   - (B) Interactive with static children -> Refactor to `.astro` slots or static leaf islands.
   - (C) Interactive -> Preserve or downgrade directive according to hydration hierarchy.
4. Audit import graphs to verify no heavy static SVG diagrams or markdown content are leaked into client JS bundles.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Mega-Islands & Static Presentation Markup (RULE-ID: ASTRO-HYDRATION-01)

##### ❌ Bad Practice / Anti-Pattern: Rendering static presentation markup inside React client components

```astro
---
// src/components/ServiceCardWrapper.astro - Contaminating client bundle with static copy
import ServiceCard from "./ServiceCard.tsx";
const { title, description, iconSvg } = Astro.props;
---
<!-- Hydrated as client:visible even though it contains 0 state or browser APIs -->
<ServiceCard
  title={title}
  description={description}
  iconSvg={iconSvg}
  client:visible
/>
```

_Why this fails:_ Adding `client:visible` forces Astro to bundle React runtime, the component code, and serialized props into a client `.js` chunk. For static content, this wastes bandwidth, increases main-thread parse time, and degrades INP.

##### ✅ Best Practice / Idiomatic: Converting static wrappers to `.astro` and isolating islands strictly to interactive leafs

```astro
---
// src/components/ServiceCardWrapper.astro - Pure static HTML with isolated leaf island
import ShareButton from "./ShareButton.tsx";
const { title, description, iconSvg } = Astro.props;
---
<!-- Level 1 Static: 0 KB JavaScript emitted for card layout and typography -->
<article class="service-card">
  <div class="icon" set:html={iconSvg} />
  <h3>{title}</h3>
  <p>{description}</p>

  <!-- Hydration strictly pushed down to interactive leaf button -->
  <ShareButton url={`/services/${title}`} client:idle />
</article>
```

#### Pattern 2: Immediate Load on Non-Critical Navigation (RULE-ID: ASTRO-HYDRATION-02)

##### ❌ Bad Practice / Anti-Pattern: `<NavigationMenu client:load />` blocking main thread during initial page load

```astro
---
// src/components/chrome/Header.astro - Blocking main thread during initial parse
import NavigationMenu from "./NavigationMenu.tsx";
---
<header>
  <!-- Anti-Pattern: client:load downloads and executes JS during critical first paint -->
  <NavigationMenu client:load />
</header>
```

_Why this fails:_ `client:load` executes immediately, directly competing with HTML parsing, stylesheet evaluation, and LCP.

##### ✅ Best Practice / Idiomatic: `<NavigationMenu client:idle />` or pure CSS dropdown in `.astro`

```astro
---
// src/components/chrome/Header.astro - Deferred or zero-JS dropdown
import NavigationMenu from "./NavigationMenu.tsx";
---
<header>
  <!-- Idiomatic: Defers hydration until main thread reaches idle state -->
  <NavigationMenu client:idle={{ timeout: 500 }} />
</header>
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
  <!-- Anti-Pattern: Both islands are downloaded & parsed on all devices despite CSS hiding -->
  <div class="hidden lg:block">
    <MegaMenu client:load />
  </div>
  <div class="block lg:hidden">
    <MobileDrawer client:load />
  </div>
</header>
```

_Why this fails:_ CSS utility classes (`hidden`, `block`) do not prevent script download. Both mobile and desktop bundles are fetched on every device.

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
`docs/audits/results/02-zero-js-hydration/11-hydration-stripper-static-react/`

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

You must create and populate the following deliverables in `docs/audits/results/02-zero-js-hydration/11-hydration-stripper-static-react/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "11-HYDRATION-STRIPPER-STATIC-REACT-001",
    "rule_id": "RULE-ID: ASTRO-HYDRATION-01 (Prefer Static Leaf Islands Over Mega-Islands)",
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
  --body "docs/audits/results/02-zero-js-hydration/11-hydration-stripper-static-react/issue-body.md" \
  --title "[Audit - Hydration Stripper & Static React De-Hydration Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/02-zero-js-hydration/11-hydration-stripper-static-react/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification commands to validate audit findings and directive strip candidates:

1. Identify all active hydration directives sitewide:
   ```bash
   git grep -n "client:" src/
   ```
2. Scan specifically for `client:load`, `client:visible`, and `client:media`:
   ```bash
   git grep -n "client:load" src/
   git grep -n "client:visible" src/
   git grep -n "client:media" src/
   ```
3. Run bundle analysis to inspect client JavaScript chunks and verify that no static components leak into the client bundle:
   ```bash
   pnpm build && ls -lh dist/_astro/
   ```
4. Verify absence of `<astro-island>` wrappers around presentational components in emitted HTML:
   ```bash
   grep -rn "<astro-island" dist/ | grep -i "StaticCard" || true
   ```
5. Cross-reference component ASTs to prove candidates for directive removal contain zero state hooks (`useState`, `useReducer`), zero effects (`useEffect`), and zero browser APIs.
6. Provide a concrete candidate table with estimated KB bundle savings and prove that removing `client:*` preserves 100% of user interactions and visual fidelity.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/02-zero-js-hydration/11-hydration-stripper-static-react/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Hydration Stripper & Static React De-Hydration Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/02-zero-js-hydration/11-hydration-stripper-static-react/findings.json` (N defects logged with RULE-ID mapping)
   - `file://docs/audits/results/02-zero-js-hydration/11-hydration-stripper-static-react/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/02-zero-js-hydration/11-hydration-stripper-static-react/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/02-zero-js-hydration/11-hydration-stripper-static-react/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/02-zero-js-hydration/11-hydration-stripper-static-react/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
