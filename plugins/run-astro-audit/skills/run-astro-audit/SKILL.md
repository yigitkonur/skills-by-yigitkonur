---
name: run-astro-audit
description: "Use if conducting comprehensive Astro audits, running multi-wave subagent remediation, validating AST rules with Astro Sentinel, or managing serial merge queues."
disable-model-invocation: true
---

# Astro Audit & Remediation Framework (run-astro-audit)

An enterprise-grade, end-to-end audit, static AST linting, and autonomous multi-agent remediation framework for modern Astro applications (Astro 4, 5, and 7+).

This framework couples **Astro Sentinel**—a high-speed AST linter powered by `@astrojs/compiler` that deterministically validates 170 architectural best practices across components and schemas—with an autonomous **6-phase remediation lifecycle** that drives issues from initial discovery to isolated worktree fixes, dedicated PR creation, review comment harvesting, and conflict-free serial merge queues.

---

## When to Use

- Conducting a comprehensive, full-repository audit of an Astro codebase across routing, performance, hydration, assets, SEO, and edge runtime boundaries.
- Running deterministic static AST and contract validation via Astro Sentinel before pull requests or releases.
- Partitioning broad architectural overhauls or audit findings into parallel, non-conflicting subagent waves in isolated Git worktrees.
- Creating structured, actionable GitHub issue trees and tracking remediation progress across multiple waves.
- Harvesting external code-review feedback (e.g. Codex, automated bot reviews, team human reviews) and routing remediation back to assigned owners.
- Managing serial rebase and merge queues to avoid merge conflicts across dozens of concurrent workload branches.

Do NOT use when:
- Performing simple, single-file bugfixes that do not require multi-wave or worktree orchestration.
- Reviewing PRs without an active audit or remediation workload (use `run-review` instead).
- Verifying arbitrary general task completion without an Astro architectural scope (use `audit-completion` instead).

---

## Architecture & System Components

```
skills/run-astro-audit/
├── SKILL.md                               # Authoritative routing, lifecycle gates, and CLI contracts
├── README.md                              # Installation and marketplace distribution metadata
├── scripts/                               # Core execution engines and helper automation
│   ├── astro-sentinel-runner.mjs          # Unified AST & contract runner with CLI flags (--strict, --json)
│   ├── astro-sentinel-guard.mjs           # Component AST scanner (@astrojs/compiler AST rules)
│   ├── astro-contract-guard.mjs           # Schema, Content Layer, and cross-file contract guard
│   ├── worktree-manager.sh                # Worktree lifecycle automation (provision, list, prune, sweep)
│   └── review-harvest.sh                  # Pull request review and comment harvester for feedback triage
└── references/
    ├── tooling/                           # Modern static analysis, ESLint & Prettier architecture
    │   └── eslint-and-prettier-alignment.md # 4-layer hierarchy, Flat Config, A11y, Prettier ordering
    ├── audit-taxonomy/                    # Thematic layer classification and scoping rules
    │   └── thematic-layers.md             # 7-layer architecture taxonomy (Layer 01 through Layer 07)
    ├── orchestration/                     # Multi-wave autonomous agent lifecycle protocols
    │   ├── github-issue-reporting.md      # Issue creation contract, naming conventions, and hierarchy
    │   ├── wave-planning-and-worktrees.md # Dependency wave mapping and worktree isolation policy
    │   ├── subagent-mission-prompting.md  # Standalone subagent brief generation engine
    │   ├── review-feedback-ingestion.md   # PR review comment triage and remediation loop
    │   └── serial-merge-and-conflict-queue.md # Conflict-free rebase queue and safe cleanup protocol
    ├── best-practices/                    # 170 atomic Astro architectural rule cards across 10 categories
    │   ├── README.md                      # Rule card index and categorization overview
    │   └── */*.md                         # 10 category directories (01-architecture through 10-auditing)
    └── workloads/                         # 70 workload specifications across 7 thematic layers
        ├── README.md                      # Workload registry and layer mapping index
        └── */*.md                         # 7 layer directories (01-templates through 07-migration)
```

---

## The 6-Phase Operating Loop

### Phase 1: Deterministic AST & Contract Linting (Astro Sentinel)

Before deploying subagents or manual inspection, execute the **Astro Sentinel** linter engine to deterministically catch syntax flaws, deprecated patterns, missing fallback slots, and schema leaks.

```bash
# Full codebase scan with detailed terminal diagnostic report
node scripts/astro-sentinel-runner.mjs

# Strict CI mode (exits with code 1 if errors are detected)
node scripts/astro-sentinel-runner.mjs --strict

# Automated tooling / JSON output mode
node scripts/astro-sentinel-runner.mjs --json

# Run against git staged files only
node scripts/astro-sentinel-runner.mjs --staged

# Isolate a specific rule
node scripts/astro-sentinel-runner.mjs --rule=01-arch/no-virtual-dom-handlers
```

#### Rule Invariant Coverage (Astro Sentinel)

**1. Component AST Guard (`astro-sentinel-guard.mjs`)**:
- `01-arch/no-virtual-dom-handlers`: Prohibits synthetic JSX events (`onClick`, `onChange`) in `.astro` templates. Use native Web Components or `<script>`.
- `01-arch/no-unscoped-global-styles`: Prohibits unscoped `<style is:global>` leaks in leaf components. Encapsulate CSS or relocate to layout root.
- `01-arch/no-process-env`: Prohibits legacy Node `process.env.*` in frontmatter; enforces standard Astro `import.meta.env.*`.
- `02-islands/no-blind-client-load`: Prevents hydration bottlenecking with `client:load` on below-the-fold components; enforces `client:idle` or `client:visible`.
- `02-islands/no-sensitive-props-leak`: Flags sensitive/gated props (`token`, `secret`, `apiKey`, `fileUrl`) passed into client islands serialized to public HTML.
- `02-islands/require-client-only-fallback`: Enforces slotted fallback markup for `client:only` components to prevent layout shift before hydration.
- `06-security/no-set-html-directive`: Guards against unescaped XSS injections via raw `set:html` (exempting structured `application/ld+json` scripts).
- `07-assets/prefer-astro-image`: Recommends `<Image />` or `<Picture />` over native unoptimized `<img>` tags.
- `07-assets/require-image-dimensions`: Mandates explicit `width` and `height` on images to eliminate Cumulative Layout Shift (CLS).
- `07-assets/require-image-alt`: Enforces WCAG 2.2 SC 1.1.1 descriptive `alt` attributes on all image elements.
- `08-i18n/no-hardcoded-locale-routes`: Prohibits hardcoded `/en/` or `/tr/` prefixes; enforces localized route helpers.
- `09-perf/no-blanket-viewport-prefetch`: Flags aggressive `data-astro-prefetch="viewport"` on anchor tags to prevent bandwidth exhaustion.
- `10-migration/no-nextjs-ghost-imports`: Prohibits residual Next.js imports (`next/image`, `next/link`, `next/router`).
- `10-migration/no-raw-css-file-imports`: Flags raw CSS file imports in `.astro` frontmatter.

**2. Contract & Schema Guard (`astro-contract-guard.mjs`)**:
- `04-content/require-zod-date-coercion`: Enforces `z.coerce.date()` over raw `z.date()` in Content Layer schemas.
- `04-content/enforce-entry-id-contract`: Enforces `entry.id` identification contracts and prevents direct `fs.readFileSync` in dynamic routes.
- `04-content/no-deprecated-getentrybyslug`: Flags deprecated `getEntryBySlug` in favor of `getEntry(collection, id)`.
- `06-middleware/static-asset-bypass-integrity`: Verifies `/_astro/` and `/assets/` bypass paths in edge middleware to prevent static chunk stalls.
- `05-edge/node-runtime-import-closure`: Prohibits `node:*` runtime imports in Cloudflare Workers and client surfaces without `nodejs_compat`.
- `03-routing/no-prerender-outside-pages`: Flags `export const prerender` defined outside `src/pages/` route entrypoints.

**3. Suppression Syntax**: Conscious architectural exceptions can be suppressed with inline pragmas:
```astro
---
// @astro-allow 02-islands/no-blind-client-load
---
<!-- @astro-allow 07-assets/prefer-astro-image -->
<img src="/assets/preview.png" alt="Preview" width="800" height="600" />
```

---

### Phase 1b: Production ESLint, Prettier & Quality Tooling Alignment

Astro Sentinel operates as **Layer 1** of a holistic 4-layer static quality architecture. Consult [`references/tooling/eslint-and-prettier-alignment.md`](file:///root/dev/skills-main/skills/run-astro-audit/references/tooling/eslint-and-prettier-alignment.md) for full configuration specs:

| Layer | Engine | Target Scope | Key Focus |
| :--- | :--- | :--- | :--- |
| **Layer 1** | **Astro Sentinel** | `.astro`, `content.config.ts`, `edge/` | AST rules, secret prop leaks, Content Layer schemas, edge runtime purity |
| **Layer 2** | **ESLint Flat Config** | `.astro`, `.ts`, `.tsx`, `.js`, `.mjs` | `eslint-plugin-astro`, `astro/jsx-a11y-recommended` (34 WCAG 2.2 rules), Tailwind utility class order |
| **Layer 3** | **`@astrojs/check`** | TypeScript & Astro templates | Type invariants, props types, Content Layer schema types |
| **Layer 4** | **Prettier Suite** | Entire repo | Astro template formatting, import sorting, Tailwind v4 class sorting |

> [!IMPORTANT]
> **Tailwind v4 Prettier Plugin Ordering Law**: `prettier-plugin-tailwindcss` MUST be the **final plugin** in `.prettierrc.json` (`prettier-plugin-astro` → `@ianvs/prettier-plugin-sort-imports` → `prettier-plugin-tailwindcss`). For Tailwind v4 without `tailwind.config.js`, specify `tailwindStylesheet: "./src/styles/globals.css"`.

---

### Phase 2: Thematic Layer Discovery & Deep Codebase Inspection

When evaluating complex architectural, data flow, or lifecycle patterns beyond static AST checks, map the target scope against the 7 thematic audit layers documented in `references/audit-taxonomy/thematic-layers.md`:

| Layer | Thematic Focus | Core Workloads | Target Systems |
| :--- | :--- | :--- | :--- |
| **Layer 01** | Templates & Routing | 01–10 | Pages, layouts, dynamic routes, pagination, funnel flows |
| **Layer 02** | Zero-JS Hydration & Islands | 11–20 | React/Solid/Svelte islands, hydration directives, bundle tree-shaking |
| **Layer 03** | Media Pipeline, Fonts & LQIP | 21–30 | Image optimization, blur-up placeholders, CLS layout stability, fonts |
| **Layer 04** | Content Layer, AST & Multi-Lang | 31–40 | Content collections, remark/rehype pipelines, i18n commercial parity |
| **Layer 05** | Edge Runtime, Security & QA | 41–50 | Edge worker adapters, cache headers, CSP Level 3, WCAG 2.2 AAA |
| **Layer 06** | Next-Gen Edge, AI & Telemetry | 51–60 | `llms.txt` streaming, content negotiation, view transitions, INP yielding |
| **Layer 07** | Migration & Core Contracts | 61–70 | Framework migration cleanup, Zod date coercion, middleware CPU bypass |

Detailed workload briefs and inspection criteria reside in:
- `references/workloads/*.md`
- `references/workloads/*/*.md`

---

### Phase 3: Issue Reporting & Handoff Ledger

Audit findings must never remain transient chat notes. Persist all verified defects into structured GitHub issues to create an immutable audit trail and enable parallel remediation tracking.

1. **Hierarchy**: One Parent Epic per workload; child sub-issues per verified atomic defect.
2. **Issue Format**: Follow the issue creation contract in `references/orchestration/github-issue-reporting.md`:
   - Title: `[Audit - <Workload Name>]: <Root Symptom>`
   - Sub-issue: `<WorkloadID>-<SLUG>-<NUM>` (e.g. `51-LLMS-TXT-AI-CRAWLER-001`)
   - Severity, reproduction proof, failing file path + line numbers, and expected architectural invariant.

---

### Phase 4: Worktree Provisioning & Wave Planning

Remediation must execute in isolated Git worktrees to prevent dirty working branches and race conditions. Follow `references/orchestration/wave-planning-and-worktrees.md`:

1. **Dependency Analysis**: Group independent workloads into sequential execution waves (Wave 1, Wave 2, etc.).
2. **Concurrency Ceiling**: Strictly cap active subagents at **maximum 10 parallel workers** per sub-wave.
3. **Single Writer Mandate**: Exactly one worktree/subagent owns any given file or directory seam.

```bash
# Provision an isolated worktree for Workload 51
bash scripts/worktree-manager.sh provision 51

# List active audit worktrees
bash scripts/worktree-manager.sh list
```

---

### Phase 5: Parallel Subagent Remediation & Scoped PR Dispatch

Dispatch worker agents into their assigned worktrees using standalone, verbose mission briefs formatted according to `references/orchestration/subagent-mission-prompting.md`.

#### Mandatory Brief Structure:
1. **Context Block**: Repository version, assigned worktree path (`.worktrees/wt-<ID>`), branch name (`fix/audit-<ID>`), parent issue, child sub-issues.
2. **Authoritative References**: Directly link relevant workload briefs (`references/workloads/*/*.md`) and best practice rule cards (`references/best-practices/*/*.md`).
3. **Architectural Invariants & Mission Objective**: Explicit, binary definition of done.
4. **Execution Boundaries**: No production builds during active coding, no server daemons, run only targeted scoped Vitest/ESLint checks.
5. **PR Delivery**: Worker commits all changes to `fix/audit-<ID>`, pushes to origin, and opens a dedicated, non-draft Pull Request via `gh pr create` referencing the parent and child issue numbers.

---

### Phase 6: Code-Review Harvesting & Serial Merge Queue

Follow `references/orchestration/review-feedback-ingestion.md` and `references/orchestration/serial-merge-and-conflict-queue.md`:

#### 1. Review Comment Harvesting
Run the harvester script to collect code-review feedback (e.g. Codex, bots, or human reviewers) on open PRs:
```bash
# Harvest feedback across PRs associated with branch prefix 'fix/audit-'
bash scripts/review-harvest.sh harvest "fix/audit-"
```

#### 2. Parent-Controlled Serial Merge Queue
Never merge parallel branches simultaneously or kill subagent worktrees prematurely:
1. **Inspect & Verify**: Run scoped integration tests in the subagent worktree.
2. **Serial Merge**: Squash-merge or rebase the verified PR branch into `main` one by one.
3. **Rebase Successors**: If successor branches touch overlapping areas, rebase them against updated `main`.
4. **Prune Worktrees**: Only after clean integration into `main`, decommission the worktree:
   ```bash
   bash scripts/worktree-manager.sh prune 51
   ```

---

## Best Practices Reference Directory

170 atomic rule cards provide authoritative guidance across 10 architectural domains:

| Category Directory | Domain Focus | Rule Count |
| :--- | :--- | :---: |
| `01-architecture-and-philosophy` | Multi-Page Architecture, zero-JS baseline, bundle isolation | 18 rules |
| `02-islands-and-hydration` | Hydration directives (`client:*`), island boundaries, state | 16 rules |
| `03-routing-and-pages` | Dynamic routes, ClientRouter SPA lifecycle, trailing slashes | 20 rules |
| `04-content-layer-and-collections` | Astro Content Layer, `entry.id`, collection loaders, Zod | 17 rules |
| `05-data-fetching-and-endpoints` | APIRoutes, Web `Response`, caching, streaming responses | 15 rules |
| `06-middleware-and-auth` | `onRequest`, `context.locals`, fast-path asset bypass, security | 15 rules |
| `07-assets-and-image-pipeline` | `<Image />`, `<Picture />`, WebP/AVIF, LQIP blur-up, fonts | 18 rules |
| `08-i18n-and-localization` | Routing contracts, hreflang, RTL direction, locale parity | 15 rules |
| `09-performance-prefetch-and-transitions` | Speculation Rules API, INP main-thread yielding, BFCache | 16 rules |
| `10-auditing-testing-and-nextjs-migration` | Container API testing, Next.js ghost import eradication | 20 rules |

Reference routing patterns:
- `references/best-practices/*.md`
- `references/best-practices/*/*.md`

---

## Workloads Catalog Directory

70 modular workload briefs across 7 thematic layers:

- **Layer 01 — Templates & Routing**: Workloads 01–10 (`references/workloads/01-templates-routing/*.md`)
- **Layer 02 — Zero-JS Hydration & Islands**: Workloads 11–20 (`references/workloads/02-zero-js-hydration/*.md`)
- **Layer 03 — Media Pipeline, Fonts & LQIP**: Workloads 21–30 (`references/workloads/03-media-pipeline-lqip/*.md`)
- **Layer 04 — Content Layer, AST & Multi-Lang**: Workloads 31–40 (`references/workloads/04-content-and-seo/*.md`)
- **Layer 05 — Edge Runtime, Security & QA**: Workloads 41–50 (`references/workloads/05-edge-workers-and-qa/*.md`)
- **Layer 06 — Next-Gen Edge, AI & Telemetry**: Workloads 51–60 (`references/workloads/06-future-edge-ai-analytics/*.md`)
- **Layer 07 — Migration & Core Contracts**: Workloads 61–70 (`references/workloads/07-migration-and-core-contracts/*.md`)

Reference routing patterns:
- `references/workloads/*.md`
- `references/workloads/*/*.md`
- `references/audit-taxonomy/*.md`
- `references/orchestration/*.md`
