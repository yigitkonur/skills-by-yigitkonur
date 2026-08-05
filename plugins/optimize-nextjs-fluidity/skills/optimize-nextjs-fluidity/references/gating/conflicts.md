# Conflicts — where one fluidity mechanism undermines another

Seven verified interference families. These are not reasons to avoid a technique; they
are the conditions under which adopting A breaks B. A fix agent that applies one side
without checking the other produces a change that looks right and behaves wrong.

**The ordering invariant, stated once:** *availability before choreography.* Cache,
prefetch, or stream the destination state first; schedule the update second; animate the
committed states last. Reversing that order is the root of conflict #1.

## 1. View Transitions × uncached or unprefetched destinations — "smooth but wrong"

A shared-element morph needs matching old and new elements **in the same navigation
commit**. If the destination suspends first, the fallback — not the intended content — is
what animates. A documented production incident: morphs worked locally and degraded to
Suspense-fallback-only in production because the underlying queries were uncached.

**Rule:** never emit a View Transitions task for a route whose destination is not already
cache-hot. If `rendering-strategy-caching` or `navigation-prefetching` findings exist for
the same route, those tasks are `Depends on` prerequisites.

**Verify:** test a warmed/prefetched route AND a forced-cold route. The cold path must
show a deliberate scoped loading state, not a broken pair.

## 2. Activity preservation × unmount-dependent logic

With `cacheComponents` enabled, Next.js hides rather than unmounts the previous route.
Reported breakage: dropdowns that stay open, dialog initialization that never re-runs,
hidden duplicate form controls breaking strict E2E selectors.

**Rule:** enabling Cache Components is a lifecycle migration, not just a caching flag. Any
Cache Components task must carry an unmount-dependency audit (dropdowns, dialogs, mounted
form init, media, subscriptions, timers, post-submit resets, scroll restoration, E2E
selectors) in its body.

**Verify:** navigate away and back with an open popover, an edited form, and a dialog;
each must follow an explicit preserve-or-reset policy.

## 3. Activity retention bounds × `bfcacheId`

Preservation is bounded — roughly the three most recent routes; older ones evict and
re-render fresh. `router.bfcacheId` changes on a fresh push/replace and stays stable for
back/forward.

**Rule:** never describe route state as durably preserved. Persist real drafts to
application storage. Use `bfcacheId` only where "fresh push resets, history restores" is
exactly the wanted semantic.

**Verify:** visit four distinct routes, return to each, and distinguish retained from
evicted behaviour.

## 4. Hidden Activity prerendering × delayed catastrophic bugs

A recursive tree inside a hidden Activity grew silently for minutes while the visible UI
stayed responsive, then exhausted memory and crashed the tab.

**Rule:** hidden subtrees need the same termination and bounded-size guarantees as visible
ones. A responsive foreground is not evidence the hidden workload is healthy.

## 5. Theme animation × `disableTransitionOnChange`

One mechanism suppresses all CSS transitions during a theme flip; the other deliberately
captures and animates old/new paint. They are contradictory as simultaneous systems.

**Rule:** choose exactly one post-click mode — instant snap with transitions suppressed,
**or** one deliberate View Transition wipe. The first-load anti-flash mechanism is separate
and required either way.

**Verify:** the click path shows either no animation or exactly one root transition —
never dozens of independent element transitions.

## 6. Theme source of truth × the Cache Components root-`<html>` gap

Under Cache Components a Suspense-scoped `cookies()` read does not de-opt the whole route.
But `<html>` itself **cannot** be Suspense-wrapped, so a cookie-derived root theme
attribute has no fully-official static-shell-preserving pattern. Running a cookie source
and a pre-paint script simultaneously without deciding which wins lets them disagree.

**Rule:** for a cache-critical root shell, the pre-paint script is the sole root
authority, and cookie reads serve inner content only. For an already-dynamic route, cookie
SSR is the authority and the script must not override it. **Do not invent a third
mechanism** — the corpus found none.

**Verify:** raw server HTML, pre-hydration DOM, and hydrated DOM must all match the chosen
authority, with only the expected root-attribute difference under the script architecture.

## 7. Locale soft navigation × unavoidable payload refetch

The recommended locale switch eliminates the full-document reload but **not** the network
round-trip for the new locale's RSC payload. Server-rendered translations were never
shipped to the client as a swappable dictionary.

**Rule:** never promise zero-network locale switching. Static-render and cache locale
routes, prefetch likely targets, preserve route params, show local pending state. Describe
the result as "soft, and as fast as a cached navigation".

**Verify:** test a prefetched and an intentionally uncached locale target; both avoid a
document reload, only the former approaches instant.

## 8. Browser-support reality × compatibility tables (shipping gate)

Raw API availability does not guarantee parity in React's integration layer — a Firefox
rendering bug in React's View Transitions integration fails silently, degrading to an
instant cut with no console error.

**Rule:** transitions are progressive enhancement. Navigation must complete correctly
without animation; never make animation the sole signal of navigation direction or state.
Test Chromium, Safari, and Firefox explicitly.

## Contradiction register

| Topic | Claim A | Claim B | Resolution |
|---|---|---|---|
| `next-themes` no-flash | "will not flash under any circumstances" | practitioner flash reports persist | Correct-by-design mechanism, not an unconditional guarantee — reproduce the exact config |
| Theme cookie under Cache Components | Suspense-scoped cookie read doesn't de-opt the route | `<html>` can't sit inside that boundary | The scoped pattern applies to inner content only |
| View Transitions "zero config" | Animations activate with no Next.js flag | React API is canary; Firefox integration can fail silently | Zero configuration ≠ zero compatibility risk |
| `<Activity>` "preserves state" | Hidden routes restore state | Only ~3 recent routes; older evict | Bounded recent-history preservation, not persistence |
| Locale "instant switch" | Soft navigation, no document reload | New locale payload still needs cache hit or request | "Instant" = router continuity + best-case cached response |
