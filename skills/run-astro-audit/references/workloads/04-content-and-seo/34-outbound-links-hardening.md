# Mission Brief: Outbound Links Hardening & Security Policy Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

The outbound-links plugin (`config/markdown-plugins/outbound-links.mjs`) is the FINAL pass in the HAST pipeline:
It enforces the site's unified outbound-link policy across all Markdown/MDX bodies.

### Authoritative Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`09-rehype-remark-pipeline-performance.md`](../../best-practices/04-content-layer-and-collections/09-rehype-remark-pipeline-performance.md) — Preventing Rehype/Remark AST bottlenecks and memory bloat during large builds (`RULE-ID: 04-content-layer-and-collections/09-rehype-remark-pipeline-performance`).
- [`05-render-entry-content-via-rendered-object.md`](../../best-practices/04-content-layer-and-collections/05-render-entry-content-via-rendered-object.md) — Rendering entry content via `entry.rendered` without recompiling markdown (`RULE-ID: 04-content-layer-and-collections/05-render-entry-content-via-rendered-object`).
- [`08-markdown-vs-mdx-performance.md`](../../best-practices/04-content-layer-and-collections/08-markdown-vs-mdx-performance.md) — Standard Markdown vs MDX compilation performance at scale, prioritizing high-speed Sätteri Rust parsing (`RULE-ID: 04-content-layer-and-collections/08-markdown-vs-mdx-performance`).
- [`15-cross-language-content-linking.md`](../../best-practices/08-i18n-and-localization/15-cross-language-content-linking.md) — Cross-language content linking and slug preservation across external and localized references (`RULE-ID: 08-i18n-and-localization/15-cross-language-content-linking`).

Key Astro Best Practice contracts for link security & MDX component mapping:

1. **Reverse Tabnabbing Prevention**: External links must receive `rel="noopener noreferrer"`. Opening external URLs with `target="_blank"` without `rel="noopener"` allows the target page to manipulate `window.opener.location`, presenting a critical security risk.
2. **Internal Link Purity**: Internal links (`example.com`, `staging.example.com`, relative `/...`, and hash `#...` anchors) must NEVER receive `target="_blank"` or `noopener`, preserving fast internal navigation.
3. **Attribute Merging Integrity**: The plugin must parse existing `rel` tokens (e.g. `sponsored`, `nofollow`, `ugc`) using a `Set` and append `noopener` and `noreferrer` without clobbering existing SEO directives.
4. **Special Scheme Handling**: Non-HTTP schemes like `mailto:` and `tel:` must never receive `target="_blank"`.
5. **MDX Component Mapping**: When passing custom anchor components to MDX via `<Content components={{ a: CustomLink }} />`, components must uphold identical security attributes without forcing client-side React hydration.

Critical files to inspect:

- `config/markdown-plugins/outbound-links.mjs`
- `config/markdown.mjs`
- `tests/int/outbound-links-policy.test.ts`
- `src/components/ui/Link.astro`

## 3.2 Mission Objective

Audit the outbound links hardening pass across all content collections.
Outcome: Prove 100% compliance with external link security standards (zero `target="_blank"` without `rel="noopener noreferrer"`), zero unintended `rel` attributes on internal example.com links, and full preservation of existing `rel` tokens.
Constraints: Read-only audit; check anchor attributes in generated AST and HTML.
Autonomy Grant: You own this mission end-to-end. Trace URL hostname parsers, protocol checks, and attribute setters. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Inspect `outbound-links.mjs`: check domain matching logic (`example.com`, `staging.example.com`, `localhost`, relative paths).
2. Verify that `mailto:` and `tel:` links are handled cleanly without `target="_blank"`.
3. Check `rel` attribute merging: ensure existing `rel` values (e.g. `sponsored`, `nofollow`) are preserved.
4. Audit MDX custom anchor components to ensure they conform to the same outbound policy.
5. Contrast naive manual link tagging with automated Rehype AST link transformations.

### ❌ Bad Practice / Anti-Pattern (Vulnerable Manual Links & Overwritten Rel)

```html
<!-- ❌ Missing rel="noopener noreferrer": Vulnerable to reverse tabnabbing attacks -->
<a href="https://external-resource.com" target="_blank">External Resource</a>

<!-- ❌ Internal links opened in new tab disrupt navigation and break SPA flow -->
<a href="/services/seo" target="_blank" rel="noopener noreferrer">SEO Services</a>

<!-- ❌ Clobbering existing SEO rel tokens (wipes "sponsored" or "nofollow") -->
<!-- Original source: <a href="https://partner.com" rel="sponsored"> -->
<!-- Faulty manual replacement output: -->
<a href="https://partner.com" target="_blank" rel="noopener noreferrer">Partner Resource</a>
```

### ✅ Best Practice / Idiomatic (Automated Rehype Plugin Link Hardening)

```js
// ✅ Idiomatic Rehype plugin transforming AST link elements
import { visit } from 'unist-util-visit'

export function outboundLinksPlugin() {
  const internalDomains = new Set(['example.com', 'staging.example.com', 'localhost'])

  return (tree) => {
    visit(tree, 'element', (node) => {
      if (node.tagName !== 'a' || !node.properties?.href) return

      const href = String(node.properties.href)
      // Skip relative links, anchors, and non-http schemes
      if (
        href.startsWith('/') ||
        href.startsWith('#') ||
        href.startsWith('mailto:') ||
        href.startsWith('tel:')
      ) {
        return
      }

      try {
        const url = new URL(href)
        if (!internalDomains.has(url.hostname)) {
          node.properties.target = '_blank'
          // Safely merge existing rel tokens without overwriting
          const existingRel = String(node.properties.rel || '')
            .split(/\s+/)
            .filter(Boolean)
          const relSet = new Set([...existingRel, 'noopener', 'noreferrer'])
          node.properties.rel = Array.from(relSet).join(' ')
        }
      } catch {
        // Leave unparseable relative URIs untouched
      }
    })
  }
}
```

### ❌ Bad Practice / Anti-Pattern (Unsafe Target on Internal Links)

```html
<!-- ❌ Internal relative links must never open in blank tabs -->
<a href="/tr/seo/" target="_blank" rel="noopener noreferrer">Hizmetlerimiz</a>
```

### ✅ Best Practice / Idiomatic (Hardened Outbound Links & Token Preservation)

```html
<!-- ✅ Secure external link with combined rel tokens -->
<a href="https://external-resource.com" target="_blank" rel="sponsored noopener noreferrer"
  >External Partner Resource</a
>

<!-- ✅ Clean internal link without target or noopener -->
<a href="/services/seo">SEO Services</a>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/04-content-and-seo/34-outbound-links-hardening/`

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

You must create and populate the following deliverables in `docs/audits/results/04-content-and-seo/34-outbound-links-hardening/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps, explicitly linked to authoritative rule IDs:

```json
[
  {
    "id": "34-OUTBOUND-LINKS-HARDENING-001",
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
  --body "docs/audits/results/04-content-and-seo/34-outbound-links-hardening/issue-body.md" \
  --title "[Audit - Outbound Links Hardening & Security Policy Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/04-content-and-seo/34-outbound-links-hardening/findings.json" \
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
2. Run outbound link vitest suite:
   ```bash
   pnpm vitest run tests/int/outbound-links-policy.test.ts
   ```
3. Check built or test HTML output for unhardened external links:
   ```bash
   grep -rn 'target="_blank"' src/ | grep -v 'rel="noopener noreferrer"'
   ```
4. Confirm zero internal `example.com` links carry `target="_blank"`:
   ```bash
   grep -rn 'href="/' src/ | grep 'target="_blank"'
   ```
5. Verify that existing `rel="sponsored"` and `rel="nofollow"` attributes are preserved.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/04-content-and-seo/34-outbound-links-hardening/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Outbound Links Hardening & Security Policy Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/04-content-and-seo/34-outbound-links-hardening/findings.json` (N defects logged with authoritative `rule_id` mapping)
   - `file://docs/audits/results/04-content-and-seo/34-outbound-links-hardening/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/04-content-and-seo/34-outbound-links-hardening/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/04-content-and-seo/34-outbound-links-hardening/issue-body.md` (Published GitHub Issue body, < 60,000 chars, <= 200 items checklist)
   - `file://docs/audits/results/04-content-and-seo/34-outbound-links-hardening/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
