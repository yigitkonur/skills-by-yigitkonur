# Fix: font-script-optimization

**Corpus lineage:** font-script-optimization/04-implementation-fonts.md, font-script-optimization/05-implementation-scripts.md, font-script-optimization/08-version-lockin-seo-vercel-practitioner.md
**Knowledge baseline:** verified 2026-08-05 against Next.js 16.3.0 docs. Confirm any
config key against the installed package first — see `references/gating/capability-probe.md`.

## Recipe index

| Recipe | Requires | Reversibility | Triggered by |
|---|---|---|---|
| Google variable font + CSS variable | Next.js ≥13.2.0 | fully-reversible | External Google Fonts request, or no `next/font` in use |
| `next/font/local` multi-weight self-hosting | Next.js ≥13.0.0 | fully-reversible | Proprietary font, or no build-time network access to Google Fonts |
| Tailwind CSS v4 font wiring | Next.js ≥13.2.0 + Tailwind v4 | fully-reversible | Font `variable` defined but not composed through Tailwind |
| `display` selection: `swap` vs `optional` | Next.js ≥13.2.0 | fully-reversible | Swap-CLS complaint, or a strict zero-CLS requirement |
| Migrating off legacy `@next/font` | Next.js ≥13.2.0 | fully-reversible | `@next/font` import found |
| `beforeInteractive` critical script | Next.js ≥13.0.0 (App Router) | fully-reversible | Consent manager / bot detector needed before hydration, or misused for non-critical work |
| `afterInteractive` → `lazyOnload` strategy tuning | Next.js ≥13.0.0 | fully-reversible | Analytics/chat/widget on the wrong strategy, or `strategy="worker"` found |
| Inline script + lifecycle callbacks | Next.js ≥12.2.4 (`onReady`) | fully-reversible | Missing `id`, or `onLoad`/`onReady`/`onError` not firing |
| `@next/third-parties` GA / GTM | separate package, experimental | component-level-revert | Manual GA/GTM `<script>` wiring found |
| `@next/third-parties` Maps + YouTube facades | separate package, experimental | component-level-revert | Raw YouTube iframe or Maps JS API embed above the fold |

## Google variable font + CSS variable — requires Next.js ≥13.2.0

**When to apply:** an external `fonts.googleapis.com`/`fonts.gstatic.com` request was
found, or no `next/font` module is in use, for a Google-catalog font.

```tsx
// app/fonts.ts — Next.js 16.3.0
import { Inter, Roboto_Mono } from 'next/font/google'

export const sans = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-sans',
  fallback: ['system-ui', 'arial'],
})

export const mono = Roboto_Mono({ subsets: ['latin'], display: 'swap', variable: '--font-mono' })
```

```tsx
// app/layout.tsx — Next.js 16.3.0
import { sans, mono } from './fonts'
import './globals.css'

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  )
}
```

**Why:** `subsets` avoids the build-time warning and restricts downloaded glyphs to what
the site renders. `adjustFontFallback` is left at its default `true` — it generates
metric overrides that prevent swap-CLS with zero hand-written CSS. Defining the font
**once** in `app/fonts.ts` and importing it elsewhere avoids duplicate hosted instances.
Call the function only in the narrowest layout that renders it — a root-layout call
preloads on every route even ones that never render it.

**Verify after applying:** Network panel filtered to `font` → URL is same-origin
(`/_next/static/media/`); zero requests to `fonts.googleapis.com`/`fonts.gstatic.com`;
Lighthouse mobile cold-cache CLS ≤0.1 with no shift at the font-swap timestamp.

**Lock-in / reversibility:** fully-reversible — delete the font function call and import.

**Rollback:** remove the `next/font/google` import and `variable`/`className` wiring.

## `next/font/local` multi-weight self-hosting — requires Next.js ≥13.0.0

**When to apply:** the font is proprietary, not in the Google catalog, or CI has no
outbound network access to Google Fonts at build time.

```tsx
// app/fonts.ts — Next.js 16.3.0
import localFont from 'next/font/local'

export const brand = localFont({
  src: [
    { path: './fonts/Brand-Regular.woff2', weight: '400', style: 'normal' },
    { path: './fonts/Brand-Bold.woff2', weight: '700', style: 'normal' },
  ],
  display: 'swap',
  adjustFontFallback: 'Arial',
  fallback: ['Arial', 'sans-serif'],
  variable: '--font-brand',
})
```

Simplify to one file if a variable binary covers the range:
`localFont({ src: './fonts/Brand-Variable.woff2', weight: '400 700', display: 'swap', variable: '--font-brand' })`.

**Why:** `src`'s type is `Array<{path, weight?, style?}>` — each file maps to a valid CSS
face; omitting weight/style makes the browser synthesize or pick unpredictably. WOFF2 is
preferred; Next.js does not convert formats. Choose `adjustFontFallback` by genre
closeness (serif-for-serif, sans-for-sans), not the bare default without checking — a
fallback matches box metrics, not glyph shape, so a mismatched genre still looks
different even with zero layout shift.

**Verify after applying:** Network → `font` filter shows only the faces used above the
fold; Performance trace shows no Layout Shift event at font swap (compare
`adjustFontFallback` values if one appears).

**Lock-in / reversibility:** fully-reversible — delete the `localFont` call.

**Rollback:** remove the font function and its `className`/`variable` wiring.

## Tailwind CSS v4 font wiring — requires Next.js ≥13.2.0 + Tailwind CSS v4

**When to apply:** a font `variable` is defined but not composed through Tailwind.

```css
/* app/globals.css — Tailwind CSS v4 */
@import 'tailwindcss';

@theme inline {
  --font-sans: var(--font-inter);
  --font-mono: var(--font-roboto-mono);
}
```

```tsx
// app/page.tsx — Next.js 16.3.0 + Tailwind CSS v4
export default function Page() {
  return <h1 className="font-sans">Readable sans heading</h1>
}
```

**Why / Verify / Lock-in / Rollback:** this is the exact Tailwind v4 pattern in current
docs (`@theme inline`, not a `tailwind.config.js` extension); for Tailwind v3 only,
configure `fontFamily: { sans: ['var(--font-inter)'] }` in `tailwind.config.js` — never
mix the two patterns in one repo. Verify: DevTools Computed Styles on `<h1>` resolves
`font-family` through `--font-sans` to the generated Inter family. Fully-reversible,
CSS/config-only. Rollback: remove the `@theme inline` block and revert to prior CSS/config.

## `display` selection: `swap` vs `optional` — requires Next.js ≥13.2.0

**When to apply:** a swap-CLS complaint on the default (`display: 'swap'`), or a stated
requirement for strict zero swap-CLS more important than guaranteed brand-font display on
a cold first visit.

```tsx
// app/fonts.ts — Next.js 16.3.0 — strict no-swap policy
import { Playfair_Display } from 'next/font/google'

export const display = Playfair_Display({
  subsets: ['latin'],
  display: 'optional',
  preload: true,
  adjustFontFallback: true,
})
```

**Why:** `swap` (default) + `adjustFontFallback` gives immediate readability with a
metrics-matched fallback — the best legibility/brand-fidelity balance for most content.
`optional` has a 100ms block period and **no swap period** afterward — the browser picks
one face for that navigation and never swaps late, a stronger no-shift guarantee, at the
cost of possibly staying in fallback for a slow first visit. These optimize different
priorities; pick per-font, not globally.

**Verify after applying:** throttle Slow 3G with cache disabled — either the custom font
wins the first render or the fallback persists for the whole navigation; it must not
swap late. Lighthouse Layout Shift trace shows no font-swap-caused shift.

**Lock-in / reversibility:** fully-reversible — a single `display` value.

**Rollback:** change `display` back to `'swap'`.

## Migrating off legacy `@next/font` — requires Next.js ≥13.2.0

**When to apply:** a `@next/font` import was found — folded into built-in `next/font` in
v13.2.0.

```diff
-import { Inter } from '@next/font/google'
+import { Inter } from 'next/font/google'
```

**Why / Verify / Lock-in / Rollback:** the import path is the only change — option names
and behavior are identical; a mechanical rename. Verify: `rg -n "from ['\"]@next/font"`
returns zero matches and `next build` compiles; remove the unused dependency if nothing
else imports it. Fully-reversible. Rollback: restore the `@next/font/google`/`local`
import.

## `beforeInteractive` critical script — requires Next.js ≥13.0.0 (App Router)

**When to apply:** a hydration-dependent script (consent manager, bot detector) needs to
load before hydration and is missing or misplaced outside the root layout — **or** the
opposite: a non-critical script (analytics, chat) is on `beforeInteractive` and needs to
move off it.

```tsx
// app/layout.tsx — Next.js 16.3.0
import Script from 'next/script'

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        {children}
        <Script src="https://example.com/cookie-consent.js" strategy="beforeInteractive" />
      </body>
    </html>
  )
}
```

**Why:** `beforeInteractive` scripts "must be placed inside the root layout" and "should
only be used for critical scripts that need to be fetched as soon as possible" — bot
detectors and cookie consent managers are the docs' own named examples. Execution does
not block hydration; the script is always injected into `<head>` regardless of JSX
placement. A non-critical script here actively regresses LCP/TTI by competing for the
earliest fetch slot — move it to `afterInteractive` instead (next recipe).

**Verify after applying:** view page source (raw HTML) — the `<script>` sits inside
`<head>`; Performance trace shows hydration's `Commit` timestamp is not delayed.

**Lock-in / reversibility:** fully-reversible.

**Rollback:** remove the `<Script strategy="beforeInteractive">` block, or restore it if
reverting a migration.

## `afterInteractive` → `lazyOnload` strategy tuning — requires Next.js ≥13.0.0

**When to apply:** analytics/tag-manager scripts sit on the wrong strategy, a background
widget (chat, social embed) is too eager, or `strategy="worker"` /
`experimental.nextScriptWorkers` was found — **unsupported on the App Router at any
version**; current docs state verbatim: "does not yet work with the App Router" and
"`worker` scripts can only currently be used in the `pages/` directory." Treat as
indefinitely unsupported, not a temporary gap.

```tsx
// app/page.tsx — Next.js 16.3.0 — analytics on the documented default strategy
import Script from 'next/script'

export default function Page() {
  return <Script src="https://example.com/analytics.js" strategy="afterInteractive" />
}
```

```tsx
// app/page.tsx — Next.js 16.3.0 — background widget, idle-time load; also the correct App Router
// replacement for strategy="worker"
import Script from 'next/script'

export default function Page() {
  return <Script src="https://widget.example.com/chat.js" strategy="lazyOnload" />
}
```

```diff
 // next.config.ts — remove if targeting App Router
 const nextConfig: NextConfig = {
-  experimental: { nextScriptWorkers: true },
 }
```

**Why:** `afterInteractive` (default) "should be used for any script that needs to load
as soon as possible but not before any first-party Next.js code" — analytics and tag
managers are the named candidates. `lazyOnload` is "injected... during browser idle time
... after all resources on the page have been fetched" — for "background or low priority
scripts." `lazyOnload` + `@next/third-parties` + manual event-priority deferral is the
corpus's documented replacement set for the unusable `worker` strategy.

**Verify after applying:** Network waterfall — `afterInteractive` requests start after
the hydration-start marker; `lazyOnload` requests start near/after the `load` event.
`rg -n 'strategy=\["\x27]worker\["\x27]|nextScriptWorkers'` returns zero matches in
`app/**`.

**Lock-in / reversibility:** fully-reversible — a `strategy` prop change.

**Rollback:** restore the prior `strategy` value.

## Inline script + lifecycle callbacks — requires Next.js ≥12.2.4 (`onReady`)

**When to apply:** an inline `<Script>` is missing `id` (silent de-optimization, no
build error), or `onLoad`/`onReady`/`onError` are not firing.

```tsx
// app/page.tsx — Next.js 16.3.0
'use client'

import { useRef } from 'react'
import Script from 'next/script'

export default function Page() {
  const mapRef = useRef<HTMLDivElement>(null)
  return (
    <>
      <div ref={mapRef} />
      <Script id="show-banner">{`document.getElementById('banner').classList.remove('hidden')`}</Script>
      <Script
        id="google-maps"
        src="https://maps.googleapis.com/maps/api/js"
        strategy="afterInteractive"
        onReady={() => {
          // fires on first load AND every remount (e.g. after client nav)
          new google.maps.Map(mapRef.current!, { center: { lat: -34.397, lng: 150.644 }, zoom: 8 })
        }}
        onError={(e: Error) => console.error('Script failed to load', e)}
      />
    </>
  )
}
```

**Why:** "An `id` property must be assigned for inline scripts in order for Next.js to
track and optimize the script." `onLoad`/`onReady`/`onError` each "does not yet work with
Server Components and can only be used in Client Components" — `'use client'` must be the
first line. Neither `onLoad` nor `onError` pairs with `strategy="beforeInteractive"`; use
`onReady` there instead. `onReady` fires on first load **and** every remount, which is
why it — not `onLoad` — is correct for a widget that must reinitialize after client-side
navigation.

**Verify after applying:** rendered HTML shows `<script id="show-banner">` exactly once
even after client navigation; navigating away and back re-fires `onReady`'s effect
without a full reload.

**Lock-in / reversibility:** fully-reversible.

**Rollback:** remove the added `id`/callbacks/`'use client'` directive.

## `@next/third-parties` GA / GTM — requires separate package install, experimental

**When to apply:** manual GA or GTM `<script>` wiring was found, or either is needed and
the project accepts the package's experimental-stability tier (pin the version).

```bash
npm install @next/third-parties@latest next@latest
```

```tsx
// app/layout.tsx — Next.js 16.3.0
import { GoogleAnalytics, GoogleTagManager } from '@next/third-parties/google'

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <GoogleTagManager gtmId="GTM-XYZ" />
      <body>{children}</body>
      <GoogleAnalytics gaId="G-XYZ" />
    </html>
  )
}
```

```tsx
// app/components/event-button.tsx — Next.js 16.3.0
'use client'
import { sendGAEvent, sendGTMEvent } from '@next/third-parties/google'

export function EventButton() {
  return <button onClick={() => sendGTMEvent({ event: 'buttonClicked' })}>Send</button>
}
```

**Why:** both wrappers "by default... fetch the original scripts after hydration occurs
on the page" — the same `afterInteractive`-equivalent timing a hand-rolled script would
need to replicate manually. GA "automatically tracks pageviews when the browser history
state changes," so client-side navigations send pageview data with no extra config.
**Caution:** this recipe only fixes each container's own bootstrap timing — tags GTM
subsequently injects are outside Next.js's control. Practitioner evidence attributes
~90% of interaction time to GTM processing vs ~10% native code, resolved by manually
delaying GTM-triggered work ~200–250ms relative to first-party handlers; that deferral is
a separate follow-up, not included here.

**Verify after applying:** Network panel — `gtag/js`/GTM container requests fire after
hydration, not blocking initial render; navigating client-side between routes records a
GA pageview via Realtime/`dataLayer` inspection without a full reload.

**Lock-in / reversibility:** component-level-revert — replace with manual `next/script`
wiring; requires re-implementing the post-hydration timing by hand.

**Rollback:** remove `<GoogleAnalytics>`/`<GoogleTagManager>`; replace with a manual
`next/script` snippet if analytics must be retained.

## `@next/third-parties` Maps + YouTube facades — requires separate package install, experimental

**When to apply:** a raw YouTube `<iframe>` or hand-rolled Google Maps JS API embed is
found — these ship the full iframe/API bootstrap even for visitors who never interact.

```tsx
// app/location/page.tsx — Next.js 16.3.0
import { GoogleMapsEmbed, YouTubeEmbed } from '@next/third-parties/google'

export default function Page() {
  return (
    <>
      <GoogleMapsEmbed apiKey={process.env.GOOGLE_MAPS_API_KEY!} height={200} width="100%" mode="place" q="Brooklyn+Bridge,New+York,NY" />
      <YouTubeEmbed videoid="ogfYd705cRs" height={400} params="controls=0" />
    </>
  )
}
```

**Why:** `GoogleMapsEmbed` "uses the `loading` attribute to lazy-load the embed below the
fold" by default. `YouTubeEmbed` "loads faster by using `lite-youtube-embed` under the
hood" — a lightweight poster/preview facade instead of the full YouTube iframe API
bootstrap. Both are opt-in per-component; a hand-placed `<iframe>` gets neither
automatically.

**Verify after applying:** Network panel — the Maps iframe does not request until
scrolled near viewport (`loading="lazy"` in rendered HTML); the YouTube initial payload is
the lightweight facade, not the full iframe API, until the user clicks play.

**Lock-in / reversibility:** component-level-revert — replace with a raw iframe/API embed
to reach parity by hand.

**Rollback:** remove `<GoogleMapsEmbed>`/`<YouTubeEmbed>`; restore the prior raw embed.

## Ordering within this domain

1. Fix external font requests (migrate to `next/font`) and remove `strategy="worker"`/
   `experimental.nextScriptWorkers` first — the most likely live regression or
   developer-time waste chasing a nonexistent bug.
2. Fix `beforeInteractive` misuse next — cheap, reversible, directly protects LCP/TTI.
3. Apply font-quality recipes (`adjustFontFallback`, `subsets`, centralizing font
   declarations) — `minor` cleanups that compound but don't block anything else.
4. Adopt `@next/third-parties` last, and only when a manual script already exists or is
   being added — keep the manual `next/script` fallback path documented given its
   experimental status.

## Conflicts to watch

- Don't stack image LCP-priority work with an above-the-fold decorative font on
  `display: 'optional'` without confirming which one actually gates the page's real LCP
  element — see `references/fix/image-optimization.md` for LCP confirmation.
- `@next/third-parties`'s GTM/GA wrappers only optimize their own container's load
  timing; don't present fixing the wrapper as a complete INP fix when downstream
  GTM-injected tags are the actual measured cause.
- A consent-manager script on `beforeInteractive` and the analytics it gates must not
  both be `beforeInteractive` — only the gate belongs there; the gated tracker moves to
  `afterInteractive` or later once consent resolves.
