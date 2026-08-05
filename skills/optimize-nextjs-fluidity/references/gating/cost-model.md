# Cost model — what each change does to the Vercel bill

Rates verified 2026-08-05; **re-check `vercel.com/pricing` before quoting a number in a
task** — pricing pages change without a dated changelog. Use this file to predict the
*direction* and *dominant driver* of a cost change, and to avoid the anti-patterns that
silently burn money.

Client-only fluidity work (View Transitions, React scheduling hooks, font/script
scheduling, theme animation) is essentially bill-neutral. Cost moves when a change alters
**rendering mode, request volume, transfer size, or build duration**.

## Reference rates

| Primitive | Rate | Boundary |
|---|---|---|
| Build — Standard | $0.014/min | 4 vCPU |
| Build — Enhanced | $0.028/min | 8 vCPU |
| Build — Turbo | **$0.105/min** (reduced from $0.126 in Apr 2026) | 30 vCPU |
| Build — Elastic | $0.0035 / CPU-minute | duration × assigned vCPUs |
| ISR writes (`iad1`) | $4.00 / M write units | 1 unit = 8 KB; unchanged revalidation writes nothing |
| ISR reads (`iad1`) | $0.40 / M read units | CDN reads are free; durable-cache reads are billed |
| Fluid invocations | $0.60 / M | plus Active CPU and Provisioned Memory |
| Fluid compute | ≈$0.128/CPU-hr + $0.0106/GB-hr (example region) | **CPU pauses during I/O; memory does not** |
| Image transformations | $0.05–$0.0812 / 1K after included tier | billed on every **MISS and STALE** |
| Image cache reads / writes | $0.40–$0.64 per M / $4.00–$6.40 per M | 8 KB units |
| Speed Insights | $10 / project / month + $0.65 / 10K events after 10K | sampling controls volume |

## Direction by domain

| Domain | Units touched | Direction | Dominant driver |
|---|---|---|---|
| rendering-strategy-caching | build CPU, ISR read/write, Active CPU | mixed — usually ↓ runtime, ↑ build/cache | Static shells avoid functions; prerender + regeneration cost more |
| image-optimization | transformations, image cache, transfer | mixed — ↓ transfer, ↑ optimization billing | Unique `url × width × quality × format` variants |
| navigation-prefetching | invocations, Active CPU, transfer | selective ↓, broad ↑ | Runtime prefetch can invoke the server per visible link |
| data-fetching-patterns | invocations, Active CPU, memory | mixed | Every Server Action is a POST invocation; parallel fetch shortens wall time |
| dark-light-theme-switching | invocations, CDN hit ratio | mixed — script neutral, root cookie ↑ | A root `cookies()` read can turn a static route dynamic |
| instant-i18n-locale-switching | build CPU, static output count | ↑ build, ↓ runtime when static | `generateStaticParams` multiplies pages by locales |
| build-performance-turbopack | build CPU, cache storage | ↓ with cache | Repeat-build cache hits; machine tier costs more per minute |
| vercel-platform-deployment | all | mixed — the largest single lever | CDN/ISR avoidance of functions, region placement, Fluid concurrency |
| measurement-regression-guardrails | Speed Insights events + base fee | ↑, controllable | Per-project fee plus traffic-scaled events |
| font/script, transitions, micro-interactions, bundle, SEO | — | neutral | No dedicated billing primitive |

## Worked scenarios

**Low-traffic marketing site.** 20 builds × 5 min on Standard = `$1.40`. 500 first-request
image variants at the low rate = `$0.025`. Speed Insights at 100K events =
`$10 + (90,000/10,000 × $0.65)` = `$15.85`. **≈$17.28/month** — measurement dominates, and
adding a root theme-cookie read would push free CDN hits toward billed functions.

**High-traffic content site with ISR.** 100K variants × 30 daily regenerations × 3 units =
9M write units = `$36.00`; 10M durable reads × 3 units = 30M = `$12.00`. **≈$48/month.**
If only 5% genuinely change daily, writes fall to 450K units = `$1.80` — a **$34.20**
difference from invalidation scope alone.

**SaaS with heavy Server Actions.** 1M invocations, 0.2s Active CPU, 2s wall, 2 GB:
CPU `55.6 hr × $0.128 = $7.11` + memory `1,111 GB-hr × $0.0106 = $11.78` + invocations
`$0.60` = **≈$19.49/month**. Billing CPU for all 2 wall-clock seconds would overstate CPU
by ~$64 — Active CPU pauses during I/O, but **memory does not**.

## Cost anti-patterns

1. **Broad ISR invalidation.** One content change invalidating article + listing + category
   + locale + sitemap variants multiplies write units. Use narrow, event-driven tags.
2. **Nondeterministic output.** `new Date()` / `Math.random()` in cached output defeats the
   "unchanged content writes nothing" optimization — every revalidation becomes billable.
3. **Oversized fixed build machines.** Turbo is 7.5× Standard per minute; it saves money
   only if elapsed time falls proportionally.
4. **Ignoring the Turbopack production cache.** Repeat builds can be materially faster.
5. **Image variant explosion.** Transformations and writes bill on MISS **and** STALE.
   Excess widths, qualities, formats, loose patterns, and short TTLs multiply variants.
6. **Assuming every image HIT is free.** Shared-global-cache retrieval incurs read units,
   plus transfer and edge requests.
7. **Unscoped viewport/runtime prefetching.** A visible forced prefetch can invoke the
   server per link. Use `prefetch={false}`, hover intent, or route-level disabling.
8. **Root cookie reads for cosmetic theming.** Converts otherwise static pages into
   per-request functions — prefer the pre-paint script for public static content.
9. **Speed Insights at full volume by default.** Set `sampleRate` / `beforeSend`; the
   per-project fee dominates small sites.
10. **Conflating Active CPU with Provisioned Memory.** CPU pauses during I/O; memory bills
    for the whole in-flight lifetime. Model them separately.
11. **Broad `proxy.ts` matching.** Proxy runs before routes, assets, and images — expensive
    work there taxes requests that would otherwise be cheap or cached.
12. **Assuming caches survive deploys.** Cache Components stores are deployment-scoped; a
    new deploy cold-starts prerenders and cache entries. Plan post-deploy origin load.

## Using this file

A task that changes caching, images, prefetch, or build machines must state its expected
cost direction and dominant driver in one line. Never present a modeled figure as a
forecast — say "modeled, assumptions stated". Where the corpus found no per-unit price
(prefetch requests, Cache Components build delta, Server-Action-specific pricing, dynamic
OG generation), say the multiplier is unquantified rather than inventing one.
