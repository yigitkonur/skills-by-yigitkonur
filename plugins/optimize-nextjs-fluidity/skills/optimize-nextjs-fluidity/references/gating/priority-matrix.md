# Priority matrix — what to do first, and in what order

Two things live here: the **dependency graph** (hard ordering constraints — violating one
produces a broken build or a wasted task) and the **priority tiers** (soft ordering by
effort-to-impact, which differs by project archetype).

Phase 4 reads this file to assign task ordinals. Phase 5 reads it to build fix waves.

## The dependency graph — hard ordering

```
measurement (baseline first — you cannot prove a regression you never measured)
  └─ everything else

vercel-platform-deployment
  └─ remove runtime='edge' / preferredRegion        ← prerequisite
       └─ rendering-strategy-caching (cacheComponents REQUIRES Node.js runtime)
            ├─ navigation-prefetching (partialPrefetching hard-gated on cacheComponents)
            └─ micro-interactions (automatic <Activity> route preservation appears here)

data-fetching-patterns
  ├─ correct parallel/Suspense boundaries → rendering-strategy-caching shells
  ├─ Server Actions / authoritative state → micro-interactions optimistic UI
  └─ cacheable route shape               → navigation-prefetching

instant-i18n-locale-switching (public URL policy)
  └─ seo-metadata (hreflang / canonical / sitemap must match the routing decision)

navigation-prefetching + rendering-strategy-caching (destination is cache-hot)
  └─ page-transitions-view-transitions (morph quality depends on it)
```

Encode each edge as a `Depends on:` field in the task file. Three edges are non-negotiable:

1. **Edge-runtime removal precedes `cacheComponents`.** Cache Components requires the
   Node.js runtime; enabling it with `runtime = 'edge'` routes present fails.
2. **`cacheComponents` precedes Partial Prefetching.** Without it, `next dev`/`next build`
   throw at config validation.
3. **Content availability precedes choreography.** A View Transition added to a route that
   suspends animates into a loading fallback — polished and wrong. Make the destination
   cache-hot first. See `references/gating/conflicts.md` §1.

## Priority tiers by archetype

`C` = content/marketing · `S` = app-heavy SaaS · `E` = e-commerce. The same domain can be
P0 for one archetype and P2 for another — never emit one flat priority list.

| Domain | Impact (CWV) | Impact (fluidity) | Cost | C | S | E |
|---|---|---|---|---|---|---|
| measurement-regression-guardrails | enables all | — | 1 | P0 | P0 | P0 |
| rendering-strategy-caching | high (TTFB/LCP via static shell) | high | 3 brownfield / 2 greenfield | P0 | P0 | P0 |
| image-optimization | high (LCP, CLS) | medium | 1 | P0 | P2 | P0 |
| font-script-optimization | high where fonts/3P are material (CLS, INP) | medium | 1 | P0 | P1 | P1 |
| seo-metadata | medium | low direct | 1 | P0 | P1 | P0 |
| data-fetching-patterns | very high (waterfalls) | very high | 2 | P1 | P0 | P0 |
| bundle-code-splitting | high on client-heavy routes | high (SaaS) | 1–2 | P1 | P0 | P1 |
| micro-interactions-react19-fluidity | high (INP) | very high | 1–2 | P2 | P0 | P0 |
| navigation-prefetching | medium/indirect | very high | 1 (after cacheComponents) | P1 | P0 | P0 |
| vercel-platform-deployment | high when misconfigured (TTFB) | medium | 1–2 | P1 | P0 | P0 |
| dark-light-theme-switching | no numeric CWV evidence | high if theming exists | 1–2 | P1 | P1 | P1 |
| instant-i18n-locale-switching | medium when multi-locale | high for multi-locale | 3 | P0 if multilingual, else P2 | P2 | P0 if multi-market |
| build-performance-turbopack | none at runtime | none for end users | 0–2 | P1 | P1 | P1 |
| page-transitions-view-transitions | no numeric evidence | high visual payoff | 1–2 | P2 | P1 | P1 |

Cost scale: `0` config-only · `1` component/route-level · `2` cross-cutting refactor ·
`3` architectural migration.

## Choosing the archetype

Infer from recon, and state the inference in `01-applicability.md`:

- **Content/marketing** — mostly static routes, a CMS, blog/resource trees, few
  authenticated paths, high `generateMetadata` count.
- **SaaS dashboard** — auth-gated routes, high client-component ratio, many mutations,
  tables/charts/filters, low public-SEO surface.
- **E-commerce** — product/category/search routes, cart and personalization, inventory
  freshness constraints, heavy media.

Mixed repos exist. Pick the dominant archetype for ordering and note the mix; if a repo is
genuinely half content-site and half dashboard, order by the content-site column for public
routes and the SaaS column for the authenticated subtree.

## Ordering rules for Phase 4

1. **Dependency edges beat priority tiers.** A P0 task that depends on a P1 task is
   ordinaled *after* it. Never emit a plan whose first task cannot be executed.
2. **Removals and deprecation cleanups go early.** They are cheap, reversible, and often
   prerequisites (Edge-runtime removal being the clearest case).
3. **Measurement is task 01** whenever the repo has no field instrumentation. Without a
   baseline, no later task can prove it helped.
4. **One-way doors go last within their dependency level** and carry
   `Status: blocked-needs-human` per `references/workflow/safety-rails.md`.
5. **Cluster, don't enumerate.** Twelve call sites of one deprecated prop is one task, not
   twelve. Prefer a task that fixes the shared wrapper over N tasks fixing N callers.

## What would change the ranking

Say so explicitly in `01-applicability.md` when any of these hold:

- Field data already passes p75 for a metric → demote the domain that targets it; promote
  whatever the actual attribution names.
- Nearly every byte is cookie/header-dependent with no shared shell → demote Cache
  Components, promote data-fetching and micro-interactions.
- A webpack-only plugin blocks Turbopack → demote the build domain until it is removed.
- The app is private/single-locale → i18n drops to P2 or out of scope entirely.
- High deploy frequency or long-lived tabs → promote deployment-safety work.
