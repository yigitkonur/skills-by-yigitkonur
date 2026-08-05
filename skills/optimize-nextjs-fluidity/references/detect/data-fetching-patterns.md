# Detect: data-fetching-patterns

**Corpus lineage:** data-fetching-patterns/00-overview-inventory.md,
data-fetching-patterns/03-when-to-use.md, data-fetching-patterns/07-pitfalls-waterfalls.md,
data-fetching-patterns/08-constraints-lockin-seo-vercel-practitioner.md

## Applicability gate

The `fetch` default-caching mental model matters more here than any single config key: the
literal reference default is **`auto no cache`**, and every row below assumes that baseline.
Probe React/Next.js versions per `references/gating/capability-probe.md` before proposing any
React-19-only primitive (`React.cache`, `use`, `useActionState`, `useOptimistic`,
`useFormStatus`) — these primitives are unconditionally unavailable, not merely
discouraged, on React <19.

| Feature / config key | Introduced | Requires | Removed-in | Gate rule |
|---|---|---|---|---|
| `fetch()` default cache behavior (`auto no cache`) | pre-15; uncached-by-default inversion at 15.0 | Node.js runtime (Server Components) | n/a | Always applicable. The literal reference default is **`auto no cache`**: Next.js fetches on every request in dev, fetches once during `next build` only if no Request-time APIs are detected on the route, and fetches every request if they are. **16 did NOT reverse the 15.0 inversion** — under `cacheComponents` the practical framing tightens to "dynamic by default." Never describe a bare `fetch()` as cached without an explicit `cache: 'force-cache'` or `use cache` wrapper. |
| `cache: 'force-cache'` / `cache: 'no-store'` (fetch option) | pre-15, stable | — | n/a | Always applicable — opt-in/opt-out cache participation per fetch call. `force-cache` matches on URL, method, headers, and body; only `200` responses are stored. |
| `next.revalidate` (fetch option) | pre-15 | — | n/a | Always applicable. `{ revalidate: 3600, cache: 'no-store' }` on the same call is an invalid combination — both are ignored, dev prints a warning. Flag as a finding, not a silent no-op. |
| `next.tags` (fetch option) | pre-15 | Pairs with `revalidateTag`/`updateTag` for invalidation | n/a | Always applicable. Max tag length 256 chars, max 128 tags per call — informational ceiling. |
| `React.cache` (`cache(fn)` from `react`) | React 19 | React 19, Server Components only | n/a | BLOCKED if React <19 installed. NOT APPLICABLE if the wrapped call site is a Client Component. |
| `use` API (`use(promise)` / `use(context)`) | React 19.0.0 | React 19 | n/a | BLOCKED if React <19. Context reads via `use` are unsupported in Server Components — a match there is a finding. |
| `'use server'` Server Actions directive | alpha 13.4, stable since 14 | Node.js runtime | n/a | BLOCKED if Next.js <14 (stable baseline). |
| `useActionState` (renamed from `useFormState` in React 19) | React 19 | React 19 | n/a | BLOCKED if React <19. Any live `useFormState` match is a migration finding regardless of whether the old name still resolves in the installed `react-dom`. |
| `useOptimistic` | React 19 | React 19 | n/a | BLOCKED if React <19. The setter must be called inside an Action — see pitfall table. |
| `useFormStatus` (react-dom) | React 19 | React 19; must be called from a component nested inside the `<form>` | n/a | BLOCKED if React <19 (only the `pending` key is available pre-19). |
| `revalidatePath` | pre-15, stable | Server Functions, Route Handlers | n/a | NOT APPLICABLE from Client Components or `proxy.ts` — Server Function/Route Handler only. |
| `revalidateTag` arity | 2-arg form current; 1-arg deprecated | Server Functions, Route Handlers | 1-arg form deprecated, "may be removed in a future version" | REMOVE single-arg `revalidateTag(tag)` calls — migrate to `revalidateTag(tag, profile)` or `updateTag(tag)`. |
| `updateTag` / `refresh()` | Next.js 16 (Cache Components) | `cacheComponents: true`; both are Server-Actions-only | n/a | NOT APPLICABLE if `cacheComponents` probes `absent` — probe first per `references/gating/capability-probe.md`. |
| SWR (`useSWR`) / TanStack Query (`useQuery`, `prefetchQuery`) | — | Separate npm dependency (`swr` / `@tanstack/react-query`) | n/a | NOT APPLICABLE if neither package is a dependency. If present, verify it is not the *primary* mechanism for content a one-time Server Component read could serve — see false-positive filters. |

## Detection commands

```bash
# 1. Two sequential `const x = await fn(...)` bindings back-to-back — same-component waterfall candidate (Pattern A)
rg -n -U 'const \w+ = await \w+\([^;]*\);\s*\n\s*const \w+ = await \w+\(' --glob '*.{ts,tsx}' <target-repo-root>

# 2. useEffect bodies that call fetch() directly — client-side fetch cascade candidate (Pattern C)
rg -n -U 'useEffect\(\s*\(\)\s*=>\s*\{[^}]*fetch\(' --glob '*.{ts,tsx}' <target-repo-root>

# 3. Files with 2+ `await get*()`/`await fetch()` calls but no Promise.all — likely unparallelized independent fetches
rg -l 'await (get\w*|fetch)\(' --glob '*.{ts,tsx}' <target-repo-root> | xargs -I{} sh -c 'test $(rg -c "await (get\w*|fetch)\(" {}) -ge 2 && ! rg -q "Promise\.all" {} && echo {}'

# 4. Legacy useFormState import/usage — renamed to useActionState in React 19
rg -n '\buseFormState\b' --glob '*.{ts,tsx}' <target-repo-root>

# 5. revalidateTag called with exactly one argument — deprecated single-arg form
rg -n "revalidateTag\(\s*[^,()]+\s*\)" --glob '*.{ts,tsx}' <target-repo-root>

# 6. 'use client' files calling fetch()/axios directly — candidate for moving the read to a Server Component
rg -n -l "^'use client'" --glob '*.tsx' <target-repo-root> | xargs -I{} sh -c 'rg -Hn "fetch\(|axios\." {}'

# 7. page.tsx files with no Suspense reference anywhere — candidate missing streaming boundary
rg -n --files-without-match '\bSuspense\b' --glob 'page.tsx' <target-repo-root>

# 8. Multiple exported cache(async ...) wrapper definitions — verify call sites share one instance, not a local re-wrap (Pattern D)
rg -n 'export const \w+ = cache\(async' --glob '*.{ts,tsx}' <target-repo-root>

# 9. Promise.all wrapping calls to imported Server Actions from a Client Component — dispatch is sequential per client, this doesn't parallelize
rg -n -U 'Promise\.all\(\s*\[\s*\w*[Aa]ction\(' --glob '*.tsx' <target-repo-root>

# 10. fetch() calls with `next: { revalidate }` AND `cache: 'no-store'` on the same call — invalid combination, both silently ignored
rg -n -U "cache:\s*['\"]no-store['\"][^}]*revalidate|revalidate[^}]*cache:\s*['\"]no-store['\"]" --glob '*.{ts,tsx}' <target-repo-root>
```

## Domain severity rubric

- **critical**
  - Same-component sequential waterfall (Pattern A) on the primary/above-the-fold content path — blocks TTFB on every visit.
  - A Server Action performing a mutation with no auth/authz check inside the action body — Server Functions are reachable via direct POST, not just through the UI.
  - `redirect()` called before `revalidatePath()`/`revalidateTag()` in the same action — `redirect` throws a control-flow exception, silently dropping the revalidation call that follows it.
- **major**
  - No Suspense boundary around an independently slow region — the whole route blocks on the slowest query.
  - `useOptimistic` setter called outside an Action (bare event handler) — visible flash-then-revert plus a console warning.
  - Single-arg `revalidateTag(tag)` in live use — deprecated, TS-error risk, may be removed.
  - Client Component `useEffect`+`fetch` for a non-interactive read a Server Component could serve directly (Pattern C).
- **minor**
  - `useFormState` still imported with React 19 installed — functions, but is the renamed-away API.
  - `React.cache` treated as if it deduped across requests/users — a misreading, not a runtime break (it is strictly per-request).
  - Duplicate `cache()`-wrapped function instances for the same logical query (Pattern D) on a low-traffic path.
- **informational**
  - `useEffect`+`fetch` for genuinely client-only/interactive data (search-as-you-type, error beacons, analytics pings) — correct as-is.
  - SWR/TanStack layered on top of RSC-provided initial data purely for revalidate-on-focus/interval — legitimate optional client layer.
  - `Promise.allSettled` chosen over `Promise.all` deliberately, to tolerate partial failure — correct pattern, note only, not a finding.

## False-positive filters

- **A genuinely dependent fetch (child needs parent's resolved id) is NOT a fixable waterfall.** This is Pattern B — structural, not accidental. The fix is an outer Suspense/`loading.js` boundary so the shell paints, never a `Promise.all` rewrite (that call literally cannot start until the parent resolves).
- Matches inside comments or docstrings are not usage.
- Test files (`*.test.ts(x)`, `*.spec.ts(x)`, `__tests__/`) are excluded from every command above.
- **A client-side `useEffect` fetch for genuinely client-only/interactive data is legitimate** — search-as-you-type, live error/analytics beacons, anything gated on real user interaction rather than component mount. Do not flag command 2/6 matches that fit this shape.
- Wrapper components/hooks that centralize many call sites (e.g. one shared `useApiData` hook used by 20 components) collapse into one shared finding at the wrapper, not N findings at each call site.
- A deliberate `Promise.allSettled` instead of `Promise.all` is not a "missing Promise.all" finding (command 3) — partial-failure tolerance is intentional per the docs' own guidance.
- Matches inside `node_modules`, generated files, or vendored copies are not project usage.

## Evidence format — what each finding file must contain

Every finding the audit subagent writes under `findings/data-fetching-patterns/` must include:
- `file:line` (exact)
- literal matched text (copied from `rg`/`grep` output)
- which gate row or pitfall signature it maps to
- severity
- one-line why-this-matters (verbatim or near-verbatim from the corpus-derived prose above)
- suggested fix recipe section name from `references/fix/data-fetching-patterns.md`

## Pitfall signatures

| Failure signature | Cause | Fix direction | Recipe section |
|---|---|---|---|
| Two backing requests' Network timing bars are stacked with a visible gap, inside one Server Component | Pattern A — sequential `await` calls to independent data sources in the same component | Parallelize with `Promise.all` | Parallel fetching with `Promise.all` |
| Same stacked-timing-bar signature, but the second call structurally needs the first's resolved value (e.g. child needs `artist.id`) | Pattern B — genuine parent→child data dependency across nested Server Components | Not fixable with `Promise.all`. Add an outer Suspense/`loading.js` boundary so the shell paints, and optimize/cache the blocking first call | Genuine dependency chain → outer Suspense boundary |
| Requests appear only after hydration completes; Network tab "Initiator" points to client JS; each subsequent request trails the previous one's completion | Pattern C — `useEffect`-in-Client-Component fetch cascade (pre-RSC pattern surviving inside `'use client'` subtrees) | Move the data origin into a Server Component and hand a promise down via `use()`; keep client fetch only for genuinely client-driven data | `use(promise)` handoff from Server to Client Component |
| Duplicate DB/API calls despite the read being wrapped in `cache()` | Pattern D — two different `cache()`-wrapped function instances for the same logical query (each `cache()` call creates a new function; no cross-instance sharing) | Ensure every call site imports the *same* exported `cache()`-wrapped function, never re-wraps locally | `React.cache` dedup for non-fetch/ORM reads |
| "Failed to find Server Action" error on submit after a deploy | Action IDs rotate on new deployments (at most every 14 days); a stale client build invokes a removed action ID | Prefer rolling deployments; surface as a retry path in the UI, not a hard failure | (deployment concern — see `fix/vercel-platform-deployment.md`) |
| `useOptimistic` update briefly renders then reverts, with a console warning | The `set` function was called **outside** an Action (bare event handler, not `startTransition`/a form `action`) | Call the optimistic setter inside the function passed to a form/button `action` or `startTransition` | Server Action mutation with `useActionState` + `useOptimistic` |
| Rapid double-click on an optimistic control produces a wrong/stuck final value | Reading the stale prop instead of the optimistic state inside the click handler | Read from the hook's returned optimistic value, not the original prop | Server Action mutation with `useActionState` + `useOptimistic` |
| Client-side data (SWR/React Query) drifts out of sync with server-rendered content after a client refetch | Mixing an RSC-rendered value with a client library that refetches independently, no shared invalidation channel | Use Server Actions + `revalidatePath`/`updateTag` as the single source of mutation truth, or let the client library own that resource entirely | (architectural decision — see `03-when-to-use.md`; no code recipe) |
| `revalidateTag(tag)` produces a TS error or is flagged deprecated | Single-argument form no longer accepted going forward | Pass the required second argument, or use `updateTag` | Single-arg `revalidateTag` → two-arg / `updateTag` migration |
| `revalidatePath('/blog')` doesn't update a *different* page showing the same data | `revalidatePath` only invalidates the specific path/layout given; other pages sharing the underlying tag stay stale | Pair `revalidatePath` with `updateTag`/`revalidateTag` for the shared tag | Single-arg `revalidateTag` → two-arg / `updateTag` migration |
| `Promise.all([serverAction1(), serverAction2()])` called from a Client Component to "speed up" two mutations | Server Actions dispatch "one at a time per client" — this doesn't parallelize anything and can produce confusing UI-state ordering | Do the parallel work *inside* one Server Action, or use a Route Handler | (architectural anti-pattern — no dedicated recipe; flag via detection command 9) |

## Cross-domain interactions

1. If a route has an unresolved Pattern A/B waterfall finding here, withhold `rendering-strategy-caching` Cache Components tasks and `navigation-prefetching` Instant Navigation tasks for that route until the waterfall is fixed — `references/gating/priority-matrix.md`'s dependency graph places `data-fetching-patterns` before both.
2. If a `page-transitions-view-transitions` task targets a route with an unresolved waterfall or missing-Suspense finding here, that route is not cache-hot — mark the transition task `Depends on` this domain's fix, per `references/gating/conflicts.md` §1 ("View Transitions × uncached or unprefetched destinations").
3. `useOptimistic`/`useActionState` findings feed `micro-interactions-react19-fluidity`'s optimistic-UI coverage — this domain owns the Server-Action-paired wiring; that domain owns the general `useTransition`/`useDeferredValue` primitives.

## Reference pointer

Fix recipes for this domain live in `references/fix/data-fetching-patterns.md`.
