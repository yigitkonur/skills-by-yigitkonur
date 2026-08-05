# Detect: font-script-optimization

**Corpus lineage:** font-script-optimization/00-overview.md, font-script-optimization/03-when-to-use.md, font-script-optimization/07-pitfalls.md, font-script-optimization/08-version-lockin-seo-vercel-practitioner.md

## Applicability gate

`next/font` and `next/script` are core, always-installed App Router APIs — no capability
probe is needed for their existence. `@next/third-parties` is a **separate npm package**;
probe `package.json`/`node_modules` for it, not the config schema. `experimental.nextScriptWorkers`
is a `next.config` key — probe it in `config-schema.js` per
`references/gating/capability-probe.md`, but its presence in the schema never means it is
usable on the App Router (see row below).

| Feature / config key | Introduced | Requires | Removed-in | Gate rule |
|---|---|---|---|---|
| `next/font/google` | `@next/font` v13.0.0 → renamed `next/font` v13.2.0 | none (built-in) | n/a | Always available on any 13.2+ install. Below 13.2.0, only the separate `@next/font` package exists — treat any `@next/font` import as a migration candidate, not a bug. |
| `next/font/local` | v13.0.0 | none (built-in) | n/a | Always available. |
| `display` default value | changed `'optional'`→`'swap'` in v13.2.0 | none | n/a | On any current install the default is `'swap'`. A repo pinned pre-13.2 with no explicit `display` silently gets `'optional'` — informational only, note the version-dependent default, never "fix" it without a stated reason. |
| `preload` | v13.0.0 | none | n/a | Always available. Default `true` — flag only when it silently costs bytes on a rarely-visited route (see pitfall table), never flag mere presence. |
| `subsets` (`next/font/google` only) | v13.0.0 | none | n/a | Always available. Absence while `preload` is `true` (the default) is a documented build-time warning — always a finding. |
| `adjustFontFallback` | v13.2.0 | none | n/a | Always available on a 13.2+ install; default `true` (Google) / `'Arial'` (local). Explicit `false`/`false`-equivalent is the CLS-risk finding, not the option's mere existence. |
| `variable` | v13.0.0 | none | n/a | Always available; absence is not a finding by itself — only flag when the same font is called repeatedly instead of composed via `variable` (anti-pattern below). |
| `fallback` | v13.0.0 | none | n/a | Always available, no default. Absent + a visually mismatched `adjustFontFallback` complaint is the trigger for the fallback-genre recipe, not the absence alone. |
| `weight` / `style` / `axes` | v13.0.0 | none | n/a | Always available. Missing `weight` on a non-variable font is a build-time requirement, not a style choice — Next.js errors, so this rarely reaches detection as live code. |
| `declarations` (`next/font/local` only) | v13.0.0 | none | n/a | Always available; advanced escape hatch — presence is informational unless paired with a reported visual-shift regression. |
| `next/script` (`<Script>`) | v11.0.0 | none | n/a | Always available. `beforeInteractive`/`afterInteractive` App Router support landed v13.0.0. |
| `strategy="beforeInteractive"` | v13.0.0 (App Router) | must live in root layout (`app/layout.tsx`) | n/a | Always available; the **placement** constraint (root layout only) and **use-case** constraint (critical scripts only) are what gate a finding, not version availability. |
| `strategy="afterInteractive"` (default) | v13.0.0 | none | n/a | Always available; this is the default when `strategy` is omitted. |
| `strategy="lazyOnload"` | v13.0.0 | none | n/a | Always available. |
| `strategy="worker"` + `experimental.nextScriptWorkers` | RFC (2022) | flag enabled in `next.config`; **Pages Router only** | n/a — still experimental, still Pages-only as of 16.3.0 | **UNSUPPORTED on the App Router at any installed version.** Current docs state verbatim: "does not yet work with the App Router" and "`worker` scripts can only currently be used in the `pages/` directory." Any `strategy="worker"` usage or `experimental.nextScriptWorkers: true` found in an App Router repo is a finding regardless of probe result — do not gate this on schema presence; the schema key existing does not make the feature usable here. |
| `onLoad` / `onReady` / `onError` | `onReady` v12.2.4; others earlier | Client Component (`'use client'`); not usable with `beforeInteractive` for `onLoad`/`onError` | n/a | Always available. The gate that matters is the constraint (Client Component required, incompatible with `beforeInteractive` for two of the three), not a version floor. |
| Inline `<Script id="...">` | v11.0.0+ | `id` attribute required | n/a | Always available. Missing `id` is a silent-degradation finding, not a build error. |
| `@next/third-parties` (`GoogleAnalytics`/`GoogleTagManager`/`GoogleMapsEmbed`/`YouTubeEmbed`) | announced 2024-02-26 | separate `npm install @next/third-parties` | n/a — **still experimental** | NOT APPLICABLE if the package is not a declared dependency. If present: treat as experimental-stability, not stable-default, in every finding — pin the version, do not silently assume future stabilization. |

## Detection commands

Read-only only. Prefer `rg`; fall back to `grep -rn` if needed. Every command maps 1:1 to a
gate row or a pitfall signature below.

```bash
# 1. External Google Fonts requests bypassing next/font — <link> tags or raw href strings
rg -n 'fonts\.(googleapis|gstatic)\.com' --glob '*.{tsx,jsx,html}' -g '!**/node_modules/**' -g '!**/*.test.*' -g '!**/*.spec.*' <target-repo-root>
```

```bash
# 2. Legacy @next/font package imports — superseded by built-in next/font since 13.2.0
rg -n "from ['\"]@next/font" --glob '*.{ts,tsx,js,jsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 3. next/font/google calls missing an explicit subsets array
rg -n -U '(Inter|Roboto|Open_Sans|\w+)\(\s*\{(?:(?!subsets|\}).)*\}\s*\)' -P --glob '*.{ts,tsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 4. adjustFontFallback explicitly disabled — reintroduces swap-CLS risk
rg -n 'adjustFontFallback\s*:\s*false' --glob '*.{ts,tsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 5. Raw <script> tags bypassing next/script (excludes next/script's own internal usage)
rg -n '<script\b' --glob '*.{tsx,jsx}' -g '!**/node_modules/**' -g '!**/*.test.*' -g '!**/*.spec.*' <target-repo-root>
```

```bash
# 6. beforeInteractive usage — confirm root-layout placement and critical-script justification
rg -n 'strategy=["\x27]beforeInteractive["\x27]' --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 7. strategy="worker" or experimental.nextScriptWorkers — unsupported on App Router
rg -n 'strategy=["\x27]worker["\x27]|nextScriptWorkers' --glob '*.{tsx,jsx,ts,js}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 8. Inline <Script> without an id attribute (heuristic — flags candidates for manual read)
rg -n -U '<Script\b(?:(?!\bid\b|/>).)*?>' -P --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 9. onLoad/onReady/onError usage — confirm the enclosing file is a Client Component
rg -n -B5 '\bon(Load|Ready|Error)\s*=' --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 10. @next/third-parties adoption — confirms deliberate use and package presence
rg -n "from ['\"]@next/third-parties" --glob '*.{tsx,jsx,ts,js}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 11. Same font function called in multiple files instead of centralized in one module
rg -n '\b(Inter|Roboto|Open_Sans|Playfair_Display|Roboto_Mono)\(' --glob '*.{ts,tsx}' -g '!**/node_modules/**' -g '!**/fonts.ts' <target-repo-root>
```

## Domain severity rubric

- **critical** — removed API/flag in live use; architectural precondition violated; user-visible breakage likely or build/runtime failure likely
  - `strategy="worker"` or `experimental.nextScriptWorkers: true` present in an App Router project — the strategy has no effect and the developer will misdiagnose it as a Partytown config bug.
  - `onLoad`/`onError` combined with `strategy="beforeInteractive"` — the callback never fires, per documented constraint.
  - `onLoad`/`onReady`/`onError` used in a file without `'use client'` — silently does not fire, or a build error.
- **major** — P0-tier practice absent or misconfigured for this archetype; likely measurable CWV/UX harm
  - External `fonts.googleapis.com`/`fonts.gstatic.com` requests found in live JSX/HTML — cross-origin DNS/TLS/HTTP round trip on the critical path that `next/font` eliminates by design.
  - `beforeInteractive` used for a non-critical script (analytics, chat, tag manager) — competes with first-party critical-path resources for the earliest fetch slot; docs scope this strategy narrowly to "critical scripts."
  - `adjustFontFallback: false` (or local-font `false`) with no `fallback` array compensating — reintroduces full swap-CLS risk that the default mechanism exists to prevent.
- **minor** — stable opt-in not adopted; deprecated-but-still-functional surface; quality gap without current breakage
  - `@next/font` legacy import present — migrate to built-in `next/font`, mechanical rename.
  - Missing `subsets` while `preload: true` (default) — produces a build warning, not a runtime break.
  - Same font function called separately across multiple files instead of centralized in one `fonts.ts` — creates duplicate hosted instances.
  - Inline `<Script>` missing `id` — Next.js silently skips tracking/optimization, no build error.
  - `preload: true` (default) left on for a decorative font called in the root layout instead of a route-scoped layout — wastes bandwidth/priority on routes that never render it.
- **informational** — intentional divergence, wrapper indirection, or a note a fixer should know, but not a task by itself
  - `display: 'optional'` deliberately chosen for strict zero-swap-CLS, accepting the fallback may persist for one navigation.
  - `next/font/local` self-hosting with weight-split `src` array and adjacent comments explaining the split — deliberate, not drift.
  - `@next/third-parties` in use with the version pinned — expected experimental-package hygiene, not a finding.
  - A consent-manager script correctly on `beforeInteractive` because it gates all downstream tracking legality.

## False-positive filters

- **`fonts.googleapis.com`/`fonts.gstatic.com` appearing only inside a Content-Security-Policy allowlist string in `next.config` (e.g. `script-src`/`font-src` directives) is NOT an external font load** — it is defensive CSP scoping, often present even when the app has zero actual requests to those origins. Confirm the match is a `<link>`/`href`/fetch call in application code, not a CSP header value, before filing.
- **A self-hosted `next/font/local` setup with deliberate weight-splitting** (separate `src` entries per weight/style with an adjacent comment explaining the split, or a single variable-font file with a documented range) **is correct, not drift** — do not propose collapsing it to a single file or "simplifying" the array without evidence the variable file is smaller.
- **A consent-manager or bot-detector script on `strategy="beforeInteractive"` is legitimate**, not a misuse finding, when it gates whether downstream tracking scripts are legal to load. The docs name "cookie consent managers" and "bot detectors" as the canonical `beforeInteractive` use case. Only flag `beforeInteractive` when the script itself is the tracker/widget, not the gate in front of it.
- Comments/docstrings mentioning `display`, `strategy`, `adjustFontFallback`, etc. do not count as live usage.
- Test files (`*.test.*`, `*.spec.*`, `__tests__/**`, `.storybook/**`) are excluded from every command above.
- `adjustFontFallback: false` paired with an explicit, closer-genre `fallback: [...]` array (serif-for-serif, sans-for-sans) addressing a documented visual-mismatch complaint is a considered tradeoff — file at `minor` at most, and only if no `fallback` array compensates at all.
- A raw `<script>` inside an `email/**` template, an `api/og`/`ImageResponse` render context, or a static HTML fixture is not a `next/script` migration candidate — those are non-page render contexts (mirrors the RSS/`ImageResponse` exemption pattern for `next/image`).
- Multiple `<Script>` call sites routed through one shared wrapper component (e.g. `components/analytics-script.tsx`) collapse into **one** finding against the wrapper, not N findings per caller.
- `strategy="worker"` found inside a `pages/**` directory in a Pages Router project (not App Router) is the **documented, supported** usage — do not flag it; this skill's App Router scope means such a repo is likely out of scope entirely, but if a mixed Pages+App repo is being audited, scope this finding to `app/**` only.

## Evidence format — what each finding file must contain

Every finding the audit subagent writes under `findings/font-script-optimization/` must include:
- `file:line` (exact)
- literal matched text (copied from rg/grep output)
- which gate row or pitfall signature it maps to
- severity
- one-line why-this-matters (verbatim or near-verbatim from the corpus-derived prose below)
- suggested fix recipe section name from `references/fix/font-script-optimization.md`

## Pitfall signatures

| Failure signature | Cause | Fix direction | Recipe section |
|---|---|---|---|
| Fallback font "looks nothing like" the target font, developer disables `adjustFontFallback` | `adjustFontFallback` matches box metrics (ascent/descent/line-gap/size), not glyph shape — a serif-vs-sans mismatch is expected even with zero layout shift | Supply an explicit `fallback: [...]` array with a closer-genre font; keep `adjustFontFallback: true` | `next/font/local` multi-weight self-hosting |
| Build-time warning about unspecified subsets | `subsets` omitted on `next/font/google` while `preload: true` (default) | Always pass `subsets: [...]` explicitly | Google variable font + CSS variable |
| Duplicate hosted font instances | Same Google/local font function called separately in many files instead of one shared module | Centralize in one `app/fonts.ts`; import the exported object everywhere | Google variable font + CSS variable |
| Rarely-visited route's font preloaded on every route | Font function called in the root layout instead of the narrowest layout that renders it | Move the font call to the route-scoped layout | Google variable font + CSS variable |
| LCP/TTI regresses after adding an analytics/chat script | `beforeInteractive` used for a non-critical script "to be safe" | Default every third-party script to `afterInteractive`; reserve `beforeInteractive` for hydration-blocking-critical scripts only | `afterInteractive` → `lazyOnload` strategy tuning |
| `onLoad`/`onReady`/`onError` callback silently does not fire | Callback used in a Server Component (missing `'use client'`) | Add `'use client'` as the first line of the file rendering the `<Script>` | Inline script + lifecycle callbacks |
| `onLoad`/`onError` never fires despite correct Client Component | Combined with `strategy="beforeInteractive"` — incompatible per docs | Use `onReady` instead of `onLoad`, or move the callback logic elsewhere; `onError` has no `beforeInteractive`-compatible substitute | Inline script + lifecycle callbacks |
| Inline script runs but Next.js does not track/optimize it | Missing `id` attribute on `<Script id="...">` | Add a unique `id` | Inline script + lifecycle callbacks |
| `strategy="worker"` has no effect, or Partytown fails to bootstrap, on the App Router | `worker` strategy is explicitly unsupported outside `pages/` as of 16.3.0 — no committed stabilization timeline | Do not use on App Router; use `lazyOnload`, `@next/third-parties`, or manual event-priority deferral instead | `afterInteractive` → `lazyOnload` strategy tuning |
| GTM container loads with correct timing but INP stays poor | `@next/third-parties`'s `GoogleTagManager` only times the container's own bootstrap — it cannot control what the container subsequently injects | Delay GTM-triggered downstream work relative to first-party handlers; do not treat the wrapper as a complete INP fix | `@next/third-parties` GA / GTM |

## Cross-domain interactions

1. Third-party npm SDKs imported directly into Client Components (not loaded as external `<script>` tags) are a `bundle-code-splitting` concern — use `next/dynamic`/on-event `import()` for those, not `next/script`. This domain owns only external-script loading strategy.
2. A no-flash theme bootstrap script legitimately using `beforeInteractive`-equivalent inline injection belongs to `dark-light-theme-switching` — do not duplicate that pattern here as an analytics-loading recipe.
3. YouTube/Maps facade poster images fall under `image-optimization`'s rules once rendered — this domain only owns the facade/embed loading strategy, not the poster image's `sizes`/`priority` correctness.

## Reference pointer

Fix recipes for this domain live in `references/fix/font-script-optimization.md`.
