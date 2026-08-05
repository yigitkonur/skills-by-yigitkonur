# Fix: dark-light-theme-switching

**Corpus lineage:** dark-light-theme-switching/03-implementation-script-based.md,
dark-light-theme-switching/04-implementation-cookie-based.md,
dark-light-theme-switching/05-implementation-animated-toggle.md,
dark-light-theme-switching/07-pitfalls-hydration-mismatch.md,
dark-light-theme-switching/08-version-lockin-seo-vercel-practitioner.md
**Knowledge baseline:** verified 2026-08-05 against Next.js 16.3.0 docs. Confirm any
config key against the installed package first — see `references/gating/capability-probe.md`.

**This domain is library-optional.** A repo with no `next-themes` dependency is not
automatically missing anything — the detect file's `APPLICABLE-CUSTOM` verdict means a
hand-rolled implementation already exists and should be **adapted**, never replaced.
Every recipe below carries a Library variant (`next-themes`) and a Custom variant
(pre-paint script you own). Apply the variant that matches the repo's actual mechanism.

## Recipe index

| Recipe | Requires | Reversibility | Triggered by |
|---|---|---|---|
| Blocking pre-paint script (no-flash) | none — browser-native `<script>` mechanism | component-level-revert | No anti-flash mechanism at all; naive `useState`+`useEffect`+`localStorage` |
| `suppressHydrationWarning` scope fix | React (any version), any theming mechanism | fully-reversible | Blocking script mutates `<html>` with no `suppressHydrationWarning` |
| Cookie-based SSR theming | `cookies()` (stable since 15.0.0-RC); Server Action for writes | component-level-revert | Already-dynamic/authenticated route wants zero-script correct-on-first-paint theming |
| CSS variable token architecture + Tailwind `dark:` wiring | Tailwind major version determines syntax (v4 vs v3) | fully-reversible | Raw hex values instead of semantic tokens; wrong-major `dark:` wiring syntax |
| Mounted-flag guard for theme-dependent UI | none | fully-reversible | `useTheme()` (or custom hook) read renders conditionally with no mount guard |
| Choose one post-click animation mode | `document.startViewTransition()` optional; browser-native | fully-reversible | Both `disableTransitionOnChange` and an animated View Transition toggle present together |
| Choose theme authority under Cache Components | `cacheComponents: true` (16.0.0+) | fully-reversible (decision, not code) | Cookie read and pre-paint script both mutate `<html>` with no declared winner |

## Blocking pre-paint script (no-flash) — requires none (browser-native mechanism)

**When to apply:** detect found no anti-flash mechanism — a naive `useState` +
`useEffect` + `localStorage` implementation (or nothing at all) that produces a visible
flash-of-wrong-theme on every load where the visitor's preference differs from the
hardcoded server default.

### Library variant — `next-themes`

```bash
npm install next-themes
```

```tsx
// app/layout.tsx — Next.js 16.3.0, next-themes 0.4.6
import { ThemeProvider } from 'next-themes'
import './globals.css'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    // suppressHydrationWarning is REQUIRED: next-themes' injected script
    // mutates this element's class/data-* attribute + inline color-scheme
    // style before React hydrates. Scope: <html>'s own attributes only.
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"           // 'class' toggles Tailwind's .dark selector;
                                       // library default is 'data-theme' if omitted
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange   // pick exactly one post-click mode — see the
                                       // "Choose one post-click animation mode" recipe
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

**Why each non-obvious line exists:**
- `attribute="class"` is required for Tailwind's `.dark` selector to work — the
  library's own default is `'data-theme'`, a different default than most Tailwind
  tutorials assume.
- `suppressHydrationWarning` on `<html>`, not `<body>` or deeper — the script only
  touches `<html>`'s own attributes.
- No `'use client'` on `layout.tsx` — `ThemeProvider` is a Client Component internally.

### Custom variant — adapt this mechanism to a hand-rolled script

**When the repo already has a custom `data-theme`/`class` mutation and no
`next-themes` dependency:** the fix is to bring the *existing* script in line with
the mechanism below, not to install a library on top of working code.

```tsx
// app/layout.tsx — Next.js 16.3.0, custom implementation
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    // Required for the identical reason as the library variant: this script
    // mutates <html> before hydration.
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          // Runs synchronously in <head>, before body paint — no async/defer/module.
          dangerouslySetInnerHTML={{
            __html: `
              (function () {
                try {
                  var stored = localStorage.getItem('theme');
                  var theme = stored === 'light' || stored === 'dark'
                    ? stored
                    : (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
                  document.documentElement.setAttribute('data-theme', theme);
                  document.documentElement.style.colorScheme = theme;
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  )
}
```

**Why each non-obvious line exists:**
- The `try/catch` guards against `localStorage` access throwing in restrictive
  environments (private browsing in some browsers) — the mechanism must not crash
  the page if the read fails.
- `document.documentElement.style.colorScheme` is set inline here for the same
  reason `next-themes`' `enableColorScheme` does it: it must land before paint, not
  wait for a stylesheet.
- `data-theme` (not `class`) matches this repo's existing convention — do not
  silently rename the attribute; every `dark:`/CSS selector in the codebase already
  targets it.

**Verify after applying:**
- Hard-reload (Cmd/Ctrl+Shift+R) with OS in dark mode and no saved preference — no
  white flash before the dark theme paints.
- Toggle the theme — no navigation/refresh (zero new document requests in the
  Network panel); every themed element updates in the same frame.
- View source (curl or "View Page Source", not DevTools' live DOM) — confirms the
  *server*-rendered HTML has the default/no-theme attribute; this is expected and is
  exactly why `suppressHydrationWarning` is required.

**Lock-in / reversibility:** component-level-revert — removing the script/provider
and re-implementing theme state manually is bounded to the layout + toggle
components, not architectural.

**Rollback:** remove the `<ThemeProvider>` (or the inline `<script>`) and the
`suppressHydrationWarning` prop; the app returns to the pre-fix flash behavior.

## `suppressHydrationWarning` scope fix — requires none

**When to apply:** a blocking pre-paint script (either variant above) mutates
`<html>` and `suppressHydrationWarning` is missing, **or** it is present but a
*different* component elsewhere in the tree also mismatches and was wrongly assumed
covered by the same suppression.

```tsx
// app/layout.tsx — Next.js 16.3.0 — the fix is exactly this one prop
<html lang="en" suppressHydrationWarning>
```

**Why this line exists:** `suppressHydrationWarning` "only works one level deep" —
it silences warnings about `<html>`'s own attributes only. It does **not** suppress
mismatches in `<html>`'s children. A component that reads theme state and renders
different output server-side vs. client-side needs the separate mounted-flag guard
below, not a second `suppressHydrationWarning`.

**Verify after applying:** DevTools console shows no `"Text content does not match
server-rendered HTML"` warning on load. If a warning persists after this fix,
confirm it names a component *other than* `<html>` itself — that is the mounted-flag
recipe's job, not this one's.

**Lock-in / reversibility:** fully-reversible — a single prop, deletes cleanly.

**Rollback:** remove `suppressHydrationWarning` from `<html>`; the console warning
returns (harmless but noisy) as long as the script itself still mutates `<html>`.

## Cookie-based SSR theming — requires `cookies()` (stable since 15.0.0-RC)

**When to apply:** the route is already dynamic/authenticated (a dashboard behind a
session cookie anyway), or JS-disabled correctness is a hard requirement. This
mechanism is inherently custom — `next-themes` does not implement cookie-based SSR
theming; adopting it means writing the Server Component read and Server Action
write yourself regardless of whether `next-themes` is also installed for its client
toggle mechanics.

```tsx
// app/layout.tsx — Next.js 16.3.0 — pre-Cache-Components model (cacheComponents: false/unset)
import { cookies } from 'next/headers'

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const cookieStore = await cookies()
  const theme = cookieStore.get('theme')?.value ?? 'light'

  // No suppressHydrationWarning needed here IF no client script also mutates
  // this element post-hydration — the server-rendered class already matches
  // what React expects to hydrate against.
  return (
    <html lang="en" className={theme === 'dark' ? 'dark' : ''}>
      <body>{children}</body>
    </html>
  )
}
```

```tsx
// app/actions/set-theme.ts — Next.js 16.3.0
'use server'

import { cookies } from 'next/headers'

export async function setThemeCookie(theme: 'light' | 'dark') {
  const cookieStore = await cookies()
  cookieStore.set('theme', theme, {
    path: '/',
    maxAge: 60 * 60 * 24 * 365, // 1 year
    sameSite: 'lax',
  })
}
```

```tsx
// components/theme-toggle-cookie.tsx — Next.js 16.3.0
'use client'

import { useTransition } from 'react'
import { setThemeCookie } from '@/app/actions/set-theme'

export function ThemeToggleCookie({ current }: { current: 'light' | 'dark' }) {
  const [isPending, startTransition] = useTransition()

  return (
    <button
      type="button"
      disabled={isPending}
      onClick={() => {
        const next = current === 'dark' ? 'light' : 'dark'
        // Flip the class immediately for instant feedback; the Server Action
        // persists the cookie for the NEXT server render/visit — it does not
        // re-render the already-painted page.
        document.documentElement.classList.toggle('dark', next === 'dark')
        startTransition(() => setThemeCookie(next))
      }}
    >
      Toggle theme
    </button>
  )
}
```

**Why each non-obvious line exists:**
- `cookies().set()` cannot run during Server Component rendering — only in a
  `'use server'` action or a Route Handler, hence the separate action file.
- The client-side `classList.toggle` still runs because the Server Action updates
  the cookie for *future* requests only; without it the user sees no visual change
  until the next full navigation.

**Cost:** calling `cookies()` anywhere in the render tree opts the route into
dynamic rendering — this is documented, expected behavior on a pre-Cache-Components
install, not a bug. On a marketing/static archetype, reading a theme cookie at the
root layout can be the single largest caching regression this domain introduces —
prefer the blocking-script recipe there instead.

**Verify after applying:**
- Disable JavaScript, hard-reload — the theme class is still correct in the raw
  HTML (proves no client-JS dependency, unlike the script recipe).
- Check `next build` output or response headers — confirm the route now reports
  dynamic rendering (`ƒ` marker, or `Cache-Control: private, no-store`) — this is
  the expected cost, not a bug.

**Lock-in / reversibility:** component-level-revert, with a caching-behavior side
effect — reverting the cookie read restores static/cacheable rendering; verify build
output confirms the route returns to static after removal.

**Rollback:** remove the `cookies()` read from the layout and the Server Action;
the route returns to static/cacheable rendering (verify via `next build`).

## CSS variable token architecture + Tailwind `dark:` wiring — version-gated by installed Tailwind major

**When to apply:** components hardcode theme-specific hex values instead of
semantic tokens, or the `dark:` wiring syntax does not match the installed Tailwind
major (probe `package.json`'s `tailwindcss` version first).

```css
/* app/globals.css — Tailwind CSS v4.x, Next.js 16.3.0 */
@import "tailwindcss";

/* v4 is CSS-first: there is no tailwind.config.js darkMode key. This directive
   is what makes `dark:` respond to the .dark class the theming mechanism sets. */
@custom-variant dark (&:where(.dark, .dark *));

:root {
  color-scheme: light;
  --color-background: oklch(1 0 0);
  --color-foreground: oklch(0.145 0 0);
  --color-surface: oklch(0.97 0 0);
  --color-border: oklch(0.9 0 0);
  --color-accent: oklch(0.55 0.2 260);
}

.dark {
  color-scheme: dark;
  --color-background: oklch(0.145 0 0);
  --color-foreground: oklch(0.98 0 0);
  --color-surface: oklch(0.2 0 0);
  --color-border: oklch(0.3 0 0);
  --color-accent: oklch(0.7 0.18 260);
}

@theme inline {
  --color-background: var(--color-background);
  --color-foreground: var(--color-foreground);
  --color-surface: var(--color-surface);
  --color-border: var(--color-border);
  --color-accent: var(--color-accent);
}
```

**Tailwind v3 variant — `darkMode: 'class'` (or `'selector'` in v3.4.1+):**

```js
// tailwind.config.js — Tailwind CSS v3.x only. Do NOT use alongside @custom-variant.
module.exports = {
  darkMode: 'class', // v3.4.1+ renamed this strategy to 'selector'; either string works pre-v4
  // ...rest of config
}
```

**Why each non-obvious line exists:**
- Semantic tokens (`--color-background`, not raw hex) are what make the switch
  instant: only the custom-property *values* change on class flip, no component
  re-render or JS work is required for the visual update to cascade.
- The v4 `@custom-variant` directive and the v3 `darkMode` config key are mutually
  exclusive syntaxes for the same purpose — installing both, or using the wrong one
  for the installed major, silently produces a `dark:` variant that never activates.

**Verify after applying:** toggle the theme and confirm every `bg-background`,
`text-foreground`, etc. utility updates in the same frame; inspect `<html>` in
DevTools to confirm the `.dark` class (or configured attribute) is present when dark
mode is active.

**Lock-in / reversibility:** fully-reversible at the CSS-token level, but changing
`attribute="class"` vs `attribute="data-*"` after the Tailwind wiring is built
requires updating every `dark:`-style selector in the codebase — config-only churn,
not architectural.

**Rollback:** revert `globals.css`/`tailwind.config.js` to raw hex values or the
prior `darkMode` setting; no schema or URL impact.

## Mounted-flag guard for theme-dependent UI — requires none

**When to apply:** a component reads theme state and renders conditionally based on
it (e.g. a toggle icon) without a mount guard — theme is `undefined` on the server
and during the initial client render, so rendering based on it mismatches.

### Library variant — `next-themes`

```tsx
// components/theme-toggle.tsx — Next.js 16.3.0, next-themes 0.4.6
'use client'

import { useEffect, useState } from 'react'
import { useTheme } from 'next-themes'

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    // Fixed-size placeholder, not null, to avoid a layout shift when the real
    // icon pops in one frame later.
    return <div className="h-9 w-9" aria-hidden="true" />
  }

  return (
    <button
      type="button"
      onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
      className="h-9 w-9 rounded-md border border-border bg-surface text-foreground"
      aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} theme`}
    >
      {resolvedTheme === 'dark' ? '☀️' : '🌙'}
    </button>
  )
}
```

**Why `resolvedTheme`, not `theme`:** `theme` reflects the stored preference
(which may literally be `'system'`); `resolvedTheme` is the computed `'light'`/
`'dark'` value the icon actually needs.

### Custom variant — adapt the same guard to a hand-rolled theme hook

```tsx
// components/theme-toggle.tsx — Next.js 16.3.0, custom implementation
'use client'

import { useEffect, useState } from 'react'
import { useCustomTheme } from '@/lib/theme' // repo's existing hook — do not replace it

export function ThemeToggle() {
  const { theme, setTheme } = useCustomTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return <div className="h-9 w-9" aria-hidden="true" />
  }

  return (
    <button
      type="button"
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="h-9 w-9 rounded-md border border-border bg-surface text-foreground"
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
    >
      {theme === 'dark' ? '☀️' : '🌙'}
    </button>
  )
}
```

**The pattern is identical regardless of which hook backs it** — the mounted flag
guards against the same root cause (the value is unknown until the client script
has run and React has mounted), not against anything library-specific.

**When this guard is NOT needed:** the component only calls the theme *setter* and
never renders conditionally on the current value; the component's server-rendered
output is identical regardless of theme; or the value came from the cookie-based
recipe above (the server already knows it at render time — no `undefined`-until-mount
window for that specific value).

**Verify after applying:** DevTools console shows no hydration warning for this
component specifically. Visually confirm the fixed-size placeholder occupies the
same box as the real icon (no layout shift when it pops in).

**Lock-in / reversibility:** fully-reversible — delete the `mounted` state and the
early return; the component reverts to reading theme state unconditionally (and
reintroduces the mismatch).

**Rollback:** remove the `useState`/`useEffect` mount-detection block and the
placeholder branch.

## Choose one post-click animation mode — requires `document.startViewTransition()` for the animated path

**When to apply:** detect found `disableTransitionOnChange` (or an equivalent
custom "suppress all transitions" mechanism) **and** an animated View Transition
toggle present at the same time — per `references/gating/conflicts.md` §5, these are
contradictory as simultaneous systems and must not both apply to the same click path.

**Mode A — instant snap, transitions suppressed (library variant, `next-themes`):**

```tsx
// app/layout.tsx — Next.js 16.3.0, next-themes 0.4.6 (excerpt)
<ThemeProvider attribute="class" disableTransitionOnChange>
  {children}
</ThemeProvider>
```

**Mode A — instant snap, transitions suppressed (custom variant):**

```tsx
// lib/theme.ts — Next.js 16.3.0, custom implementation
// Reproduces the same technique next-themes runs internally.
export function setThemeWithoutTransition(next: 'light' | 'dark') {
  const css = document.createElement('style')
  css.appendChild(
    document.createTextNode(
      `* { transition: none !important; }`
    )
  )
  document.head.appendChild(css)
  document.documentElement.setAttribute('data-theme', next)
  // Force a synchronous reflow before removing the override.
  void window.getComputedStyle(css).opacity
  document.head.removeChild(css)
}
```

**Mode B — one deliberate View Transition wipe (either variant, same code):**

```tsx
// components/theme-toggle-animated.tsx — Next.js 16.3.0
'use client'

import { flushSync } from 'react-dom'
import { useRef } from 'react'

export function ThemeToggleAnimated({
  resolvedTheme,
  setTheme,
}: {
  resolvedTheme: 'light' | 'dark'
  setTheme: (t: 'light' | 'dark') => void
}) {
  const buttonRef = useRef<HTMLButtonElement>(null)

  async function toggleTheme() {
    const next = resolvedTheme === 'dark' ? 'light' : 'dark'

    if (
      !buttonRef.current ||
      !document.startViewTransition ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ) {
      setTheme(next)
      return
    }

    const { top, left, width, height } = buttonRef.current.getBoundingClientRect()
    const x = left + width / 2
    const y = top + height / 2
    const maxRadius = Math.hypot(
      Math.max(x, window.innerWidth - x),
      Math.max(y, window.innerHeight - y)
    )

    const transition = document.startViewTransition(() => {
      flushSync(() => {
        setTheme(next)
      })
    })

    await transition.ready

    document.documentElement.animate(
      {
        clipPath: [
          `circle(0px at ${x}px ${y}px)`,
          `circle(${maxRadius}px at ${x}px ${y}px)`,
        ],
      },
      { duration: 500, easing: 'ease-in-out', pseudoElement: '::view-transition-new(root)' }
    )
  }

  return (
    <button ref={buttonRef} type="button" onClick={toggleTheme} aria-label="Toggle theme">
      {resolvedTheme === 'dark' ? '☀️' : '🌙'}
    </button>
  )
}
```

```css
/* app/globals.css — disable the browser's default cross-fade so only the
   custom circular clip-path animation is visible */
::view-transition-old(root),
::view-transition-new(root) {
  animation: none;
  mix-blend-mode: normal;
}
```

**Why the reduced-motion + feature-detection guard is not optional:** both checks
gate the *entire* animated path, falling back to a plain `setTheme(next)` call — the
toggle never breaks, it just loses the animation on unsupported browsers or reduced
motion.

**Verify after applying:**
- Confirm exactly one mechanism is active for the click path: either `* {
  transition: none }` fires with no visible animation, or the circular wipe plays —
  never both, never neither.
- Enable "prefers reduced motion" in OS settings, reload, click — theme switches
  with no animation.
- `delete document.startViewTransition` in DevTools console before clicking — theme
  still switches correctly via the fallback path.

**Lock-in / reversibility:** fully-reversible — additive, isolated to the toggle
component; removing either mode reverts to the other with zero side effects.

**Rollback:** remove `disableTransitionOnChange` (or the custom suppression call),
or remove the `startViewTransition` wrapper — restoring whichever single mode was
previously in place.

## Choose theme authority under Cache Components — requires `cacheComponents: true` for the conflict to apply

**When to apply:** a cookie read and a pre-paint script both mutate `<html>` with
no declared winner — or the repo is deciding how to theme the root `<html>` element
specifically while adopting Cache Components.

**The honest limit, stated once:** under Cache Components, a Suspense-scoped
`cookies()` read does not de-opt the whole route — but `<html>` itself cannot be
wrapped in `<Suspense>`. There is **no fully-official static-shell-preserving
pattern for cookie-based root-`<html>` theming** as of this corpus's capture. The
corpus found no third mechanism — do not invent one.

**The rule:**
- **Cache-critical root shell** (static/marketing archetype) → the pre-paint script
  is the sole root authority. Cookie reads, if used at all, serve inner content
  only, wrapped in `<Suspense>`.
- **Already-dynamic route** (authenticated dashboard) → cookie SSR is the
  authority; the script must not also run and override it.
- Never run both as independent, un-reconciled sources of truth for the same
  `<html>` attribute.

**Verify after applying:** compare raw server HTML, pre-hydration DOM, and hydrated
DOM — all three must match the chosen authority, with only the expected
root-attribute difference under the script architecture (server sends default,
script sets correct before paint).

**Lock-in / reversibility:** fully-reversible — this is a decision, not a code
change with its own rollback; reverting means picking the other authority and
removing the one that was overridden.

**Rollback:** n/a — re-apply this recipe choosing the other authority.

## Ordering within this domain

1. Fix `suppressHydrationWarning` scope and choose the theme authority (this
   domain's two decision-level recipes) **before** adding the animated toggle —
   an unresolved authority conflict will make the animation appear to flicker for
   reasons unrelated to the animation itself.
2. Install the blocking pre-paint script (library or custom) or cookie-based SSR
   first — the mounted-flag guard and animated toggle both assume a working
   first-paint mechanism already exists.
3. Add the mounted-flag guard to any theme-dependent UI next — cheap, isolated,
   fully reversible.
4. Add the CSS token architecture + Tailwind wiring fix whenever raw hex values or
   a version-mismatched `dark:` syntax is found — independent of the other steps,
   but confirm the Tailwind major first via the capability probe.
5. Choose exactly one post-click animation mode last, once first-paint correctness
   is confirmed working.

## Conflicts to watch

- `references/gating/conflicts.md` §5 — theme animation × `disableTransitionOnChange`
  are contradictory as simultaneous systems; choose exactly one post-click mode.
- `references/gating/conflicts.md` §6 — the Cache Components root-`<html>` gap; no
  third mechanism exists, do not invent one.
- Shares the root-`<html>`-attribute-cannot-be-Suspended constraint with
  `instant-i18n-locale-switching` — a fix touching one domain's root-attribute
  strategy should stay consistent with the other if both are present in the same
  root layout.
