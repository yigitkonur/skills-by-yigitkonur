# Mission Brief: React useEffect Data Fetching to Frontmatter Await Audit

## 3.0 Skills / Tools: view_file, run_command, react-doctor.

## 3.1 Context Block

In Next.js SPA/client components, data fetching was commonly executed inside `useEffect(() => { fetch(...) }, [])` hooks or via SWR / TanStack Query client wrappers:

- Architectural Paradigm Shift: In React, components could not be async without React Server Components (RSC) and Suspense boundaries. In Astro's Multi-Page Architecture (MPA), every `.astro` component is inherently async. Direct top-level `await` executes in the frontmatter script fence (`---`).
- Performance & Core Web Vitals Penalties: Executing initial data fetching inside client-side `useEffect` hooks in Astro causes:
  1. Largest Contentful Paint (LCP) Delays: The browser renders an empty shell, waits for client hydration, and initiates a secondary network round-trip back to origin/API before rendering.
  2. Cumulative Layout Shift (CLS): Layout jumps occur when loading spinners or skeletons are abruptly replaced by fetched content.
  3. SEO Degradation: Search engine crawlers (Googlebot, Bingbot) and social parsers frequently do not wait for secondary client fetch promises, leaving critical content un-indexed.
  4. Client Bundle Inflation: Hydration forces the client to download React runtime code, state managers, and component trees merely to render static HTML.
- Best Practice Blueprint: Move initial data retrieval into `.astro` frontmatter (`const data = await fetchData();`), rendering semantic HTML on the server (SSG at build time or SSR on Cloudflare Workers edge) with zero client JavaScript.

### Astro Architectural & Best Practice Rules

Every finding, classification, and recommended refactoring in this audit must strictly align with the authoritative rules in `../../best-practices`:

- [`17-replace-use-effect-data-fetching-with-frontmatter-await.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/17-replace-use-effect-data-fetching-with-frontmatter-await.md) — Replacing client `useEffect` fetching waterfalls with top-level `await` in frontmatter (`RULE-ID: ASTRO-MIGRATE-17`).
- [`10-replace-react-server-components-with-native-astro.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/10-replace-react-server-components-with-native-astro.md) — Replacing RSC patterns and client hydration wrappers with native `.astro` components (`RULE-ID: ASTRO-MIGRATE-10`).
- [`11-eliminate-use-client-spillover-with-scoped-islands.md`](../../best-practices/10-auditing-testing-and-nextjs-migration/11-eliminate-use-client-spillover-with-scoped-islands.md) — Eliminating unnecessary client hydration directives on data-display components (`RULE-ID: ASTRO-MIGRATE-11`).
- [`04-html-chunk-streaming.md`](../../best-practices/01-architecture-and-philosophy/04-html-chunk-streaming.md) — Unblocking edge HTML chunk streaming for server-fetched data (`RULE-ID: ASTRO-ARCH-04`).

Critical directories to inspect:

- `src/components/`
- `src/features/`
- `src/pages/`
- `src/lib/`

## 3.2 Mission Objective

Perform an exhaustive audit of all React client islands to identify client-side data fetching waterfalls (`useEffect` + `fetch` / `axios` / `useSWR` / `useQuery`) that should be executed at build-time or SSR in Astro frontmatter.
Outcome: Catalog all client-side fetching waterfalls and formulate frontmatter data passing blueprints with zero client JS overhead.
Constraints: Read-only audit; do not alter production code.
Autonomy Grant: You own this mission end-to-end. Trace component data flows, analyze API calls, and distinguish between initial page data and authentic user-triggered mutations. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Search for `useEffect` containing `fetch`, `axios`, or async data retrieval in `src/features/` and `src/components/`.
2. Distinguish between authentic interactive mutations (form submissions, filter toggles, live search bars) and initial page data loading.
3. For each initial data fetch, draft a blueprint to move the fetch call to the host `.astro` component frontmatter.
4. Verify that data passed from frontmatter to islands remains minimal and serializable.

### Concrete Bad vs. Best Practice Architectural Patterns

#### Pattern 1: Client useEffect Fetch Waterfall vs. Frontmatter Top-Level Await (RULE-ID: ASTRO-MIGRATE-17)

##### ❌ Bad Practice / Anti-Pattern: Client-side useEffect fetching causing loading spinners and waterfall delays

```tsx
// React Client Component: Delayed client-side fetch waterfall with loading spinner
'use client'
import { useState, useEffect } from 'react'

export default function UserProfileIsland({ userId }: { userId: string }) {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // ❌ Client waterfall: delays LCP, renders empty skeleton, hurts SEO indexing
    fetch(`/api/users/${userId}`)
      .then((res) => res.json())
      .then((data) => {
        setUser(data)
        setLoading(false)
      })
  }, [userId])

  if (loading) return <div class="skeleton">Loading profile...</div>
  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.bio}</p>
    </div>
  )
}
```

_Why this fails:_ Client-side `useEffect()` data fetching blocks initial paint, triggers Cumulative Layout Shift (CLS) when replacing loading skeletons, severely penalizes Largest Contentful Paint (LCP), and leaves search engines and social crawlers with blank HTML shells.

##### ✅ Best Practice / Idiomatic: Direct top-level await in Astro frontmatter with zero client JavaScript

```astro
---
// Astro Component: Direct top-level await in frontmatter; zero client JS or skeletons
// src/components/UserProfile.astro
interface Props {
  userId: string;
}
const { userId } = Astro.props;

// Server-side fetch at SSG build or SSR request time
const response = await fetch(`https://api.internal/users/${userId}`);
const user = await response.json();
---
<div class="user-profile">
  <h1>{user.name}</h1>
  <p>{user.bio}</p>
</div>
```

#### Pattern 2: Hydrating Display Components vs. Native Static Astro Rendering (RULE-ID: ASTRO-MIGRATE-10, RULE-ID: ASTRO-MIGRATE-11)

##### ❌ Bad Practice / Anti-Pattern: Using client hydration on read-only data presentation components

```astro
---
// ❌ Anti-Pattern: Unnecessary client:load pulls React runtime for static data
import MetricCardIsland from '../components/MetricCardIsland';
---
<MetricCardIsland client:load metricId="seo-performance" />
```

##### ✅ Best Practice / Idiomatic: Pure server-rendered Astro component with zero JS bundle footprint

```astro
---
// ✅ Idiomatic: Fully compiled to static HTML on server; 0 KB client JavaScript
import { getMetricData } from '@/lib/metrics';
const data = await getMetricData('seo-performance');
---
<div class="metric-card rounded-[4px] p-6 border border-neutral-200">
  <span class="text-3xl font-bold font-gilroy">{data.value}</span>
  <p class="text-sm text-neutral-600">{data.label}</p>
</div>
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/07-migration-and-core-contracts/62-react-use-effect-fetching-to-frontmatter/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Astro Best Practice Mapping (`RULE-ID`)**:
   - All findings in `findings.json` must map to a specific `RULE-ID` corresponding to an Astro best practice rule in `../../best-practices/` (e.g. `RULE-ID: ASTRO-MIGRATE-17`, `RULE-ID: ASTRO-MIGRATE-10`, `RULE-ID: ASTRO-MIGRATE-11`, `RULE-ID: ASTRO-ARCH-04`).
   - Findings lacking a valid `RULE-ID` will fail audit validation.

You must create and populate the following deliverables in `docs/audits/results/07-migration-and-core-contracts/62-react-use-effect-fetching-to-frontmatter/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "62-REACT-USE-EFFECT-FETCHING-TO-FRONTMATTER-001",
    "rule_id": "RULE-ID: ASTRO-MIGRATE-17 (Replace useEffect Data Fetching with Frontmatter Await)",
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
  --body "docs/audits/results/07-migration-and-core-contracts/62-react-use-effect-fetching-to-frontmatter/issue-body.md" \
  --title "[Audit - React useEffect Data Fetching to Frontmatter Await Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/07-migration-and-core-contracts/62-react-use-effect-fetching-to-frontmatter/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Identify every client island performing initial data fetching in `useEffect`.
2. Provide exact frontmatter refactoring blueprints in `handoff.md` for each identified island.
3. Audit client data fetching patterns via terminal commands:

```bash
# 1. Detect useEffect containing fetch, axios, or async requests in client islands
git grep -rnE "useEffect\s*\(\s*\(\)\s*=>\s*\{[^}]*fetch\(" src/features/ src/components/

# 2. Search for client-side data fetching libraries (SWR, TanStack Query, axios)
git grep -rnE "(useSWR|useQuery|axios\.)" src/

# 3. Detect client hydration directives on components that only render fetched data
git grep -rnE "client:(load|idle|visible)" src/pages/ src/components/

# 4. Search for useEffect hooks across all components and features
git grep -n "useEffect" src/features/ src/components/

# 5. Confirm server-rendered HTML contains fetched content without client JS execution
# curl -s http://localhost:4321/target-route | grep -i "expected-content"
```

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/07-migration-and-core-contracts/62-react-use-effect-fetching-to-frontmatter/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** React useEffect Data Fetching to Frontmatter Await Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/07-migration-and-core-contracts/62-react-use-effect-fetching-to-frontmatter/findings.json` (N defects logged)
   - `file://docs/audits/results/07-migration-and-core-contracts/62-react-use-effect-fetching-to-frontmatter/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/07-migration-and-core-contracts/62-react-use-effect-fetching-to-frontmatter/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/07-migration-and-core-contracts/62-react-use-effect-fetching-to-frontmatter/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/07-migration-and-core-contracts/62-react-use-effect-fetching-to-frontmatter/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
