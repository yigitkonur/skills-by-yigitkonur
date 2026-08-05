# Detect: instant-i18n-locale-switching

**Corpus lineage:** instant-i18n-locale-switching/00-overview.md,
instant-i18n-locale-switching/03-when-to-use.md,
instant-i18n-locale-switching/07-pitfalls.md,
instant-i18n-locale-switching/08-version-lockin-seo-vercel-practitioner.md

## Applicability gate

The App Router has **no built-in i18n routing feature.** The `i18n` key in
`next.config.js` (`locales`, `defaultLocale`, `domains`) is **Pages Router-only** —
its presence in an App Router repo is a migration artifact, not a config choice to
tune. Every App Router i18n solution — `next-intl` or hand-rolled — is built on the
same documented pattern: a `[locale]` dynamic segment, a `proxy.ts`-based locale
negotiator, and (16.3+) `next/root-params` for prop-drill-free locale access. A
repo with no `next-intl` dependency but a working `[locale]` segment + `proxy.ts` +
custom `src/lib/i18n/` dictionary loader is not missing a library — it already
implements the pattern the library also implements. Audit the **mechanism**, never
propose a library migration for a working custom implementation.

| Feature / config key | Introduced | Requires | Removed-in | Gate rule |
|---|---|---|---|---|
| `i18n` block in `next.config.js` | Next.js 10.0.0, Pages Router | Pages Router | n/a — simply inapplicable to App Router | Found in an App Router repo (`app/` directory present) → **critical** migration-note finding, never a "tune this config" finding. Route to `[locale]` segment + `proxy.ts`, not a config edit. |
| `[locale]`/`[lang]` dynamic segment pattern | Documented App Router guide pattern, no version | App Router | n/a | Always APPLICABLE on any App Router repo. Absent while the repo serves multiple languages via query param or a single hardcoded locale → the finding is the missing pattern itself, not a version gate. |
| `next-intl` package | 4.13.5 (npm-latest) | Next.js 16.x peer-compatible | n/a | Probe `package.json` + `node_modules/next-intl`. `present` → **library path**; audit its config (`defineRouting`, `createNavigation`, `proxy.ts` wiring) against this domain's pattern. `absent` → check for a custom `[locale]` + `proxy.ts` + dictionary-loader mechanism before concluding no i18n exists — verdict **APPLICABLE-CUSTOM** if found. |
| `proxy.ts` file convention (locale negotiation) | Next.js 16 rename of `middleware.ts` | Next.js ≥16.0.0; Node.js runtime | `middleware.ts` still works but is flagged for eventual removal | A repo on Next.js ≥16.0.0 with locale-negotiation logic still in `middleware.ts` → `major` finding, rename required (this is the documented cause of `"Unable to find next-intl locale"` post-16-upgrade, and applies identically to a custom middleware-based negotiator). |
| `next/root-params` | **v16.3.0** | Next.js ≥16.3.0; Server Components only | n/a | NOT APPLICABLE (do not propose) if installed next <16.3.0 — route to the legacy `setRequestLocale` (library) or an equivalent prop-drilled/param-read pattern (custom) instead. On ≥16.3.0: absence alongside a `headers()`-based or prop-drilled locale read is a `minor`/`major` migration candidate (severity depends on whether the repo also lacks static rendering — see below). |
| `setRequestLocale` (next-intl) | Stabilized from `unstable_setRequestLocale` in next-intl 3.22 | next-intl only | n/a — legacy, not removed | Library path, installed next <16.3.0, or a next-intl repo that hasn't migrated to root-params yet → current-and-correct for that floor; do not flag as broken. On next-intl + installed next ≥16.3.0: `minor` migration-opportunity finding toward `next/root-params`. |
| `alternates.languages` (Metadata API) | Next.js 13.2.0+ | none | n/a | Always APPLICABLE. Absent on any locale route that should be indexable → `major` SEO finding. |
| `alternates.languages` (sitemap.ts) | Next.js 14.2.0+ | none | n/a | Always APPLICABLE on ≥14.2.0 (every 16.x install qualifies). Absent or hand-written (not derived from the locale list) → finding per severity rubric below. |
| `generateStaticParams` over locales | Core API, no version gate | `[locale]` dynamic segment | n/a | Always APPLICABLE. Absent → every locale route stays dynamically rendered regardless of which locale-reading API is used — this is the single biggest "instant switch" and cost lever in this domain. |
| `cacheComponents: true` | 16.0.0+ | Node.js runtime | n/a | Not required for the core i18n pattern (static rendering works via plain `generateStaticParams` alone). Probe only to determine whether `next/root-params`-inside-`use cache` cache-key-narrowing claims apply — absent means skip that specific claim, not the whole domain. |

## Detection commands

Read-only only. Every command maps 1:1 to a gate row or a pitfall signature below.

```bash
# 1. Pages-Router-only i18n config in an App Router repo — migration-note finding, not a config tune
rg -n '\bi18n\s*:' --glob 'next.config.*' <target-repo-root>
```

```bash
# 2. [locale]/[lang] dynamic segment presence — confirms the App Router pattern is adopted
find <target-repo-root>/app -maxdepth 1 -type d -name '[[]*[]]'
```

```bash
# 3. next-intl adoption — import usage (library path signal)
rg -n "from ['\"]next-intl(/.*)?['\"]" --glob '*.{tsx,jsx,ts,js}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 4. next-intl declared dependency + resolved version
rg -n '"next-intl"' <target-repo-root>/package.json
```

```bash
# 5. Custom i18n mechanism — dictionary/locale JSON loader with no next-intl (heuristic)
find <target-repo-root>/src -iname 'i18n' -type d 2>/dev/null
find <target-repo-root> -maxdepth 4 -iname '*.json' -path '*messages*' -o -iname '*.json' -path '*locales*' 2>/dev/null
```

```bash
# 6. proxy.ts vs middleware.ts — the Next.js 16 rename, applies to any locale-negotiation logic
find <target-repo-root>/src <target-repo-root> -maxdepth 1 -iname 'proxy.ts' -o -maxdepth 1 -iname 'middleware.ts' 2>/dev/null
```

```bash
# 7. next/root-params usage — current-recommended locale-access path on 16.3+
rg -n "from ['\"]next/root-params['\"]" --glob '*.{tsx,ts}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 8. setRequestLocale (legacy next-intl path) usage — migration-opportunity signal on 16.3+
rg -n '\bsetRequestLocale\(' --glob '*.{tsx,ts}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 9. generateStaticParams over locale — confirms static rendering is actually wired
rg -n 'generateStaticParams' -A5 --glob '*.{tsx,ts}' -g '!**/node_modules/**' <target-repo-root> | rg -n 'locale|lang'
```

```bash
# 10. Hardcoded <html lang> — should be derived from the resolved locale, not a literal
rg -n '<html\s+lang=["\x27][a-z]{2}' -P --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 11. alternates.languages presence — metadata hreflang
rg -n 'alternates' -A5 --glob '*.{tsx,ts}' -g '!**/node_modules/**' <target-repo-root> | rg -n 'languages'
```

```bash
# 12. sitemap.ts alternates.languages presence — sitemap hreflang
rg -n 'alternates' -A5 --glob 'sitemap.{ts,tsx}' <target-repo-root>
```

```bash
# 13. Locale switch via full reload instead of client navigation — the "instant switch" regression
rg -n 'window\.location\.(href|assign|replace)\s*=' --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root> -B5 | rg -n 'locale|lang'
```

```bash
# 14. localePrefix: 'never' (or an equivalent URL-less custom config) — forfeits automatic hreflang
rg -n "localePrefix\s*:\s*['\"]never['\"]" --glob '*.{ts,tsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 15. next/root-params called from a Client Component, Server Action, or Route Handler — unsupported surface
rg -n "from ['\"]next/root-params['\"]" -B3 --glob '*.{tsx,ts}' -g '!**/node_modules/**' <target-repo-root> | rg -n "'use client'|'use server'|route\.ts"
```

## Domain severity rubric

- **critical** — removed API/flag in live use; architectural precondition violated; user-visible breakage likely or build/runtime failure likely
  - Pages-Router `i18n` config block found in an App Router repo — dead config, does nothing; the repo has no real locale routing despite appearing configured.
  - A root `app/layout.tsx` exists **above** the `[locale]` segment while using `next/root-params` — the documented cause of root-params silently returning an empty object.
  - `next/root-params` called from a Client Component, Server Action, or Route Handler — unsupported surface, throws or misbehaves.
- **major** — P0-tier practice absent or misconfigured for this archetype; likely measurable CWV/UX harm
  - No `generateStaticParams` over locales on an indexable content/marketing archetype — every locale route stays dynamically rendered, multiplying per-request compute cost by locale count.
  - Locale switch implemented via `window.location` assignment instead of client-side router navigation — full-document reload, the exact "instant switch" failure this domain exists to prevent.
  - Missing `alternates.languages` on an indexable locale route — search engines cannot discover locale variants; direct SEO risk.
  - `middleware.ts` still used for locale negotiation on a Next.js ≥16.0.0 install — the documented cause of `"Unable to find next-intl locale"` and the equivalent failure for a custom negotiator.
- **minor** — stable opt-in not adopted; deprecated-but-still-functional surface; quality gap without current breakage
  - `setRequestLocale` (legacy) still in use on an install ≥16.3.0 that could migrate to `next/root-params`.
  - Hand-written hreflang URL strings instead of deriving them from the locale list + a path-builder — drift risk, not yet broken.
  - `<html lang>` hardcoded to a single value on a genuinely single-locale repo — informational unless multi-locale is confirmed planned.
- **informational** — intentional divergence, wrapper indirection, or a note a fixer should know, but not a task by itself
  - `localePrefix: 'never'`-style URL-less locale routing deliberately chosen for a logged-in-only, non-indexable app — legitimate choice, not a finding, as long as the archetype has no SEO exposure.
  - A single-locale repo with no i18n at all — valid, zero cost to skip.
  - `next-intl`'s reference `LocaleSwitcherSelect` pattern already correctly implemented — confirms the pattern, not itself a finding.

## False-positive filters

- Comments/docstrings mentioning `i18n`, `locale`, `next-intl`, etc. do not count as live usage.
- Test files (`*.test.*`, `*.spec.*`, `__tests__/**`) are excluded.
- A `middleware.ts` file that does **not** contain locale-negotiation logic (e.g. an
  auth-only middleware in a single-locale repo) is not a finding for this domain.
- `localePrefix: 'never'` (or an equivalent custom URL-less design) on a
  logged-in-only, auth-gated app with no SEO exposure is **informational**, not a
  finding — the SEO forfeiture named in the pitfalls only matters when indexability
  is actually a goal for that archetype.
- `window.location` assignments unrelated to locale switching (e.g. an OAuth
  redirect, an external link) are not findings — confirm the literal context before
  writing a finding from command #13's heuristic match.
- A repo genuinely targeting a single market/language with no near-term multi-locale
  plan is out of scope entirely — do not propose adding i18n routing as a
  speculative feature; this domain audits existing i18n implementations, not their
  absence on single-locale repos.
- `next/root-params` usage inside a `'use cache'` scope is the **documented,
  recommended** pattern (cache-key narrowing) — do not flag it as a Server
  Component/cache conflict; only flag usage inside `unstable_cache` (which throws)
  or inside Client Components/Server Actions/Route Handlers (unsupported).

## Evidence format — what each finding file must contain

Every finding the audit subagent writes under `findings/instant-i18n-locale-switching/`
must include:
- `file:line` (exact)
- literal matched text (copied from rg/grep output)
- which gate row or pitfall signature it maps to
- severity
- one-line why-this-matters (verbatim or near-verbatim from the corpus-derived prose below)
- suggested fix recipe section name from `references/fix/instant-i18n-locale-switching.md`
- **which variant applies** — library (`next-intl`) or custom — so the fix agent reads the matching recipe half, not both

## Pitfall signatures

| Failure signature | Cause | Fix direction | Recipe section |
|---|---|---|---|
| `"Unable to find next-intl locale"` (or equivalent for a custom negotiator) after upgrading to Next.js 16 | Locale-negotiation logic still lives in `middleware.ts`, which Next.js 16 no longer loads for this hook | Rename `middleware.ts` → `proxy.ts`; the internal negotiator import/logic itself does not change | `proxy.ts` locale negotiation |
| Locale resets to a previous choice on navigation | `localePrefix: 'never'`-style URL-less routing relying entirely on cookie/header persistence with no URL signal; any navigation path that doesn't propagate the cookie falls back silently | Prefer URL-prefixed routing (`'always'`/`'as-needed'`) if persistence across arbitrary navigation matters | Locale routing config |
| Route unexpectedly stays dynamic ("opts into dynamic rendering") | Locale read via `headers()` (pre-root-params default) instead of `next/root-params` or `setRequestLocale`, with no `generateStaticParams` | Add `generateStaticParams` + `next/root-params` (16.3+) or `setRequestLocale` (legacy) | Static rendering via next/root-params / Static rendering — legacy setRequestLocale |
| `next/root-params` returns an empty object / wrong value | A layout exists at `app/layout.tsx` **above** the `[locale]` segment | Move the actual root layout inside `app/[locale]/layout.tsx`; no layout above the segment | Root layout under `[locale]` |
| `next/root-params` throws or misbehaves | Called from a Client Component, Server Action, or Route Handler — unsupported surface as of this capture | Pass the locale explicitly as an argument instead, or confirm the call site is a Server Component | n/a — architectural restriction, no code recipe |
| `next/root-params` throws inside a cache wrapper | Called inside `unstable_cache` — root-param getters are documented to throw there | Migrate the caching mechanism to `'use cache'` | Cache-key narrowing with next/root-params |
| Sitemap/metadata hreflang silently wrong | Hreflang codes hand-written as string literals instead of derived from the locale list, or entries not mutually reciprocal | Derive every hreflang URL from the locale list + a path-builder function | hreflang via alternates.languages (metadata + sitemap) |
| Locale switch feels like a full reload | `window.location` assignment used instead of the locale-aware router | Use the locale-aware `router.replace` inside `startTransition` | Soft locale switch |

## Cross-domain interactions

1. Direct dependency on `seo-metadata`: every locale route this domain creates needs
   a corresponding `alternates.languages` entry; keep findings for the two domains
   internally consistent (both should point at the same path-builder pattern).
2. Amplifies `navigation-prefetching`: the "instant" ceiling of a locale switch is
   identical to the general client-side navigation performance ceiling — a locale
   switch on a route with no prefetch/cache coverage is not a locale-specific bug,
   it is the same navigation-cost finding that domain already owns.
3. Shares the exact **root-`<html>`-attribute-cannot-be-Suspended** constraint with
   `dark-light-theme-switching` (`lang`/`dir` here, `class`/`data-theme` there) — see
   `references/gating/conflicts.md` §6-equivalent reasoning; a fix touching
   `<html lang>` should stay consistent with any co-located theme-attribute fix in
   the same root layout.
4. `references/gating/conflicts.md` §7 — locale soft navigation cannot be
   zero-network; never let a finding or fix promise "instant" without the caveat.

## Reference pointer

Fix recipes for this domain live in `references/fix/instant-i18n-locale-switching.md`.
