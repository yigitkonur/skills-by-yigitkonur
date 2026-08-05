# Recon report template — `nextjs-enhancement/00-recon.md`

Phase 1 output. Orchestrator-personal — never delegated. Produced by running
`scripts/recon.py <repo-root>` and `scripts/probe-capabilities.py <repo-root>` and pasting
their output under the headings below, plus the judgement calls only a reader can make
(archetype, custom-vs-library).

Everything downstream cites this file. A fact that is not here may not be assumed later.

```markdown
# Recon — <repo name>

**Captured:** <YYYY-MM-DD> · **Repo root:** `<absolute path>`
**Skill knowledge baseline:** Next.js 16.3.0 (verified 2026-08-05)

## Versions

| What | Installed | Declared | Note |
|---|---|---|---|
| next | `<from node_modules/next/package.json>` | `<from package.json>` | mismatch is itself a finding |
| react / react-dom | | | gates React 19.2 APIs |
| node engine | | | |
| typescript | | | |
| package manager | | | affects node_modules layout |

**Version delta vs knowledge baseline:** <e.g. "installed 16.2.9 is 1 minor behind the
16.3.0 baseline — every 16.3-only surface must be probed before recommendation">

## Capability probe

Paste the probe table verbatim. Every row: `key → present | absent | unresolved`.

| Config key | Probe | Set in repo? | Consequence |
|---|---|---|---|

If the probe returned `unresolved` (no `node_modules`), say so here in bold and stamp
every downstream finding `confidence: version-inferred`.

## Project shape

- Router: App Router | Pages Router | mixed — app dir at `<path>`
- `src/` prefixed: yes/no
- Network boundary: `proxy.ts` | `middleware.ts` | none — at `<path>`
- Deployment: Vercel-linked (`.vercel/` present) | other | unknown
- `vercel.json`: present/absent — notable keys
- Monorepo: yes/no

## Config inventory

Every top-level and `experimental.*` key found in `next.config.*`, with its value. Flag
which are: stable-default · stable-opt-in · experimental · removed/superseded
(per `references/gating/version-matrix.md`).

| Key | Value | Tier | Note |
|---|---|---|---|

## Feature inventory

| Signal | Count | Representative paths |
|---|---|---|
| `.tsx`/`.ts` source files (excl. tests) | | |
| `'use client'` files | | ratio to total; are any at layout level? |
| `next/image` importers | | |
| Raw `<img>` in JSX (excl. tests, RSS, og) | | |
| `next/font` usage | | self-hosted vs external font links |
| External font requests (`fonts.googleapis.com`) | | |
| `next/dynamic` / `React.lazy` | | |
| `'use server'` Server Actions | | |
| `useEffect` + `fetch` (client data fetching) | | legitimate vs page-content |
| `<Suspense>` boundaries | | |
| `loading.tsx` files | | |
| `generateMetadata` / static `metadata` | | |
| `'use cache'` / `cacheLife` / `cacheTag` | | |
| Legacy `export const revalidate\|dynamic\|fetchCache` | | comment-only matches excluded |
| `unstable_cache` | | |
| `runtime = 'edge'` / `preferredRegion` | | Cache Components blocker if present |
| `next/script` + third-party tags | | |
| Sitemap / robots / OG routes | | |

## Library vs custom

| Concern | Implementation | Verdict input |
|---|---|---|
| Theming | `next-themes` \| custom (`<mechanism>`) \| none | drives APPLICABLE-CUSTOM |
| i18n | `next-intl` \| custom (`<mechanism>`) \| none/single-locale | |
| Styling | Tailwind v3 \| v4 \| CSS Modules \| other | v3/v4 changes dark-mode wiring |
| Data layer | RSC-only \| SWR \| TanStack Query \| mixed | |
| CMS | | affects cache-tag strategy |
| Monitoring | Speed Insights \| Sentry \| none | baseline availability |

## Archetype

**<content/marketing | app-heavy SaaS | e-commerce | mixed>** — one paragraph of evidence
(route shapes, auth surface, client ratio, SEO surface). Drives priority ordering in
`references/gating/priority-matrix.md`.

## Baseline

- Field data available? <Speed Insights / CrUX / none>
- Current p75 LCP / INP / CLS if known: <values or "unmeasured">
- Build time / bundle baseline if obtainable: <or "not captured">

If no baseline exists, task 01 is measurement instrumentation, and every later performance
claim is reported as unmeasured.

## Existing good practice — do not re-propose

Explicit list of what the repo already does correctly. This is what prevents the audit
from generating work that is already done.

## Notes and anomalies

Anything surprising: pinned/patched versions, unusual layouts, disabled checks, in-repo
comments explaining a deliberate divergence. These become false-positive guards for the
audit wave.
```

## Rules

1. **Only observed facts.** Every number comes from a command that was run. No estimates.
2. **Never print secret values.** `.env*` file *names* only.
3. **Installed beats declared.** When they disagree, record both and treat installed as truth.
4. **Comment-only matches are excluded from counts** — see
   `references/workflow/false-positives.md` §1.
5. **The "existing good practice" section is mandatory**, even when short.
