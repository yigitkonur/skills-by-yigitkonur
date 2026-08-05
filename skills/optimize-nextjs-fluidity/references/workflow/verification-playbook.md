# Verification playbook — how to prove a change worked

Every task carries a **Verification command**. This file supplies the vocabulary so those
commands are reproducible and honest. A change without a passing verification is not done.

**Claim only the rung you reached.** Reading a diff is not running a build; a passing build
is not an observed behaviour change; a local observation is not production evidence.

## The rungs

1. **Static** — the code says what it should (grep/read). Weakest; fine for config removals.
2. **Type/lint** — `tsc --noEmit`, `eslint`. Proves shape, not behaviour.
3. **Build** — the app compiles under the real bundler. Catches config-schema errors,
   invalid segment exports, Cache Components boundary violations.
4. **Runtime observation** — the behaviour is visible: HTML output, response headers,
   network waterfall, DevTools panel.
5. **Measured** — a metric moved (CWV, bundle bytes, build time), compared against baseline.

State the rung in the task's Fix tracking block.

## Verification by change class

**Config key added or removed**
```bash
rg -n '<key>' next.config.* || echo "absent — as intended"
npx next build            # only if the task declares a build check
```
A key the installed schema rejects fails config validation at build — that is the check.

**Removed/renamed API cleanup** (Edge runtime, `middleware.ts`, `images.domains`, legacy
segment exports)
```bash
rg -n "runtime = 'edge'|export const (revalidate|dynamic|fetchCache)" src/ || echo clean
```
Plus a build if the surface participates in compilation.

**Image work** — inspect the rendered HTML, not the source:
- the LCP image carries exactly one early-load signal; no other image does
- `srcset` candidates match the authored `sizes` (check the `w=` values in the Network panel)
- intrinsic `width`/`height` or a positioned `fill` parent is present (CLS)
- Lighthouse: "Largest Contentful Paint image was not lazily loaded" passes

**Font work**
```bash
# no external font requests should remain
rg -n 'fonts\.(googleapis|gstatic)\.com' src/ app/ || echo "self-hosted"
```
Then confirm in the Network panel that no third-party font origin is contacted, and that
CLS does not regress on a slow-network profile.

**Script work** — confirm the strategy actually changed *when* the script executes: the
request should move after hydration (`afterInteractive`) or to idle (`lazyOnload`) in the
Network waterfall, and long tasks on the interaction path should shrink.

**Data-fetching / waterfall fixes** — the proof is the waterfall shape: previously stacked
request bars must overlap after a `Promise.all` fix. For a genuine dependency chain, the
proof is that the shell paints before the chain resolves.

**Cache Components / caching** — build succeeds; then per route confirm the static shell is
served immediately and dynamic holes stream; confirm bots receive a complete request-time
render (`curl -A 'Googlebot' <url>` and check the critical content is present).

**Navigation / prefetch** — DevTools Network shows the prefetch for the hovered/visible
link; the click paints a shell without a blocking round-trip. On 16.3+, Instant Insights
and the `instant()` Playwright helper are the first-class checks.

**Theme** — hard-reload with the OS in dark mode and confirm **no light frame** before
paint. Compare raw server HTML (`curl`), pre-hydration DOM, and hydrated DOM: all three
must agree with the chosen root authority. No hydration warning in the console beyond the
one intentionally suppressed root attribute.

**Locale switch** — the switch performs a soft navigation: no full document reload (the
Network panel shows an RSC payload, not a document request), route params preserved,
`<html lang>` correct on the target, hreflang reciprocal.

**Micro-interactions** — the optimistic state appears in the first paint after the
interaction; a forced server failure visibly rolls it back; typing stays responsive while
an expensive list re-renders.

**Transitions** — test warm/prefetched **and** forced-cold destinations. Cold must degrade
to a deliberate loading state, never a broken pair. Test reduced-motion and Firefox.

**Bundle** — the build-output size table was removed in 16.0. Use `next experimental-analyze`
(Turbopack) or `@next/bundle-analyzer` with `--webpack`. Compare against the baseline
captured in Phase 1.

**SEO** — run the relevant items from `references/gating/seo-obligations.md` against the
deployed origin, not localhost.

## Baseline discipline

Phase 1 records the baseline; Phase 6 compares against it. Without a before-state, "faster"
is unfalsifiable. When no baseline exists, say the task is verified at the build/runtime
rung and that the performance claim is unmeasured — never imply a metric moved.

## When verification fails

Revert that task's commit, set `Status: blocked`, paste the actual output into the task's
Fix tracking block, and continue with independent tasks. Do not retry the same approach
twice; do not weaken the check to make it pass. If more than a third of tasks fail, stop
the run (`references/workflow/safety-rails.md`, rail 8).

## Reporting language

- "Applied; verified at the build rung — the app compiles with the flag removed."
- "Applied; verified at runtime — the hero image now loads eagerly with `fetchpriority=high`."
- "Applied; **not** measured — no field baseline exists, so the LCP effect is unverified."
- "Reverted — verification failed with: `<output>`."

Never: "should improve performance", "this makes it faster", "done ✅" without a rung.
