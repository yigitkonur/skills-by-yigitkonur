# Customer IDs

> Documents how payment-provider customer IDs are persisted on users or organizations. Consult this when a portal link or checkout flow cannot find a customer, or when changing whether billing attaches to users or organizations.

## Key files

- `packages/payments/lib/customer.ts`
- `packages/database/prisma/queries/users.ts`
- `packages/database/prisma/queries/organizations.ts`

## Representative code

```ts
export async function setCustomerIdToEntity(customerId: string, { organizationId, userId }: { organizationId?: string; userId?: string }) {
  if (organizationId) {
    await updateOrganization({ id: organizationId, paymentsCustomerId: customerId });
  } else if (userId) {
    await updateUser({ id: userId, paymentsCustomerId: customerId });
  }
}

export const getCustomerIdFromEntity = async (
  props: { organizationId: string } | { userId: string },
) => {
  if ("organizationId" in props) {
    return (await getOrganizationById(props.organizationId))?.paymentsCustomerId ?? null;
  }
  return (await getUserById(props.userId))?.paymentsCustomerId ?? null;
};
```

## Implementation notes

- Organization IDs take precedence when both are present.
- Persisted customer IDs let future checkout, portal, and seat operations reuse the same provider customer.
- The storage field lives directly on `User` and `Organization` in the Prisma schema.

---

**Related references:**
- `references/payments/plans-config.md` — Billing attachment mode
- `references/database/schema-overview.md` — Where `paymentsCustomerId` lives
- `references/payments/stripe-provider.md` — Flows that consume these IDs
