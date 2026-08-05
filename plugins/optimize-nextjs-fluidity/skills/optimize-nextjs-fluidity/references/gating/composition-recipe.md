# Composition recipe — the ordered blueprint

Fourteen steps that compose every instant-feel mechanism into one coherent app. Phase 4
uses this to order tasks; a fix agent uses it to know what must already be true before its
own change makes sense.

Steps 1–8 establish correctness and availability. 9–10 add instant global switches. 11–12
add choreography. 13 protects deployed continuity. 14 proves the composed system.

**Every step names its exit check.** A step whose exit check cannot be run is not done.

## 1. Establish measurement before changing behaviour

Instrument field CWV (LCP / INP / CLS at p75) and add navigation-level assertions. Field
RUM covers hard navigations; soft navigations need their own checks.

*Exit:* a baseline exists, and a test can distinguish "shell visible now" from "content
visible after stream". → `references/fix/measurement-regression-guardrails.md`

## 2. Stabilise pixels before adding animation

Reserve image geometry, author real `sizes`, signal the true LCP image only. Adopt
`next/font` with metric-matched fallback; defer non-critical third-party scripts.

*Exit:* no image-driven layout pop, no FOIT, no early third-party long task on the first
interaction path. → `references/fix/image-optimization.md`, `references/fix/font-script-optimization.md`

## 3. Minimise browser work on every route

Push `'use client'` boundaries down, move transformation-heavy work server-side, lazy-load
genuinely deferred browser-only features with shape-preserving fallbacks.

*Exit:* primary route content stays server-rendered; deferred chunks create no blank or
shifting regions. → `references/fix/bundle-code-splitting.md`

## 4. Resolve deprecations and runtime prerequisites

Remove `runtime = 'edge'` / `preferredRegion`; rename `middleware.ts` → `proxy.ts`; fix
image/metadata renames; migrate `revalidateTag` arity. These are cheap, reversible, and
several are hard prerequisites for step 6.

*Exit:* no removed/renamed surface remains in live use.
→ `references/fix/vercel-platform-deployment.md`, `references/gating/version-matrix.md`

## 5. Fix data shape — waterfalls and boundaries

Parallelise independent fetches, preload where useful, dedup shared reads, place Suspense
boundaries around genuinely independent regions.

*Exit:* no same-component sequential waterfall; independent regions stream independently.
→ `references/fix/data-fetching-patterns.md`

## 6. Adopt Cache Components deliberately (one-way door)

Only after 4 and 5. Run the pre-flight checklist in
`references/gating/lockin-reversibility.md`. Classify data into `"use cache"`,
`"use cache: private"`, `"use cache: remote"`. Stage with `instant = false`.

*Exit:* static shell, cached regions, and runtime regions are each intentional; every
cache scope has an explicit `cacheLife`; no legacy segment exports remain.
**Never auto-applied** — `Status: blocked-needs-human`. → `references/fix/rendering-strategy-caching.md`

## 7. Make route state preservation safe

Cache Components auto-wires `<Activity>`. Audit everything that assumed unmount: dialogs,
popovers, form resets, timers, subscriptions, global styles, E2E selectors.

*Exit:* retained routes restore drafts and scroll; transient UI closes; behaviour stays
correct after visiting more than three routes (eviction).
→ `references/fix/micro-interactions-react19-fluidity.md`, `references/gating/conflicts.md` §2–3

## 8. Build responsive in-page interactions

Keep urgent input synchronous; move expensive rendering behind `useTransition` /
`useDeferredValue`; add optimistic UI only for predictable, reversible mutations with
explicit pending, confirm, and rollback states.

*Exit:* optimistic state appears in the first post-interaction paint; a forced server
failure visibly rolls back. → `references/fix/micro-interactions-react19-fluidity.md`

## 9. Install a no-flash theme architecture

Pick one root authority: pre-paint script (preserves cacheability) or cookie SSR (for
already-dynamic routes). Semantic CSS variables make the switch one attribute mutation.

*Exit:* hard reload in dark system mode shows no light frame; raw server HTML matches the
chosen architecture; the toggle triggers no document request.
→ `references/fix/dark-light-theme-switching.md`, `references/gating/conflicts.md` §6

## 10. Add locale routing, static locale output, soft switching

URL-addressable locale routes, `generateStaticParams` over locales, locale-aware
`router.replace` inside `startTransition`. Treat the target locale as another route to
cache and prefetch.

*Exit:* one RSC request or a cache hit, no document reload, params preserved, pending
state visible, `<html lang>` and hreflang correct.
→ `references/fix/instant-i18n-locale-switching.md`

## 11. Add page View Transitions — only after content readiness

Start with one shared-element pair. Route-level wrappers belong in `page.tsx`, not
persistent layouts. Keep transitions short; browser back/forward carries no transition
types.

*Exit:* warm/prefetched AND cold/uncached destinations both behave correctly; reduced
motion and Firefox have defined behaviour.
→ `references/fix/page-transitions-view-transitions.md`, `references/gating/conflicts.md` §1

## 12. Choose exactly one theme-toggle animation mode

Either the instant snap with incidental transitions suppressed, or one deliberate,
feature-detected, reduced-motion-safe View Transition. Never both.

*Exit:* the click path shows one controlled animation or none.
→ `references/gating/conflicts.md` §5

## 13. Protect deployment continuity

Verify Skew Protection where client navigation, Server Actions, and optimistic payload
contracts can span a deploy. Place functions near their data.

*Exit:* an old open tab can navigate and submit against a compatible deployment; CDN/ISR
hit paths avoid function execution. → `references/fix/vercel-platform-deployment.md`

## 14. Verify the composed five-scenario story

Run all five: warm and cold page navigation · hard-load and post-mount theme switch ·
prefetched and uncached locale switch · successful, failed, and rapid optimistic
mutations · back/forward within and beyond the Activity retention window.

*Exit:* every mechanism still improves the user-visible path when composed; no check
passes merely because an animation hid stale or fallback content.
→ `references/workflow/verification-playbook.md`

## Using this file in Phase 4

1. Map each finding to its step number.
2. Task ordinals follow step order; a task at step N gets `Depends on` any open task at a
   lower step that touches the same route or subsystem.
3. Steps 6 and 10 (URL policy) are one-way doors → `blocked-needs-human`.
4. If a repo has already completed a step, say so in `01-applicability.md` and skip it —
   never re-propose work a repo has already done.
