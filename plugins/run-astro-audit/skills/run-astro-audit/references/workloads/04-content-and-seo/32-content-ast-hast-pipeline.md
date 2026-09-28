# Mission Brief: Sätteri Rust Processor HAST Pipeline Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

Following the MDAST stage, Sätteri converts the syntax tree into HAST (HTML AST) and executes an ordered chain of HAST plugins:

1. `raw-segment-parity`: escapes unknown literal tags/comments and repairs raw HTML img sources.
2. `heading-id-parity`: site `heading-<slug>` scheme and legacy anchor preservation.
3. `content-images`: dims/alt/lazy and broken-source repair.
4. `youtube-embed`: responsive iframe wrappers for YouTube video embeds.

### Authoritative Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`09-rehype-remark-pipeline-performance.md`](../../best-practices/04-content-layer-and-collections/09-rehype-remark-pipeline-performance.md) — Preventing Rehype/Remark AST bottlenecks and memory bloat during large builds (`RULE-ID: 04-content-layer-and-collections/09-rehype-remark-pipeline-performance`).
- [`05-render-entry-content-via-rendered-object.md`](../../best-practices/04-content-layer-and-collections/05-render-entry-content-via-rendered-object.md) — Rendering entry content via `entry.rendered` without recompiling markdown (`RULE-ID: 04-content-layer-and-collections/05-render-entry-content-via-rendered-object`).
- [`08-markdown-vs-mdx-performance.md`](../../best-practices/04-content-layer-and-collections/08-markdown-vs-mdx-performance.md) — Standard Markdown vs MDX compilation performance at scale, prioritizing high-speed Sätteri Rust parsing (`RULE-ID: 04-content-layer-and-collections/08-markdown-vs-mdx-performance`).
- [`15-cross-language-content-linking.md`](../../best-practices/08-i18n-and-localization/15-cross-language-content-linking.md) — Cross-language content linking and slug preservation across multilingual articles (`RULE-ID: 08-i18n-and-localization/15-cross-language-content-linking`).

Key Astro Best Practice contracts for HAST transformation:

1. **Zero-CLS Image Optimization**: Frontmatter images must use Astro's `schema: ({ image }) => ...` helper to extract intrinsic dimensions, while `content-images.mjs` must inject explicit `width`, `height`, `loading="lazy"`, and `decoding="async"` attributes onto markdown `<img>` tags to completely eliminate Cumulative Layout Shift (CLS).
2. **Accessible Alt Text Enforcement**: Images must carry descriptive `alt` text. Generic placeholders like "image", "screenshot", or file basenames ("cover.png") violate accessibility standards.
3. **Deterministic Heading IDs**: Duplicate headings within a document (e.g. multiple `## Overview` sections) must receive deterministic sequential suffixes (`heading-overview-1`, `heading-overview-2`) to avoid broken anchor navigation.
4. **HTML Sanitization Purity**: Raw `<script>` tags or unescaped dangerous HTML entities must be sanitized during AST conversion to prevent XSS.

Critical files to inspect:

- `config/markdown.mjs`
- `config/markdown-plugins/raw-segment-parity.mjs`
- `config/markdown-plugins/heading-id-parity.mjs`
- `config/markdown-plugins/content-images.mjs`
- `config/markdown-plugins/youtube-embed.mjs`
- `src/content.config.ts`

## 3.2 Mission Objective

Audit the 4 initial HAST plugins for AST node mutation purity, sanitization, and responsive image attribute generation.
Outcome: Ensure heading IDs are unique and deterministic, images receive intrinsic dimensions to prevent CLS, markdown `<img>` alt-text attributes contain meaningful descriptions rather than generic filenames, and YouTube embeds use privacy-enhanced responsive iframes.
Constraints: Read-only audit; verify HAST node visitors.
Autonomy Grant: You own this mission end-to-end. Inspect element node transformations, attribute injections, and sanitize passes. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `heading-id-parity.mjs`: ensure duplicate headings receive deterministic sequential suffixes (`-1`, `-2`).
2. Inspect `content-images.mjs`: verify that remote and local images receive intrinsic `width` and `height` attributes to prevent CLS.
3. Audit alt-text generation in `content-images.mjs`: flag any images with missing, empty, or placeholder alt text (e.g. "image", "screenshot").
4. Inspect `youtube-embed.mjs`: verify that iframe wrappers use `youtube-nocookie.com` and do not get re-escaped by subsequent HAST passes.
5. Contrast naive regex or runtime DOM replacements with linear HAST AST node manipulation.

### ❌ Bad Practice / Anti-Pattern (Unsized Content Images & Duplicate Heading IDs)

```html
<!-- ❌ Unsized image triggers severe CLS; generic alt text fails accessibility -->
<img src="/assets/diagram.png" alt="screenshot" />

<!-- ❌ Duplicate heading IDs break anchor navigation -->
<h2 id="heading-overview">Overview</h2>
...
<h2 id="heading-overview">Overview</h2>
```

### ✅ Best Practice / Idiomatic (Intrinsic Dimensions, Alt Enforcement & Unique IDs)

```html
<!-- ✅ Explicit dimensions prevent layout shift; descriptive alt text supports screen readers -->
<img
  src="/assets/diagram.png"
  alt="Architecture diagram showing Sätteri HAST plugin pipeline stages"
  width="1200"
  height="630"
  loading="lazy"
  decoding="async"
/>

<!-- ✅ Deterministic suffix ensures valid unique fragment navigation -->
<h2 id="heading-overview">Overview</h2>
...
<h2 id="heading-overview-1">Overview</h2>
```

### ❌ Bad Practice / Anti-Pattern (String Replacement in HAST Loops)

```js
// ❌ Anti-Pattern: String serialization and regex parsing inside AST visitor
import { visit } from 'unist-util-visit'

export function inefficientHastPlugin() {
  return (tree) => {
    visit(tree, 'element', (node) => {
      if (node.tagName === 'iframe') {
        // Unsafe string manipulation breaks AST tree invariants
        node.properties.src = node.properties.src.replace('youtube.com', 'youtube-nocookie.com')
      }
    })
  }
}
```

### ✅ Best Practice / Idiomatic (Direct HAST AST Node Mutation)

```js
// ✅ Idiomatic: Safe, linear HAST property transformation preserving AST integrity
import { visit } from 'unist-util-visit'

export function idiomaticHastPlugin() {
  return (tree) => {
    visit(tree, 'element', (node) => {
      if (node.tagName === 'iframe' && typeof node.properties?.src === 'string') {
        try {
          const url = new URL(node.properties.src)
          if (url.hostname.includes('youtube.com')) {
            url.hostname = 'www.youtube-nocookie.com'
            node.properties.src = url.toString()
          }
        } catch {
          // Graceful fallback on relative or malformed URIs
        }
      }
    })
  }
}
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/04-content-and-seo/32-satteri-rust-hast-pipeline/`

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

You must create and populate the following deliverables in `docs/audits/results/04-content-and-seo/32-satteri-rust-hast-pipeline/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "32-SATTERI-RUST-HAST-PIPELINE-001",
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
  --body "docs/audits/results/04-content-and-seo/32-satteri-rust-hast-pipeline/issue-body.md" \
  --title "[Audit - Sätteri Rust Processor HAST Pipeline Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/04-content-and-seo/32-satteri-rust-hast-pipeline/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

Execute the following verification battery to validate compliance across all audit criteria:

1. Run AST plugin configuration audits:
   ```bash
   git grep -n "rehype" astro.config.* config/markdown.mjs
   git grep -n "remark" astro.config.* config/markdown.mjs
   ```
2. Verify that all article headings have matching `id="heading-..."` attributes with zero duplicate IDs across each page.
3. Prove that no raw, unescaped HTML `<script>` tags survive into emitted HTML:
   ```bash
   grep -rn "<script" config/markdown-plugins/
   ```
4. Run HAST image and heading parity tests:
   ```bash
   pnpm vitest run tests/int/heading-id-parity.test.ts
   pnpm vitest run tests/int/content-images.test.ts
   ```
5. Verify that content images render with explicit `width` and `height` attributes to guarantee 0 CLS.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/04-content-and-seo/32-satteri-rust-hast-pipeline/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Sätteri Rust Processor HAST Pipeline Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/04-content-and-seo/32-satteri-rust-hast-pipeline/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/04-content-and-seo/32-satteri-rust-hast-pipeline/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/04-content-and-seo/32-satteri-rust-hast-pipeline/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/04-content-and-seo/32-satteri-rust-hast-pipeline/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/04-content-and-seo/32-satteri-rust-hast-pipeline/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
