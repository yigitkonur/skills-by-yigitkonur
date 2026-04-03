# Pattern: Server Prefetch

> Documents the server-prefetch + hydration flow used in the SaaS layouts. Consult this when you want client queries to render with prefetched data.

## Where it happens

The root SaaS layout prefetches session, organization list, and purchase data server-side, then wraps children in `HydrationBoundary`.

## Why it matters

This avoids immediate client waterfalls for data that every dashboard screen needs.

## Pattern summary

1. Create/query a shared query client on the server
2. Prefetch the data
3. Dehydrate the cache
4. Pass it into `HydrationBoundary`
5. Read it on the client with the same `orpc` query keys

---

**Related references:**
- `references/routing/layout-chain.md` — Provider nesting including `HydrationBoundary`
- `references/patterns/react-query-orpc.md` — Matching client-side query usage
- `references/auth/server-session-helpers.md` — Server helpers commonly prefetched
