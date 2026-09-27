# Mission Brief: Sätteri Rust Processor MDAST Pipeline Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

Astro 7 replaced the unified remark JavaScript markdown parser with Sätteri (`@astrojs/markdown-satteri`), a Rust-native engine based on pulldown-cmark and oxc.
The application configures Sätteri in `config/markdown.mjs` with ordered MDAST plugins:

1. `code-line-merge` (`config/markdown-plugins/code-line-merge.mjs`): restructures per-line code chips into fenced code nodes with detected language BEFORE Sätteri highlighting.

### Authoritative Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`08-markdown-vs-mdx-performance.md`](../../best-practices/04-content-layer-and-collections/08-markdown-vs-mdx-performance.md) — Standard Markdown vs MDX compilation performance at scale, prioritizing high-speed Sätteri Rust parsing (`RULE-ID: 04-content-layer-and-collections/08-markdown-vs-mdx-performance`).
- [`09-rehype-remark-pipeline-performance.md`](../../best-practices/04-content-layer-and-collections/09-rehype-remark-pipeline-performance.md) — Preventing Rehype/Remark AST bottlenecks and memory bloat during large builds (`RULE-ID: 04-content-layer-and-collections/09-rehype-remark-pipeline-performance`).
- [`05-render-entry-content-via-rendered-object.md`](../../best-practices/04-content-layer-and-collections/05-render-entry-content-via-rendered-object.md) — Rendering entry content via `entry.rendered` without recompiling markdown (`RULE-ID: 04-content-layer-and-collections/05-render-entry-content-via-rendered-object`).
- [`15-cross-language-content-linking.md`](../../best-practices/08-i18n-and-localization/15-cross-language-content-linking.md) — Cross-language content linking and slug preservation across multilingual articles (`RULE-ID: 08-i18n-and-localization/15-cross-language-content-linking`).

Key Astro Best Practice contracts for Content Layer & Markdown parsing:

1. **Content Layer Migration**: Astro replaces legacy `src/content/config.ts` and `type: 'content'` with `src/content.config.ts` and the built-in `glob()` loader (`import { glob } from 'astro/loaders'`). This decouples content from Vite's module graph, eliminating memory spikes across thousands of markdown entries.
2. **Punctuation Parity**: `smartypants` / `smartPunctuation` must remain strictly disabled in Sätteri config. Enabling smartypants corrupts technical markdown, converting straight quotes to curly quotes and double hyphens (`--`) to en-dashes, breaking copy-paste for code snippets.
3. **AST Node Coalescence**: Adjacent inline code lines within tutorials must merge cleanly into single Shiki-compatible fenced code blocks before syntax highlighting runs.
4. **Precompiled Rendered Output**: Rendered HTML and extracted headings are stored directly in `entry.rendered`. Avoid re-parsing raw markdown strings on static routes.

Critical files to inspect:

- `config/markdown.mjs`
- `config/markdown-plugins/code-line-merge.mjs`
- `src/content.config.ts`
- `src/content/articles/`
- `src/content/guides/`

## 3.2 Mission Objective

Audit the Sätteri MDAST plugin stage for compatibility, syntax highlighting accuracy, and edge-case handling.
Outcome: Verify that code-line-merge cleanly transforms inline code chips into Shiki-compatible code blocks without corrupting indentation or escaping characters, confirm Content Layer collections use modern `glob()` loaders, and ensure zero redundant markdown parsing passes exist across the rendering pipeline.
Constraints: Read-only audit; inspect MDAST node visitor trees.
Autonomy Grant: You own this mission end-to-end. Trace markdown parsing passes, language identifiers, and fenced code blocks. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `code-line-merge.mjs`: verify node traversal logic across code and text AST nodes.
2. Test sample markdown articles containing nested code blocks, bash commands, and JSON payloads.
3. Ensure smartypants / smartPunctuation remains disabled in `config/markdown.mjs` to preserve exact character parity.
4. Verify collections are defined using `glob()` in `src/content.config.ts`, not legacy `Astro.glob()`.
5. Verify template render sites consume precompiled `entry.rendered` or idiomatic `render(entry)` instead of ad-hoc parser runs.

### ❌ Bad Practice / Anti-Pattern (Redundant Parser Calls in Render Loops)

```astro
---
// ❌ Anti-Pattern: Re-running markdown parser on every render loop
import { getEntry } from 'astro:content';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkHtml from 'remark-html';

const post = await getEntry('articles', Astro.params.slug);
// Slower Next.js-style runtime markdown compilation during template evaluation:
const processed = await unified()
  .use(remarkParse)
  .use(remarkHtml)
  .process(post.body);
---
<article set:html={processed.toString()} />
```

### ✅ Best Practice / Idiomatic (Precompiled AST / HTML via entry.rendered)

```astro
---
// ✅ Idiomatic Astro 5/7: Consume precompiled rendered HTML or canonical render(entry)
import { getEntry, render } from 'astro:content';

const post = await getEntry('articles', Astro.params.slug);
if (!post) throw new Error('Article not found');

// Option A: Canonical render component
const { Content, headings } = await render(post);

// Option B: Direct access to precompiled rendered HTML from DataStore
const precompiledHtml = post.rendered?.html;
---
<article>
  {precompiledHtml ? <Fragment set:html={precompiledHtml} /> : <Content />}
</article>
```

### ❌ Bad Practice / Anti-Pattern (Smartypants Corruption & Legacy Globs)

```astro
---
// ❌ Deprecated Astro.glob() lacks Content Layer schema validation and caching
const posts = await Astro.glob('../../content/articles/*.md');
---
```

```js
// ❌ Enabling smartypants corrupts code flags and quotes in technical documentation
export default {
  markdown: {
    smartypants: true, // Converts --flag to –flag (broken CLI commands!)
  },
}
```

### ✅ Best Practice / Idiomatic (Astro Content Layer & Pure MDAST Processing)

```ts
// src/content.config.ts (Astro Content Layer with glob loader)
import { defineCollection, z } from 'astro:content'
import { glob } from 'astro/loaders'

export const collections = {
  articles: defineCollection({
    loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/articles' }),
    schema: ({ image }) =>
      z.object({
        title: z.string(),
        description: z.string(),
        pubDate: z.coerce.date(),
      }),
  }),
}
```

```js
// config/markdown.mjs (Sätteri Rust processor with exact character parity)
export const markdownConfig = {
  smartypants: false, // Preserves exact code characters and CLI flags
  gfm: true,
  remarkPlugins: [codeLineMergePlugin],
}
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/04-content-and-seo/31-satteri-rust-mdast-pipeline/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: 04-content-layer-and-collections/08-markdown-vs-mdx-performance`, `RULE-ID: 04-content-layer-and-collections/09-rehype-remark-pipeline-performance`, `RULE-ID: 04-content-layer-and-collections/05-render-entry-content-via-rendered-object`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/04-content-and-seo/31-satteri-rust-mdast-pipeline/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "31-SATTERI-RUST-MDAST-PIPELINE-001",
    "rule_id": "RULE-ID: 04-content-layer-and-collections/08-markdown-vs-mdx-performance",
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
  --body "docs/audits/results/04-content-and-seo/31-satteri-rust-mdast-pipeline/issue-body.md" \
  --title "[Audit - Sätteri Rust Processor MDAST Pipeline Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/04-content-and-seo/31-satteri-rust-mdast-pipeline/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Run AST configuration checks:
   ```bash
   git grep -n "remark" astro.config.* config/markdown.mjs
   git grep -n "rehype" astro.config.* config/markdown.mjs
   ```
2. Run vitest parity suite:
   ```bash
   pnpm vitest run tests/int/markdown-pipeline-parity.test.ts
   ```
3. Verify smartypants is explicitly disabled in `config/markdown.mjs`:
   ```bash
   grep -rn "smartypants" config/markdown.mjs
   ```
4. Confirm zero deprecated `Astro.glob()` calls remain in content pages:
   ```bash
   grep -rn "Astro\.glob(" src/
   ```
5. Confirm zero redundant unified/remark markdown re-parsing calls exist in components or routes:
   ```bash
   git grep -n "unified().*use(" src/pages/ src/components/
   ```
6. Confirm zero unhighlighted or broken code blocks across rendered article samples.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/04-content-and-seo/31-satteri-rust-mdast-pipeline/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Sätteri Rust Processor MDAST Pipeline Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/04-content-and-seo/31-satteri-rust-mdast-pipeline/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/04-content-and-seo/31-satteri-rust-mdast-pipeline/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/04-content-and-seo/31-satteri-rust-mdast-pipeline/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/04-content-and-seo/31-satteri-rust-mdast-pipeline/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/04-content-and-seo/31-satteri-rust-mdast-pipeline/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
