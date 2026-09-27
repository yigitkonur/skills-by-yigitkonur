# Mission Brief: React to Native Web Component Modernization Audit

## 3.0 Skills / Tools: view_file, run_command, react-doctor.

## 3.1 Context Block

Astro allows embedding native HTML Web Components (`<custom-element>`) backed by small (<1 KB) vanilla TypeScript scripts in `src/scripts/elements/`.
`ContactDrawer.astro` successfully uses a custom element (`<contact-drawer>`) instead of React, saving 40+ KB of React runtime for a simple drawer toggle.
Many other micro-interactions in the site (accordions, copy-to-clipboard, filter tabs, modal dialogs) might still be using heavy React islands.

- Architecture Rule: Native Web Components vs React Runtime Inflation. For micro-interactions whose state footprint is trivial (e.g. `isOpen: boolean`, `isCopied: boolean`, or active tab index), importing a React component and adding `client:load` or `client:visible` forces the browser to download the entire React runtime, scheduler, and virtual DOM reconciler (~45 KB compressed). Astro natively supports Custom Elements (`<custom-element>`), allowing micro-interactions to execute with tiny (<1 KB) vanilla TypeScript handlers in `src/scripts/elements/`.
- Accessible DOM Manipulation Lifecycle: Native Custom Elements must implement standard lifecycle callbacks (`connectedCallback`, `disconnectedCallback`) and maintain strict WAI-ARIA conformance (`aria-expanded="false"`, `aria-controls`, keyboard triggers on Enter/Space, and Escape key dismissal).
- Island Elimination on Static Landing Pages: Many content and landing pages on example.com require zero dynamic user state except for a copy-to-clipboard button or an accordion FAQ. Replacing these micro-islands with native Custom Elements eliminates React completely from these routes, resulting in 100% zero-JS pages.

### Astro Architectural & Best Practice Rules

- **[08-client-scripts-over-ui-frameworks.md](../../best-practices/01-architecture-and-philosophy/08-client-scripts-over-ui-frameworks.md)**: Replace heavy UI framework components with native Web Components (`HTMLElement`) and bundled vanilla scripts. Micro-interactions with trivial state (`isOpen`, `isCopied`, active tab) must never ship React's ~45 KB runtime.
- **[13-passing-data-to-client-via-dataset.md](../../best-practices/01-architecture-and-philosophy/13-passing-data-to-client-via-dataset.md)**: Pass server data safely via HTML `data-*` attributes and `HTMLElement.dataset` rather than inline scripts or serialized props, preserving CSP compliance and XSS safety.
- **[06-pass-static-children-through-astro-slots-not-props.md](../../best-practices/02-islands-and-hydration/06-pass-static-children-through-astro-slots-not-props.md)**: Pass static content through Astro `<slot />` or named slots instead of serializing markup into React island props.
- **[07-never-share-state-with-react-context-across-islands.md](../../best-practices/02-islands-and-hydration/07-never-share-state-with-react-context-across-islands.md)**: Never use React Context across separate Astro islands; each island mounts into an isolated root.
- **[08-use-nanostores-for-cross-island-and-cross-framework-state.md](../../best-practices/02-islands-and-hydration/08-use-nanostores-for-cross-island-and-cross-framework-state.md)**: Use Nanostores (`atom`, `map`) as zero-dependency module singletons for cross-island and cross-framework state synchronization.

Critical files to inspect:

- `src/components/chrome/ContactDrawer.astro`
- `src/scripts/elements/contact-form-element.ts`
- `src/components/molecules/`
- `src/components/atoms/`
- `src/components/content/`

## 3.2 Mission Objective

Audit all micro-interactive React components across the UI.
Outcome: Identify components that can be rewritten as zero-dependency native HTML Custom Elements, eliminating React runtime overhead entirely on pages that don't need it.
Constraints: Read-only audit; verify that accessibility (WAI-ARIA) and keyboard navigation are maintained.
Autonomy Grant: You own this mission end-to-end. Evaluate DOM manipulation complexity, event listeners, and bundle footprints. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Survey all components in `src/components/atoms/` and `src/components/molecules/` for React state usage.
2. Identify components whose only state is `isOpen: boolean`, `activeTab: string`, or `copied: boolean`.
3. Outline a conversion blueprint to native Custom Elements with `connectedCallback()` and `attributeChangedCallback()`.
4. Check that scripts in `src/scripts/elements/` have zero external framework dependencies.

### ❌ Bad Practice vs. ✅ Best Practice Code Comparisons

#### 1. Micro-Interaction Runtime: React Island vs. Native Web Component

- ❌ **Bad Practice (React runtime inflation for simple click/toggle)**:

  ```tsx
  // src/components/molecules/CopyButton.tsx - Heavy React island for a single click
  import { useState } from 'react'

  export default function CopyButton({ text }: { text: string }) {
    const [copied, setCopied] = useState(false)
    const handleCopy = () => {
      navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
    return (
      <button onClick={handleCopy} className="btn-copy">
        {copied ? 'Copied!' : 'Copy Snippet'}
      </button>
    )
  }
  ```

  _Why this fails:_ Mounting this button with `client:visible` pulls in `@astrojs/react`, `react`, and `react-dom` (~45 KB gzip). On a documentation or code-heavy page with 10 code blocks, shipping the entire React engine just to copy a string to clipboard is severe runtime waste.

- ✅ **Best Practice (Pure native Web Component < 0.5 KB)**:
  ```astro
  <!-- src/components/molecules/CopyButton.astro - Pure native Web Component (< 0.5 KB) -->
  <copy-button data-text={Astro.props.text}>
    <button type="button" class="btn-copy" aria-live="polite">
      <span class="btn-label">Copy Snippet</span>
    </button>
  </copy-button>

  <script>
    class CopyButtonElement extends HTMLElement {
      connectedCallback() {
        const btn = this.querySelector('button');
        const label = this.querySelector('.btn-label');
        const text = this.dataset.text || '';
        btn?.addEventListener('click', async () => {
          await navigator.clipboard.writeText(text);
          if (label) label.textContent = 'Copied!';
          setTimeout(() => { if (label) label.textContent = 'Copy Snippet'; }, 2000);
        });
      }
    }
    if (!customElements.get('copy-button')) {
      customElements.define('copy-button', CopyButtonElement);
    }
  </script>
  ```

#### 2. Accordion & Dropdown Toggles: Heavy Framework vs. Native Details / Custom Element

- ❌ **Bad Practice (Importing full React runtime for simple accordion toggles)**:

  ```astro
  ---
  // src/components/FAQAccordion.astro
  // Anti-pattern: Hydrating React for a simple class/visibility toggle
  import ReactAccordion from './ReactAccordion.jsx';
  const { items } = Astro.props;
  ---
  <!-- Forces React runtime (~45 KB gzip) solely to toggle open/closed state -->
  <ReactAccordion client:load items={items} />
  ```

- ✅ **Best Practice (Native Web Component or Semantic `<details><summary>`)**:
  ```astro
  ---
  // src/components/FAQAccordion.astro
  // Idiomatic: Semantic HTML + lightweight Custom Element for animated accordion
  interface Props {
    items: Array<{ question: string; answer: string }>;
  }
  const { items } = Astro.props;
  ---
  <faq-accordion class="block divide-y divide-border">
    {items.map((item) => (
      <details class="group py-4">
        <summary class="flex cursor-pointer list-none items-center justify-between font-medium">
          <span>{item.question}</span>
          <span class="transition-transform group-open:rotate-180">▾</span>
        </summary>
        <p class="mt-2 text-muted-foreground">{item.answer}</p>
      </details>
    ))}
  </faq-accordion>
  ```

#### 3. Cross-Island State Sharing: React Context Provider vs. Nanostores

- ❌ **Bad Practice (Wrapping independent islands in a React Context Provider at layout root)**:

  ```astro
  <!-- Anti-Pattern: Context provider cannot bridge isolated Astro island DOM roots -->
  <CartProvider client:load>
    <HeaderCartBadge client:load />
    <AddToCartButton client:idle />
  </CartProvider>
  ```

- ✅ **Best Practice (Nanostores module singleton imported into both islands)**:
  ```typescript
  // src/stores/cart.ts - Shared Nanostores singleton (< 1 KB)
  import { atom } from 'nanostores'
  export const $cartCount = atom<number>(0)
  ```
  ```astro
  <!-- Idiomatic: Independent islands subscribe directly to the Nanostores singleton -->
  <HeaderCartBadge client:load />
  <AddToCartButton client:idle />
  ```

#### 4. Large Data Payloads: Monolithic Props vs. Static Slot Projection

- ❌ **Bad Practice (Passing 200KB JSON blog array into a React island prop)**:

  ```astro
  <!-- Anti-Pattern: Serializes entire 200KB article ASTs into inline HTML props attribute -->
  <Feed articles={allArticles} client:visible />
  ```

- ✅ **Best Practice (Passing HTML via Astro `<slot />` or passing minimal ID arrays)**:
  ```astro
  <!-- Idiomatic: Server renders static markup into children; client island receives zero serialized JSON bloat -->
  <Feed client:visible>
    {allArticles.map((article) => (
      <article class="feed-item">
        <h2>{article.data.title}</h2>
        <p>{article.data.excerpt}</p>
      </article>
    ))}
  </Feed>
  ```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/02-zero-js-hydration/14-react-to-native-web-components/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Authoritative Best Practice Rule Mapping**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an authoritative Astro best practice rule in `../../best-practices/`.

You must create and populate the following deliverables in `docs/audits/results/02-zero-js-hydration/14-react-to-native-web-components/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "14-REACT-TO-NATIVE-WEB-COMPONENTS-001",
    "rule_id": "RULE-ID (e.g. ASTRO-BP-0108 / ../../best-practices/01-architecture-and-philosophy/08-client-scripts-over-ui-frameworks.md)",
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
   Execute the turnkey publisher script which automatically verifies the 60,000-char limit, checklist nesting, creates the primary issue, spawns linked sub-issues (up to 20) for critical/high defects, and pushes the JSON deliverables to `origin main`:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
# node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/02-zero-js-hydration/14-react-to-native-web-components/issue-body.md" \
  --title "[Audit - React to Native Web Component Modernization Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/02-zero-js-hydration/14-react-to-native-web-components/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute these verifiable commands to discover candidate micro-islands and evaluate hydration overhead:

1. Scan for forbidden cross-island React Context usage:
   ```bash
   git grep -n "createContext\|useContext" src/
   ```
2. Verify Nanostores presence and cross-island store implementations:
   ```bash
   git grep -n "nanostores" src/
   ```
3. Inspect Astro HTML output for serialized `<astro-island props="...">` payload sizes:
   ```bash
   find dist/ -type f -name "*.html" -exec grep -oP 'props="[^"]{10240,}"' {} + || echo "Clean: No island props >10KB"
   grep -roP '(?<=props=")[^"]*' dist/ | awk '{print length, $0}' | sort -nr | head -n 10
   ```
4. Search for candidate micro-islands using trivial React state:
   ```bash
   grep -rn "useState" src/components/atoms/ src/components/molecules/
   ```
5. Verify zero framework dependencies in `src/scripts/elements/`:
   ```bash
   grep -rn "from 'react'" src/scripts/elements/ || echo "PASS: Zero React dependencies"
   ```
6. Check emitted bundle chunks in `dist/_astro/`: verify that pages using only Web Components contain 0 KB React runtime.
7. Calculate total JavaScript bundle reduction if target micro-islands are migrated to Web Components.
8. Verify that candidate Web Components pass full keyboard accessibility (Enter/Space, Esc, Focus traps).

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/02-zero-js-hydration/14-react-to-native-web-components/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** React to Native Web Component Modernization Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/02-zero-js-hydration/14-react-to-native-web-components/findings.json` (N defects logged)
   - `file://docs/audits/results/02-zero-js-hydration/14-react-to-native-web-components/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/02-zero-js-hydration/14-react-to-native-web-components/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/02-zero-js-hydration/14-react-to-native-web-components/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/02-zero-js-hydration/14-react-to-native-web-components/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
