# Task: Add an API Endpoint

> Step-by-step guide for adding a new oRPC endpoint in this codebase. Consult this when creating a new server procedure and exposing it to the web app.

## File locations

1. Create a procedure in `packages/api/modules/<module>/procedures/<action>.ts`
2. Export it from that module's router
3. Wire the module router into `packages/api/orpc/router.ts` if needed
4. Consume it through `@shared/lib/orpc-query-utils` on the client

## Minimal procedure shape

```ts
export const createItem = protectedProcedure
  .route({
    method: "POST",
    path: "/items",
    tags: ["Items"],
    summary: "Create a new item",
  })
  .input(z.object({ name: z.string().min(1) }))
  .handler(async ({ input, context }) => {
    // implementation
  });
```

## Repo-grounded checklist

- Start from `publicProcedure`, `protectedProcedure`, or `adminProcedure`
- Add route metadata (`method`, `path`, `tags`, `summary`)
- Validate input with Zod
- Keep business logic inside the handler
- If a client page needs it, use `orpc.<module>.<action>.queryOptions()` or `.mutationOptions()`

## Good references in this repo

- `packages/api/modules/contact/procedures/submit-contact-form.ts`
- `packages/api/modules/payments/procedures/create-checkout-link.ts`
- `apps/web/modules/shared/lib/orpc-query-utils.ts`

---

**Related references:**
- `references/api/procedure-tiers.md` — Which procedure tier to choose
- `references/api/root-router.md` — How routers are composed
- `references/patterns/react-query-orpc.md` — Client consumption pattern
