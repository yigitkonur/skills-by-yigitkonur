# Pattern: React Query + oRPC

> Documents the standard client data-fetching integration. Consult this before adding a new query or mutation in client components.

## Shared utility

`apps/web/modules/shared/lib/orpc-query-utils.ts` exposes `orpc` helpers for TanStack Query.

## Query pattern

```tsx
const { data, isLoading } = useQuery(
  orpc.admin.organizations.list.queryOptions({
    input: { limit: 10, offset: 0, query: debouncedSearchTerm },
  }),
);
```

## Mutation pattern

Components typically combine `orpc` with toast feedback or query invalidation after success.

## Why this matters

This keeps procedure input/output types aligned with the server without manual fetch wrappers.

---

**Related references:**
- `references/api/client-integration.md` — Browser-side client creation
- `references/api/procedure-tiers.md` — Server procedures consumed through `orpc`
- `references/patterns/server-prefetch.md` — How prefetched data hydrates into the same cache
