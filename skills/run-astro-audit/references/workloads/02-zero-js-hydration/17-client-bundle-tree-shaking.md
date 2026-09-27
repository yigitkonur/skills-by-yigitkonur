# Mission Brief: Client Bundle Tree-Shaking & Dead Code Audit

## 3.0 Skills / Tools: view_file, run_command, run-ts-cleanup.

## 3.1 Context Block

Astro leverages Vite (and esbuild/Rolldown under the hood) to bundle client island JavaScript.
Heavy libraries imported into client islands can rapidly balloon bundle sizes if not properly tree-shaken:

1. **Barrel-File Tree-Shaking Penalty**: Importing icons or utilities from root barrel packages (e.g. `import { Search, ChevronDown } from 'lucide-react'` or `lodash`) often bypasses subpath tree-shaking, bundling hundreds of unused exports into client chunks.
2. **Server-Only Module Leakage**: Modules containing heavy server-side dictionaries (like `src/data/assets/image-placeholders.json` at 13 MB) or Node runtimes must NEVER be imported into React client islands.
3. **Dead Code & Unused Island Exports**: Unused props, unmounted subcomponents, and unused utility functions must be purged to minimize JS downloaded by mobile clients.

### Astro Architectural & Best Practice Rules

- **[08-client-scripts-over-ui-frameworks.md](../../best-practices/01-architecture-and-philosophy/08-client-scripts-over-ui-frameworks.md)**: Replacing heavyweight UI framework components with native Web Components and vanilla scripts. Micro-interactions with trivial state (`isOpen`, `isCopied`, active tab) must never ship React's ~45 KB runtime.
- **[13-passing-data-to-client-via-dataset.md](../../best-practices/01-architecture-and-philosophy/13-passing-data-to-client-via-dataset.md)**: Passing server data via HTML `data-*` attributes instead of serialized props or unsafe inline scripts, keeping bundles clean and CSP-compliant.
- **[06-pass-static-children-through-astro-slots-not-props.md](../../best-practices/02-islands-and-hydration/06-pass-static-children-through-astro-slots-not-props.md)**: Passing static markup through Astro slots to avoid JS serialization bloat in client bundles.
- **[07-never-share-state-with-react-context-across-islands.md](../../best-practices/02-islands-and-hydration/07-never-share-state-with-react-context-across-islands.md)**: Understanding why React Context cannot bridge island boundaries; isolated island roots cannot communicate via React virtual DOM Context.
- **[08-use-nanostores-for-cross-island-and-cross-framework-state.md](../../best-practices/02-islands-and-hydration/08-use-nanostores-for-cross-island-and-cross-framework-state.md)**: Atomic, zero-dependency state management across islands with Nanostores module singletons (<1 KB).

Critical files to inspect:

- `package.json` (dependencies vs devDependencies)
- `src/components/molecules/`
- `src/components/common/`
- `src/lib/assets/`
- `dist/_astro/` (emitted client JavaScript chunks)

## 3.2 Mission Objective

Perform a deep tree-shaking and client bundle audit across all client islands.
Outcome: Identify all oversized dependencies, barrel-file imports, server-only module leaks, and unused exported functions bundled into client chunks.
Constraints: Read-only audit; inspect bundle manifests, emitted chunks, and dependency graphs.
Autonomy Grant: You own this mission end-to-end. Inspect chunk boundaries, source maps, and dependency graphs. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Audit client islands for barrel file imports that prevent subpath tree-shaking.
2. Verify strict server-only boundaries: ensure server helpers and heavy data collections are never transitively pulled into `src/components/*.tsx`.
3. Analyze chunk sizes in `dist/_astro/` and identify any island chunk exceeding 50 KB uncompressed.
4. Scan for duplicate runtime dependencies or unpruned framework packages.

### ❌ Bad Practice vs. ✅ Best Practice Code Comparisons

#### 1. Icon & Utility Imports: Root Barrel Packages vs. Deep Subpaths / Bespoke SVGs

- ❌ **Bad Practice (Root Barrel Imports bypassing subpath tree-shaking)**:

  ```tsx
  // src/components/molecules/SearchBar.tsx
  // Anti-Pattern: Pulls massive module tables and hundreds of unused icons into island chunk
  import { ChevronDown, Check, ArrowRight } from 'lucide-react'
  import { debounce } from 'lodash'
  ```

  _Why this fails:_ Bundlers must parse the entire barrel export table. If tree-shaking is imperfect or side-effects are declared in `package.json`, dozens of unused icon SVGs and helper functions end up in the client bundle chunk.

- ✅ **Best Practice (Deep Subpath Imports or Bespoke Inline SVGs)**:
  ```tsx
  // src/components/molecules/SearchBar.tsx
  // Idiomatic: Deep subpath imports allow precise bundler tree-shaking
  import ChevronDown from 'lucide-react/dist/esm/icons/chevron-down'
  import Check from 'lucide-react/dist/esm/icons/check'
  import debounce from 'lodash-es/debounce'
  // Or idiomatic The application inline SVG icons with zero runtime dependency:
  // import { IconChevronDown } from '../atoms/icons';
  ```

#### 2. Cross-Island State Synchronization: React Context vs. Nanostores

- ❌ **Bad Practice (Wrapping independent islands in a React Context Provider at layout root)**:

  ```astro
  <!-- Anti-Pattern: Context provider cannot bridge isolated Astro island DOM roots -->
  <CartProvider client:load>
    <HeaderCartBadge client:load />
    <AddToCartButton client:idle />
  </CartProvider>
  ```

- ✅ **Best Practice (Using Nanostores atom/map imported into both islands)**:
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

#### 3. Large Data Payloads: Monolithic Props vs. Static Slot Projection

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

#### 4. Micro-Interaction UI Runtime: Heavy Framework vs. Native Elements

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

#### 5. Server-Only Module Leakage: Heavy Data Dictionaries in Client Islands

- ❌ **Bad Practice (Importing server-side helpers or data dictionaries into client components)**:

  ```tsx
  // src/components/molecules/ImageCover.tsx
  // Anti-Pattern: Imports 13 MB server placeholder dictionary into client bundle!
  import placeholders from '../../data/assets/image-placeholders.json'
  ```

- ✅ **Best Practice (Strict server-only boundary isolation)**:
  ```astro
  ---
  // src/components/molecules/ImageCover.astro (Server-only)
  import { resolveIllustrationPlaceholder } from '../../lib/assets/image-placeholders';
  const lqip = resolveIllustrationPlaceholder(Astro.props.src);
  ---
  <!-- Pass minimal string via dataset or inline style to client component -->
  <img src={Astro.props.src} style={`background-image: url(${lqip.base64})`} loading="lazy" />
  ```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/02-zero-js-hydration/17-client-bundle-tree-shaking/`

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

You must create and populate the following deliverables in `docs/audits/results/02-zero-js-hydration/17-client-bundle-tree-shaking/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "17-CLIENT-BUNDLE-TREE-SHAKING-001",
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
  --body "docs/audits/results/02-zero-js-hydration/17-client-bundle-tree-shaking/issue-body.md" \
  --title "[Audit - Client Bundle Tree-Shaking & Dead Code Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/02-zero-js-hydration/17-client-bundle-tree-shaking/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute these runnable terminal commands to evaluate tree-shaking efficiency and chunk budgets:

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
4. Audit barrel imports of icon / utility libraries in client components:
   ```bash
   git grep -E "from ['\"](lucide-react|lodash|date-fns)['\"]" src/components/ || echo "Clean: No root barrel imports"
   ```
5. Audit client bundle directory for server-only leaks (e.g. image-placeholders.json):
   ```bash
   grep -ro "image-placeholders" dist/_astro/ || echo "Clean: Zero server placeholder leaks in client chunks"
   ```
6. List top 15 largest client JavaScript chunks in emitted dist/_astro/:
   ```bash
   ls -lh dist/_astro/*.js | sort -k5 -hr | head -n 15
   ```
7. Check for duplicate framework runtimes (e.g. multiple react versions or react + preact conflicts):
   ```bash
   pnpm why react
   ```
8. Prove that all client chunks conform to budget targets (<50 KB gzipped) and zero server-only modules leak into client bundles.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/02-zero-js-hydration/17-client-bundle-tree-shaking/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Client Bundle Tree-Shaking & Dead Code Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/02-zero-js-hydration/17-client-bundle-tree-shaking/findings.json` (N defects logged)
   - `file://docs/audits/results/02-zero-js-hydration/17-client-bundle-tree-shaking/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/02-zero-js-hydration/17-client-bundle-tree-shaking/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/02-zero-js-hydration/17-client-bundle-tree-shaking/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/02-zero-js-hydration/17-client-bundle-tree-shaking/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
