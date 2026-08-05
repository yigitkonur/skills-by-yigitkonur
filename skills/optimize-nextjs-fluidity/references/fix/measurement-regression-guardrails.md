# Fix: measurement-regression-guardrails

**Corpus lineage:** measurement-regression-guardrails/04-field-instrumentation-code.md,
05-navigation-and-ci-code.md, 06-adoption-tradeoffs-and-platform.md
**Knowledge baseline:** verified 2026-08-05 against Next.js 16.3.0 docs. Confirm any
version-gated surface against the installed package first — see
`references/gating/capability-probe.md`.

Every recipe here is `fully-reversible`: instrumentation deletes cleanly. That makes this
domain the safest first task in almost every plan, and the reason it is usually task 01.

## Recipe index

| Recipe | Requires | Reversibility | Triggered by |
|---|---|---|---|
| Field Web Vitals with `useReportWebVitals` | any App Router version | fully-reversible | no field instrumentation found |
| Speed Insights with cost control | Vercel project | fully-reversible | Vercel repo, no vitals coverage, or unsampled at traffic |
| `web-vitals` attribution for debugging | npm install | fully-reversible | a metric is bad but its cause is unattributed |
| Soft-navigation regression test with `instant()` | **Next.js ≥16.3.0** + `@next/playwright` | fully-reversible | client navigation dominates and has no regression guard |
| Lighthouse CI performance gate | production build in CI | fully-reversible | no CI perf gate, or one auditing `next dev` |
| Baseline → change → verify → gate | — | n/a (process) | any run whose tasks must be provable |

---

## Field Web Vitals with `useReportWebVitals` — requires any App Router version

**When to apply:** the repo has no field instrumentation, so no task in this run can be
verified at the measured rung.

```tsx
// app/_components/web-vitals.tsx — Next.js 16.3.0
'use client'

import { useReportWebVitals } from 'next/web-vitals'

type ReportWebVitalsCallback = Parameters<typeof useReportWebVitals>[0]

// Defined OUTSIDE the component so the reference stays stable across renders.
const postWebVitals: ReportWebVitalsCallback = (metric) => {
  const body = JSON.stringify({
    name: metric.name,        // 'LCP' | 'INP' | 'CLS' | 'FCP' | 'TTFB'
    value: metric.value,
    rating: metric.rating,    // 'good' | 'needs-improvement' | 'poor'
    id: metric.id,
    path: window.location.pathname,
  })
  const url = '/api/vitals'

  if (navigator.sendBeacon) {
    navigator.sendBeacon(url, body)
  } else {
    fetch(url, { body, method: 'POST', keepalive: true })
  }
}

export function WebVitals() {
  useReportWebVitals(postWebVitals)
  return null
}
```

```tsx
// app/layout.tsx — Next.js 16.3.0
import { WebVitals } from './_components/web-vitals'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <WebVitals />
        {children}
      </body>
    </html>
  )
}
```

**Why each non-obvious line exists:**
- `'use client'` is required — the hook only runs in the browser. Keeping it in a dedicated
  component confines the client boundary to this file instead of spreading it through the
  layout tree.
- The callback is defined outside the component because a changing reference causes
  duplicate reporting.
- `navigator.sendBeacon` flushes during unload without blocking navigation;
  `fetch(..., { keepalive: true })` is the documented fallback.
- `path` is added because a metric without a route is unactionable at triage time.

**Verify after applying:** DevTools → Network, filter for `/api/vitals`, interact and
navigate. A beacon/fetch fires with a JSON body containing `name`, `value`, `rating`, `id`.
If nothing fires, `console.log(metric)` inside the callback first to confirm the hook runs
at all. **Rung:** runtime.

**Lock-in / reversibility:** fully-reversible — delete the component and its import.

**Rollback:** remove `<WebVitals />` from the layout and delete `app/_components/web-vitals.tsx`.

---

## Speed Insights with cost control — requires a Vercel project

**When to apply:** the repo deploys on Vercel and either has no vitals coverage, or has
Speed Insights collecting unsampled events at meaningful traffic.

```tsx
// app/layout.tsx — Next.js 16.3.0
import { SpeedInsights } from '@vercel/speed-insights/next'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
        <SpeedInsights
          // Collect a fraction of traffic once volume is meaningful. 1 = 100%.
          sampleRate={0.25}
          // Drop or rewrite events before they leave the browser: strip query
          // strings, skip internal routes, honour a consent decision.
          beforeSend={(event) => {
            if (event.url.includes('/admin')) return null
            return { ...event, url: event.url.split('?')[0] }
          }}
        />
      </body>
    </html>
  )
}
```

**Why each non-obvious line exists:**
- `sampleRate` is the cost lever — Speed Insights bills a per-project base plus per-event
  cost beyond an included tier (`references/gating/cost-model.md`). p75 does not need 100%
  of traffic to be stable.
- `beforeSend` returning `null` drops an event entirely; it is also where PII in query
  strings gets stripped before leaving the browser.

**Verify after applying:** deploy, then confirm the Speed Insights dashboard receives data
for public routes and none for the excluded ones. Check the events counter against the
included tier after a day. **Rung:** runtime (production).

**Lock-in / reversibility:** fully-reversible in code — but note that removing the
component does not by itself stop billing; the product must also be disabled in the
project dashboard.

**Rollback:** remove `<SpeedInsights />` and uninstall `@vercel/speed-insights`, then
disable Speed Insights in the Vercel project settings.

---

## `web-vitals` attribution for debugging — requires the `web-vitals` package

**When to apply:** a metric is failing and the field data says *what* but not *which
element*.

```tsx
// app/_components/vitals-debug.tsx — Next.js 16.3.0
'use client'

import { useEffect } from 'react'
import { onLCP, onINP, onCLS } from 'web-vitals/attribution'

export function VitalsDebug() {
  useEffect(() => {
    onLCP((metric) => {
      // attribution names the actual element that was the LCP candidate
      console.log('LCP', metric.value, metric.attribution.element)
    })
    onINP((metric) => {
      console.log('INP', metric.value, metric.attribution.interactionTarget)
    })
    onCLS((metric) => {
      console.log('CLS', metric.value, metric.attribution.largestShiftTarget)
    })
  }, [])
  return null
}
```

**Why each non-obvious line exists:**
- The import is `web-vitals/attribution`, not `web-vitals` — the attribution build carries
  the element-level detail; the base build does not.
- `attribution.element` / `interactionTarget` / `largestShiftTarget` are what turn "LCP is
  3.4s" into "the hero image is the LCP element", which is what routes the fix to a domain.

**Verify after applying:** load a slow route, interact, and read the console — each metric
logs with a concrete element selector. **Rung:** runtime.

**Lock-in / reversibility:** fully-reversible. This is a debugging aid; remove it once the
cause is attributed rather than shipping it permanently.

**Rollback:** delete the component and its import.

---

## Soft-navigation regression test with `instant()` — requires Next.js ≥16.3.0 AND `@next/playwright`

**If the capability probe reports this version absent, do not emit this recipe** —
recommend a version upgrade as its own separate task instead.

**When to apply:** client navigation dominates the experience and nothing guards against a
refactor reintroducing a blocking navigation.

```ts
// e2e/instant-navigation.spec.ts — Next.js 16.3.0
import { test, expect } from '@playwright/test'
import { instant } from '@next/playwright'

test('product navigation shows its shell immediately', async ({ page }) => {
  await page.goto('/')

  // instant() scopes assertions to what is visible at navigation commit —
  // before the server finishes streaming the dynamic holes.
  await instant(page, async () => {
    await page.getByRole('link', { name: 'Products' }).click()
    await expect(page.getByRole('heading', { name: 'Products' })).toBeVisible()
  })
})
```

**Why each non-obvious line exists:**
- `instant()` is what distinguishes "the shell painted now" from "the page eventually
  loaded" — an ordinary Playwright assertion passes either way, so it cannot catch the
  regression this test exists for.
- The assertion inside the callback must target shell content, not streamed content;
  asserting on a dynamic hole makes the test flaky by design.

**Verify after applying:** run the test against a production build. Then deliberately
break it — move a data fetch above the Suspense boundary — and confirm the test fails.
A regression test that has never failed proves nothing. **Rung:** measured.

**Lock-in / reversibility:** fully-reversible. If `experimental.exposeTestingApiInProductionBuild`
is needed to run against `next start`, scope it to CI builds only — enabled in a production
deploy it is a `critical` finding.

**Rollback:** delete the spec; remove the experimental flag if it was added.

---

## Lighthouse CI performance gate — requires a production build in CI

**When to apply:** no CI gate exists, or the existing one audits `next dev`.

```json
// .lighthouserc.json — audits a production build, never `next dev`
{
  "ci": {
    "collect": {
      "startServerCommand": "npm run start",
      "url": ["http://localhost:3000/", "http://localhost:3000/products"],
      "numberOfRuns": 3
    },
    "assert": {
      "assertions": {
        "categories:performance": ["warn", { "minScore": 0.9 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }]
      }
    }
  }
}
```

```yaml
# .github/workflows/perf.yml
name: perf
on: [pull_request]
jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22 }
      - run: npm ci && npm run build
      - run: npx @lhci/cli autorun
```

**Why each non-obvious line exists:**
- `startServerCommand` runs the **production** server; auditing `next dev` measures
  unminified, unoptimized output and produces numbers that mean nothing.
- `numberOfRuns: 3` smooths per-run variance — a single run flags noise as regression.
- Thresholds are set from the repo's measured baseline, not from aspiration. A gate that
  fails on day one gets disabled by the team on day two.

**Verify after applying:** open a PR that deliberately regresses LCP (e.g. lazy-load the
hero) and confirm the gate fails; revert and confirm it passes. **Rung:** measured.

**Lock-in / reversibility:** fully-reversible — delete the config and workflow.

**Rollback:** remove `.lighthouserc.json` and the workflow file.

---

## Baseline → change → verify → gate — the process every task inherits

1. **Baseline before anything.** Record p75 LCP/INP/CLS by route family, plus build time
   and bundle size if obtainable. Without a before-state, "faster" is unfalsifiable.
2. **One change at a time.** A wave that lands six tasks at once cannot attribute the
   delta to any of them.
3. **Verify at the highest rung available.** With field data: measured. Without it:
   runtime or build — and the task says its performance effect is unmeasured.
4. **Keep the test that caught it.** A regression found once will return; the guard is the
   deliverable, not the fix.

**Verify after applying:** the completion report's measurement section shows before/after
rows with real numbers, or explicitly states the effect is unverified. Never both silent
and implied. See `references/artifact/completion-report-template.md`.

---

## Ordering within this domain

1. Field instrumentation first — it gates every other task's verification rung.
2. Attribution second, and only where a metric is actually failing.
3. Navigation regression tests after the navigation domain's work lands (there is nothing
   to guard before then).
4. CI gates last, with thresholds derived from the measured baseline.

## Conflicts to watch

- **A green dashboard is not crawlability.** RUM measures humans; bots are a separate probe
  entirely (`references/gating/seo-obligations.md`).
- **Sampling and route allowlists change what you can see, not what users experience.**
  Excluding a route from Speed Insights does not make it fast.
- **Instant Insights inherits the Cache Components prerequisite** — if that flag is off,
  this tooling is not available regardless of version.
