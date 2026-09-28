# Mission Brief: Cross-Island State & Nano Stores Communication Audit

## 3.0 Skills / Tools: view_file, run_command, react-doctor.

## 3.1 Context Block

In Astro's island architecture, every client island mounts into an isolated DOM root (`createRoot` or `hydrateRoot`).
Astro best practices mandate strict cross-island state laws:

1. **Never Share State with React Context Across Islands**: React Context Providers in `.astro` layouts cannot cross the static HTML boundary to reach separate islands. Attempting to wrap multiple islands in a `<Provider client:load>` leaves child islands with silent default state or throws runtime `useContext` exceptions.
2. **Use Nanostores for Cross-Island State**: Use micro Nanostores (`atom`, `map` from `nanostores`, subscribed via `@nanostores/react`) exported as ES module singletons. Nanostores adds <1 KB and works seamlessly across React, vanilla TS, and multi-framework islands.
3. **Read Nanostores with `.get()` in Event Handlers**: Do not subscribe components to full re-renders using `useStore($store)` if the component only reads data inside an event handler, form submission, or callback. Always call `$store.get()` directly in handlers.
4. **Prevent SSR Hydration Mismatches from Browser APIs**: Never access `window`, `document`, or `localStorage` during module evaluation or initial component body execution (`useState(localStorage.getItem(...))`). Use deterministic initial state and reconcile inside `useEffect(() => { ... }, [])`.

### Astro Architectural & Best Practice Rules

- **[07-never-share-state-with-react-context-across-islands.md](../../best-practices/02-islands-and-hydration/07-never-share-state-with-react-context-across-islands.md)**: Understanding why React Context cannot bridge island boundaries; isolated island roots cannot communicate via React virtual DOM Context.
- **[08-use-nanostores-for-cross-island-and-cross-framework-state.md](../../best-practices/02-islands-and-hydration/08-use-nanostores-for-cross-island-and-cross-framework-state.md)**: Atomic, zero-dependency state management across islands with Nanostores module singletons (<1 KB).
- **[06-pass-static-children-through-astro-slots-not-props.md](../../best-practices/02-islands-and-hydration/06-pass-static-children-through-astro-slots-not-props.md)**: Pass static markup through Astro slots to avoid JS serialization.
- **[08-client-scripts-over-ui-frameworks.md](../../best-practices/01-architecture-and-philosophy/08-client-scripts-over-ui-frameworks.md)**: Replace heavyweight UI framework components with native Web Components and vanilla scripts.
- **[13-passing-data-to-client-via-dataset.md](../../best-practices/01-architecture-and-philosophy/13-passing-data-to-client-via-dataset.md)**: Pass server data via HTML `data-*` attributes instead of serialized props or unsafe inline scripts.

Critical files to inspect:

- `src/scripts/`
- `src/components/chrome/`
- `src/lib/navigation/client-navigation.ts`
- `src/stores/`

## 3.2 Mission Objective

Audit all cross-island communication and shared state mechanisms across the site.
Outcome: Confirm that cross-island communication is strictly memory-safe, SSR-safe (zero window access before mount), uses Nanostores singletons instead of React Context, reads with `.get()` in handlers, and enforces clean unsubscribe lifecycles.
Constraints: Read-only audit; ensure zero window mutation pollution or hydration mismatches.
Autonomy Grant: You own this mission end-to-end. Trace event listeners, global variables, and reactive stores. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Audit for forbidden cross-island React Context providers and replace with Nanostores.
2. Check Nanostores reading habits in event handlers (avoid unnecessary reactive subscriptions).
3. Check for SSR hydration safety (guard browser globals behind `useEffect` or lifecycle hooks).
4. Verify clean event listener teardowns and store subscription lifecycles.

### ❌ Bad Practice vs. ✅ Best Practice Code Comparisons

#### 1. Cross-Island State Synchronization: React Context vs. Nanostores

- ❌ **Bad Practice (Wrapping independent islands in a React Context Provider at layout root)**:

  ```astro
  ---
  // src/layouts/BaseLayout.astro
  // Anti-Pattern: Provider cannot bridge across isolated island roots
  import { CartProvider } from '../context/CartContext.jsx';
  import HeaderCartBadge from '../components/HeaderCartBadge.jsx';
  import AddToCartButton from '../components/AddToCartButton.jsx';
  ---
  <!-- CartProvider creates an isolated root; HeaderCartBadge receives default state and throws runtime warning -->
  <CartProvider client:load>
    <header>
      <HeaderCartBadge client:load />
    </header>
    <main>
      <AddToCartButton client:idle />
    </main>
  </CartProvider>
  ```

  _Why this fails:_ In Next.js/React SPAs, one root wraps the DOM tree. In Astro, every `client:*` directive creates an isolated `createRoot` enclave. React Context cannot penetrate through the static HTML boundary between `<header>` and `<main>`.

- ✅ **Best Practice (Using Nanostores atom/map imported into both islands)**:
  ```typescript
  // src/stores/cart.ts - Shared ES module singleton (< 1 KB)
  import { atom, map } from 'nanostores'

  export type CartItem = { id: string; name: string; quantity: number }
  export const cartCount = atom<number>(0)
  export const cartItems = map<Record<string, CartItem>>({})

  export function addCartItem(item: Omit<CartItem, 'quantity'>) {
    const current = cartItems.get()
    const existing = current[item.id]
    if (existing) {
      cartItems.setKey(item.id, { ...existing, quantity: existing.quantity + 1 })
    } else {
      cartItems.setKey(item.id, { ...item, quantity: 1 })
    }
    cartCount.set(cartCount.get() + 1)
  }
  ```
  ```astro
  ---
  // src/layouts/BaseLayout.astro - Islands subscribe independently to Nanostores
  import HeaderCartBadge from '../components/HeaderCartBadge.jsx';
  import AddToCartButton from '../components/AddToCartButton.jsx';
  ---
  <header>
    <HeaderCartBadge client:load />
  </header>
  <main>
    <AddToCartButton client:idle />
  </main>
  ```

#### 2. Large Data Payloads: Monolithic Props vs. Static Slot Projection

- ❌ **Bad Practice (Passing 200KB JSON blog array into a React island prop)**:

  ```astro
  <!-- Anti-Pattern: Serializes massive JSON object into HTML inline props -->
  <Feed articles={allArticles} client:visible />
  ```

- ✅ **Best Practice (Passing HTML via Astro `<slot />` or passing minimal ID arrays)**:
  ```astro
  <!-- Idiomatic: Static HTML projected via slot without JSON serialization overhead -->
  <Feed client:visible>
    {allArticles.map((article) => (
      <article class="feed-item">
        <h3>{article.data.title}</h3>
      </article>
    ))}
  </Feed>
  ```

#### 3. Micro-Interaction UI Runtime: Heavy Framework vs. Native Elements

- ❌ **Bad Practice (Importing full React runtime for simple accordion toggles)**:

  ```astro
  <!-- Anti-Pattern: Downloads React reconciler solely to toggle an accordion -->
  <Accordion client:load items={items} />
  ```

- ✅ **Best Practice (Native Web Component or `<details><summary>`)**:
  ```astro
  <!-- Idiomatic: Native Custom Element with 0 KB framework runtime -->
  <faq-accordion>
    <details><summary>Question</summary><p>Answer</p></details>
  </faq-accordion>
  ```

#### 4. Event Handler Reading Habits: Reactive Subscriptions vs. Synchronous `.get()`

- ❌ **Bad Practice (Unnecessary subscription to state in handler-only components)**:

  ```tsx
  // Re-renders AddToCartButton every time ANY item in cart changes!
  import { useStore } from '@nanostores/react'
  import { cartItems, addCartItem } from '../stores/cart'

  export function AddToCartButton({ item }: { item: Item }) {
    const $cart = useStore(cartItems) // Unnecessary reactive subscription!
    return <button onClick={() => addCartItem(item)}>Add</button>
  }
  ```

- ✅ **Best Practice (Read synchronously via `.get()` inside event handlers)**:
  ```tsx
  // Zero re-renders on cart mutation; pure event-driven dispatch
  import { cartItems, addCartItem } from '../stores/cart'

  export function AddToCartButton({ item }: { item: Item }) {
    const handleClick = () => {
      console.log('Current cart total keys:', Object.keys(cartItems.get()).length)
      addCartItem(item)
    }
    return <button onClick={handleClick}>Add</button>
  }
  ```

#### 5. SSR Hydration Safety: Direct Window/Storage vs. Effect Reconciliation

- ❌ **Bad Practice (Accessing localStorage during module or component initial evaluation)**:

  ```tsx
  // Anti-Pattern: Server renders 'light' or throws ReferenceError; client mismatches on 'dark'
  const [theme] = useState(localStorage.getItem('theme') || 'light')
  ```

- ✅ **Best Practice (Deterministic initial SSR state reconciled in useEffect)**:
  ```tsx
  // Idiomatic: Consistent initial SSR state; reconciled after DOM mount
  const [theme, setTheme] = useState('light')
  useEffect(() => {
    const saved = localStorage.getItem('theme')
    if (saved) setTheme(saved)
  }, [])
  ```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/02-zero-js-hydration/16-cross-island-state-nano-stores/`

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

You must create and populate the following deliverables in `docs/audits/results/02-zero-js-hydration/16-cross-island-state-nano-stores/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "16-CROSS-ISLAND-STATE-NANO-STORES-001",
    "rule_id": "RULE-ID (e.g. ASTRO-BP-0208 / ../../best-practices/02-islands-and-hydration/08-use-nanostores-for-cross-island-and-cross-framework-state.md)",
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
  --body "docs/audits/results/02-zero-js-hydration/16-cross-island-state-nano-stores/issue-body.md" \
  --title "[Audit - Cross-Island State & Nano Stores Communication Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/02-zero-js-hydration/16-cross-island-state-nano-stores/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute these runnable terminal commands to discover state leakage and cross-island misconfigurations:

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
4. Audit for forbidden React Context Provider wraps across islands in `.astro` templates:
   ```bash
   git grep -E "<[A-Z][a-zA-Z0-9]*Provider.*client:" src/ || echo "Clean: Zero cross-island React Context providers"
   ```
5. Audit for direct window/localStorage access in components outside useEffect:
   ```bash
   git grep -n -E "localStorage\.(getItem|setItem)" src/components/ | grep -v "useEffect" || echo "Verify: All localStorage access inside useEffect"
   ```
6. Audit for useStore subscriptions in handler-only components:
   ```bash
   git grep -n "useStore(" src/components/
   ```
7. Verify Nanostores package presence and footprint:
   ```bash
   pnpm list nanostores @nanostores/react
   ```
8. Verify that no client script accesses `window` or `document` at module evaluation time.
9. Verify zero memory leak warnings or detached event listener accumulation during automated navigation tests.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/02-zero-js-hydration/16-cross-island-state-nano-stores/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Cross-Island State & Nano Stores Communication Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/02-zero-js-hydration/16-cross-island-state-nano-stores/findings.json` (N defects logged)
   - `file://docs/audits/results/02-zero-js-hydration/16-cross-island-state-nano-stores/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/02-zero-js-hydration/16-cross-island-state-nano-stores/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/02-zero-js-hydration/16-cross-island-state-nano-stores/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/02-zero-js-hydration/16-cross-island-state-nano-stores/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
