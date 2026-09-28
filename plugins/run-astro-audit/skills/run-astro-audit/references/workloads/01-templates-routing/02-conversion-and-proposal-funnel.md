# Mission Brief: Conversion & Proposal Funnel Template Audit

## 3.0 Skills / Tools: view_file, run_command, form-capture, astro-component-architect.

## 3.1 Context Block

The The application proposal and lead funnel consists of the Hello Chooser (`src/pages/hello/[...rest].astro`), Service Proposal Brief (`HelloBriefRoute.astro`), Career Application Brief, and Contact Us (`src/pages/contact/[...rest].astro`).
Form submissions are handled via Astro Actions (`src/actions/index.ts`) communicating with `workers/forms` satellite and Turnstile bot protection.
`HelloBriefFormIsland.tsx` is currently hydrated with `client:load` for prefill effects, and submits multipart form data including resume CV uploads up to 10 MiB.

### Authoritative Astro Architectural & Best Practice Rules

- **Zero-JS Outer Shell & Island Pruning** — [`[01-zero-js-by-default.md]`](../../best-practices/01-architecture-and-philosophy/01-zero-js-by-default.md): Proposal funnels must keep all outer layouts, progress headers, step indicators, and trust proof bands as static zero-JS `.astro` components. Hydration (`client:*`) should be strictly confined to interactive form inputs. Avoid `client:load` where `client:idle` or progressive enhancement suffices.
- **Slots Over Render Props** — [`[06-slots-over-render-props.md]`](../../best-practices/01-architecture-and-philosophy/06-slots-over-render-props.md): Astro cannot serialize functions across the server-client boundary. Never pass render functions or callback props (`renderFooter={(step) => ...}`) from `.astro` files to React islands. Pass static markup via Astro `<slot>` or pass serializable JSON objects as props.
- **Scoped Style Encapsulation** — [`[07-scoped-styles-encapsulation.md]`](../../best-practices/01-architecture-and-philosophy/07-scoped-styles-encapsulation.md): Component styles in `.astro` files are scoped automatically via `[data-astro-cid-*]`. Indiscriminate `<style is:global>` in funnel and form components leaks input, button, and layout specificity sitewide.
- **Client Scripts Over Heavy Frameworks** — [`[08-client-scripts-over-ui-frameworks.md]`](../../best-practices/01-architecture-and-philosophy/08-client-scripts-over-ui-frameworks.md): Toggling contact drawers, mobile slide-outs, and modal scroll locks should use native Web Components (`HTMLElement`) and bundled `<script>` tags rather than hydrating a 45KB+ React runtime for trivial DOM class toggles.
- **Pure HTML Templates (No Virtual DOM)** — [`[12-no-virtual-dom-in-astro-templates.md]`](../../best-practices/01-architecture-and-philosophy/12-no-virtual-dom-in-astro-templates.md): `.astro` templates compile strictly on the server once per render. Inline JSX handlers (`onClick={...}`) and reactive frontmatter variables are non-functional anti-patterns.
- **Catch-All Rest Parameters** — [`[02-rest-parameters-and-catch-all.md]`](../../best-practices/03-routing-and-pages/02-rest-parameters-and-catch-all.md): Route files using `[...rest].astro` (such as `src/pages/hello/[...rest].astro` and `src/pages/contact/[...rest].astro`) must return `{ params: { rest: undefined } }` in `getStaticPaths()` to match the parent root URL without 404s, never empty string `""` or `"/"`.
- **Prerendering Model & SSR Opt-In** — [`[07-ssr-on-demand-routes-vs-prerendering.md]`](../../best-practices/03-routing-and-pages/07-ssr-on-demand-routes-vs-prerendering.md): In Astro 5's unified static-first model, funnel routes pre-render to static HTML by default. Only dynamic callback or receipt handlers requiring session cookies, dynamic parameters, or decryption (`form-result.astro`) should execute on-demand SSR.
- **ClientRouter SPA Analytics Tracking** — [`[21-track-pageviews-in-client-router-with-astro-page-load.md]`](../../best-practices/03-routing-and-pages/21-track-pageviews-in-client-router-with-astro-page-load.md): Tracking funnel step completions and form view conversions on `astro:page-load` guarantees valid page titles and URLs across soft transitions.
- **Progressive Enhancement with Astro Actions** — [`[14-progressive-enhancement-with-astro-actions.md]`](../../best-practices/05-data-fetching-and-endpoints/14-progressive-enhancement-with-astro-actions.md): Form mutations should leverage type-safe Astro Actions (`src/actions/index.ts`) with standard HTML form fallbacks to ensure conversion resilience even if client-side hydration fails or scripts are delayed.

Critical files to inspect:

- `src/pages/hello/[...rest].astro`
- `src/features/company/components/HelloRoute.astro`
- `src/features/company/components/HelloBriefRoute.astro`
- `src/features/company/components/HelloBriefFormIsland.tsx`
- `src/pages/contact/[...rest].astro`
- `src/features/contact/components/ContactRoute.astro`
- `src/actions/index.ts`
- `src/pages/form-result.astro` and `src/pages/ar/form-result.astro`

## 3.2 Mission Objective

Perform an exhaustive audit of all conversion funnels, form action handlers, and form-result receivers.
Outcome: Verify that all form inputs have accessible associated `<label>`s, valid native autocomplete tokens (`autocomplete="name"`, `autocomplete="email"`, `autocomplete="tel"`, `autocomplete="organization"` for 1-click Chrome/1Password autofill), body scroll is locked when drawer opens, CSRF tokens/Turnstile states are handled cleanly, file size bounds (10 MiB) are enforced defensively, and form-result redirection handles loops and locale resolution across EN, TR, and AR.
Constraints: Read-only; do not trigger real third-party webhooks or submit dummy leads to production workers.
Autonomy Grant: You own this mission end-to-end. Analyze form state lifecycles, error branch mapping, and server action schemas. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

Trace the complete form flow:

1. Inspect `HelloBriefFormIsland.tsx`: verify whether `client:load` is truly required or if progressive enhancement / `client:idle` can eliminate main-thread blocking.

2. Zero-JS Shell & Island Pruning:
   Keep outer layout containers strictly static. Hydrate only the inner interactive inputs.

```astro
<!-- ❌ Bad Practice: Hydrating entire proposal funnel container with client:load -->
<ProposalFunnelContainer client:load steps={steps}>
  <FunnelProgressHeader />
  <BriefStepForm />
  <ClientReviewsMarquee />
</ProposalFunnelContainer>

<!-- ✅ Best Practice: Static .astro shell; isolate hydration strictly to the interactive form island -->
<section class="proposal-funnel-shell">
  <FunnelProgressHeader currentStep={1} totalSteps={3} />
  <HelloBriefFormIsland client:idle locale={locale} />
  <ClientReviewsMarquee />
</section>
```

3. Slots over Render Props across Island Boundary:
   Never attempt to pass functions across the Astro server-to-client component bridge.

```astro
<!-- ❌ Bad Practice: Passing non-serializable render function across server-client boundary -->
<HelloBriefFormIsland
  client:idle
  renderFooter={(step) => <button type="submit">Submit Step {step}</button>}
/>

<!-- ✅ Best Practice: Passing static markup via Astro slot or serializable JSON props -->
<HelloBriefFormIsland client:idle locale={locale}>
  <div slot="footer" class="form-actions">
    <button type="submit" class="btn-primary">Submit Proposal Brief</button>
  </div>
</HelloBriefFormIsland>
```

4. Client Scripts vs Heavy UI Libraries (Scroll Lock & Drawers):
   Avoid heavy React dialog runtimes for simple drawers and scroll lock management.

```astro
<!-- ❌ Bad Practice: Hydrating React Dialog + Framer Motion (60KB+) to toggle drawer & overflow -->
<ContactDrawerIsland client:load />

<!-- ✅ Best Practice: Native Web Component with zero runtime overhead -->
<contact-drawer>
  <button type="button" data-drawer-open>Get in Touch</button>
  <dialog data-drawer-dialog class="drawer">
    <button type="button" data-drawer-close>Close</button>
    <div class="drawer-content"><slot /></div>
  </dialog>
</contact-drawer>
<script>
  class ContactDrawer extends HTMLElement {
    connectedCallback() {
      const dialog = this.querySelector<HTMLDialogElement>('[data-drawer-dialog]');
      this.querySelector('[data-drawer-open]')?.addEventListener('click', () => {
        dialog?.showModal();
        document.body.style.overflow = 'hidden';
      });
      this.querySelector('[data-drawer-close]')?.addEventListener('click', () => {
        dialog?.close();
        document.body.style.overflow = '';
      });
    }
  }
  customElements.define('contact-drawer', ContactDrawer);
</script>
```

5. Progressive Enhancement with Astro Actions:
   Use native HTML forms posting to Astro Actions with progressive enhancement.

```astro
<!-- ❌ Bad Practice: Client-only fetch without native form action fallback or Turnstile verification -->
<form onSubmit={async (e) => { e.preventDefault(); await fetch('/api/submit', ...); }}>
  <input name="email" />
  <button>Send</button>
</form>

<!-- ✅ Best Practice: Native HTML form posting directly to type-safe Astro Action with progressive enhancement -->
---
import { actions } from 'astro:actions';
---
<form method="POST" action={actions.submitProposal}>
  <label for="work-email">Work Email</label>
  <input id="work-email" name="email" type="email" autocomplete="email" required />
  <button type="submit">Send Brief</button>
</form>
```

6. Catch-All Rest Parameters for Funnel Routes:
   Match the root `/hello` route segment by explicitly providing `undefined`.

```astro
---
// src/pages/hello/[...rest].astro
export async function getStaticPaths() {
  return [
    // ❌ Bad Practice: Returning "" or "/" causes routing ambiguity or build-time 404s
    // { params: { rest: "" } },
    // { params: { rest: "/" } },

    // ✅ Best Practice: Explicitly return undefined to match the root /hello route segment
    { params: { rest: undefined } },
    { params: { rest: "brief" } },
    { params: { rest: "career" } },
  ];
}
---
```

7. Style Scoping & Isolation:
   Isolate modal and form styles using Astro's scoped `<style>` to avoid specificity contamination.

```astro
<!-- ❌ Bad Practice: Indiscriminate global styles polluting global specificity and other components -->
<style is:global>
  .drawer { position: fixed; inset: 0; z-index: 50; }
  input { border: 1px solid #E2E8F0; }
</style>

<!-- ✅ Best Practice: Native scoped styles compiled to unique data-astro-cid attributes -->
<style>
  .drawer { position: fixed; inset: 0; z-index: 50; }
  input { border: 1px solid var(--color-border); }
</style>
```

8. Inspect `src/actions/index.ts`: verify input validation schemas (Zod) and error localization (`mapFormsError`) across all three locales.
9. Verify `/form-result` and `/ar/form-result`: ensure loop detection logic and download token decryption cannot throw unhandled exceptions.
10. Check native autocomplete attributes on all text inputs to maximize mobile conversion rates.
11. Confirm that opening the contact drawer locks the background body scroll (`document.body.style.overflow = "hidden"`) and releases on close.

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/01-templates-routing/02-conversion-and-proposal-funnel/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Rule ID Mapping**: Every defect recorded in `findings.json` must explicitly map to an authoritative Astro best practice rule identifier using the `rule_id` field (e.g. `RULE-ID: 01-architecture-and-philosophy/06-slots-over-render-props`, `RULE-ID: 01-architecture-and-philosophy/08-client-scripts-over-ui-frameworks`, `RULE-ID: 05-data-fetching-and-endpoints/14-progressive-enhancement-with-astro-actions`, `RULE-ID: 03-routing-and-pages/02-rest-parameters-and-catch-all`).

You must create and populate the following deliverables in `docs/audits/results/01-templates-routing/02-conversion-and-proposal-funnel/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps. Every item MUST include a valid `rule_id` linking to `../../best-practices/`:

```json
[
  {
    "id": "02-CONVERSION-AND-PROPOSAL-FUNNEL-001",
    "rule_id": "RULE-ID: 05-data-fetching-and-endpoints/14-progressive-enhancement-with-astro-actions",
    "file": "src/features/company/components/HelloBriefFormIsland.tsx",
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
   Execute the turnkey publisher script `scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, validates the checklist (<= 200 items, <= 3 levels nesting), creates the primary issue, spawns linked sub-issues (capped at 20) for critical and high severity defects, and commits/pushes results directly to `main` without PR:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
# node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/01-templates-routing/02-conversion-and-proposal-funnel/issue-body.md" \
  --title "[Audit - Conversion & Proposal Funnel Template Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/01-templates-routing/02-conversion-and-proposal-funnel/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Run `pnpm vitest run tests/int/form-result-receiver.test.ts` to prove form receiver test pass (39/39 green).
2. Run `git grep -n "renderRow\|renderItem\|renderFooter" src/features/company/ src/features/contact/` to verify zero render props passed to islands.
3. Run `git grep -n "client:load\|client:only" src/features/company/ src/features/contact/ src/pages/hello/` to audit hydration directives and verify minimal runtime.
4. Run `git grep -n "<style is:global>" src/features/company/ src/features/contact/` to audit for global CSS leaks.
5. Run `git grep -n "onClick=\|onChange=" src/pages/hello/ src/pages/contact/ src/features/contact/` to ensure no raw JSX event handlers in `.astro` wrappers.
6. Run `find dist/ -name "*.js" -size +0c` and verify that static funnel shells emit zero client JavaScript chunks.
7. Inspect `src/actions/index.ts` for complete error code mappings and zero unhandled promise rejections.
8. Verify body scroll lock cleanup on unmount/drawer closure across all locales.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/01-templates-routing/02-conversion-and-proposal-funnel/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Conversion & Proposal Funnel Template Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/01-templates-routing/02-conversion-and-proposal-funnel/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/01-templates-routing/02-conversion-and-proposal-funnel/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/01-templates-routing/02-conversion-and-proposal-funnel/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/01-templates-routing/02-conversion-and-proposal-funnel/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/01-templates-routing/02-conversion-and-proposal-funnel/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
