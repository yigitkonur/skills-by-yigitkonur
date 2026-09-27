# Mission Brief: Glossary Autolink Engine & Collision Prevention Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

The glossary-autolink plugin (`config/markdown-plugins/glossary-autolink.mjs`) runs AFTER `youtube-embed`:
It walks TEXT nodes in the 4 body-rich roots (`articles`, `guides`, `case studies`, `service details`) and links registered glossary terms to their definition pages.

### Authoritative Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`09-rehype-remark-pipeline-performance.md`](../../best-practices/04-content-layer-and-collections/09-rehype-remark-pipeline-performance.md) — Preventing Rehype/Remark AST bottlenecks and memory bloat during large builds (`RULE-ID: 04-content-layer-and-collections/09-rehype-remark-pipeline-performance`).
- [`05-render-entry-content-via-rendered-object.md`](../../best-practices/04-content-layer-and-collections/05-render-entry-content-via-rendered-object.md) — Rendering entry content via `entry.rendered` without recompiling markdown (`RULE-ID: 04-content-layer-and-collections/05-render-entry-content-via-rendered-object`).
- [`08-markdown-vs-mdx-performance.md`](../../best-practices/04-content-layer-and-collections/08-markdown-vs-mdx-performance.md) — Standard Markdown vs MDX compilation performance at scale, prioritizing high-speed Sätteri Rust parsing (`RULE-ID: 04-content-layer-and-collections/08-markdown-vs-mdx-performance`).
- [`15-cross-language-content-linking.md`](../../best-practices/08-i18n-and-localization/15-cross-language-content-linking.md) — Cross-language content linking and slug preservation across multilingual glossary terms (`RULE-ID: 08-i18n-and-localization/15-cross-language-content-linking`).

Key Astro Best Practice contracts for content transformation & rendering:

1. **Strict Ancestor Exclusion**: It must skip `<a>`, `<pre>`, `<code>`, and `<h1>`–`<h6>` tags. Nesting an `<a>` inside another `<a>` tag creates invalid HTML that browsers reject or improperly restructure, corrupting the DOM tree.
2. **Density Throttling**: It must not link multiple occurrences of the same term within a single paragraph block to avoid visual clutter and aggressive link spam.
3. **Canonical Render Pipeline**: Content entries are compiled using `const { Content } = await render(entry)` imported from `astro:content`. Calling `entry.render()` is deprecated in Astro 5 Content Layer and throws a runtime `TypeError`.
4. **Accessible Link Semantics**: Autolinked terms must carry descriptive `title` and `aria-label` attributes to clarify their glossary context for screen readers.

Critical files to inspect:

- `config/markdown-plugins/glossary-autolink.mjs`
- `src/features/glossary/data/data.ts`
- `config/markdown.mjs`
- `src/pages/blog/[...slug].astro`
- `src/content.config.ts`

## 3.2 Mission Objective

Audit the glossary autolinking engine across long-form editorial content.
Outcome: Prove zero link-in-link collisions, zero autolinking inside code/heading elements, correct `render(entry)` usage, and high-performance compilation even on 10,000-word comprehensive guides.
Constraints: Read-only audit; verify regex match boundaries and text node splits.
Autonomy Grant: You own this mission end-to-end. Trace regex tokenization, anchor nesting prevention, and factory contexts. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `glossary-autolink.mjs`: check how ancestor tags are checked to skip headings, `<pre>`, `<code>`, and existing anchors.
2. Test autolinking with multi-word terms (e.g. "Generative Engine Optimization" vs "SEO").
3. Measure compilation speed impact across 100+ articles.
4. Verify entry compilation: confirm pages import `render` from `astro:content` rather than invoking `entry.render()`.
5. Contrast heavy string replacement loops with linear AST text node walking.

### ❌ Bad Practice / Anti-Pattern (Heavy Regex Replacements Over HTML Strings)

```js
// ❌ Anti-Pattern: Heavy JavaScript regex replacement loops over thousands of HTML strings
// This Next.js / legacy CMS pattern parses raw HTML strings repeatedly, exploding build times
function autolinkHtmlString(htmlString, glossaryTerms) {
  let result = htmlString
  for (const term of glossaryTerms) {
    // Dangerous: Can replace text inside existing <a href="..."> or <code> blocks!
    const regex = new RegExp(`\\b${term.name}\\b`, 'gi')
    result = result.replace(regex, `<a href="/glossary/${term.slug}">${term.name}</a>`)
  }
  return result
}
```

### ✅ Best Practice / Idiomatic (AST-Native Text Walker Before Serialization)

```js
// ✅ Idiomatic Astro: Native MDAST/HAST AST walker traversing text nodes before serialization
import { visit, SKIP } from 'unist-util-visit'

export function glossaryAutolinkPlugin({ termsMap }) {
  return (tree) => {
    // 1. Guard against linking inside forbidden ancestors
    visit(tree, 'element', (node) => {
      if (['a', 'pre', 'code', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(node.tagName)) {
        return SKIP // Exclude node and its entire subtree
      }
    })

    // 2. Perform atomic text node splits on pure text nodes only
    visit(tree, 'text', (node, index, parent) => {
      // Split node and insert semantic <a> elements without regex collision
    })
  }
}
```

### ❌ Bad Practice / Anti-Pattern (Nested Links & Heading Corruption)

```html
<!-- ❌ Invalid HTML: nested anchor tags corrupt DOM parsing -->
<a href="/guides/seo-fundamentals">
  Learn more in our guide to <a href="/glossary/seo">SEO</a> strategies.
</a>

<!-- ❌ Linking inside headings or code blocks degrades readability and copy-paste -->
<h2>What is <a href="/glossary/geo">GEO</a>?</h2>
<code>const <a href="/glossary/api">api</a> = new Client();</code>
```

### ✅ Best Practice / Idiomatic (Ancestor Barrier & Semantic Autolinks)

```html
<!-- ✅ Clean anchor separation with accessible glossary title -->
<p>
  Learn more about modern
  <a
    href="/glossary/generative-engine-optimization"
    class="glossary-term"
    title="Generative Engine Optimization glossary definition"
    aria-label="Generative Engine Optimization definition"
    >Generative Engine Optimization</a
  >
  and how it transforms search visibility.
</p>
```

```astro
---
// Canonical entry compilation via Astro 5 Content Layer
import { getEntry, render } from 'astro:content';

const post = await getEntry('articles', Astro.params.slug);
const { Content } = await render(post);
---
<article>
  <Content />
</article>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/04-content-and-seo/33-glossary-autolink-engine/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: 04-content-layer-and-collections/09-rehype-remark-pipeline-performance`, `RULE-ID: 04-content-layer-and-collections/05-render-entry-content-via-rendered-object`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/04-content-and-seo/33-glossary-autolink-engine/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "33-GLOSSARY-AUTOLINK-ENGINE-001",
    "rule_id": "RULE-ID: 04-content-layer-and-collections/09-rehype-remark-pipeline-performance",
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
   Execute the turnkey publisher script `scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting (<= 200 items, max 3 levels deep), creates the primary issue, spawns linked sub-issues (capped at 20) for critical and high severity defects, and commits/pushes results directly to `main` without PR:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
# node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/04-content-and-seo/33-glossary-autolink-engine/issue-body.md" \
  --title "[Audit - Glossary Autolink Engine & Collision Prevention Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/04-content-and-seo/33-glossary-autolink-engine/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Run AST configuration checks:
   ```bash
   git grep -n "rehype" astro.config.* config/markdown.mjs
   git grep -n "remark" astro.config.* config/markdown.mjs
   ```
2. Verify zero `<a>` tags nested inside other `<a>` tags in rendered HTML.
3. Confirm that glossary links include appropriate `title` and `aria-label` attributes.
4. Run vitest suite for glossary autolinking:
   ```bash
   pnpm vitest run tests/int/glossary-autolink.test.ts
   ```
5. Verify that no components or pages call deprecated `entry.render()`:
   ```bash
   grep -rn "\.render()" src/pages/ src/components/
   ```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/04-content-and-seo/33-glossary-autolink-engine/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Glossary Autolink Engine & Collision Prevention Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/04-content-and-seo/33-glossary-autolink-engine/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/04-content-and-seo/33-glossary-autolink-engine/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/04-content-and-seo/33-glossary-autolink-engine/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/04-content-and-seo/33-glossary-autolink-engine/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/04-content-and-seo/33-glossary-autolink-engine/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
