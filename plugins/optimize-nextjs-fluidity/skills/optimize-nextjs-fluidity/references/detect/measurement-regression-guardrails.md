# Detect: measurement-regression-guardrails

**Corpus lineage:** measurement-regression-guardrails/00-overview-and-inventory.md,
01-measurement-methodology.md, 02-field-instrumentation-tools.md,
03-when-to-use-and-cwv-triage.md, 07-pitfalls-and-anti-patterns.md,
08-version-support-and-practitioners.md

This domain proves every other domain's claims. It fixes nothing itself — it makes
outcomes observable and stops a later refactor from silently undoing them. When a repo has
no field instrumentation, **this becomes task 01** and every other task's performance
claim is reported as unmeasured until it lands.

## Applicability gate

Core Web Vitals and the `web-vitals` library have no Next.js version floor. The 16.3
navigation tooling does — probe before recommending any of it
(`references/gating/capability-probe.md`).

| Feature / config key | Introduced | Requires | Removed-in | Gate rule |
|---|---|---|---|---|
| CWV set: LCP ≤2.5s, INP ≤200ms, CLS ≤0.1 (all p75) | n/a — web standard | none | n/a | Always applicable. These are the acceptance thresholds every other domain's claims are measured against. |
| CrUX (field dataset) | n/a | public traffic volume | n/a | Applicable only when the site has enough public traffic to appear in CrUX. Authenticated/low-volume apps get no CrUX row — say so rather than reporting "no data" as a failure. |
| `useReportWebVitals` (`next/web-vitals`) | Long-stable | must live in a Client Component | n/a | Always applicable. Docs recommend a dedicated component imported by the root layout so the client boundary stays confined to it. |
| Next.js custom metrics (hydration / route-change / render) | Pages Router | — | n/a | **Documented on the Pages Router page only.** Do not promise these on App Router — absence there is not a bug. |
| `web-vitals` v5 + `web-vitals/attribution` | Library, independent of Next.js | npm install | n/a | Always applicable. Use when the framework hook is insufficient (element-level attribution for debugging). |
| `@vercel/speed-insights` v2 (`<SpeedInsights />`) | Platform product | Vercel project; `./next` export path | n/a | Applicable on Vercel. Availability ≠ free: $10/project/month base plus event-scaled cost — see `references/gating/cost-model.md`. |
| `sampleRate` / `beforeSend` / `route` (Speed Insights) | v2 package | Speed Insights installed | n/a | Applicable wherever Speed Insights is. Absence at high traffic is a cost finding, not a correctness one. |
| Vercel Web Analytics | Platform product | Vercel project | n/a | Distinct product — page views and events, **not** vitals. Never treat it as CWV coverage. |
| Instant Insights / Navigation Inspector | **16.3.0** | `cacheComponents: true` | n/a | Probe. `absent` → NOT APPLICABLE; emit no task. An upgrade is its own separate task, never smuggled into a measurement task. |
| `instant()` (`@next/playwright`) | **16.3.0** | separate package + `@playwright/test` | n/a | Probe the Next version. `absent` → NOT APPLICABLE. On ≥16.3 it is the only first-class soft-navigation regression check. |
| `experimental.exposeTestingApiInProductionBuild` | **16.3.0** | for `instant()` against `next start` | n/a | Experimental. Applicable only for CI/test builds; **enabled in a production deploy is a finding**. |
| Lighthouse / Lighthouse CI | External tooling | production-like build | n/a | Always applicable. Must audit a production build — auditing `next dev` produces numbers that mean nothing. |

## Detection commands

```bash
# 1. Any field instrumentation at all? Zero hits = the highest-value finding in this domain.
rg -n "useReportWebVitals|@vercel/speed-insights|from ['\"]web-vitals" \
  -g '!**/node_modules/**' -g '!**/*.test.*' <target-repo-root>
```

```bash
# 2. Speed Insights present but unsampled (cost risk at traffic)
rg -n "SpeedInsights" -A3 -g '!**/node_modules/**' <target-repo-root> | rg -n "sampleRate|beforeSend" || echo "no sampling configured"
```

```bash
# 3. useReportWebVitals hook placement — must be a Client Component, ideally a dedicated one
rg -ln "useReportWebVitals" -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 4. Production exposure of the testing API (finding if set outside CI)
rg -n "exposeTestingApiInProductionBuild" next.config.* <target-repo-root>
```

```bash
# 5. Any CI performance gate at all
rg -n "lighthouse|lhci|@next/playwright|instant\(" \
  -g '!**/node_modules/**' .github/ package.json <target-repo-root> 2>/dev/null
```

```bash
# 6. Lighthouse pointed at a dev server (numbers are meaningless)
rg -n "localhost:3000|next dev" .lighthouserc* lighthouserc* .github/workflows/ 2>/dev/null
```

## Domain severity rubric

- **critical** — `exposeTestingApiInProductionBuild` enabled in a production deploy
  (exposes a testing surface to real users).
- **major** — no field instrumentation of any kind on a production site, so no task in this
  run can be verified at the measured rung; a CI perf gate that audits `next dev`.
- **minor** — Speed Insights unsampled at meaningful traffic (cost); `useReportWebVitals`
  placed in a broad client boundary instead of a dedicated component; no soft-navigation
  regression test on a repo where client navigation dominates.
- **informational** — CrUX absent because the app is authenticated/low-traffic; Web
  Analytics present without Speed Insights (a deliberate product choice).

## False-positive filters

- **Web Analytics is not Speed Insights.** A repo with `@vercel/analytics` still has no
  vitals coverage — but do not report it as "analytics missing".
- **No CrUX data is not a defect** for authenticated or low-traffic apps. Report the
  population limit, not a failure.
- **A repo measuring via a third-party RUM** (Sentry performance, Datadog, custom beacon)
  already has field data. Confirm what it captures before filing "no instrumentation".
- **Sampling below 100% is correct at scale**, not under-measurement.
- Comments and test files are excluded, per `references/workflow/false-positives.md`.
- Do not file a finding proposing Instant Insights or `instant()` on an install where the
  probe says they do not exist.

## Evidence format

Per `references/artifact/finding-template.md`. For this domain, state explicitly whether
the repo can currently verify a performance claim at the **measured** rung — that single
fact determines whether the whole run's other tasks can be verified numerically or only
behaviourally (`references/workflow/verification-playbook.md`).

## Pitfall signatures

| Failure signature | Cause | Fix direction | Recipe section |
|---|---|---|---|
| Lab score is green, field p75 is bad | One controlled path ≠ real device/network/geography mix; cold caches, conditional third parties, different LCP candidates | Instrument the field first, then route by attribution | Field instrumentation wiring |
| CWV all pass, navigation still feels slow | Hard-navigation CWV does not measure soft navigations | Add soft-navigation checks (Instant Insights / `instant()` on 16.3+) | Navigation regression test |
| Metric moved but nobody can prove which change did it | No baseline captured before the change | Capture the baseline before any optimization task runs | Baseline → change → verify → gate |
| Speed Insights bill grows with traffic | Unsampled event collection | `sampleRate` / `beforeSend` / route allowlist | Speed Insights setup with cost control |
| CI "perf gate" never fails | Auditing `next dev`, or thresholds set below current values | Audit a production build; set assertions from the real baseline | Lighthouse CI gate |
| Green dashboard, broken crawler output | RUM measures humans, not bots | Crawlability is a separate probe entirely | see `references/gating/seo-obligations.md` |

## CWV triage — symptom → cause → owning domain

The routing column is a corpus-local judgement (**inference**); the metric mechanisms are
evidence-backed. Route a fix to exactly **one** owning domain.

| Symptom | Signal to inspect | Likely Next.js-specific causes | Route to |
|---|---|---|---|
| Bad LCP | LCP element from field attribution | late/unoptimized hero image; blocking font; slow TTFB; client-only hero; competing prefetch/script requests | `image-optimization` · `font-script-optimization` · `rendering-strategy-caching` · `bundle-code-splitting` |
| Bad INP | interacted element + interaction type | large client bundle/hydration work; long event handlers; synchronous state updates; third-party scripts | `bundle-code-splitting` · `micro-interactions-react19-fluidity` · `font-script-optimization` |
| Bad CLS | shifting elements from attribution | images without reserved space; font swap mismatch; injected banners; theme/locale hydration; transition wrappers | `image-optimization` · `font-script-optimization` · `dark-light-theme-switching` · `page-transitions-view-transitions` |
| Good lab, bad field | compare route/device/geography | conditional third parties; cold caches; slow regions; authenticated variants | this domain first, then the domain attribution names |
| Good CWV, slow-feeling navigation | Instant Insights / Navigation Inspector | missing or misplaced Suspense; uncached data above the boundary; shell not prefetched | `navigation-prefetching` · `rendering-strategy-caching` |
| Instant but stale/wrong content | cache behaviour, not CWV | over-broad caching; stale client-router data | `rendering-strategy-caching` · `data-fetching-patterns` |

Triage order: confirm the symptom at p75 → segment mobile/desktop → narrow to route →
collect attribution → reproduce with a production-like trace → route to one domain → keep
the test that reproduced it.

## Cross-domain interactions

1. **This domain gates the others' verification rung.** With no field data, other tasks
   verify at build/runtime only and must say their performance effect is unmeasured.
2. **Instant Insights inherits the Cache Components prerequisite.** If
   `rendering-strategy-caching` reports `cacheComponents` absent, every Instant Insights
   finding here is NOT APPLICABLE.
3. **Measurement amplifies; it never replaces.** Never propose instrumentation as the fix
   for a metric problem — it is how you find and prove the fix.

## Reference pointer

Fix recipes: `references/fix/measurement-regression-guardrails.md`.
