# Detect: rendering-strategy-caching

**Corpus lineage:** rendering-strategy-caching/00-overview-feature-inventory.md,
rendering-strategy-caching/03-when-to-use.md, rendering-strategy-caching/07-pitfalls-anti-patterns.md,
rendering-strategy-caching/08-version-lockin-seo-vercel.md

## Applicability gate

| Feature / config key | Introduced | Requires | Removed-in | Gate rule |
|---|---|---|---|---|
| `cacheComponents` (`next.config.ts`) | v16.0.0 | Next.js ≥16.0.0; Node.js runtime (no `runtime = 'edge'` anywhere) | n/a | NOT APPLICABLE if the installed `next` resolves below 16.0.0 (probe `node_modules/next/package.json`). BLOCKED if any route still exports `runtime = 'edge'` — resolve via the Edge→Node recipe first (see `fix/vercel-platform-deployment.md`), never in the same task as enabling this flag. |
| `"use cache"` directive | experimental v15.0.0 → stable v16.0.0 | `cacheComponents: true` | n/a | NOT APPLICABLE if `cacheComponents` is absent — the directive has no meaning under the pre-16 model. If `cacheComponents: true` is already set, do not propose "enable Cache Components" again — only look for adoption gaps. |
| `"use cache: private"` | v16.0.0 | `cacheComponents: true`; Server Components only | n/a | NOT APPLICABLE if `cacheComponents` absent. BLOCKED if the directive appears inside a Route Handler — not supported, per docs. |
| `"use cache: remote"` | v16.0.0 | `cacheComponents: true`; `cacheHandlers.remote` configured (self-hosted) or platform-provided (Vercel) | n/a | NOT APPLICABLE if `cacheComponents` absent. INFORMATIONAL if used without a confirmed remote handler — flag the gap, don't assume Vercel auto-provides it (unconfirmed in the corpus). |
| `cacheLife()` (function + `next.config.ts` profile object) | v16.0.0 (was `unstable_cacheLife`) | `cacheComponents: true`; called inside a cache-directive scope | n/a | NOT APPLICABLE if `cacheComponents` absent. A bare `unstable_cacheLife` match belongs to the graveyard row below, not this row. |
| `cacheTag()` | v16.0.0 (was `unstable_cacheTag`) | `cacheComponents: true` | n/a | Same rule as `cacheLife()`. |
| `revalidateTag(tag, profile)` two-arg form | v16.0.0 (arity change) | `next/cache` import | n/a | BLOCKED (TypeScript error) if only the single-argument form is present on an install ≥16.0.0 — see graveyard row below. |
| `updateTag(tag)` | v16.0.0 (new) | Server Actions only (`'use server'`) | n/a | BLOCKED if called from a Route Handler or Client Component — throws at runtime, per docs. |
| `refresh()` | v16.0.0 (new) | Server Actions only | n/a | Same constraint as `updateTag`. Does not touch any cache entry — a call expecting it to invalidate `"use cache"` data is a misuse, not a valid finding for this row. |
| `experimental.ppr` / `experimental_ppr` | pre-16.x, experimental | n/a | Removed v16.0.0 | REMOVE if found on an install ≥16.0.0 — but probe first: a project that adopted this on a 15.x canary is a go/no-go migration decision, not a mechanical cleanup (see `references/gating/lockin-reversibility.md` #1). |
| `experimental.dynamicIO` | pre-16.x, experimental | n/a | Removed/renamed v16.0.0 | REMOVE if found on an install ≥16.0.0; replace with `cacheComponents: true`. |
| `experimental.useCache` | pre-16.x, experimental | n/a | Folded into `cacheComponents` v16.0.0 | REMOVE if found on an install ≥16.0.0; replace with `cacheComponents: true`. |
| `export const revalidate` / `dynamic` / `fetchCache` (legacy segment exports) | classic | n/a — valid, supported without `cacheComponents` | Errors when `cacheComponents: true` is also set | BLOCKED (build error) if both coexist. NOT APPLICABLE as a removal task if `cacheComponents` is absent — this is still the fully supported "previous model," not dead code. |
| `unstable_cache` | classic | n/a — valid without `cacheComponents` | Superseded (not removed) once `cacheComponents` is on | NOT APPLICABLE as a migration task if `cacheComponents` is absent. If `cacheComponents` is present, flag for migration to `"use cache"`. |
| Node.js-runtime prerequisite (absence of `runtime = 'edge'`) | n/a — prerequisite | — | `runtime = 'edge'` deprecated 16.3 for pages/layouts/route handlers | BLOCKED — `cacheComponents` cannot be enabled while any route exports `runtime = 'edge'`. This is the hard precondition named in `03-when-to-use.md`; treat it as its own upstream task, not a sub-step of the Cache Components task. |

## Detection commands

```bash
# 1. Is cacheComponents enabled at all — never propose "enable" if this already hits
rg -n "cacheComponents" --glob 'next.config.*' <target-repo-root>
```

```bash
# 2. Removed/superseded experimental flags (graveyard rows) — dead surface on Next.js >=16
rg -n "experimental\.(ppr|dynamicIO|useCache)|experimental_ppr\s*[:=]" --glob 'next.config.*' --glob '**/*.{ts,tsx,js,jsx}' <target-repo-root>
```

```bash
# 3. Legacy route segment exports — errors once cacheComponents is on; valid without it
rg -n "^\s*export const (revalidate|dynamic|fetchCache|dynamicParams)\s*=" --glob 'app/**/*.{ts,tsx}' <target-repo-root>
```

```bash
# 4. unstable_cache usage — superseded once cacheComponents is on, still valid without it
rg -n "unstable_cache\(" --glob '**/*.{ts,tsx}' --glob '!**/*.test.{ts,tsx}' --glob '!**/*.spec.{ts,tsx}' <target-repo-root>
```

```bash
# 5. unstable_-prefixed cacheLife/cacheTag imports — mechanical rename, prefix dropped in 16
rg -n "unstable_cacheLife|unstable_cacheTag" --glob '**/*.{ts,tsx}' <target-repo-root>
```

```bash
# 6. Node.js-runtime prerequisite blocker — must clear before cacheComponents can be enabled
rg -n "export const runtime\s*=\s*['\"]edge['\"]" --glob 'app/**/*.{ts,tsx}' <target-repo-root>
```

```bash
# 7. Single-argument revalidateTag calls — deprecated form, TS error on install >=16.0.0
rg -n "revalidateTag\([^,)]+\)" --glob '**/*.{ts,tsx}' <target-repo-root>
```

```bash
# 8. Request-time API reads in page/layout files — each hit needs a parent <Suspense> check
rg -n "cookies\(\)|headers\(\)|connection\(\)" --glob 'app/**/{page,layout}.tsx' <target-repo-root>
```

```bash
# 9. generateStaticParams call sites — open -A5 context and check for a literal `return []`
rg -n "generateStaticParams" -A 5 --glob 'app/**/*.{ts,tsx}' <target-repo-root>
```

## Domain severity rubric

- **critical**
  - `experimental.ppr` / `experimental_ppr` / `experimental.dynamicIO` / `experimental.useCache` present in `next.config.*` while the installed `next` resolves to ≥16.0.0 — dead flags, config validation can throw.
  - `cacheComponents: true` set while a route still exports `runtime = 'edge'` — hard architectural precondition violated.
  - A request-time API read (`cookies()`, `headers()`, `connection()`, unawaited `params`/`searchParams`) with no parent `<Suspense>` boundary while `cacheComponents` is enabled — the documented `blocking-route` build/runtime failure.
  - A single-argument `revalidateTag(tag)` call on an install where the two-argument form is already required — TypeScript build failure.

- **major**
  - `cacheComponents: true` is set, but no `"use cache"` directive exists anywhere in the data-fetching layer despite shareable, cacheable data — the architecture's core lever sits unused.
  - `unstable_cache(...)` calls present while `cacheComponents: true` — a superseded pattern coexisting with the new model.
  - A `"use cache"` scope with no explicit `cacheLife(...)` call — silently applies the `default` profile (5 min stale / 15 min revalidate / never expires), an easy-to-misread lifetime per the docs' own recommendation.
  - A `"use cache"` function keyed on a high-cardinality argument (raw search-filter object, per-user ID, price range) — collapses cache utilization toward zero in production.

- **minor**
  - A single-argument `revalidateTag(tag)` call that still compiles (older install, or a suppressed TS error) — flagged for removal before the behavior disappears in a future major.
  - `unstable_cacheLife` / `unstable_cacheTag` prefixed imports still present post-16.0 — mechanical rename available, no behavior risk today.
  - `loading.tsx` used at a shallow segment edge where a deeper inline `<Suspense>` boundary would let more of the page join the static shell — a missed optimization, not a break.

- **informational**
  - The repo intentionally has no `cacheComponents` and uses the classic `revalidate`/`dynamic`/`fetchCache` model — a fully supported, coexisting path per the docs; not a task by itself.
  - `export const instant = false` present on a segment — a deliberate incremental-migration marker, note it, don't silently remove it.
  - `cacheComponents: true` already set and every `"use cache"` scope already carries `cacheLife`/`cacheTag` — nothing to propose.

## False-positive filters

- **Comments/docstrings are not live usage.** A literal match inside `//`, `/* */`, or a JSDoc block — e.g. a route file containing `export const dynamic` inside a `NOTE: do not add this` comment — is not a finding. Open the file and confirm the match is an executing statement.
- **Test files are excluded.** `**/*.test.{ts,tsx}`, `**/*.spec.{ts,tsx}`, `**/__tests__/**`, `**/e2e/**` — cache-directive or segment-export usage in test fixtures does not represent production caching behavior.
- **A repo that already sets `cacheComponents: true` must not be told to "enable Cache Components."** Check gate row 1 (detection command 1) first; if it already hits, only surface adoption gaps (missing `cacheLife`, uncached data above Suspense, unmigrated `unstable_cache`), never re-propose the flag itself.
- **Markdown/MDX content is not live usage.** Exclude `**/*.md`, `**/*.mdx` — docs and blog posts that quote code samples are not code paths. Add `--glob '!**/*.{md,mdx}'` to any command run against a content-heavy repo.
- **`runtime = 'edge'` matches inside `.next/`, `node_modules/`, or other build/dependency output are not live usage** — restrict globs to source directories (`app/**`, `src/**`).
- **`generateStaticParams` findings require the literal empty return.** A call site that returns a non-empty array, or an array built from a data source, is not a finding — only flag a literal `return []` or `return [];` in the `-A5` context.
- **`unstable_cache` inside a file whose own purpose is documenting the "previous model"** (e.g. a repo's own internal caching-guide reference implementation kept for the pre-16 path deliberately) is informational, not a migration target — confirm `cacheComponents` is actually enabled before flagging.

## Evidence format — what each finding file must contain

Every finding the audit subagent writes under `findings/rendering-strategy-caching/` must include:
- `file:line` (exact)
- literal matched text (copied from the `rg` output)
- which gate row or pitfall signature it maps to
- severity
- one-line why-this-matters (drawn from the corpus prose above)
- suggested fix recipe section name from `references/fix/rendering-strategy-caching.md`
- the resolved `cacheComponents` probe verdict (`present`/`absent`/`unresolved`) — every finding in this domain is downstream of that one gate, so record it once at the top of the findings file, not per-finding.

## Pitfall signatures

| Failure signature | Cause | Fix direction | Recipe section |
|---|---|---|---|
| "Uncached data was accessed outside of `<Suspense>`" (`blocking-route`) | An async component reads `params`/`searchParams`/`cookies()`/`headers()`/`connection()`, or fetches uncached data, with no parent `<Suspense>` boundary, while `cacheComponents` is enabled | Wrap in `"use cache"` if the data should join the static shell; wrap the consuming component in `<Suspense>` if it's genuinely per-request | Static shell + `<Suspense>` dynamic-hole page pattern |
| Build hang / "Filling a cache during prerender timed out" (50s Cache Timeout) | A Promise resolving to uncached/runtime data, created *outside* a `"use cache"` boundary, is passed as a prop, closure, or `Map` value into a cached function | `await` the runtime value first in the calling (uncached) component, then pass the resolved value — not the promise — into the cached function | `"use cache"` on a component or function, with a cacheLife profile |
| "`use cache` works locally but does nothing on Vercel production" | The default in-memory cache handler doesn't persist across serverless instances; every cold instance is a cache miss | Switch to `"use cache: remote"` with a configured remote handler | `"use cache: remote"` — durable shared caching |
| `dynamicParams` incompatibility | The route segment config `dynamicParams` export coexists with `cacheComponents: true` | Delete the export; use `notFound()` inside the page for params that shouldn't resolve | 15→16 migration — remove legacy flags, segment exports, `unstable_cache` |
| `generateStaticParams` returning an empty array now errors (`empty-generate-static-params`) | Cache Components requires at least one param so it can validate a non-empty static shell | Return at least one param, or restructure so the route is genuinely not statically generated | 15→16 migration — remove legacy flags, segment exports, `unstable_cache` |
| High-cardinality cache keys collapse hit rate | Caching on a high-cardinality argument (raw search filter, per-user ID, price range) | Cache on the lowest-cardinality dimension available (category, currency, locale) and filter/select the rest in memory | `"use cache"` on a component or function, with a cacheLife profile |
| Unmount-driven UI reset breaks after `<Activity>` auto-wiring | Dropdowns/dialogs/post-submit forms assumed navigation unmounts and resets them; `cacheComponents` preserves state via React `<Activity>` instead of unmounting | Close dropdowns in a `useLayoutEffect` cleanup; derive dialog state from the URL; reset forms explicitly in the submit handler | Enable Cache Components (pre-flight `<Activity>` UI audit) |
| Nested short-lived cache error | An outer `"use cache"` scope has no explicit `cacheLife` while it contains/depends on an inner scope whose `expire` is under 5 minutes | Set an explicit `cacheLife` on the outer scope, or move the short-lived content behind its own `<Suspense>` boundary with `"use cache: remote"` | `"use cache"` on a component or function, with a cacheLife profile |

## Cross-domain interactions

1. If the capability probe shows `cacheComponents` absent (unset in config, or the key is not accepted by the installed schema), **skip every Partial Prefetching recommendation** (`navigation-prefetching` domain) and **downgrade automatic `<Activity>` findings** (`micro-interactions-react19-fluidity` domain) to NOT APPLICABLE — both are hard-gated on this flag.
2. `runtime = 'edge'` findings are a hard prerequisite blocker: route them to `fix/vercel-platform-deployment.md`'s Edge→Node migration first. Never propose enabling `cacheComponents` in the same task as the runtime migration — sequence them.
3. Root `<html>` attributes that depend on `cookies()`/`headers()` (theme, locale) cannot be Suspense-wrapped. A finding here interacts with `dark-light-theme-switching` and `instant-i18n-locale-switching` — do not propose wrapping the root layout itself in `<Suspense>` as a fix; see `references/gating/lockin-reversibility.md`'s pre-flight checklist.

## Reference pointer

Fix recipes for this domain live in `references/fix/rendering-strategy-caching.md`.
