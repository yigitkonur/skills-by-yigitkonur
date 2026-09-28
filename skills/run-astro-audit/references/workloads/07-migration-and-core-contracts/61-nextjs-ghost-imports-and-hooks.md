# Mission Brief: Next.js Ghost Imports & Residual Hooks Audit

## 3.0 Skills / Tools: view_file, run_command, react-doctor.

## 3.1 Context Block

The Astro application was historically migrated from Next.js App/Pages Router to Astro's Multi-Page Architecture (MPA).
During mass code migrations, residual imports from `next/navigation`, `next/router`, `next/link`, `next/image`, or `next/head` and hooks like `useRouter`, `usePathname`, and `useSearchParams` can linger inside React client islands or shared utilities:

- Runtime Failures: In Astro client islands, mounting Next.js router hooks throws fatal runtime exceptions (e.g., `Error: NextRouter was not mounted`) because Next.js router contexts do not exist in Astro.
- Client Bundle Bloat: Importing Next.js packages drags heavy polyfills, history managers, and unnecessary router runtime code into client bundles.
- Web Standards Replacement: Astro returns to native web standards:
  - Routing: Standard HTML `<a>` tags replace `<Link>`, enriched with optional native `data-astro-prefetch`.
  - Server URL Inspection: `.astro` frontmatter accesses `Astro.url` (a standard browser `URL` instance with `.pathname` and `.searchParams`) on the server before emitting HTML.
  - Client Islands: Interactive React components receive route data as props from frontmatter or inspect `window.location.pathname` and `new URLSearchParams(window.location.search)` directly.
  - Images & Head: Native `<Image />` from `astro:assets` replaces `next/image`; standard HTML `<head>` tags in layout templates replace `next/head`.
  - Directives: Next.js `'use client'` directives are redundant and non-functional in Astro, where hydration is controlled at component call sites (`client:load`, `client:visible`, `client:idle`).

### Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`13-replace-next-navigation-with-native-web-standards.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/13-replace-next-navigation-with-native-web-standards.md) — Replacing `next/navigation` hooks (`useRouter`, `usePathname`, `useSearchParams`) and `next/link` with native HTML anchors, `data-astro-prefetch`, and `Astro.url` Web API (`RULE-ID: ASTRO-MIGRATE-13`).
- [`10-replace-react-server-components-with-native-astro.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/10-replace-react-server-components-with-native-astro.md) — Replacing RSC patterns and client hydration overhead with native `.astro` components (`RULE-ID: ASTRO-MIGRATE-10`).
- [`17-replace-use-effect-data-fetching-with-frontmatter-await.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/17-replace-use-effect-data-fetching-with-frontmatter-await.md) — Replacing client-side fetching waterfalls with server frontmatter `await` (`RULE-ID: ASTRO-MIGRATE-17`).
- [`19-migrate-next-image-to-astro-image-assets.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/19-migrate-next-image-to-astro-image-assets.md) — Migrating legacy `next/image` components to native Astro `<Image />` and `<Picture />` assets (`RULE-ID: ASTRO-MIGRATE-19`).
- [`11-eliminate-use-client-spillover-with-scoped-islands.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/11-eliminate-use-client-spillover-with-scoped-islands.md) — Eliminating redundant `'use client'` directives and scoping client islands (`RULE-ID: ASTRO-MIGRATE-11`).

Critical directories to inspect:

- `src/features/`
- `src/components/`
- `src/lib/`
- `src/pages/`

## 3.2 Mission Objective

Perform an exhaustive, read-only audit across all React client islands and TypeScript utilities to detect and catalog any residual Next.js imports, hooks, or component wrappers.
Outcome: Prove zero `next/*` imports exist in production code and provide drop-in replacements using native web standards (`window.location`, `URL`, `Astro.url`, Astro props).
Constraints: Read-only audit; do not edit production code. Catalog exact file paths, line numbers, and replacement snippets.
Autonomy Grant: You own this mission end-to-end. Explore freely, search module graphs, and verify imports directly. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Run `git grep -n "from ['\"]next/" src/` to identify any direct Next.js imports.
2. Search for `useRouter`, `usePathname`, `useSearchParams`, and ensure navigation state is passed via Astro props or standard `window.location`.
3. Check for `next/image` residues: ensure all image components use Astro's `<Image />`, `<Picture />`, or standard `<img>`.
4. Verify that client islands do not import `'use client'` directives unnecessarily.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Residual Next.js Router Hooks vs. Native Web URL Standards (RULE-ID: ASTRO-MIGRATE-13)

##### ❌ Bad Practice / Anti-Pattern: Mounting Next.js navigation hooks inside client components

```tsx
// Next.js: Client component importing Next.js router abstractions
'use client' // Redundant in Astro
import Link from 'next/link'
import { useRouter, usePathname, useSearchParams } from 'next/navigation'
import Image from 'next/image'

export default function SearchHeader() {
  const router = useRouter() // ❌ Crashes in Astro: NextRouter not mounted
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const query = searchParams.get('q') || ''

  return (
    <nav>
      <Link href="/services">Services</Link>
      <p>
        Path: {pathname} | Query: {query}
      </p>
      <button onClick={() => router.push('/contact')}>Contact</button>
    </nav>
  )
}
```

_Why this fails:_ In Astro, Next.js context providers are absent. Invoking `useRouter()`, `usePathname()`, or `useSearchParams()` throws fatal runtime errors (`Error: NextRouter was not mounted`), breaks hydration, and inflates the client bundle with Next.js polyfills.

##### ✅ Best Practice / Idiomatic: Server evaluation in Astro frontmatter or standard window.location in client islands

```astro
---
// Astro Component: Server evaluation with native Web URL standards
// src/components/SearchHeader.astro
const query = Astro.url.searchParams.get('q') || '';
const pathname = Astro.url.pathname;
---
<nav>
  <!-- Standard HTML anchor with native Astro prefetch directive -->
  <a href="/services" data-astro-prefetch="hover">Services</a>
  <p>Path: {pathname} | Query: {query}</p>
  <a href="/contact">Contact</a>
</nav>
```

```tsx
// React Client Island: Using standard Web APIs when client interactivity is required
// src/components/InteractiveSearch.tsx
export default function InteractiveSearch({ initialQuery }: { initialQuery?: string }) {
  const handleNav = (url: string) => {
    // ✅ Standard browser Web API replaces router.push()
    window.location.assign(url)
  }
  return <button onClick={() => handleNav('/contact')}>Contact</button>
}
```

#### Pattern 2: Residual next/image Imports vs. Native Astro `<Image />` (RULE-ID: ASTRO-MIGRATE-19)

##### ❌ Bad Practice / Anti-Pattern: Importing `next/image` in client or shared components

```tsx
// ❌ Anti-Pattern: Next.js image component imported in Astro project
import Image from 'next/image'

export function HeroBanner({ src, alt }: { src: string; alt: string }) {
  return <Image src={src} alt={alt} width={800} height={400} priority />
}
```

##### ✅ Best Practice / Idiomatic: Using native Astro `<Image />` or optimized `<img>`

```astro
---
// ✅ Idiomatic: Native Astro asset optimization
import { Image } from 'astro:assets';
import heroGraphic from '@/assets/hero-graphic.png';
---
<Image
  src={heroGraphic}
  alt="The application Marketing Architecture"
  width={800}
  height={400}
  loading="eager"
  decoding="async"
/>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/07-migration-and-core-contracts/61-nextjs-ghost-imports-and-hooks/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: ASTRO-MIGRATE-13`, `RULE-ID: ASTRO-MIGRATE-10`, `RULE-ID: ASTRO-MIGRATE-19`, `RULE-ID: ASTRO-MIGRATE-11`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/07-migration-and-core-contracts/61-nextjs-ghost-imports-and-hooks/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "61-NEXTJS-GHOST-IMPORTS-AND-HOOKS-001",
    "rule_id": "RULE-ID: ASTRO-MIGRATE-13 (Replace Next.js Navigation with Web Standards)",
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
   Execute the turnkey publisher script using `node scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting, creates the primary issue, spawns linked sub-issues (up to 20) for critical/high defects, and pushes the JSON deliverables to `origin main`:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/07-migration-and-core-contracts/61-nextjs-ghost-imports-and-hooks/issue-body.md" \
  --title "[Audit - Next.js Ghost Imports & Residual Hooks Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/07-migration-and-core-contracts/61-nextjs-ghost-imports-and-hooks/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Run `git grep -n "from ['\"]next/" src/` and confirm zero undetected Next.js imports.
2. Run `git grep -n "useRouter\|usePathname\|useSearchParams" src/` and confirm zero unhandled router hooks.
3. Verify all detected instances have complete drop-in replacement snippets documented in `handoff.md`.
4. Audit Next.js ghost packages and hook residues via terminal commands:

```bash
# 1. Exhaustive search for direct Next.js imports across all source code
git grep -n "from ['\"]next/" src/

# 2. Search for Next.js navigation hook usage in client components
git grep -n "useRouter\|usePathname\|useSearchParams" src/

# 3. Detect redundant 'use client' directives
git grep -n "'use client'" src/

# 4. Search for legacy next/image imports
git grep -n "from ['\"]next/image['\"]" src/

# 5. Search for legacy next/link imports
git grep -n "from ['\"]next/link['\"]" src/

# 6. Confirm 'next' is not present in runtime dependencies
grep -nE '"next":' package.json

# 7. Verify standard HTML anchors in built distribution
grep -rnE '<a\s+href=' dist/ | head -n 5
```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/07-migration-and-core-contracts/61-nextjs-ghost-imports-and-hooks/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Next.js Ghost Imports & Residual Hooks Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/07-migration-and-core-contracts/61-nextjs-ghost-imports-and-hooks/findings.json` (N defects logged)
   - `file://docs/audits/results/07-migration-and-core-contracts/61-nextjs-ghost-imports-and-hooks/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/07-migration-and-core-contracts/61-nextjs-ghost-imports-and-hooks/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/07-migration-and-core-contracts/61-nextjs-ghost-imports-and-hooks/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/07-migration-and-core-contracts/61-nextjs-ghost-imports-and-hooks/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
