# Fix: page-transitions-view-transitions

**Corpus lineage:** page-transitions-view-transitions/04-implementation-patterns-setup-morph-suspense.md,
page-transitions-view-transitions/05-implementation-patterns-directional-css.md,
page-transitions-view-transitions/08-version-lockin-seo-vercel-practitioner.md

**Knowledge baseline:** verified 2026-08-05 against Next.js 16.3.0 docs and react.dev's
`ViewTransition`/`addTransitionType` references. Confirm `experimental.viewTransition`
against the installed package first — see `references/gating/capability-probe.md`. Every
prop/import here is verbatim from the corpus; no invented signatures.

## Recipe index

| Recipe | Requires | Reversibility | Triggered by |
|---|---|---|---|
| Basic route crossfade (setup) | Next.js 16.x, any | fully-reversible | No View Transitions adoption at all; wants a first, low-risk win |
| Shared-element list→detail morph | Next.js 16.x, any | fully-reversible | List/gallery to detail navigation has no visual continuity |
| Suspense reveal (loading → content) | Next.js 16.x, any | fully-reversible | Skeleton-to-content swap pops instead of revealing |
| Directional/typed transition | Next.js ≥16.2.0 (manual fallback for 16.0.0–16.1.x) | fully-reversible | Drill-down hierarchy has no forward/back sense |
| Same-route crossfade (tabs, dynamic segments) | Next.js 16.x, any | fully-reversible | Tab/segment switch shows an abrupt content swap |
| CSS `::view-transition-*` customization | Next.js 16.x, any | fully-reversible | Default timing/easing needs project-specific values |
| `prefers-reduced-motion` guard | Next.js 16.x, any | fully-reversible | Any directional/positional transition shipped with no accessibility floor |
| 15.x `unstable_ViewTransition` → 16.x migration | Next.js ≥16.0.0 | fully-reversible (mechanical rename) | `unstable_ViewTransition`/`experimental.viewTransition` found; probe confirms action |

## Basic route crossfade (setup) — requires Next.js ≥16.0.0

**When to apply:** repo has zero `<ViewTransition>` usage; wants the smallest first step.

```tsx
// app/layout.tsx or any page.tsx — Next.js 16.3.0
// No next.config.js change needed. Import directly from 'react'.
import { ViewTransition } from 'react'
```

**Why:** the App Router bundles React's canary channel automatically, where
`ViewTransition` lives — no flag, no `react@canary` install. The component only does
something once it wraps content participating in a Transition, Suspense, or
`useDeferredValue` update.

**Verify after applying:** DevTools → Elements panel during a navigation between two pages
sharing a `<ViewTransition name>` pair — a `::view-transition` pseudo-element tree should
appear briefly (slow `animation-duration` or use the Animations panel to pause mid-transition).

**Lock-in / reversibility:** fully-reversible — matches
`references/gating/lockin-reversibility.md`'s safe-to-auto-apply list.

**Rollback:** delete the import and any wrapper; no config to unwind.

## Shared-element list→detail morph — requires Next.js ≥16.0.0

**When to apply:** a list/grid navigates to a detail page for the same visual object
(gallery, product list) with no visual connection between the two views.

```tsx
// components/photo-grid.tsx — Next.js 16.3.0
import { ViewTransition } from 'react'
import Image from 'next/image'
import Link from 'next/link'

type Photo = { id: string; src: string; title: string }

export function PhotoGrid({ photos }: { photos: Photo[] }) {
  return (
    <div className="grid grid-cols-3 gap-3">
      {photos.map((photo) => (
        <Link key={photo.id} href={`/photo/${photo.id}`}>
          <ViewTransition name={`photo-${photo.id}`} share="morph" default="none">
            <Image src={photo.src} alt={photo.title} width={400} height={300} />
          </ViewTransition>
        </Link>
      ))}
    </div>
  )
}
```

```tsx
// app/photo/[id]/photo-content.tsx — Next.js 16.3.0
import { ViewTransition } from 'react'
import Image from 'next/image'

export async function PhotoContent({ id }: { id: string }) {
  const photo = await getPhoto(id)
  return (
    <ViewTransition name={`photo-${photo.id}`} share="morph" default="none">
      <div style={{ position: 'relative', aspectRatio: '3 / 2' }}>
        <Image src={photo.src} alt={photo.title} fill />
      </div>
    </ViewTransition>
  )
}

declare function getPhoto(id: string): Promise<{ id: string; src: string; title: string }>
```

```css
/* app/globals.css */
::view-transition-group(.morph) { animation-duration: 400ms; }
::view-transition-image-pair(.morph) { animation-name: via-blur; }
@keyframes via-blur { 30% { filter: blur(3px); } }
```

**Why each non-obvious line exists:**
- `name` must match **exactly** on both grid and detail-page `<ViewTransition>` — identity
  is what creates the shared-element pair.
- `default="none"` prevents the image crossfading on unrelated transitions, but **must
  always pair with an explicit `share`** — omitting `share` after `default="none"`
  silently kills the pair's own morph too.

**Verify after applying:** click a thumbnail — the image should scale/reposition from grid
cell into hero slot rather than instantly swap; back-navigate to confirm the morph
reverses. If nothing animates: confirm both `name`s match exactly, confirm the destination
isn't suspending into a fallback first (see Conflicts below), confirm browser support.

**Lock-in / reversibility:** fully-reversible — delete the wrappers and CSS.

**Rollback:** remove `<ViewTransition>` wrappers (keep children), remove the `.morph` CSS.

## Suspense reveal (loading → content) — requires Next.js ≥16.0.0

**When to apply:** a skeleton-to-content swap pops instantly instead of a deliberate
hand-off, on an explicit `<Suspense>` boundary or `loading.tsx`.

```tsx
// app/photo/[id]/page.tsx — Next.js 16.3.0
import { Suspense, ViewTransition } from 'react'
import { PhotoContent } from './photo-content'
import { PhotoContentSkeleton } from './photo-content-skeleton'

export default async function PhotoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  return (
    <Suspense
      fallback={<ViewTransition exit="slide-down" default="none"><PhotoContentSkeleton /></ViewTransition>}
    >
      <ViewTransition enter="slide-up" default="none">
        <PhotoContent id={id} />
      </ViewTransition>
    </Suspense>
  )
}
```

```css
/* app/globals.css */
:root { --duration-exit: 150ms; --duration-enter: 210ms; --duration-move: 400ms; }
::view-transition-old(.slide-down) {
  animation: var(--duration-exit) ease-out both fade reverse, var(--duration-exit) ease-out both slide-y reverse;
}
::view-transition-new(.slide-up) {
  animation: var(--duration-enter) ease-in var(--duration-exit) both fade, var(--duration-move) ease-in both slide-y;
}
@keyframes fade { from { filter: blur(3px); opacity: 0; } to { filter: blur(0); opacity: 1; } }
@keyframes slide-y { from { transform: translateY(10px); } to { transform: translateY(0); } }
```

**`loading.tsx` variant** (an implicit Suspense boundary — same rule, just move the
skeleton's `<ViewTransition exit="slide-down">` into `app/photo/[id]/loading.tsx` as its
default export; the page keeps its `enter="slide-up" default="none"` wrapper unchanged).

**Why each non-obvious line exists:**
- Exit (150ms) is shorter than enter (210ms, delayed by the exit duration) — old content
  leaves quickly so it doesn't compete for attention; new content arrives more gently.
- `default="none"` on both sides keeps this pair from firing on unrelated transitions.

**Verify after applying:** refresh the detail page (or navigate with unprefetched data) —
skeleton slides down/fades out, then content slides up/fades in with a visible gap. An
instant pop means the destination resolved in the same commit (expected, not a bug) —
slow the network to confirm the animation exists.

**Lock-in / reversibility:** fully-reversible — remove wrappers and CSS.

**Rollback:** remove both `<ViewTransition>` wrappers and the `.slide-down`/`.slide-up` CSS.

## Directional/typed transition — requires Next.js ≥16.2.0 (manual fallback for 16.0.0–16.1.x)

**When to apply:** a drill-down hierarchy (gallery → photo, settings → sub-setting) has no
sense of direction. Probe the installed Next.js version first — below 16.2.0,
`transitionTypes` is unavailable on `<Link>`/`router.push`; use the manual variant instead.

```tsx
// components/photo-grid.tsx — Next.js ≥16.2.0 (declarative, works in Server Components)
<Link href={`/photo/${photo.id}`} transitionTypes={['nav-forward']}>{/* thumbnail */}</Link>
```

```tsx
// components/detail-button.tsx — Next.js 16.0.0–16.1.x (manual fallback; also use for
// non-Link triggers like buttons/forms regardless of version)
'use client'
import { useRouter } from 'next/navigation'
import { startTransition, addTransitionType } from 'react'

export function DetailButton({ href }: { href: string }) {
  const router = useRouter()
  function handleNavigate() {
    startTransition(() => {
      addTransitionType('nav-forward')
      router.push(href)
    })
  }
  return <button onClick={handleNavigate}>Open</button>
}
```

```tsx
// app/photo/[id]/page.tsx — Next.js 16.3.0 (wrap the page, never the layout)
<ViewTransition
  enter={{ 'nav-forward': 'nav-forward', 'nav-back': 'nav-back', default: 'none' }}
  exit={{ 'nav-forward': 'nav-forward', 'nav-back': 'nav-back', default: 'none' }}
  default="none"
>
  {/* page content */}
</ViewTransition>
```

```css
/* app/globals.css — anchor a persistent header + directional slide */
::view-transition-group(site-header) { animation: none; z-index: 100; }
::view-transition-old(site-header) { display: none; }
::view-transition-new(site-header) { animation: none; }

::view-transition-old(.nav-forward) { --slide-offset: -60px; animation: 150ms ease-in both fade reverse, 400ms ease-in-out both slide reverse; }
::view-transition-new(.nav-forward) { --slide-offset: 60px; animation: 210ms ease-out 150ms both fade, 400ms ease-in-out both slide; }
::view-transition-old(.nav-back) { --slide-offset: 60px; animation: 150ms ease-in both fade reverse, 400ms ease-in-out both slide reverse; }
::view-transition-new(.nav-back) { --slide-offset: -60px; animation: 210ms ease-out 150ms both fade, 400ms ease-in-out both slide; }
@keyframes slide { from { translate: var(--slide-offset); } to { translate: 0; } }
```

**Why each non-obvious line exists:**
- `transitionTypes` on `<Link>` works in Server Components — internally calls
  `React.addTransitionType` inside the navigation Transition.
- The page-level wrapper must sit in **each `page.tsx`, not the layout** — layouts persist
  across navigations, so their `enter`/`exit` never fire (nesting inside a parent VT also
  silently disables the child's own enter/exit).
- `default: 'none'` on the type-keyed object ensures untyped transitions (browser
  back/forward, `router.refresh()`, Suspense reveals) get no directional animation instead
  of an undefined one — browser-initiated back navigation never carries a transition type.
- Header `display: none` on the old snapshot prevents a flash of both headers visible.

**Verify after applying:** click a forward-tagged link — slides left, header fixed; click
`nav-back` — slides right; press the actual browser back button — no slide (expected), but
a shared-element morph still fires if `name`s match.

**Lock-in / reversibility:** fully-reversible, component-level.

**Rollback:** remove `transitionTypes` (or the manual wrapper), revert `enter`/`exit` to
`"auto"` or remove the wrapper, delete the directional/`site-header` CSS.

## Same-route crossfade (tabs, dynamic segments) — requires Next.js ≥16.0.0

**When to apply:** navigating between dynamic segments of the same route (tabs, filters)
doesn't communicate "same place, different content" — or enter/exit don't fire reliably.

```tsx
// app/collection/[slug]/page.tsx — Next.js 16.3.0
import { Suspense, ViewTransition } from 'react'

export default async function CollectionPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  return (
    <Suspense fallback={<CollectionGridSkeleton />}>
      <ViewTransition key={slug} name="collection-content" share="auto" enter="auto" default="none">
        <CollectionGrid slug={slug} />
      </ViewTransition>
    </Suspense>
  )
}
```

**Why:** `key={slug}` is required — without it the router swaps subtrees keyed by segment
value instead of an unmount/mount pair, so enter/exit don't fire reliably. `share="auto"` +
`enter="auto"` use React's default crossfade — a directional slide would be semantically
wrong here (slides mean "new place"; a crossfade means "same place, different content").

**Verify after applying:** click between tabs on the same route with a different dynamic
segment — the grid crossfades in place; tab bar and layout must not move or flash.

**Lock-in / reversibility:** fully-reversible.

**Rollback:** remove the `<ViewTransition>` wrapper; render `<CollectionGrid>` directly.

## CSS `::view-transition-*` customization — requires Next.js ≥16.0.0

**When to apply:** any recipe above is in place and default timing/easing needs
project-specific values, or clicks during a transition feel unresponsive.

```css
/* app/globals.css */
/* ::view-transition               overlay above everything; set a background here */
/* ::view-transition-group(x)      container; controls group-level morph duration */
/* ::view-transition-image-pair(x) wrapper with isolation around old/new snapshots */
/* ::view-transition-old(x)        screenshot of the previous state */
/* ::view-transition-new(x)        live representation of the new state */
::view-transition {
  pointer-events: none;
}
```

**Why:** `view-transition-name` **must be unique** — two elements sharing one name at the
same time cause the transition to be skipped entirely, silently. `pointer-events: none` on
`::view-transition` restores interactivity for unnamed content — without it, clicks during
a transition are lost because the overlay captures pointer events. Named participants
(e.g. an anchored header) still skip hit-testing for the transition's duration even with
this fix — keep transitions short for elements users click rapidly.

**Verify after applying:** during an active transition, click an unnamed element outside
the transitioning region — it should respond immediately.

**Lock-in / reversibility:** fully-reversible — CSS-only.

**Rollback:** remove the `pointer-events: none` rule and any custom pseudo-element blocks.

## `prefers-reduced-motion` guard — requires Next.js ≥16.0.0

**When to apply:** any directional-slide/positional transition ships. Directional slides
are the highest motion-sensitivity trigger; morphs/reveals/crossfades carry less risk
(opacity/size, not position) but should still be covered.

```css
/* app/globals.css */
@media (prefers-reduced-motion: reduce) {
  ::view-transition-old(*),
  ::view-transition-new(*),
  ::view-transition-group(*) {
    animation-duration: 0s !important;
    animation-delay: 0s !important;
  }
}
```

**Why:** targeting `*` applies the guard to every named and unnamed transition. Zeroing
duration/delay (rather than removing the transition) means content still swaps instantly —
the browser's default, accessible behavior — rather than breaking navigation.

**Verify after applying:** DevTools Rendering tab → "Emulate CSS media feature
prefers-reduced-motion" → "reduce" → re-trigger a directional navigation — content should
swap with no slide/duration.

**Lock-in / reversibility:** fully-reversible. **Rollback:** remove the media query block.

## 15.x `unstable_ViewTransition` → 16.x migration — requires Next.js ≥16.0.0

**When to apply:** detect found `unstable_ViewTransition` and/or `experimental.viewTransition`,
**and** the capability probe confirms the action (see
`references/detect/page-transitions-view-transitions.md`'s gate rule — probe `absent`
means proceed with full removal below; probe `present` means skip config deletion and emit
only the informational re-check note).

```js
// next.config.js — before (Next.js 15.x)
/** @type {import('next').NextConfig} */
const nextConfig = { experimental: { viewTransition: true } }
module.exports = nextConfig
```
```tsx
// any component — before (Next.js 15.x)
import { unstable_ViewTransition as ViewTransition } from 'react'
```
```js
// next.config.js — after (Next.js 16.3.0): no viewTransition key at all; delete it entirely
```
```tsx
// any component — after (Next.js 16.3.0)
import { ViewTransition } from 'react'
```

**Why:** the rename is a straight import-alias drop — `unstable_ViewTransition` is the
same component re-exported under a different name in 15.x. Config deletion is conditional
on the probe (see gate rule) — deleting a key the installed schema still accepts isn't
itself harmful, but skipping the probe and assuming removal is always safe is exactly the
mistake this skill's gating exists to catch.

**Verify after applying:** `rg -n "unstable_ViewTransition|experimental.*viewTransition"`
across the project — zero hits. `npx @next/codemod@canary upgrade latest` lists "Remove
`unstable_` prefix from stabilized APIs" as a general capability, but `ViewTransition` is
not named as a specifically-covered case — verify manually after running it.

**Lock-in / reversibility:** fully-reversible for the import rename. The 15.x flag +
`unstable_` import was itself a flagged one-way door while in place — staying on it means
re-verifying every transition against the current four patterns whenever the repo does
eventually upgrade.

**Rollback:** revert to `import { unstable_ViewTransition as ViewTransition } from 'react'`
and re-add the config flag — only meaningful if downgrading to 15.x, not a normal path.

## Ordering within this domain

1. **15.x migration** (if detected) runs first — every other recipe assumes the 16.x
   zero-config import already in place.
2. **Setup** (import) — a prerequisite for every other recipe.
3. **`prefers-reduced-motion` guard** before shipping anything directional — a near-zero
   -cost accessibility floor that precedes feature expansion, not a follow-up.
4. **Shared-element morph** or **Suspense reveal** on one low-traffic route pair first —
   smallest blast radius, surfaces the caching dependency early.
5. **Directional/typed transitions** only after confirming `<Link transitionTypes>`
   availability via the probe.
6. **CSS customization** last, once base patterns fire correctly.

## Conflicts to watch

- **View Transitions × uncached/unprefetched destinations ("smooth but wrong")** — a
  morph or Suspense-reveal needs the destination to commit in the same navigation commit.
  If it suspends first, the fallback — not the destination — is what animates. Never emit
  a View Transitions task for a route whose destination isn't cache-hot; if
  `rendering-strategy-caching`/`navigation-prefetching` findings exist for the same route,
  treat them as `Depends on` prerequisites. Verify with both a warmed and a forced-cold
  route. See `references/gating/conflicts.md` §1.
- **Browser-support reality × compatibility tables** — caniuse availability doesn't
  guarantee parity in React's own integration layer; a confirmed Firefox rendering bug
  fails silently (no console error, no animation). Transitions are progressive
  enhancement — navigation must succeed identically with or without animation. Test
  Chromium, Safari, and Firefox explicitly. See `references/gating/conflicts.md` §8.
