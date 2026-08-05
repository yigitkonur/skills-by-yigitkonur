# Detect: dark-light-theme-switching

**Corpus lineage:** dark-light-theme-switching/00-overview.md,
dark-light-theme-switching/01-mechanism-and-paint-sequence.md,
dark-light-theme-switching/02-when-to-use.md,
dark-light-theme-switching/07-pitfalls-hydration-mismatch.md,
dark-light-theme-switching/08-version-lockin-seo-vercel-practitioner.md

## Applicability gate

Theming is **not a Next.js framework feature** — there is no config flag, file
convention, or `next.config` key to probe via `config-schema.js`. Two independent
mechanisms exist instead: the `next-themes` npm package (probe `package.json`
dependencies + `node_modules/next-themes/package.json` resolution — a package
lookup, not a schema lookup) and a hand-rolled equivalent built on the same
documented mechanism (blocking pre-paint `<script>`, `data-theme`/`class`
attribute mutation on `<html>`). **Both are equally valid; neither is "the
correct" one.** A repo with a working custom implementation is not missing a
dependency — it already solved the problem the library also solves.

| Feature / config key | Introduced | Requires | Removed-in | Gate rule |
|---|---|---|---|---|
| `next-themes` package | v0.4.6 (npm-latest, published 2025-03-11) | React peer `^16.8\|\|^17\|\|^18` (works with React 19 in practice, install-time warning) | n/a — no release in ~17 months as of corpus capture, not archived | Probe `package.json` dependencies + `node_modules/next-themes` resolution. `present` → this repo is on the **library path**; audit its config/props. `absent` → check the custom-mechanism row below before concluding no theming exists. |
| Custom theming mechanism (inline blocking `<script>` mutating `<html>`'s `class`/`data-theme` before hydration, no `next-themes` import) | Practitioner pattern, no version | Root layout owns `<html>` | n/a | `next-themes` absent AND a blocking inline script mutating `<html>`'s theme attribute is found in the root layout → verdict **APPLICABLE-CUSTOM**. Audit the *mechanism* against this domain's pattern (pre-paint blocking, `suppressHydrationWarning`, mounted-flag reads) — never propose installing `next-themes` as "the fix" for a working custom implementation; that is a false positive, not a finding. |
| `suppressHydrationWarning` (React, not Next.js-specific) | Stable, official, no version gate | Any script-based (library or custom) `<html>` mutation | n/a | Always APPLICABLE whenever a pre-paint script (either path) mutates `<html>` attributes. Its absence alongside a live script is the single highest-value finding in this domain. |
| `cookies()` async API | Stable since 15.0.0-RC | none | n/a | Always APPLICABLE on any 16.x install (well above the floor). Gate the *cost* of using it for theming (forces dynamic rendering unless Suspense-scoped under Cache Components), not its availability. |
| `cacheComponents: true` + Suspense-scoped `cookies()` reads | Stable, opt-in since 16.0.0 | Node.js runtime | n/a | Probe per `references/gating/capability-probe.md`. `absent` → every theme-cookie read (root or content) forces full-route dynamic under the pre-16 model — do not describe Suspense-narrowing as available. `present` → the narrowing applies to theme-dependent *content* only; the root-`<html>` gap below still applies regardless. |
| Tailwind `dark:` variant mechanism (`@custom-variant dark` v4 vs `darkMode: 'class'`/`'selector'` v3) | v4 current, CSS-first; v3 config-file based | Installed `tailwindcss` major version | v3 config-file approach superseded by v4, not hard-removed | Probe `tailwindcss` in `package.json`/`node_modules`. Major **4** → expect `@custom-variant dark (&:where(.dark, .dark *));` in CSS; a lingering `tailwind.config.js` `darkMode` key is dead config. Major **3** → expect `darkMode: 'class'`/`'selector'`; a `@custom-variant` block will not be recognized by the v3 build. |
| `document.startViewTransition()` (theme-toggle usage) | Baseline 2025 (Chromium 111+, Safari 18+, Firefox 144+) | none — browser-native | n/a | Always APPLICABLE as progressive enhancement. Gate the *finding* (missing feature-detection guard, missing `prefers-reduced-motion` check, or simultaneous use with `disableTransitionOnChange`), never the API's existence. |

## Detection commands

Read-only only. Every command maps 1:1 to a gate row or a pitfall signature below.

```bash
# 1. next-themes adoption — import usage (library path signal)
rg -n "from ['\"]next-themes['\"]" --glob '*.{tsx,jsx,ts,js}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 2. next-themes declared dependency + resolved version (confirms library path + maintenance-gap context)
rg -n '"next-themes"' <target-repo-root>/package.json
```

```bash
# 3. Custom blocking pre-paint script — inline <script> in the root layout mutating theme state
# (heuristic: looks for a dangerouslySetInnerHTML/inline script near localStorage + theme identifiers)
rg -n 'dangerouslySetInnerHTML|<script' --glob 'app/layout.{tsx,jsx}' -A3 -B3 <target-repo-root> | rg -n 'localStorage|data-theme|classList|prefers-color-scheme'
```

```bash
# 4. suppressHydrationWarning presence on <html> — confirm scope is exactly <html>, not deeper
rg -n '<html\b' -A2 --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 5. useTheme() (or a custom theme hook) calls — inventory components reading theme state
rg -n '\buseTheme\(' --glob '*.{tsx,jsx}' -g '!**/node_modules/**' -g '!**/*.test.*' <target-repo-root>
```

```bash
# 6. Mounted-flag guard presence near useTheme — heuristic only; confirm manually per finding
rg -n 'useState\(false\)' -B2 -A6 --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root> | rg -n 'mounted|useTheme'
```

```bash
# 7. Cookie-based theme reads — server-side theming source of truth
rg -n "cookies\(\).*get\(['\"]theme['\"]\)|cookieStore\.get\(['\"]theme['\"]\)" --glob '*.{tsx,ts}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 8. color-scheme CSS property presence — confirms native-UI (scrollbar/form-control) palette hint
rg -n 'color-scheme\s*:' --glob '*.css' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 9. Tailwind major version — gates which dark: wiring syntax is expected (command 10)
rg -n '"tailwindcss"' <target-repo-root>/package.json
```

```bash
# 10. Tailwind dark: wiring — v4 @custom-variant vs v3 darkMode config key (cross-check against #9)
rg -n '@custom-variant\s+dark|darkMode\s*:' --glob '*.{css,js,ts}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 11. Conflict #5 signal — disableTransitionOnChange and startViewTransition co-existing
rg -n 'disableTransitionOnChange' --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root>
rg -n 'startViewTransition' --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 12. Root-layout theme source-of-truth inventory — both a cookie read AND a script/library
# provider present is the "two sources of truth" pitfall; run both, compare results by hand
rg -n "cookies\(\)" --glob 'app/layout.{tsx,jsx}' <target-repo-root>
rg -n "ThemeProvider|dangerouslySetInnerHTML" --glob 'app/layout.{tsx,jsx}' <target-repo-root>
```

## Domain severity rubric

- **critical** — removed API/flag in live use; architectural precondition violated; user-visible breakage likely or build/runtime failure likely
  - No anti-flash mechanism at all (naive `useState`+`useEffect`+`localStorage`, no script, no cookie) → guaranteed flash-of-wrong-theme on every load for every visitor whose preference differs from the hardcoded default.
  - Cookie-derived server class **and** a pre-paint script **both** mutate `<html>` independently, with no declared authority → the two can disagree, producing a visible flicker or race between a Server Action cookie write and the next full load.
  - `attribute="class"` omitted from `ThemeProvider` (or the custom script targets `data-theme` while Tailwind is wired for `.dark`) while Tailwind's `dark:` variant assumes a `.dark` class → dark mode silently never activates.
- **major** — P0-tier practice absent or misconfigured for this archetype; likely measurable CWV/UX harm
  - Blocking script (library or custom) mutates `<html>` but `suppressHydrationWarning` is missing → guaranteed hydration-mismatch console warning on every load; if the mismatch reaches a text-content diff, React logs the class of error this domain exists to prevent.
  - A theme-cookie read at the root layout/page level on a static/marketing archetype with `cacheComponents` absent (or the read targets the root `<html>` attribute even with Cache Components present) → forces the route fully dynamic, the single largest caching regression this domain can introduce.
  - Missing `color-scheme` CSS property (neither `enableColorScheme` nor a CSS declaration) → native browser UI (scrollbars, form controls) renders in the wrong palette even though app content is themed correctly.
- **minor** — stable opt-in not adopted; deprecated-but-still-functional surface; quality gap without current breakage
  - `next-themes` pinned with no release in ~17 months and open issues matching the repo's exact `enableSystem`/`attribute`/`disableTransitionOnChange` combination — verify against the specific reported issue before treating it as risk.
  - Tailwind v3 `darkMode: 'class'`/`'selector'` config retained after an upgrade to Tailwind v4 — dead config key, not currently broken.
  - `View Transitions` animated toggle missing the `prefers-reduced-motion` guard or the `!document.startViewTransition` feature-detection guard.
- **informational** — intentional divergence, wrapper indirection, or a note a fixer should know, but not a task by itself
  - Repo deliberately has no theming at all — valid, zero cost to skip.
  - `next-themes` React 19 "script tag" console warning (documented open, cosmetic-only upstream issue) — functionality unaffected.
  - `color-scheme` set redundantly in both CSS and `enableColorScheme` — belt-and-suspenders, deliberate.
  - `forcedTheme` (or an equivalent custom override) intentionally pinning specific routes to one theme (e.g. print/embed views).

## False-positive filters

- Comments/docstrings mentioning `useTheme`, `data-theme`, `darkMode`, etc. do not count as live usage.
- Test files (`*.test.*`, `*.spec.*`, `__tests__/**`) are excluded.
- `next-themes`' own default `attribute="data-theme"` (not `class`) is **not** itself a finding — only flag it when it conflicts with a detected Tailwind `dark:` wiring that assumes `.dark`.
- Theme-cookie reads for *content* deep in the tree, wrapped in `<Suspense>`, under `cacheComponents: true` are the documented, correct pattern — do not flag as a caching regression; only the **root `<html>` attribute** case has the unresolved Suspense gap.
- A deliberately single-theme app (`forcedTheme`/equivalent custom constant, no toggle UI) is informational, not a missing feature.
- `suppressHydrationWarning` found elsewhere in the tree unrelated to theming (e.g. on a `<time>` element for locale-formatted dates) is not a theme finding.
- A component that only calls the theme *setter* (never reads `theme`/`resolvedTheme` conditionally) needs no mounted-flag guard — do not flag its absence.

## Evidence format — what each finding file must contain

Every finding the audit subagent writes under `findings/dark-light-theme-switching/`
must include:
- `file:line` (exact)
- literal matched text (copied from rg/grep output)
- which gate row or pitfall signature it maps to
- severity
- one-line why-this-matters (verbatim or near-verbatim from the corpus-derived prose below)
- suggested fix recipe section name from `references/fix/dark-light-theme-switching.md`
- **which variant applies** — library (`next-themes`) or custom — so the fix agent reads the matching recipe half, not both

## Pitfall signatures

| Failure signature | Cause | Fix direction | Recipe section |
|---|---|---|---|
| `"Text content does not match server-rendered HTML"` mentioning `<html>`'s class/data attribute | Missing `suppressHydrationWarning` on `<html>` while a blocking script (library or custom) mutates it | Add `suppressHydrationWarning` to `<html>` | Blocking pre-paint script (library or custom variant) |
| Same warning, about a component deep in the tree (e.g. a toggle icon) | Component reads theme state and renders conditionally without the mounted-flag guard | Apply the mounted-flag pattern — the root `<html>` suppression does not cover it | Mounted-flag guard for theme-dependent UI |
| White/wrong-theme flash on every load | No pre-paint mechanism at all | Add a blocking pre-paint script or cookie-based SSR | Blocking pre-paint script / Cookie-based SSR theming |
| Theme rapidly flashes back and forth, sometimes with no interaction | Reported `next-themes` bug pattern tied to a specific config combo (`enableSystem={false}`, `attribute="class"`, `disableTransitionOnChange`) | Verify against the exact reported config before assuming a general library flaw | n/a — reproduce against issue #323 config first |
| Route unexpectedly loses static/ISR caching after adding theme-cookie logic | `cookies()` read at layout/page level without Suspense-scoping under Cache Components | Suspense-scope inner content; keep the pre-paint script as sole root authority | Cookie-based SSR theming / Choose theme authority under Cache Components |
| `"Encountered a script tag while rendering React component..."` | React 19 flags `next-themes`' injected `<script>` as a false positive; script still runs correctly | No fix required — cosmetic, open upstream, functionality unaffected | n/a — informational only |
| Stale extra class (e.g. `high-contrast`) stuck on `<html>` after switching away from a multi-class theme value | Reported architectural limitation of multi-class theme mapping | Avoid multi-class theme values, or clear the previous class set explicitly on switch | n/a — architectural limitation, avoid the pattern |
| Two sources of truth (cookie + script) disagree about `<html>`'s class | Both mechanisms mutate `<html>` independently with no declared authority | Pick exactly one root authority per `references/gating/conflicts.md` §6 | Choose theme authority under Cache Components |

## Cross-domain interactions

1. Shares the exact **root-`<html>`-attribute-cannot-be-Suspended** constraint with
   `instant-i18n-locale-switching` (`lang`/`dir` there, `class`/`data-theme` here) — see
   `references/gating/conflicts.md` §6. Any general Next.js fix for one constraint likely
   applies to both.
2. Depends on `rendering-strategy-caching`'s `cacheComponents` probe result: if absent,
   every theme-cookie read forces full-route dynamic regardless of Suspense placement —
   downgrade any "Suspense-scoped narrowing" recommendation to NOT APPLICABLE until that
   flag is confirmed `present`.
3. `references/gating/conflicts.md` §5 — `disableTransitionOnChange` and an animated View
   Transition toggle are contradictory as simultaneous systems; a finding matching both
   commands #11 above is `major`, not two independent `minor` findings.

## Reference pointer

Fix recipes for this domain live in `references/fix/dark-light-theme-switching.md`.
