# Fix: image-optimization

**Corpus lineage:** image-optimization/04-implementation-patterns.md, image-optimization/05-config-and-migration.md, image-optimization/08-platform-seo-practitioner.md
**Knowledge baseline:** verified 2026-08-05 against Next.js 16.3.0 docs. Confirm any
config key against the installed package first — see `references/gating/capability-probe.md`.

## Recipe index

| Recipe | Requires | Reversibility | Triggered by |
|---|---|---|---|
| Hero/LCP image | `next/image` 13.x+ | fully-reversible | Confirmed LCP image with no early-load signal, or bad `sizes` |
| `priority` → successor | Next.js ≥16.0.0 for deprecation note | fully-reversible | `priority` found; fix shared wrapper when one exists |
| Responsive grid/card image | none | fully-reversible | `fill` without matching `sizes`, or `sizes="100vw"` on a grid |
| `fill` + aspect-ratio | none | fully-reversible | `fill` with no reserved parent height — CLS risk |
| Blur placeholder | none | fully-reversible | `placeholder="blur"` missing `blurDataURL` on non-static `src` |
| 16.x `next.config` images block | Next.js ≥16.0.0 for enforcement | fully-reversible (security-sensitive for allowlist) | `images.domains`, missing allowlist entries, unconfigured cost keys |
| 15→16 migration diff | Upgrading 15.x → 16.x | component-level-revert | Probe shows next <16.0.0 moving to ≥16.0.0 |

## Hero/LCP image — requires Next.js ≥13.0.0 (`fetchPriority` pass-through ≥13.3.0)

**When to apply:** the detect audit confirmed (via Lighthouse/DevTools, not assumption)
which single image is the LCP element, and that image currently has no early-load
signal — or has `sizes` missing/wrong.

```tsx
// app/page.tsx — Next.js 16.3.0
import Image from 'next/image'
import heroPhoto from '../public/hero.jpg' // static import: width/height/blurDataURL auto-derived

export default function Page() {
  return (
    <Image
      src={heroPhoto}
      alt="Product hero shot"
      sizes="100vw" // hero renders full viewport width on every breakpoint in this layout
      // Single confirmed LCP element — signal early loading. Current docs recommend
      // fetchPriority/loading over preload in most cases.
      fetchPriority="high"
      loading="eager"
      style={{ width: '100%', height: 'auto' }}
      placeholder="blur" // blurDataURL is auto-populated for the static import
    />
  )
}
```

**Why each non-obvious line exists:** `sizes="100vw"` matches the real rendered width;
missing `sizes` produces only a limited 1x/2x `srcset` instead of a full responsive
set, and defaults to assuming full-viewport width once `fill` is involved.
`fetchPriority="high"` + `loading="eager"` is what current docs recommend over
`preload` in most cases. `placeholder="blur"` needs no manual `blurDataURL` here —
auto-added for static imports unless the image is animated.

**Alternative — `preload` for a single, viewport-stable known LCP image only:**
`<Image src={heroPhoto} alt="..." sizes="100vw" preload />` inserts a `<link>` in
`<head>`. Use only when the image is the LCP element on every viewport — never when
multiple images could be the LCP element depending on viewport, never on more than one
image per page, and never stacked with `priority` (deprecated in 16.0.0).

**Verify after applying:**
- DevTools → Network panel: hero request starts near the top of the waterfall, with
  `fetchpriority: high` in the Priority column. Lighthouse → Performance: LCP element
  callout points at this `<img>`; "Preload Largest Contentful Paint image" audit
  passes if `preload` was used. Confirm no more than one or two images on the page
  carry an early-load signal.

**Lock-in / reversibility:** fully-reversible — props delete cleanly, no schema/URL
impact. **Rollback:** remove `fetchPriority`, `loading="eager"`, and/or `preload`; the
image reverts to default lazy-loading.

## `priority` → successor migration — deprecated in Next.js 16.0.0, still functional

**When to apply:** detect gate row 1 found `priority` prop usage. Confirm via the
capability probe whether the installed version is ≥16.0.0 (deprecated-but-functional)
or below (still the current recommended API — do not migrate on pre-16 installs).
**If many call sites pass `priority` through a shared wrapper component** (e.g.
`components/project-image.tsx`), fix the wrapper's prop-forwarding logic once — do not
touch every caller individually.

```diff
 // components/project-image.tsx — Next.js 16.3.0
-<Image src={src} alt={alt} priority />
+<Image src={src} alt={alt} fetchPriority="high" loading="eager" />
```

Or, for one known stable LCP image: `<Image src={hero} alt="Hero" preload />`
(replacing `<Image src={hero} alt="Hero" priority />`).

**Why each non-obvious line exists:** `priority` still works on 16.x — deprecated, not
removed; this is a `minor` severity cleanup, not an urgent fix. `fetchPriority="high"`
+ `loading="eager"` is the direct successor for the common case; `preload` is the
successor only for a single confirmed LCP image. Never leave `priority` on more than
one image per page even before migrating — the underlying anti-pattern predates the
deprecation and remains wrong either way.

**Verify after applying:** grep confirms zero remaining `priority` props on `<Image>`
(or the count matches the known deferred inventory); re-run the Hero/LCP verification
above — request timing must stay unchanged after the swap.

**Lock-in / reversibility:** fully-reversible — a straight prop swap. **Rollback:**
restore `priority` in place of `fetchPriority`/`loading`/`preload`; it still functions
identically to its pre-16 behavior on any 16.x install.

## Responsive grid/card image — requires Next.js ≥13.0.0

**When to apply:** `fill` is used in a repeated card/grid layout with `sizes` missing
or set to `100vw`/an inaccurate value on a multi-column desktop layout.

```tsx
// components/ProductCard.tsx — Next.js 16.3.0
import Image from 'next/image'

export function ProductCard({ src, alt }: { src: string; alt: string }) {
  return (
    <div className="grid-element" style={{ position: 'relative', aspectRatio: '4 / 3' }}>
      <Image
        fill
        src={src}
        alt={alt}
        // 4 cards across on desktop (>=1200px), 2 across on tablet (>=768px), 1 across on mobile
        sizes="(min-width: 1200px) 25vw, (min-width: 768px) 50vw, 100vw"
        style={{ objectFit: 'cover' }}
      />
    </div>
  )
}
```

**Why each non-obvious line exists:** `sizes` is authored directly from the CSS grid
breakpoints (4 cols ≥1200px → 25vw, 2 cols ≥768px → 50vw, 1 col below → 100vw) — not
guessed; a narrower slot produces a blurry image, a wider slot wastes bytes.
`aspectRatio: '4 / 3'` on the parent reserves box height before the image paints —
`fill` alone does not guarantee a non-zero-height container. `objectFit: 'cover'` crops
to fill the reserved box rather than distorting the image.

**Verify after applying:**
- DevTools → Network panel: at desktop width, the requested `w=` on `/_next/image?...`
  should be a smaller `deviceSizes`/`imageSizes` entry (e.g. ~384–640px), not
  1920/2048/3840 — resize the viewport and confirm it tracks.
- Lighthouse → "Properly size images" audit does not flag this component; toggle
  DevTools "Layout Shift Regions" and confirm no shift when the image loads.

**Lock-in / reversibility:** fully-reversible — `sizes` is a prop, no schema/URL
impact. **Rollback:** remove or widen `sizes` back to its prior value.

## `fill` + positioned parent + aspect-ratio — requires Next.js ≥13.0.0

**When to apply:** `fill` is used on an image whose real pixel dimensions are unknown
at build time (remote/CMS source) and the parent has no reserved height —
CLS-producing per detect gate.

```tsx
// components/RemoteHero.tsx — Next.js 16.3.0
import Image from 'next/image'

export function RemoteHero({ photoUrl }: { photoUrl: string }) {
  return (
    <div style={{ position: 'relative', width: '100%', aspectRatio: '16 / 9' }}>
      <Image
        src={photoUrl}
        alt="Remote hero"
        fill
        sizes="100vw"
        style={{ objectFit: 'cover' }}
      />
    </div>
  )
}
```

**Why each non-obvious line exists:**
- `position: 'relative'` on the parent is required by `fill`; `aspectRatio: '16 / 9'`
  reserves the box before the network response returns — Next.js has no build-time
  access to remote files, so CSS `aspect-ratio` substitutes for build-time dimension
  inference.
- `sizes="100vw"` is required alongside `fill`; omitting it makes the browser assume
  full-viewport width regardless of the real rendered size.
- `remotePatterns` must allow this host — see the config recipe below.

**Verify after applying:** Lighthouse CLS diagnostics ("Avoid large layout shifts")
show zero shift attributable to this element — the reserved box holds size before the
network response returns.

**Lock-in / reversibility:** fully-reversible — CSS/prop-only change. **Rollback:**
remove `fill`/`aspectRatio` and switch to explicit `width`/`height` if real
dimensions become known, or delete the CSS reservation to restore prior behavior.

## Blur placeholder: static import vs remote — requires Next.js ≥11.0.0

**When to apply:** `placeholder="blur"` is set without a `blurDataURL` on a
non-static-import `src` (remote/dynamic source) — this either throws/warns or silently
shows no blur.

**Static import (automatic — no action needed beyond the prop):**

```tsx
// components/TeamPhoto.tsx — Next.js 16.3.0
import Image from 'next/image'
import teamPhoto from '../public/team.png'

export function TeamPhoto() {
  return (
    <Image src={teamPhoto} alt="Team photo" placeholder="blur" /> // blurDataURL auto-generated at build time
  )
}
```

**Remote image (manual `blurDataURL` required):**

```tsx
// components/RemoteTeamPhoto.tsx — Next.js 16.3.0
import Image from 'next/image'

export function RemoteTeamPhoto({ src, blurDataURL }: { src: string; blurDataURL: string }) {
  return (
    <Image
      src={src}
      alt="Team photo"
      width={800}
      height={533}
      placeholder="blur"
      blurDataURL={blurDataURL} // must be generated and supplied by the caller
    />
  )
}
```

**Why each non-obvious line exists:** static imports get `blurDataURL` added
automatically (unless animated); remote/dynamic sources never do — Next.js has no
build-time access to remote files. For remote sources, generate the tiny data URL at
ingestion/build time (e.g. with the `plaiceholder` library, named directly in Next.js
docs as one of two options) and store it with the image record (CMS field or DB
column), passing it as `blurDataURL` at render time — a practitioner convention, not a
built-in function. Keep it small: a large `blurDataURL` inflates HTML/RSC payload — a
very small source image (≤10px) is the recommended input.

**Verify after applying:** throttle to "Slow 4G" in DevTools and confirm a blurred
low-res placeholder paints before the final image with no gray/blank flash; inspect
the DOM for a `data:image/...` value in the placeholder background. If a blur overlay
appears to linger, retest with `next build && next start` first — App Router `next dev`
has a known hydration-delay artifact that does not reproduce in production.

**Lock-in / reversibility:** fully-reversible — prop/data addition, no schema
migration for the component itself (`migration-required` only for the *pipeline*
storing `blurDataURL`, per `references/gating/lockin-reversibility.md`). **Rollback:**
remove `placeholder="blur"` and `blurDataURL`.

## 16.x `next.config` images block — requires Next.js ≥16.0.0 for full enforcement

**When to apply:** `images.domains` found in config, a remote host missing from
`remotePatterns`, a local query-string `src` missing from `localPatterns`, or
cost-relevant keys (`qualities`, `formats`, `minimumCacheTTL`) left unconfigured on a
repo where variant cost matters.

```ts
// next.config.ts — Next.js 16.3.0
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  images: {
    // Remote allowlist replaces deprecated `domains`.
    remotePatterns: [
      { protocol: 'https', hostname: 'assets.example.com', port: '', pathname: '/account123/**', search: '' },
    ],
    // Required in 16.x if any local <Image src> ever carries a query string.
    localPatterns: [{ pathname: '/assets/images/**', search: '' }], // e.g. '?v=1' to allow one exact query value
    // Defaults shown explicitly for clarity; omitting these falls back to the same values.
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [32, 48, 64, 96, 128, 256, 384], // '16' removed from default in 16.0.0
    formats: ['image/webp'], // AVIF is opt-in: ['image/avif', 'image/webp']
    minimumCacheTTL: 14400, // 4 hours — 16.0.0 default (was 60s in 15.x)
    qualities: [75], // 16.0.0 default and now required allowlist (was unrestricted 1-100 in 15.x)
    dangerouslyAllowSVG: false, // leave false unless SVGs are explicitly needed
    contentDispositionType: 'attachment', // default since 15.0.0
    // No documented default string for contentSecurityPolicy; set it explicitly
    // whenever dangerouslyAllowSVG is true (docs' own recommended value):
    // contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },
}

export default nextConfig
```

**Why each non-obvious line exists:** `remotePatterns` (not `domains`) restricts
protocol/host/port/path/search; `domains` cannot restrict any of those and is
deprecated since v14. `localPatterns` with an explicit `search` is required starting
in 16.0.0 for any local `<Image src>` carrying a query string, or the request 400s.
`imageSizes` no longer includes `16` by default in 16.0.0 — very few projects served
16px images, so the array shrank to reduce `srcset` payload. `qualities` is a required
allowlist starting in 16.0.0 (was unrestricted 1–100) — a `quality` prop outside the
array is coerced to the nearest allowed value. `minimumCacheTTL` changed from 60s to
14400s (4h) in 16.0.0, to reduce revalidation cost for images without an upstream
`cache-control` header. `dangerouslyAllowSVG: false` stays the safe default; enabling
it without a matching `contentSecurityPolicy` and `contentDispositionType:
'attachment'` is unsafe.

**Vercel cost note (constrains how many `qualities`/`deviceSizes`/`formats` to set):**
Vercel bills Image Transformations and Image Cache Writes on every cache **MISS** and
**STALE** — never on a HIT. Maximum warmable variant count is approximately
`source images × used widths × allowed qualities × negotiated formats`; every actually
requested combination can produce one transformation and one cache-write. A 20,000-image
site with 8 widths, 3 qualities, and AVIF+WebP has a theoretical ceiling of
`20,000 × 8 × 3 × 2 = 960,000` — WebP-only + 1 quality collapses that 6x. Before
widening `qualities`/`deviceSizes`/`formats`, narrow `qualities` to values actually used
in code (cross-reference detect command #6/#7), keep `formats` to `['image/webp']`
unless AVIF's smaller-but-slower-to-encode tradeoff is deliberately accepted, and raise
`minimumCacheTTL` for images that don't change within a month (`2678400` seconds).

**Verify after applying:**
- `next build` completes with no `Invalid images config` error.
- Load every page with a local query-string image and every page with a remote image;
  confirm no `400 Bad Request` from `/_next/image` in either case. Cross-check every
  distinct `quality={n}` literal found by detect command #6 against the configured
  `qualities` array — add the value or accept nearest-value coercion.

**Lock-in / reversibility:** fully-reversible for `remotePatterns`/`localPatterns`
narrowing and quality/format/TTL tuning — config-only. Treat **broadening** an
allowlist as security-sensitive even though it is technically reversible.
**Rollback:** revert the `images` block to its prior state; a wider `minimumCacheTTL`
leaves existing cached variants stale-for-longer until natural expiry — Vercel
supports manual/programmatic purge, and self-hosted deployments may need to delete
`<distDir>/cache/images` or change `src` to force invalidation.

## 15→16 migration diff

**When to apply:** the capability probe shows the installed `next` version crossing
from <16.0.0 to ≥16.0.0. Treat this as one reviewed migration unit, not a
free-standing config edit.

```diff
 // next.config.ts
 const nextConfig: NextConfig = {
   images: {
-    domains: ['assets.acme.com'],
+    remotePatterns: [{ protocol: 'https', hostname: 'assets.acme.com' }],
+    // Add every distinct quality={n} value found in the codebase, or accept
+    // coercion-to-nearest-value under the new [75]-only default.
+    qualities: [50, 75, 100],
+    // Add localPatterns for any local <Image src> that carries a query string.
+    localPatterns: [{ pathname: '/assets/**', search: '?v=1' }],
+    // Explicit if sub-60-second freshness is required; otherwise accept the new 4h default.
+    // minimumCacheTTL: 60,
   },
 }
```

```diff
-<Image src={hero} alt="Hero" priority />
+<Image src={hero} alt="Hero" fetchPriority="high" loading="eager" />
```

**Migration checklist (image-scoped):**
1. Replace every `images.domains` entry with an equivalent `remotePatterns` object.
2. Grep local `<Image src=".../*?...">` (query strings); add matching `localPatterns`
   entries with an explicit `search` value.
3. Grep every `quality={n}` literal; add each distinct value to `qualities`, or accept
   coercion-to-nearest-value. Set `minimumCacheTTL` explicitly if sub-60-second
   freshness is required; otherwise accept the new 4-hour default.
4. Replace `priority` with `preload`, or better, `fetchPriority="high"` /
   `loading="eager"` — opportunistic, `priority` still works on 16.x.
5. Replace `next/legacy/image` imports with `next/image`; re-audit dimensions/`sizes`,
   since legacy-image layout modes do not map 1:1.
6. Self-hosting outside Vercel: confirm `sharp` is installed (`npm i sharp`).
7. `npx @next/codemod@canary upgrade latest` handles the mechanical parts; it does
   **not** auto-migrate steps 1–5 above.

**Verify after applying:** `next build` completes with no `Invalid images config`
error; load every page with a local query-string image and every page with a remote
image and confirm no 400 from `/_next/image`. Diff the effective `qualities` and
`minimumCacheTTL` against pre-migration behavior and confirm the change is
intentional, not silently accepted.

**Lock-in / reversibility:** component-level-revert — each key change is mechanical
and individually reversible, but review the diff as one migration unit since the keys
interact (e.g. a `qualities` gap combined with coercion can silently change visual
output across many images at once). **Rollback:** revert `next.config` to the
pre-migration values and restore `priority` props; only safe while still pinned to a
<16.0.0 install, since `qualities` and `localPatterns` enforcement do not exist below
16.0.0 to roll back to.

## Ordering within this domain

1. Fix layout reservation (`fill` + aspect-ratio, or `width`/`height`) and `sizes`
   authoring **before** touching `quality` or priority signals.
2. Migrate `priority` → successor and `next/legacy/image` → `next/image` next.
3. Apply the `16.x next.config images block` only after the above, so the allowlist
   reflects the final set of image sources and quality values actually used.
4. Run the 15→16 migration diff as one reviewed unit only if the capability probe
   confirms the version is crossing that boundary — never apply 16.x-only keys below
   16.0.0.

## Conflicts to watch

- `dangerouslyAllowSVG: true` without a matching `contentSecurityPolicy` and
  `contentDispositionType: 'attachment'` is unsafe — never enable one without the other.
- Widening `remotePatterns`/`localPatterns` to fix a 400 must stay as narrow as
  possible — a wildcard `hostname: '**'` fix is itself a new finding, not a resolution.
- Increasing `formats`/`qualities` to fix a visual-quality complaint directly grows
  the Vercel variant space — check the cost note above first.
