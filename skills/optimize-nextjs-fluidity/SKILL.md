---
name: optimize-nextjs-fluidity
description: "Use if auditing and optimizing a Next.js App Router repo for performance and fluidity, producing a version-gated task plan the agent then executes."
---

# Optimize Next.js Fluidity

Turn an unknown Next.js repo into a measured, ordered, executed optimization pass —
without ever recommending something the installed version does not support.

This skill profiles the repo, gates every practice against what that install *actually*
accepts, fans out parallel audit agents, writes a dependency-ordered plan as **one
markdown file per task** under `nextjs-enhancement/`, then executes the safe tasks and
verifies each one. One-way doors are prepared for a human, never auto-applied.

The knowledge baseline is Next.js 16.3.0 / React 19.2, verified 2026-08-05. The skill
does not assume the target repo is on that version — that is the entire point.

## When to use

- *"audit this Next.js app for performance"*, *"make the app feel faster / more fluid"*
- *"apply Next.js best practices to this repo"*, *"find and fix our Core Web Vitals problems"*
- *"we're on an older Next — what should we adopt, and what should we not?"*
- *"plan and execute a performance pass, one task per file, so I can review the trail"*
- After a Next.js major upgrade, to find dead flags and newly available features

Do **not** use for:

- *A single known bug.* Fix it inline; this skill's recon and gating overhead pays back
  across many routes and domains, not one component.
- *Generic code review.* Use `run-review`. This skill is performance/fluidity-specific.
- *Visual/CSS bugs.* Use `audit-ui-and-save-files` — that one drives a real browser.
- *Non-Next.js projects, or Pages Router-only apps.* The corpus is App Router-shaped.
  Pages Router surfaces appear only as migration notes.

## Two non-negotiables

### 1. Nothing is recommended without a capability probe

Version arithmetic is not a gate. The skill reads the **installed package** —
`node_modules/next/package.json` and the bundled `config-schema.js` — and asks whether
each config key actually exists on this install. Three failures this prevents, all
observed on a real 16.2.9 repo during design:

- `partialPrefetching` (16.3-only) probes `absent` → **withheld entirely**, even though
  its documented prerequisite `cacheComponents` was satisfied.
- `experimental.viewTransition` is recorded as removed in the 16 line, but probes
  `present` and is deliberately set → **no removal task**, because deleting it would
  have been a breaking change. At most a note to re-check on upgrade.
- `staleTimes` probes `present` and is set → the finding is justified by its *stability
  tier* (experimental, production-discouraged), never by absence.

Full mechanism and the withhold-list discipline: `references/gating/capability-probe.md`.
The graveyard of removed/renamed surfaces and every version floor:
`references/gating/version-matrix.md`.

### 2. Execution is autonomous, but one-way doors are not

There is no mid-run approval prompt. Safety comes from hard rails instead: a task whose
reversibility is `migration-required` is written with `Status: blocked-needs-human` and
its pre-flight checklist, and is reported as prepared work — never executed. Fixes run on
a branch, one commit per task, and a task is `done` only after its own verification
command passes; a failure is reverted and reported with output.

The complete contract — dirty-tree refusal, side-effect bans, the severity/reversibility
auto-apply matrix, and the stop conditions — is `references/workflow/safety-rails.md`.

## The workflow — six phases

Phases 1, 2, 4, and 6 are **orchestrator-personal**. Delegating judgement produces a plan
nobody owns.

### Phase 1 — Recon (personal)

```bash
python3 scripts/recon.py <repo-root>              # profile → markdown
python3 scripts/probe-capabilities.py <repo-root> # the gate primitive
```

Both are read-only. Paste their output into `nextjs-enhancement/00-recon.md`, then add
the judgement calls only a reader can make: archetype, baseline availability, and an
explicit **"existing good practice — do not re-propose"** list. Shape and rules:
`references/artifact/recon-report-template.md`.

### Phase 2 — Applicability gating (personal)

Evaluate every gate row in each `references/detect/*.md` against the recon facts. Produce
`nextjs-enhancement/01-applicability.md`: one verdict per domain
(`APPLICABLE` · `APPLICABLE-WITH-REMOVAL` · `BLOCKED-PARTIAL` · `APPLICABLE-CUSTOM` ·
`NOT-APPLICABLE`) plus the **withhold list** — features this skill knows but must not
recommend here. A `NOT-APPLICABLE` domain gets zero agents. Verdict computation rules and
worked rows: `references/artifact/applicability-template.md`.

Then scaffold the artifact tree and plant the format authority:

```bash
python3 scripts/scaffold-plan.py <repo-root> --apply \
  --domains <applicable,domains> \
  --readme references/artifact/artifact-readme.md
```

Dry-run is the default; `--apply` creates directories and `README.md` only — never
content. The plantable body lives in `references/artifact/artifact-readme.md`.

### Phase 3 — Audit wave (parallel agents)

One `nextjs-perf-auditor` per applicable domain, **dispatched in one message**. These are
read-only Grep/Read agents writing to disjoint folders — no shared lock, so full
parallelism is correct here (unlike browser-driven audits, which must stagger).

Each agent gets: its domain's `references/detect/<domain>.md`, its applicability verdict,
a short repo-profile excerpt, and a write scope of `findings/<domain>/` **only**. Brief
template: `references/subagent-briefs/audit-brief-template.md`. Caps, gates, and
partitioning: `references/subagent-briefs/dispatch-rules.md`.

Finding shape — literal `file:line`, the matched text, the command that found it, and six
cleared false-positive checks: `references/artifact/finding-template.md`.

**Zero findings is a valid result.** A clean domain writes nothing.

### Phase 4 — Synthesize the plan (personal)

Read every finding. Cluster them into tasks — twelve call sites of one deprecated prop is
**one** task against the shared wrapper, not twelve. Order by dependency, not by
discovery: `references/gating/priority-matrix.md` supplies both the hard dependency graph
and the per-archetype priority tiers; `references/gating/composition-recipe.md` supplies
the 14-step blueprint each task maps onto.

Write one file per task (`references/artifact/task-template.md`) plus the index
(`references/artifact/index-template.md`). Every task carries evidence, a recipe pointer,
the exact change, a verification command, a rollback, and its reversibility.

Set reversibility from `references/gating/lockin-reversibility.md`. Check every task
against `references/gating/conflicts.md` — adding a transition to a route that suspends,
or a cookie-read to a cached root, produces changes that look right and behave wrong.
Cost direction for anything touching caching, images, prefetch, or build machines:
`references/gating/cost-model.md`. SEO obligations for anything touching rendering,
routing, or metadata: `references/gating/seo-obligations.md`.

### Phase 5 — Fix waves (parallel agents)

Cluster auto-apply tasks by **shared target files** so no two agents edit the same file.
Dispatch in dependency-respecting waves: prerequisites and cleanups first, architectural
work second, work that assumes the architecture third. Gate between waves by reading task
statuses. Brief: `references/subagent-briefs/fix-brief-template.md`.

Each agent applies only its task's stated change, runs the verification, commits one
task per commit, and on failure reverts and records the output.

### Phase 6 — Verify and reconcile (personal)

```bash
python3 scripts/status-report.py <repo-root>/nextjs-enhancement
```

Read-only; exits non-zero on integrity problems — a `done` task whose dependency is not
`done`, a `migration-required` task marked applied, a `done` task with no verification
section. Then write `nextjs-enhancement/02-completion-report.md`
(`references/artifact/completion-report-template.md`): applied and verified · prepared
but blocked on a human · failed and reverted · withheld and why.

Verification vocabulary and the honesty rules for claiming a rung:
`references/workflow/verification-playbook.md`.

## The 14 domains

Each has a `detect` file (gate table, detection commands, severity rubric, false-positive
filters, pitfall signatures) and a `fix` file (version-annotated recipes with Why /
Verify / Lock-in / Rollback). Full set: `references/detect/*.md` and `references/fix/*.md`.

| Domain | Owns |
|---|---|
| `rendering-strategy-caching` | Cache Components, `use cache` family, static shell + dynamic holes |
| `image-optimization` | `next/image`, sizes/LCP/CLS, config allowlists, `priority` successor |
| `font-script-optimization` | `next/font` self-hosting, `next/script` strategies, third parties |
| `bundle-code-splitting` | client boundaries, `next/dynamic`, package imports, React Compiler |
| `navigation-prefetching` | `<Link>` prefetch, router cache, Instant Navigations, staleness rule |
| `page-transitions-view-transitions` | `<ViewTransition>`, morphs, transition types, browser floors |
| `micro-interactions-react19-fluidity` | `useTransition`, `useOptimistic`, `useDeferredValue`, `<Activity>` |
| `dark-light-theme-switching` | no-flash theming, script vs cookie authority, hydration |
| `instant-i18n-locale-switching` | locale routing, soft switch, static locales, hreflang |
| `data-fetching-patterns` | RSC fetching, waterfall taxonomy, Server Actions, optimistic forms |
| `seo-metadata` | Metadata API, streaming metadata + bots, OG, JSON-LD, crawlability |
| `build-performance-turbopack` | Turbopack, filesystem caches, slow-build diagnosis |
| `vercel-platform-deployment` | Fluid compute, regions, `proxy.ts`, CDN/ISR, Skew Protection |
| `measurement-regression-guardrails` | CWV methodology, instrumentation, CI perf gates |

Domains are library-optional where the ecosystem is: a repo with custom theming or custom
i18n gets `APPLICABLE-CUSTOM`, and the fix files carry custom-implementation variants.
Proposing a library migration for a working custom implementation is a false positive.

## Writing new domain references

The two contracts every domain file obeys:
`references/workflow/detect-file-contract.md` and
`references/workflow/fix-file-contract.md`.

## Footguns

1. **Dispatching before gating.** Agents for `NOT-APPLICABLE` domains produce noise and
   waste the wave. Phase 2 exists to prevent it.
2. **Version arithmetic instead of the probe.** `16.2.9 ≥ 16` is true and useless — the
   feature you want may have shipped in 16.3.
3. **Blind-deleting a graveyard flag.** If the install still accepts it, removal is a
   breaking change. Probe first.
4. **Treating availability as endorsement.** `staleTimes` exists on most installs and is
   still production-discouraged.
5. **One task per grep hit.** Cluster to the shared wrapper, or the fix wave will fight
   itself over one file.
6. **Auto-applying a one-way door.** `cacheComponents`, URL policy, canonical changes —
   prepared, never executed.
7. **Marking done without running the verification.** Reading the diff is not evidence.
8. **Flagging deliberate divergence.** Tuned config with an explanatory comment is
   `informational`. See `references/workflow/false-positives.md`.
9. **Counting comments as usage**, or counting test files, RSS routes, and `ImageResponse`
   contexts against page rules.
10. **Animating before the destination is cache-hot** — the "smooth but wrong" trap.
11. **Recommending a library to a working custom implementation.**
12. **Re-proposing what the repo already does correctly.** Recon lists it; honour the list.

## Scripts

| Script | Mode | Purpose |
|---|---|---|
| `scripts/recon.py` | read-only | Repo profile: versions, shape, config keys, feature counts, library-vs-custom. `--json` available. |
| `scripts/probe-capabilities.py` | read-only | The gate primitive — installed-package config-key availability + withhold list. `--json` available. |
| `scripts/scaffold-plan.py` | **dry-run default** | Creates the artifact tree and plants `README.md`. `--apply` to write; refuses a non-empty tree without `--force`. |
| `scripts/status-report.py` | read-only | Status counts, dependency violations, one-way-door violations. Exits 1 on integrity problems. |

All take the target repo (or plan root) as an explicit argument, so they work from any
working directory.

## Bottom line

Profile the repo, gate every practice against the installed package, audit in parallel,
plan one file per task in dependency order, execute what is safely reversible, prepare
what is not, and verify everything you claim. The `nextjs-enhancement/` folder is the
deliverable — it outlives the session and tells the next reader exactly what was decided
and why.
