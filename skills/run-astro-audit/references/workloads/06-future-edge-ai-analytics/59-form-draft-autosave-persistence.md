# Mission Brief: Form Draft Auto-Save & Zero Data Loss Session Persistence Audit

## 3.0 Skills / Tools: view_file, run_command, form-capture.

## 3.1 Context Block

High-value B2B proposal briefs (`HelloBriefRoute.astro`) contain detailed project scopes, budget tiers, and decision-maker contact details.
If an enterprise prospect experiences an accidental tab close, browser crash, or network drop while composing a proposal, un-persisted inputs are completely lost, jeopardizing enterprise revenue opportunities ($50K-$100K+).
Astro form islands and custom form elements require resilient, non-blocking auto-save and draft restoration:

- Storage Strategy: Debounced synchronization (300-500ms) to `sessionStorage` (or `localStorage`) allows seamless input restoration across refreshes.
- Safari Incognito / Private Browsing Guard: Un-shielded storage calls throw `SecurityError` or `QuotaExceededError` when browser security policies block local storage. All storage operations must be wrapped in defensive try/catch blocks with in-memory fallbacks.
- Draft Purge Lifecycle: Persisted drafts must be purged atomically upon successful submission (`form-result` redirection or HTTP 200 payload) to prevent stale form repopulation.
- Privacy & File Handling: Passwords and credit cards must never be serialized. File inputs (e.g. CV attachments) cannot be reconstructed from string storage and must present clear re-attachment prompts without crashing.
- Autocomplete: Form inputs must declare standard `autocomplete` tokens (`name`, `email`, `tel`, `organization`) to minimize user friction.

### Astro Architectural & Best Practice Rules

All form state management, persistence lifecycles, and client routing hooks must adhere to the authoritative best practices:

- [14-script-execution-mechanics-and-data-astro-rerun.md](../../best-practices/03-routing-and-pages/14-script-execution-mechanics-and-data-astro-rerun.md) — Script execution mechanics, bundled module scripts vs inline, and `data-astro-rerun` handling.
- [15-astro-page-load-vs-domcontentloaded-and-listener-leaks.md](../../best-practices/03-routing-and-pages/15-astro-page-load-vs-domcontentloaded-and-listener-leaks.md) — Using `astro:page-load` instead of `DOMContentLoaded` for form element initialization and teardown on `astro:before-swap`.
- [18-custom-dom-swap-and-state-carryover-on-before-swap.md](../../best-practices/03-routing-and-pages/18-custom-dom-swap-and-state-carryover-on-before-swap.md) — State carryover and draft restoration on `astro:before-swap`.
- [16-transition-persist-and-persistent-islands.md](../../best-practices/03-routing-and-pages/16-transition-persist-and-persistent-islands.md) — Using `transition:persist` on multi-step form islands to preserve draft inputs across soft navigations.
- [08-actions-vs-endpoints-mutations.md](../../best-practices/05-data-fetching-and-endpoints/08-actions-vs-endpoints-mutations.md) — Standardized backend form mutations with atomic client draft purge upon successful execution.
- [14-progressive-enhancement-with-astro-actions.md](../../best-practices/05-data-fetching-and-endpoints/14-progressive-enhancement-with-astro-actions.md) — Progressive enhancement ensuring forms submit without JS dependency even if client storage fails.
- [21-track-pageviews-in-client-router-with-astro-page-load.md](../../best-practices/03-routing-and-pages/21-track-pageviews-in-client-router-with-astro-page-load.md) — Reliable pageview tracking under ClientRouter without interfering with form input state.
- [01-avoid-blanket-viewport-prefetching.md](../../best-practices/09-performance-prefetch-and-transitions/01-avoid-blanket-viewport-prefetching.md) — Preventing prefetch interference on form action routes.
- [03-configure-native-prefetch-engine.md](../../best-practices/09-performance-prefetch-and-transitions/03-configure-native-prefetch-engine.md) — Configuring native prefetch engine in `astro.config.mjs`.
- [17-leverage-speculation-rules-client-prerendering.md](../../best-practices/09-performance-prefetch-and-transitions/17-leverage-speculation-rules-client-prerendering.md) — Disabling speculative prerendering on form submission routes to prevent unintended draft state corruption.

Critical files to inspect:

- src/features/company/components/HelloBriefFormIsland.tsx
- src/features/contact/components/ContactRoute.astro
- src/scripts/elements/contact-form-element.ts

## 3.2 Mission Objective

Audit form state persistence, recovery, and security across proposal and contact forms.
Outcome: Ensure that form inputs auto-save locally with debounce, restore seamlessly if the page is refreshed, purge cached drafts immediately upon successful submission, wrap all storage access in defensive try/catch blocks for Safari Incognito / Private Browsing quota safety, and include native autocomplete attributes.
Constraints: Read-only audit; verify storage privacy (never persist credit cards or passwords).
Autonomy Grant: You own this mission end-to-end. Trace form change listeners, storage keys, and cleanup lifecycles. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect HelloBriefFormIsland.tsx: check if form input states are synchronized with sessionStorage using debounced handlers.
2. Ensure draft data is cleared upon successful form submission (form-result redirection).
3. Validate that file inputs (CV upload) handle re-attachment prompts gracefully without throwing errors.
4. Wrap storage calls in defensive try/catch: prevent SecurityError or QuotaExceededError in Safari Private Browsing mode.
5. Verify native autocomplete tokens (autocomplete="name", autocomplete="email", autocomplete="tel", autocomplete="organization") on all inputs.

### ❌ Bad Practice / Anti-Pattern

```tsx
// ❌ FAILS: Using DOMContentLoaded for form autosave fails on soft client transitions under ClientRouter!
// Subsequent visits to proposal forms never attach the auto-save listener.
// Unshielded synchronous writes also throw SecurityError/QuotaExceededError in Safari Private Browsing.
document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form')
  form?.addEventListener('input', (e) => {
    // ❌ Synchronous un-debounced write throws QuotaExceededError/SecurityError in private mode
    localStorage.setItem(
      'lead_draft',
      JSON.stringify({
        ...formData,
        [(e.target as HTMLInputElement).name]: (e.target as HTMLInputElement).value,
      }),
    )
  })
})

// ❌ Missing cleanup on submit: stale data reappears if user revisits proposal form
async function handleSubmit() {
  await fetch('/api/forms/submit', { method: 'POST', body: JSON.stringify(formData) })
  window.location.href = '/thank-you' // Draft remains stuck in local storage!
}
```

### ✅ Best Practice / Idiomatic

```typescript
// Safe storage utility with defensive try/catch and in-memory fallback
const safeDraftStorage = {
  setItem(key: string, value: string): void {
    try {
      sessionStorage.setItem(key, value)
    } catch {
      /* Safari Private Browsing or quota exceeded: ignore gracefully */
    }
  },
  getItem(key: string): string | null {
    try {
      return sessionStorage.getItem(key)
    } catch {
      return null
    }
  },
  removeItem(key: string): void {
    try {
      sessionStorage.removeItem(key)
    } catch {
      /* Ignore storage access errors */
    }
  },
}

// Debounced auto-save & atomic post-submission purge
const debouncedSave = debounce((data: Record<string, unknown>) => {
  safeDraftStorage.setItem('form_brief_draft_v1', JSON.stringify(data))
}, 400)

function onSubmissionSuccess() {
  safeDraftStorage.removeItem('form_brief_draft_v1')
}
```

```astro
---
// src/components/BriefForm.astro - Idiomatic Astro ClientRouter lifecycle integration
---
<form id="brief-form">
  <input name="name" type="text" autocomplete="name" required />
  <input name="email" type="email" autocomplete="email" required />
  <input name="organization" type="text" autocomplete="organization" />
  <button type="submit">Submit Brief</button>
</form>

<script>
  let activeCleanup: (() => void) | null = null;

  // ✅ Best Practice: Use astro:page-load to attach autosave listeners on every transition
  document.addEventListener('astro:page-load', () => {
    const form = document.getElementById('brief-form') as HTMLFormElement | null;
    if (!form) return;

    // Restore draft if present
    const saved = safeDraftStorage.getItem('form_brief_draft_v1');
    if (saved) {
      try {
        const data = JSON.parse(saved);
        Object.entries(data).forEach(([key, val]) => {
          const input = form.elements.namedItem(key) as HTMLInputElement | null;
          if (input) input.value = String(val);
        });
      } catch { /* Ignore malformed JSON */ }
    }

    const handleInput = () => {
      const formData = new FormData(form);
      const entries = Object.fromEntries(formData.entries());
      debouncedSave(entries);
    };

    form.addEventListener('input', handleInput);
    activeCleanup = () => form.removeEventListener('input', handleInput);
  });

  // ✅ Best Practice: Clean up listeners on astro:before-swap to prevent memory leaks
  document.addEventListener('astro:before-swap', () => {
    if (activeCleanup) {
      activeCleanup();
      activeCleanup = null;
    }
  });
</script>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/06-future-edge-ai-analytics/59-form-draft-autosave-persistence/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Best Practice Mapping Requirement**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule (e.g. `RULE-ID: 03-14-script-execution-mechanics-and-data-astro-rerun`, `RULE-ID: 03-15-astro-page-load-vs-domcontentloaded-and-listener-leaks`, `RULE-ID: 03-16-transition-persist-and-persistent-islands`, `RULE-ID: 03-18-custom-dom-swap-and-state-carryover-on-before-swap`, `RULE-ID: 05-08-actions-vs-endpoints-mutations`, `RULE-ID: 05-14-progressive-enhancement-with-astro-actions`, `RULE-ID: 03-21-track-pageviews-in-client-router-with-astro-page-load`, `RULE-ID: 09-01-avoid-blanket-viewport-prefetching`, `RULE-ID: 09-03-configure-native-prefetch-engine`, or `RULE-ID: 09-17-leverage-speculation-rules-client-prerendering`).

You must create and populate the following deliverables in `docs/audits/results/06-future-edge-ai-analytics/59-form-draft-autosave-persistence/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "59-FORM-DRAFT-AUTOSAVE-PERSISTENCE-001",
    "rule_id": "RULE-ID (e.g. 03-15-astro-page-load-vs-domcontentloaded-and-listener-leaks)",
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
   Execute the turnkey publisher script using `node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting (max 200 items, <= 3 levels deep), creates the primary issue, spawns linked sub-issues (up to 20) for critical/high defects, and pushes the JSON deliverables directly to `origin main` without PR:

```bash
# Turnkey Script (node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/06-future-edge-ai-analytics/59-form-draft-autosave-persistence/issue-body.md" \
  --title "[Audit - Form Draft Auto-Save & Zero Data Loss Session Persistence Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/06-future-edge-ai-analytics/59-form-draft-autosave-persistence/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Verify that refreshing an in-progress proposal form retains user-typed inputs.
2. Confirm that successfully submitted forms leave zero residual draft data in local storage.
3. Audit form storage safety, autocomplete compliance, and prefetch exclusions via terminal commands:

```bash
# 1. Audit unshielded localStorage / sessionStorage access in form features
grep -rnE '(localStorage|sessionStorage)\.(setItem|getItem|removeItem)' src/features/company/ src/features/contact/ src/scripts/

# 2. Check for missing autocomplete attributes on form input elements
grep -rn '<input' src/features/company/ src/features/contact/ | grep -v 'autocomplete='

# 3. Check for debounce implementation in input handlers
grep -rn 'debounce' src/features/company/ src/scripts/

# 4. Audit storage draft key cleanup on form submission endpoints
grep -rnE 'removeItem\([^)]*draft' src/features/ src/scripts/

# 5. Audit ClientRouter lifecycle hooks and transition:persist usage on form islands
git grep -n "transition:persist" src/features/ src/components/
git grep -n "astro:page-load" src/features/company/ src/features/contact/ src/scripts/
git grep -n "astro:before-swap" src/features/company/ src/features/contact/ src/scripts/

# 6. Audit for speculation rules and prefetch directives on form routes
git grep -n "speculationrules" src/
git grep -n "data-astro-prefetch" src/
```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/06-future-edge-ai-analytics/59-form-draft-autosave-persistence/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Form Draft Auto-Save & Zero Data Loss Session Persistence Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/06-future-edge-ai-analytics/59-form-draft-autosave-persistence/findings.json` (N defects logged)
   - `file://docs/audits/results/06-future-edge-ai-analytics/59-form-draft-autosave-persistence/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/06-future-edge-ai-analytics/59-form-draft-autosave-persistence/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/06-future-edge-ai-analytics/59-form-draft-autosave-persistence/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/06-future-edge-ai-analytics/59-form-draft-autosave-persistence/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
