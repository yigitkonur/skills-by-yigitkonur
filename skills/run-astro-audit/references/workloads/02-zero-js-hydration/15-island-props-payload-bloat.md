# Mission Brief: Island Props Serialization & HTML Payload Bloat Audit

## 3.0 Skills / Tools: view_file, run_command, react-doctor.

## 3.1 Context Block

When Astro hydrates a React component with `client:*`, it serializes all component props into an inline HTML attribute on `<astro-island props="...">` (or legacy comments).
If an author passes a large object (e.g. an entire Content Layer entry with markdown AST, an array of 500 references, or full static prose) to a client island, that JSON string is duplicated verbatim in the HTML stream, drastically inflating document size and TTFB.
Astro best practices mandate:

1. **Pass Static Content Through Slots, Not Props**: Project static HTML and markdown bodies through Astro `<slot />` or named slots (`slot="name"`) into React `props.children` instead of serializing strings as JSON props.
2. **Minimal Scalar View-Models**: Client islands must only receive minimal scalar primitives, IDs, or trimmed view-models rather than entire unpruned CMS records.

### Astro Architectural & Best Practice Rules

- **[06-pass-static-children-through-astro-slots-not-props.md](../../best-practices/02-islands-and-hydration/06-pass-static-children-through-astro-slots-not-props.md)**: Pass static markup through Astro slots to avoid JS serialization. Large strings and rendered markdown must never be serialized into island `props`.
- **[13-passing-data-to-client-via-dataset.md](../../best-practices/01-architecture-and-philosophy/13-passing-data-to-client-via-dataset.md)**: Pass server data safely via HTML `data-*` attributes and `HTMLElement.dataset` rather than inline scripts or serialized props, preserving CSP compliance and XSS safety.
- **[08-client-scripts-over-ui-frameworks.md](../../best-practices/01-architecture-and-philosophy/08-client-scripts-over-ui-frameworks.md)**: Replace heavy UI framework components with native Web Components and vanilla scripts. Micro-interactions with trivial state (`isOpen`, `isCopied`, active tab) must never ship React's ~45 KB runtime.
- **[07-never-share-state-with-react-context-across-islands.md](../../best-practices/02-islands-and-hydration/07-never-share-state-with-react-context-across-islands.md)**: Never use React Context across separate Astro islands; each island mounts into an isolated root.
- **[08-use-nanostores-for-cross-island-and-cross-framework-state.md](../../best-practices/02-islands-and-hydration/08-use-nanostores-for-cross-island-and-cross-framework-state.md)**: Atomic, zero-dependency state management across islands with Nanostores singletons.

Critical files to inspect:

- `src/pages/compare/[slug].astro` (MatrixPage schema prop)
- `src/features/events/components/EventsRoute.astro` (events list prop)
- `src/features/community/components/DigitalzoneRoute.astro` (videos list prop)
- `src/features/tools/components/matrix/MatrixPage.tsx`
- `dist/` (built HTML output across all routes)

## 3.2 Mission Objective

Inspect all prop payloads passed into hydrated client islands across the entire site.
Outcome: Detect any oversized JSON payloads in emitted HTML, and define prop pruning strategies and slot projections so islands receive only minimal scalar IDs or trimmed view-models.
Constraints: Read-only audit; inspect rendered HTML output artifacts.
Autonomy Grant: You own this mission end-to-end. Measure prop JSON byte sizes and assess serialization overhead. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Search for Astro island prop serialization in `dist/` or dev SSR output and flag any payload exceeding 10 KB.
2. Measure the character length of props passed to `MatrixPage`, `EventsRoute` islands, and `DigitalzoneRoute` islands.
3. Identify instances where static text, article bodies, or lists are passed via props instead of projected through Astro slots.
4. Recommend trimmed interfaces that pass only necessary display fields rather than entire CMS records.

### ❌ Bad Practice vs. ✅ Best Practice Code Comparisons

#### 1. Content Layer & Feed Payloads: Monolithic Props vs. Slot Projection / Minimal IDs

- ❌ **Bad Practice (Passing 200KB JSON blog array into a React island prop)**:

  ```astro
  ---
  // Anti-Pattern: Passes full Content Layer records with body, AST, and metadata
  import { getCollection } from 'astro:content';
  import Feed from '../components/Feed.jsx';
  const allArticles = await getCollection('blog');
  ---
  <!-- Serializes hundreds of KB of JSON into inline HTML props attribute on <astro-island> -->
  <Feed articles={allArticles} client:visible />
  ```

  _Why this fails:_ Astro serializes the entire `allArticles` JavaScript array into the HTML attribute `props="[{\"id\":\"article-1\",\"body\":\"...\"}]"`. The browser downloads this payload twice: once as HTML and once as JSON in the hydration bundle.

- ✅ **Best Practice (Passing HTML via Astro `<slot />` or passing minimal ID arrays)**:
  ```astro
  ---
  // Idiomatic: Server-rendered HTML projected into slot or minimal ID array
  import { getCollection } from 'astro:content';
  import Feed from '../components/Feed.jsx';
  const allArticles = await getCollection('blog');
  const articleIds = allArticles.map((a) => a.id);
  ---
  <!-- Option A: Pure slot projection with zero serialized prop bloat -->
  <Feed client:visible>
    {allArticles.map((article) => (
      <article class="feed-item">
        <h3>{article.data.title}</h3>
        <p>{article.data.summary}</p>
      </article>
    ))}
  </Feed>

  <!-- Option B: Passing minimal scalar IDs if dynamic client filtering is needed -->
  <!-- <Feed articleIds={articleIds} client:visible /> -->
  ```

#### 2. Accordion & Content Wrappers: Serialized Strings vs. Slot Projection

- ❌ **Bad Practice (Serializes fullMarkdownHtml into inline JSON metadata)**:

  ```astro
  ---
  // Anti-pattern: Passing massive markdown HTML string as a prop
  import Accordion from './Accordion.jsx';
  const { title, fullMarkdownHtml } = Astro.props;
  ---
  <Accordion client:idle title={title} contentHtml={fullMarkdownHtml} />
  ```

- ✅ **Best Practice (Projecting static content via Astro slots)**:
  ```astro
  ---
  // Idiomatic: Content remains pure server-rendered HTML inside props.children
  import Accordion from './Accordion.jsx';
  const { title } = Astro.props;
  ---
  <Accordion client:idle>
    <span slot="title">{title}</span>
    <div class="prose"><slot /></div>
  </Accordion>
  ```

#### 3. Cross-Island State Synchronization: React Context vs. Nanostores

- ❌ **Bad Practice (Wrapping independent islands in a React Context Provider at layout root)**:

  ```astro
  <!-- Anti-Pattern: Provider cannot bridge across isolated island roots -->
  <CartProvider client:load>
    <HeaderCartBadge client:load />
    <AddToCartButton client:idle />
  </CartProvider>
  ```

- ✅ **Best Practice (Using Nanostores atom/map imported into both islands)**:
  ```typescript
  // src/stores/cart.ts
  import { atom } from 'nanostores'
  export const $cartCount = atom<number>(0)
  ```
  ```astro
  <!-- Idiomatic: Islands subscribe independently to Nanostores -->
  <HeaderCartBadge client:load />
  <AddToCartButton client:idle />
  ```

#### 4. Micro-Interaction Overhead: Full Framework vs. Native Elements

- ❌ **Bad Practice (Importing full React runtime for simple accordion toggles)**:

  ```astro
  <ReactAccordion client:load items={items} />
  ```

- ✅ **Best Practice (Native Web Component or `<details><summary>`)**:
  ```astro
  <details class="accordion-item">
    <summary class="cursor-pointer font-medium">{title}</summary>
    <div class="mt-2"><slot /></div>
  </details>
  ```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/02-zero-js-hydration/15-island-props-payload-bloat/`

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

You must create and populate the following deliverables in `docs/audits/results/02-zero-js-hydration/15-island-props-payload-bloat/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "15-ISLAND-PROPS-PAYLOAD-BLOAT-001",
    "rule_id": "RULE-ID (e.g. ASTRO-BP-0206 / ../../best-practices/02-islands-and-hydration/06-pass-static-children-through-astro-slots-not-props.md)",
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
  --body "docs/audits/results/02-zero-js-hydration/15-island-props-payload-bloat/issue-body.md" \
  --title "[Audit - Island Props Serialization & HTML Payload Bloat Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/02-zero-js-hydration/15-island-props-payload-bloat/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute these runnable terminal commands to detect oversized prop payloads and state leakage:

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
   # Audit dist/ for bloated astro-island prop JSON serialization (>10KB)
   find dist/ -type f -name "*.html" -exec grep -oP 'props="[^"]{10240,}"' {} + || echo "Clean: No island props >10KB"
   # Extract and sort top 10 largest serialized island props across built pages
   grep -roP '(?<=props=")[^"]*' dist/ | awk '{print length, $0}' | sort -nr | head -n 10
   # Verify specific route island props (e.g. MatrixPage)
   curl -s http://localhost:4321/compare/ | grep -o 'props="[^"]*"' | wc -c
   ```
4. Verify that proposed prop reductions preserve all client interactive capabilities while eliminating duplicated JSON payloads.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/02-zero-js-hydration/15-island-props-payload-bloat/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Island Props Serialization & HTML Payload Bloat Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/02-zero-js-hydration/15-island-props-payload-bloat/findings.json` (N defects logged)
   - `file://docs/audits/results/02-zero-js-hydration/15-island-props-payload-bloat/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/02-zero-js-hydration/15-island-props-payload-bloat/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/02-zero-js-hydration/15-island-props-payload-bloat/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/02-zero-js-hydration/15-island-props-payload-bloat/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
