# Applicability template — `nextjs-enhancement/01-applicability.md`

Phase 2 output. Orchestrator-personal. Computed by evaluating every gate row in each
`references/detect/<domain>.md` against the facts in `00-recon.md`.

**This file decides how many audit agents get dispatched.** A domain marked
`NOT-APPLICABLE` gets zero agents — that is the whole point of the phase.

## Verdict vocabulary (fixed — five values)

| Verdict | Meaning | Dispatch? |
|---|---|---|
| `APPLICABLE` | Domain applies; standard recipes fit | yes |
| `APPLICABLE-WITH-REMOVAL` | Applies **and** a dead/removed surface is present (probe-confirmed absent from the install while still referenced) | yes — removal task is ≥major |
| `BLOCKED-PARTIAL` | Applies, but some features are gated out by version or a missing prerequisite | yes — agent is told which sub-features to skip |
| `APPLICABLE-CUSTOM` | Applies, but the repo uses a custom/library-free implementation | yes — compare mechanism, never propose a library migration |
| `NOT-APPLICABLE` | Version floor unmet with nothing else in scope, or the repo has no surface for it | **no agent** |

## Template

```markdown
# Applicability — <repo name>

**Computed:** <YYYY-MM-DD> · **Source:** [`00-recon.md`](00-recon.md)
**Installed Next.js:** `<version>` · **React:** `<version>` · **Archetype:** `<archetype>`

## Domain verdicts

| # | Domain | Verdict | Reason | Gated-out features | Agent |
|---|---|---|---|---|---|
| 1 | rendering-strategy-caching | | | | yes/no |
| 2 | image-optimization | | | | |
| 3 | font-script-optimization | | | | |
| 4 | bundle-code-splitting | | | | |
| 5 | navigation-prefetching | | | | |
| 6 | page-transitions-view-transitions | | | | |
| 7 | micro-interactions-react19-fluidity | | | | |
| 8 | dark-light-theme-switching | | | | |
| 9 | instant-i18n-locale-switching | | | | |
| 10 | data-fetching-patterns | | | | |
| 11 | seo-metadata | | | | |
| 12 | build-performance-turbopack | | | | |
| 13 | vercel-platform-deployment | | | | |
| 14 | measurement-regression-guardrails | | | | |

**Dispatching `<N>` audit agents.** Skipped: `<list with one-line reasons>`.

## Gated-out features — the withhold list

Features that exist in this skill's knowledge but must NOT be recommended to this repo.
Being explicit here is what stops a later phase from reintroducing them.

| Feature | Domain | Why withheld | Revisit when |
|---|---|---|---|
| | | probe `absent` / floor unmet / prerequisite missing | e.g. "upgrade to ≥16.3" |

## Prerequisite chain for this repo

Which ordering constraints from `references/gating/priority-matrix.md` actually bind here.
Omit edges whose prerequisite is already satisfied — say so rather than listing them as work.

## Custom implementations

For every `APPLICABLE-CUSTOM` verdict: what the repo does instead of the library, and what
the audit agent should therefore compare against. Frame as mechanism comparison.

## Already satisfied — do not propose

Carried from `00-recon.md`'s "existing good practice". Explicitly out of scope for the audit.

## Confidence

`probe-verified` | `version-inferred` (no `node_modules` — every finding carries the weaker
basis). State which, and why.
```

## How to compute a verdict

For each gate row in the domain's detect file:

1. `installed < introduced` → feature `NOT-APPLICABLE`. Never recommend it.
2. Probe says `absent` → feature `NOT-APPLICABLE`, even if the version suggests otherwise.
   **The probe overrules the version.**
3. Probe says `present` **and** the repo sets a surface the graveyard calls removed →
   do **not** file a removal; the install still accepts it. At most a `minor` upgrade note.
4. Probe says `absent` **and** the repo still references the surface →
   `APPLICABLE-WITH-REMOVAL`.
5. Version and probe both fine, but a prerequisite is missing → `BLOCKED-PARTIAL`; the
   prerequisite becomes its own task and the dependent feature depends on it.
6. Otherwise → `APPLICABLE`.

**Domain rollup:** any row at `APPLICABLE-WITH-REMOVAL` makes the domain
`APPLICABLE-WITH-REMOVAL` (dead code always earns attention). A domain is
`NOT-APPLICABLE` only when *every* row fails **and** the repo has no surface for it.
A library-free implementation of an applicable concern is `APPLICABLE-CUSTOM`, never
`NOT-APPLICABLE`.

## Worked rows

```markdown
| 5 | navigation-prefetching | BLOCKED-PARTIAL | Base `<Link>`/router-cache work applies; every 16.3 Instant-Navigations feature probes `absent` on 16.2.9 | `partialPrefetching`, `export const instant`, `export const prefetch`, Instant Insights, `instant()`, `useOffline` | yes |
| 6 | page-transitions-view-transitions | APPLICABLE | `<ViewTransition>` available via bundled React; `experimental.viewTransition` probes **present** and is set deliberately — no removal task | — | yes |
| 8 | dark-light-theme-switching | APPLICABLE-CUSTOM | No `next-themes`; custom `data-theme` + pre-paint script. Compare mechanism (color-scheme, root-authority under Cache Components) | — | yes |
```

The middle row is the one that matters most: a version-only gate would have emitted a
removal task and broken a working config. The probe prevented it.
